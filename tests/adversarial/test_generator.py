"""Generator tests with injected mock LLM caller."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.generator import (
    AdversarialGenerator,
    GENERATOR_VERSION,
    GenerationResult,
    LLMCallResult,
    _parse_json_response,
)
from uofa_cli.adversarial.hash_utils import (
    HASH_FIELD,
    PROVENANCE_BLOCK_KEY,
    verify_provenance_block_hash,
)
from uofa_cli.adversarial.spec_loader import load_spec


MOCK_FIXTURE = Path(__file__).parent / "fixtures" / "mock_response.jsonld"


def _mock_caller(response_path: Path = MOCK_FIXTURE):
    """Return an llm_caller that always yields the given fixture text."""
    text = response_path.read_text()

    def caller(system, user, params):
        assert system
        assert user
        return LLMCallResult(
            text=text,
            tokens=1234,
            effective_params={
                k: v for k, v in params.items() if v is not None
            },
            call_metadata={
                "dropParamsActive": False,
                "deprecationFallbackFired": False,
                "modelReturned": params.get("model", "test"),
                "litellmVersion": "test",
            },
        )

    return caller


def test_generator_init():
    gen = AdversarialGenerator(pack="vv40")
    assert gen.pack == "vv40"
    assert callable(gen._llm)


def test_dry_run_skips_llm_call(valid_spec_path, tmp_path, capsys):
    spec = load_spec(valid_spec_path)

    def fail_caller(*a, **kw):
        pytest.fail("llm_caller should not be invoked during dry-run")

    gen = AdversarialGenerator(pack=spec.pack, llm_caller=fail_caller)
    result = gen.generate(spec, tmp_path, dry_run=True)
    assert isinstance(result, GenerationResult)
    assert result.variants_generated == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "W-AR-05" in out


def test_provenance_injected_into_package(valid_spec_path, tmp_path):
    spec = load_spec(valid_spec_path)
    gen = AdversarialGenerator(pack=spec.pack, llm_caller=_mock_caller())
    result = gen.generate(spec, tmp_path, max_shacl_retries=0)

    assert result.variants_generated == spec.n_variants
    for pkg_path in result.package_paths:
        pkg = json.loads(pkg_path.read_text())
        assert pkg["synthetic"] is True
        assert "uofa:SyntheticAdversarialSample" in pkg["type"]
        assert PROVENANCE_BLOCK_KEY in pkg
        block = pkg[PROVENANCE_BLOCK_KEY]
        assert block["targetWeakener"] == "W-AR-05"
        assert block["targetDefeaterType"] == "D3"
        assert block["specId"] == spec.spec_id
        assert block["generatorVersion"] == GENERATOR_VERSION
        assert block["promptTemplateId"].startswith("d3_undercutting_inference.")
        # v1.2 callMetadata block.
        assert "callMetadata" in block
        cm = block["callMetadata"]
        assert cm["modelRequested"] == spec.generation_model
        assert cm["litellmVersion"] == "test"
        assert cm["dropParamsActive"] is False
        assert cm["deprecationFallbackFired"] is False
        assert cm["shaclRetries"] == 0
        # modelParams reflects effective params (not hardcoded keys).
        assert "modelParams" in block
        # Hash verifies (covers callMetadata automatically).
        ok, stored, recomputed = verify_provenance_block_hash(block)
        assert ok, (stored, recomputed)


def test_manifest_written(valid_spec_path, tmp_path):
    spec = load_spec(valid_spec_path)
    gen = AdversarialGenerator(pack=spec.pack, llm_caller=_mock_caller())
    result = gen.generate(spec, tmp_path)
    assert result.manifest_path == tmp_path / "manifest.json"
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["specId"] == spec.spec_id
    assert manifest["generated"] == spec.n_variants
    assert len(manifest["variants"]) == spec.n_variants


def test_force_flag_overwrites_manifest(valid_spec_path, tmp_path):
    spec = load_spec(valid_spec_path)
    gen = AdversarialGenerator(pack=spec.pack, llm_caller=_mock_caller())
    gen.generate(spec, tmp_path)

    # Second run without --force → raises.
    with pytest.raises(FileExistsError):
        gen.generate(spec, tmp_path)

    # With force=True, succeeds.
    result = gen.generate(spec, tmp_path, force=True)
    assert result.variants_generated == spec.n_variants


def test_shacl_failure_exhausts_retries(valid_spec_path, tmp_path):
    """If the LLM response fails SHACL, generator retries up to max_shacl_retries."""
    spec = load_spec(valid_spec_path)

    # A package that is well-formed JSON but fails ProfileMinimal SHACL
    # (missing bindsRequirement).
    bad_pkg = {
        "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld",
        "id": "https://uofa.net/synth/bad",
        "type": "UnitOfAssurance",
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
    }

    call_count = {"n": 0}

    def bad_caller(system, user, params):
        call_count["n"] += 1
        return LLMCallResult(
            text=json.dumps(bad_pkg),
            tokens=100,
            effective_params={k: v for k, v in params.items() if v is not None},
            call_metadata={
                "dropParamsActive": False,
                "deprecationFallbackFired": False,
                "modelReturned": params.get("model", "test"),
                "litellmVersion": "test",
            },
        )

    gen = AdversarialGenerator(pack=spec.pack, llm_caller=bad_caller)
    result = gen.generate(spec, tmp_path, max_shacl_retries=2)
    assert result.variants_generated == 0
    assert result.variants_shacl_failed == spec.n_variants
    # Each variant: 1 initial attempt + 2 retries = 3 calls.
    assert call_count["n"] == spec.n_variants * 3
    for v in result.variants:
        assert v.shacl_passed is False
        assert v.shacl_retries == 2


def test_parse_json_response_handles_fences():
    text = "```json\n{\"a\": 1}\n```"
    assert _parse_json_response(text) == {"a": 1}


def test_parse_json_response_handles_preamble():
    text = 'Sure, here is the package:\n{"a": 1, "b": "c"}\nLet me know.'
    assert _parse_json_response(text) == {"a": 1, "b": "c"}


def test_parse_json_response_rejects_empty():
    with pytest.raises(ValueError):
        _parse_json_response("")


def test_generated_package_passes_shacl(valid_spec_path, tmp_path):
    """Integration check: generated variants must pass the same SHACL pipeline."""
    from uofa_cli import paths as cli_paths
    from uofa_cli.shacl_friendly import run_shacl_multi

    cli_paths.find_repo_root()
    spec = load_spec(valid_spec_path)
    gen = AdversarialGenerator(pack=spec.pack, llm_caller=_mock_caller())
    result = gen.generate(spec, tmp_path)
    assert result.variants_generated == spec.n_variants
    for p in result.package_paths:
        conforms, violations = run_shacl_multi(p, cli_paths.all_shacl_schemas())
        assert conforms, f"{p.name} failed SHACL: {violations}"

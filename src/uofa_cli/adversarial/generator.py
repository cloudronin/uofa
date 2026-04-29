"""Adversarial synthetic-package generator.

Filled out progressively across Hours 3-5 of the implementation plan.
Hour 3: skeleton + dry-run + provenance.
Hour 4: SHACL retry loop + manifest.
Hour 5: full CLI run_generate().
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from uofa_cli import __version__, paths
from uofa_cli.adversarial.circularity import (
    CircularityViolation,
    check_circularity,
    resolve_extract_model,
)
from uofa_cli.adversarial.hash_utils import (
    HASH_FIELD,
    PROVENANCE_BLOCK_KEY,
    compute_provenance_block_hash,
)
from uofa_cli.adversarial.model_costs import estimate_cost
from uofa_cli.adversarial.prompts import (
    get_template,
    get_template_for_spec,
    mock_response,
)
from uofa_cli.adversarial.skeleton import SkeletonLoadError, load_base_cou_skeleton
from uofa_cli.adversarial.spec_loader import (
    AdversarialSpec,
    SpecValidationError,
    VALID_SUBTLETIES,
    _resolve_base_cou,
    load_spec,
)

GENERATOR_VERSION = "0.1.0"


@dataclass
class LLMCallResult:
    """Result of one LLM call, carrying the effective params actually sent.

    ``effective_params`` reflects what was transmitted after litellm's
    drop_params behavior and any provider-side deprecation fallbacks.
    ``call_metadata`` documents observable facts about how the call
    proceeded (reproducibility-relevant).
    """

    text: str
    tokens: int
    effective_params: dict
    call_metadata: dict


LLMCaller = Callable[[str, str, dict], LLMCallResult]


@dataclass
class VariantResult:
    variant_num: int
    package_path: Path | None
    shacl_passed: bool
    shacl_retries: int
    tokens: int
    error: str | None = None


@dataclass
class GenerationResult:
    spec_id: str
    spec_path: Path
    spec_hash: str
    variants_requested: int
    variants_generated: int
    variants_shacl_failed: int
    manifest_path: Path | None
    package_paths: list[Path] = field(default_factory=list)
    total_llm_tokens_used: int = 0
    total_cost_estimate: float = 0.0
    variants: list[VariantResult] = field(default_factory=list)
    circularity_warning: str | None = None


class AdversarialGenerator:
    def __init__(
        self,
        pack: str = "vv40",
        llm_caller: LLMCaller | None = None,
        logger: logging.Logger | None = None,
    ):
        self.pack = pack
        self.logger = logger or logging.getLogger("uofa.adversarial")
        self._llm = llm_caller or _default_llm_caller
        self._skeleton_cache: dict[str, dict] | None = None

    # ── Public API ────────────────────────────────────────────

    def generate(
        self,
        spec: AdversarialSpec,
        output_dir: Path,
        *,
        max_shacl_retries: int = 3,
        dry_run: bool = False,
        force: bool = False,
    ) -> GenerationResult:
        output_dir = Path(output_dir)
        manifest_path = output_dir / "manifest.json"

        if not dry_run:
            self._check_manifest_collision(manifest_path, spec.spec_id, force)
            output_dir.mkdir(parents=True, exist_ok=True)

        skeleton = self._load_skeleton(spec)
        variants: list[VariantResult] = []
        generated_paths: list[Path] = []
        total_tokens = 0

        if dry_run:
            system_prompt, user_prompt = self._render_prompts(spec, 1, skeleton)
            print("=" * 60)
            print(f"DRY RUN — spec: {spec.spec_id} | weakener: {spec.target_weakener}")
            print("=" * 60)
            print("\n── SYSTEM PROMPT ──\n")
            print(system_prompt)
            print("\n── USER PROMPT ──\n")
            print(user_prompt)
            return GenerationResult(
                spec_id=spec.spec_id,
                spec_path=spec.spec_path,
                spec_hash=spec.spec_hash,
                variants_requested=spec.n_variants,
                variants_generated=0,
                variants_shacl_failed=0,
                manifest_path=None,
            )

        for variant_num in range(1, spec.n_variants + 1):
            result = self._attempt_variant(
                spec, variant_num, output_dir, skeleton, max_shacl_retries
            )
            variants.append(result)
            total_tokens += result.tokens
            if result.shacl_passed and result.package_path is not None:
                generated_paths.append(result.package_path)

        gen_result = GenerationResult(
            spec_id=spec.spec_id,
            spec_path=spec.spec_path,
            spec_hash=spec.spec_hash,
            variants_requested=spec.n_variants,
            variants_generated=len(generated_paths),
            variants_shacl_failed=spec.n_variants - len(generated_paths),
            manifest_path=manifest_path,
            package_paths=generated_paths,
            total_llm_tokens_used=total_tokens,
            total_cost_estimate=estimate_cost(spec.generation_model, total_tokens),
            variants=variants,
        )

        self._write_manifest(gen_result, manifest_path)
        return gen_result

    # ── Internals ─────────────────────────────────────────────

    def _load_skeleton(self, spec: AdversarialSpec) -> dict:
        if spec.mode == "narrative-only" or spec.base_cou is None:
            return {
                "identity": {},
                "context_of_use": None,
                "decision_shell": None,
                "factor_scaffold": [],
                "top_level_stamps": {},
                "context_url": "",
                "source_path": None,
            }
        if self._skeleton_cache is None:
            self._skeleton_cache = {}
        key = str(spec.base_cou)
        if key not in self._skeleton_cache:
            try:
                self._skeleton_cache[key] = load_base_cou_skeleton(
                    spec.base_cou, pack=spec.pack
                )
            except SkeletonLoadError as e:
                self.logger.warning(
                    "skeleton load failed (%s); falling back to narrative-only", e
                )
                self._skeleton_cache[key] = {
                    "identity": {},
                    "context_of_use": None,
                    "decision_shell": None,
                    "factor_scaffold": [],
                    "top_level_stamps": {},
                    "context_url": "",
                    "source_path": str(spec.base_cou),
                }
        return self._skeleton_cache[key]

    def _render_prompts(
        self, spec: AdversarialSpec, variant_num: int, skeleton: dict
    ) -> tuple[str, str]:
        template = get_template_for_spec(spec)
        return template.render(spec, skeleton)

    def _attempt_variant(
        self,
        spec: AdversarialSpec,
        variant_num: int,
        output_dir: Path,
        skeleton: dict,
        max_retries: int,
    ) -> VariantResult:
        from uofa_cli.shacl_friendly import run_shacl_multi

        system_prompt, user_prompt = self._render_prompts(spec, variant_num, skeleton)
        attempt = 0
        last_error: str | None = None
        tokens_total = 0
        prior_violations: list[dict] = []

        variant_id = spec.package_name_template.format(
            spec_id=spec.spec_id, variant_num=variant_num
        )
        target_path = output_dir / f"{variant_id}.jsonld"
        failed_dir = output_dir / "failed"

        prior_pkg: dict | None = None  # last-attempt parsed package, for retry context
        while attempt <= max_retries:
            attempt += 1
            retry_prompt = user_prompt
            if prior_violations:
                # Phase 2.5 v0.5.15: enhanced retry feedback. Include a
                # truncated snippet of the LLM's prior output so it can
                # diff against its own work instead of regenerating from
                # scratch. Pre-v0.5.15 only the violation list was echoed,
                # which left the LLM guessing at which fields it had
                # already emitted vs which were missing.
                prior_pkg_snippet = ""
                if isinstance(prior_pkg, dict):
                    pkg_text = json.dumps(prior_pkg, indent=1, ensure_ascii=False)
                    prior_pkg_snippet = (
                        "\n\nYour previous output (truncated to 800 chars):\n"
                        + pkg_text[:800]
                        + ("..." if len(pkg_text) > 800 else "")
                    )
                retry_prompt = user_prompt + (
                    "\n\nPrevious attempt failed SHACL validation. Fix the "
                    "violations below and re-emit the package. Other fields "
                    "can remain unchanged."
                    + prior_pkg_snippet
                    + "\n\nViolations to fix:\n"
                    + json.dumps(prior_violations, indent=2)
                )

            try:
                call = self._llm(
                    system_prompt,
                    retry_prompt,
                    {
                        "model": spec.generation_model,
                        "temperature": spec.temperature,
                        "max_tokens": spec.max_tokens,
                        "seed": spec.seed,
                        "context_url": skeleton.get("context_url", ""),
                    },
                )
            except Exception as e:
                last_error = f"LLM call failed: {e}"
                self.logger.warning("variant %d attempt %d: %s", variant_num, attempt, last_error)
                break

            tokens_total += call.tokens

            try:
                pkg = _parse_json_response(call.text)
            except ValueError as e:
                last_error = f"unparseable JSON response: {e}"
                self.logger.warning(
                    "variant %d attempt %d: %s", variant_num, attempt, last_error
                )
                prior_violations = [{"path": "response", "message": last_error}]
                continue

            pkg = self._inject_provenance(
                pkg,
                spec,
                variant_num,
                effective_params=call.effective_params,
                call_metadata=call.call_metadata,
                shacl_retries=attempt - 1,
                model_requested=spec.generation_model,
                tokens=call.tokens,
            )
            pkg = self._merge_stamps(pkg, skeleton.get("top_level_stamps", {}))

            # Phase 2.5 post-LLM mutation hooks for NC specs.
            #
            # Each hook fixes a specific corpus-quality gap that the LLM
            # would otherwise produce (because the rule's noValue check
            # would fire on a structurally-omitted field). Hooks run
            # AFTER the LLM responds and BEFORE SHACL validation, so a
            # fresh-generated NC ships clean without separate patch-tool
            # post-processing.
            #
            # CE / gap-probe / interaction templates intentionally SKIP
            # all of these — preserving the rule's correct firing on
            # confirm_existing target packages.
            #
            # Phase 2 v2 will replace these hooks with prompt-template
            # improvements (have the LLM emit substantively-meaningful
            # content instead of placeholder stubs). See
            # `out/phase2_5/2026-04-27/v0512_phase2v2_prompt_proposal.md`.
            if spec.coverage_intent == "negative_control":
                # All three helpers are imported from the same module
                # in src/uofa_cli/, so the installed wheel ships them.
                # (Phase 2.5 v0.5.12.1: prior to this release the
                # offset-rationale helper lived under tools/phase2_5/
                # which silently broke post-install — `uofa adversarial
                # generate` would throw ModuleNotFoundError on every NC
                # spec. The PYTHONPATH-set test suite hid the bug.)
                from uofa_cli.adversarial.skeleton import (
                    _augment_cou_with_envelope_stubs,
                    _augment_dr_with_offset_rationale,
                    _augment_uofa_with_sensitivity_analysis_stub,
                )

                # v0.5.10 (re-wired in v0.5.12.1): envelope stubs on COU.
                # Fixes W-ON-02 (noValue on hasApplicabilityConstraint /
                # hasOperatingEnvelope). Was previously pre-LLM only —
                # relied on the LLM faithfully copying the augmented COU.
                # Post-LLM is the safety net.
                cou = pkg.get("hasContextOfUse")
                if isinstance(cou, dict):
                    _augment_cou_with_envelope_stubs(cou)

                # v0.5.11: offset rationale on Accepted decisions whose
                # factors have achievedLevel < requiredLevel. Fixes
                # W-AR-02 (vacuous-noValue on hasOffsetRationale).
                pkg, _ = _augment_dr_with_offset_rationale(pkg)

                # v0.5.12 (re-wired in v0.5.12.1): SensitivityAnalysis
                # stub on Complete-profile UofAs. Fixes W-CON-04
                # (noValue on hasSensitivityAnalysis). Was previously
                # text-hint-only in extra_schema_rules — relied on the
                # LLM following the schema-rule nudge. Post-LLM is the
                # safety net.
                _augment_uofa_with_sensitivity_analysis_stub(pkg)

            # Write to a temp path for SHACL validation.
            candidate_path = target_path if attempt == 1 else failed_dir / f"{variant_id}-attempt{attempt}.jsonld"
            candidate_path.parent.mkdir(parents=True, exist_ok=True)
            candidate_path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False))

            try:
                conforms, violations = run_shacl_multi(
                    candidate_path, paths.all_shacl_schemas()
                )
            except Exception as e:
                last_error = f"SHACL run failed: {e}"
                self.logger.warning("variant %d attempt %d: %s", variant_num, attempt, last_error)
                conforms, violations = False, []

            if conforms:
                # Move/copy to target path if we wrote to a failed path on retry.
                if candidate_path != target_path:
                    target_path.write_text(candidate_path.read_text())
                return VariantResult(
                    variant_num=variant_num,
                    package_path=target_path,
                    shacl_passed=True,
                    shacl_retries=attempt - 1,
                    tokens=tokens_total,
                )

            prior_violations = violations
            prior_pkg = pkg  # v0.5.15: keep prior pkg for retry-feedback snippet
            last_error = f"SHACL violations: {len(violations)}"

        # All attempts exhausted.
        return VariantResult(
            variant_num=variant_num,
            package_path=None,
            shacl_passed=False,
            shacl_retries=attempt - 1,
            tokens=tokens_total,
            error=last_error,
        )

    def _inject_provenance(
        self,
        pkg: dict,
        spec: AdversarialSpec,
        variant_num: int,
        effective_params: dict,
        call_metadata: dict,
        shacl_retries: int,
        model_requested: str,
        tokens: int,
    ) -> dict:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # modelParams now reflects what was actually sent (post drop_params
        # and deprecation fallback), NOT the spec-requested values. Exclude
        # transport-level keys like `model` and `messages`.
        model_params = {
            k: v for k, v in effective_params.items()
            if k not in {"model", "messages"}
        }

        block = {
            "generatorVersion": GENERATOR_VERSION,
            "toolVersion": f"uofa-cli {__version__}",
            "promptTemplateVersion": get_template_for_spec(spec).PROMPT_VERSION,
            "promptTemplateId": spec.prompt_template_id(),
            "specId": spec.spec_id,
            "specPath": str(spec.spec_path),
            "specHash": f"sha256:{spec.spec_hash}",
            "generationModel": effective_params.get("model", model_requested),
            "modelParams": model_params,
            "callMetadata": {
                "dropParamsActive":         call_metadata.get("dropParamsActive", False),
                "deprecationFallbackFired": call_metadata.get("deprecationFallbackFired", False),
                "shaclRetries":             shacl_retries,
                "modelRequested":           model_requested,
                "modelReturned":            call_metadata.get("modelReturned"),
                "litellmVersion":           call_metadata.get("litellmVersion"),
            },
            "generationTimestamp": timestamp,
            "targetWeakener": spec.target_weakener,
            "targetDefeaterType": spec.defeater_type,
            "coverageIntent": spec.coverage_intent,
            "sourceTaxonomy": spec.source_taxonomy,
            "subtletyLevel": spec.subtlety,
            "tokens": tokens,
            "variantNum": variant_num,
        }
        block[HASH_FIELD] = f"sha256:{compute_provenance_block_hash(block)}"
        pkg[PROVENANCE_BLOCK_KEY] = block
        pkg["synthetic"] = True

        # Ensure the type array includes the synthetic marker.
        t = pkg.get("type") or pkg.get("@type")
        if isinstance(t, str):
            t = [t]
        if not t:
            t = ["UnitOfAssurance"]
        if "uofa:SyntheticAdversarialSample" not in t:
            t = [*t, "uofa:SyntheticAdversarialSample"]
        pkg["type"] = t
        pkg.pop("@type", None)
        return pkg

    def _merge_stamps(self, pkg: dict, stamps: dict) -> dict:
        for k, v in stamps.items():
            pkg.setdefault(k, v)
        return pkg

    def _write_manifest(self, result: GenerationResult, manifest_path: Path) -> None:
        manifest = {
            "specId": result.spec_id,
            "specPath": str(result.spec_path),
            "specHash": f"sha256:{result.spec_hash}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generatorVersion": GENERATOR_VERSION,
            "toolVersion": f"uofa-cli {__version__}",
            "requested": result.variants_requested,
            "generated": result.variants_generated,
            "shaclFailed": result.variants_shacl_failed,
            "totalTokens": result.total_llm_tokens_used,
            "estimatedCostUsd": round(result.total_cost_estimate, 4),
            "circularityWarning": result.circularity_warning,
            "variants": [
                {
                    "variantNum": v.variant_num,
                    "packagePath": str(v.package_path.name) if v.package_path else None,
                    "shaclPassed": v.shacl_passed,
                    "shaclRetries": v.shacl_retries,
                    "tokens": v.tokens,
                    "error": v.error,
                }
                for v in result.variants
            ],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    def _check_manifest_collision(
        self, manifest_path: Path, spec_id: str, force: bool
    ) -> None:
        if not manifest_path.exists():
            return
        if force:
            return
        try:
            existing = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            return
        if existing.get("specId") == spec_id:
            raise FileExistsError(
                f"manifest.json already exists for spec {spec_id!r} in "
                f"{manifest_path.parent}. Pass --force to overwrite."
            )


# ── Default LLM caller (mock / ollama / litellm) ─────────────


def _default_llm_caller(system_prompt: str, user_prompt: str, params: dict) -> LLMCallResult:
    """Dispatch by ``params['model']`` to mock / ollama HTTP / litellm.

    Any model id starting with ``mock`` (``mock``, ``mock-haiku``,
    ``mock-sonnet`` etc.) routes to the mock fixture path. Phase 2 §7.7
    tests use the prefixed forms to exercise multi-model fan-out without
    real API calls.
    """
    model = params["model"]
    if model == "mock" or model.startswith("mock-"):
        return LLMCallResult(
            text=mock_response(params),
            tokens=0,
            effective_params=dict(params),
            call_metadata={
                "dropParamsActive": False,
                "deprecationFallbackFired": False,
                "modelReturned": model,
                "litellmVersion": "n/a",
            },
        )
    if model.startswith("ollama/"):
        return _call_ollama(system_prompt, user_prompt, params)
    return _call_litellm(system_prompt, user_prompt, params)


def _call_ollama(system_prompt: str, user_prompt: str, params: dict) -> LLMCallResult:
    import requests

    model_name = params["model"].replace("ollama/", "", 1)
    resp = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": params.get("temperature", 0.7),
                "num_predict": params.get("max_tokens", 4000),
            },
        },
        timeout=1800,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data.get("message", {}).get("content", "")
    tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

    # Ollama honors temperature/max_tokens/seed. All spec params survive.
    effective_params = {k: v for k, v in params.items() if v is not None}
    return LLMCallResult(
        text=content,
        tokens=tokens,
        effective_params=effective_params,
        call_metadata={
            "dropParamsActive": False,
            "deprecationFallbackFired": False,
            "modelReturned": params["model"],
            "litellmVersion": "n/a",
        },
    )


def _call_litellm(system_prompt: str, user_prompt: str, params: dict) -> LLMCallResult:
    """Call the LLM via litellm. Phase 2.5 v0.5.15: switched from
    free-form text generation to tool-calling (Anthropic ``tool_use`` /
    OpenAI function-calling, mediated by litellm).

    Tool-calling enforces JSON-Schema constraints at the SDK boundary
    so:

    * Malformed JSON failures (~5% on free-form) → 0%
    * Schema-required field omissions → blocked before reaching us
    * The LLM's submitted package arrives as a parsed dict via
      ``response.choices[0].message.tool_calls[0].function.arguments``

    Free-form fallback is retained for non-Anthropic models that don't
    support tool_use (e.g., earlier OpenAI Davinci, some Llama variants).
    The fallback also kicks in if the LLM refuses to call the tool
    (returns a plain text response despite ``tool_choice`` being set).

    Phase 2 v3 v0.5.15 finding: Anthropic's tool-input-schema validator
    rejects property keys that don't match ``^[a-zA-Z0-9_.-]{1,64}$``,
    excluding JSON-LD ``@context``. We omit ``@context`` from the tool
    schema and inject it post-tool-call from
    ``params['context_url']`` (or ``CONTEXT_URL`` fallback).
    """
    import litellm

    from uofa_cli.adversarial.tool_schema import UOFA_TOOL, UOFA_TOOL_CHOICE
    from uofa_cli.excel_constants import CONTEXT_URL

    # Drop provider-unsupported params silently (e.g. Anthropic rejects `seed`).
    litellm.drop_params = True

    model = params["model"]
    is_anthropic = "claude" in model.lower() or "anthropic" in model.lower()
    use_tool_calling = is_anthropic or "gpt" in model.lower()  # both support function calling

    # Start from the spec params; we'll mutate as drop_params / fallback apply.
    effective_params: dict = {"model": model}
    if params.get("max_tokens") is not None:
        effective_params["max_tokens"] = params["max_tokens"]
    if params.get("seed") is not None and not is_anthropic:
        # Anthropic's API does not accept `seed`; litellm drops it when
        # drop_params is True. Reflect that in the effective params.
        effective_params["seed"] = params["seed"]
    if params.get("temperature") is not None:
        effective_params["temperature"] = params["temperature"]
    if use_tool_calling:
        effective_params["tool"] = UOFA_TOOL["function"]["name"]

    base_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": params.get("max_tokens", 4000),
        "timeout": 1800,
    }
    if use_tool_calling:
        base_kwargs["tools"] = [UOFA_TOOL]
        base_kwargs["tool_choice"] = UOFA_TOOL_CHOICE

    seed = params.get("seed")
    if seed is not None:
        base_kwargs["seed"] = seed  # litellm strips for Anthropic with drop_params=True.

    # Newer Claude Opus/Sonnet models (4.7+) deprecated `temperature` — attempt
    # with it, fall back gracefully if the provider rejects it.
    temperature = params.get("temperature", 0.7)
    deprecation_fallback_fired = False
    try:
        response = litellm.completion(**base_kwargs, temperature=temperature)
    except litellm.BadRequestError as e:
        msg = str(e).lower()
        if "temperature" in msg and "deprecated" in msg:
            deprecation_fallback_fired = True
            effective_params.pop("temperature", None)
            response = litellm.completion(**base_kwargs)
        else:
            raise

    msg = response.choices[0].message
    content = msg.content or ""
    tool_used = False

    # Tool-call extraction path (preferred when use_tool_calling).
    if use_tool_calling:
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            first = tool_calls[0]
            if hasattr(first, "function"):
                args_str = first.function.arguments
            elif isinstance(first, dict):
                args_str = first.get("function", {}).get("arguments", "{}")
            else:
                args_str = "{}"
            try:
                pkg = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                pkg = None

            if isinstance(pkg, dict):
                # Inject @context (omitted from schema due to Anthropic
                # property-key regex; see tool_schema.py docstring).
                ctx_url = params.get("context_url") or CONTEXT_URL
                pkg.setdefault("@context", ctx_url)
                content = json.dumps(pkg, ensure_ascii=False)
                tool_used = True

    # Fallback to free-form text content if tool-calling didn't yield a
    # parseable result (defensive: e.g., LLM refuses tool, network glitch).

    tokens = 0
    usage = getattr(response, "usage", None)
    if usage:
        tokens = getattr(usage, "total_tokens", 0) or 0

    model_returned = getattr(response, "model", None) or model
    litellm_version = _litellm_version()

    return LLMCallResult(
        text=content,
        tokens=tokens,
        effective_params=effective_params,
        call_metadata={
            "dropParamsActive": bool(litellm.drop_params),
            "deprecationFallbackFired": deprecation_fallback_fired,
            "modelReturned": model_returned,
            "litellmVersion": litellm_version,
            "toolCallingUsed": tool_used,
        },
    )


def _litellm_version() -> str:
    """Resolve the installed litellm version via importlib.metadata.

    litellm's package does not expose ``__version__``; the canonical source
    is the distribution metadata. Falls back to "unknown" on any failure.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version("litellm")
    except Exception:
        return "unknown"


def _parse_json_response(text: str) -> dict:
    """Parse a JSON response, tolerating optional markdown code fences."""
    text = (text or "").strip()
    if not text:
        raise ValueError("empty response")
    if text.startswith("```"):
        # Strip the opening fence (```json or ```)
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Best-effort brace-matching to find a JSON object.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                pass
        raise ValueError(f"JSON decode error: {e}") from e


# ── CLI entry ────────────────────────────────────────────────


def run_generate(args) -> int:
    """Top-level entry for ``uofa adversarial generate``. Returns exit code."""
    from uofa_cli.output import error, info, result_line, warn

    try:
        spec = load_spec(args.spec)
    except SpecValidationError as e:
        error(f"spec validation failed: {e}")
        return 3
    except FileNotFoundError as e:
        error(str(e))
        return 3

    gen_model = args.model or spec.generation_model
    extract_model = resolve_extract_model()
    circ = check_circularity(
        gen_model,
        extract_model,
        strict=bool(getattr(args, "strict_circularity", False)),
        allow_circular=bool(getattr(args, "allow_circular_model", False)),
        explicit_override=bool(args.model),
    )
    if circ.warning:
        warn(circ.warning)
    if circ.exit_code != 0:
        return circ.exit_code

    # Apply the effective model to the spec in-place for downstream uses.
    if args.model:
        spec.generation_model = args.model

    # Apply runner fan-out overrides (Phase 2 v1.8 §3): when set, replace
    # the spec's declared subtlety / base_cou for this run only. Validation
    # mirrors spec_loader (subtlety is enum; base_cou is resolved against
    # the repo). Module-level imports avoid Python's local-variable
    # shadowing footgun on the SpecValidationError except clause above.
    subtlety_override = getattr(args, "subtlety_override", None)
    if subtlety_override:
        if subtlety_override not in VALID_SUBTLETIES:
            error(
                f"--subtlety-override has invalid value {subtlety_override!r}; "
                f"allowed: {sorted(VALID_SUBTLETIES)}"
            )
            return 3
        spec.subtlety = subtlety_override

    base_cou_override = getattr(args, "base_cou_override", None)
    if base_cou_override:
        try:
            spec.base_cou = _resolve_base_cou(base_cou_override)
        except SpecValidationError as e:
            error(f"--base-cou-override resolution failed: {e}")
            return 3

    generator = AdversarialGenerator(pack=spec.pack, llm_caller=_default_llm_caller)

    dry_run = bool(getattr(args, "dry_run", False))
    try:
        result = generator.generate(
            spec,
            Path(args.out),
            max_shacl_retries=int(getattr(args, "max_retries", 3)),
            dry_run=dry_run,
            force=bool(getattr(args, "force", False)),
        )
    except FileExistsError as e:
        error(str(e))
        return 2
    except CircularityViolation as e:
        error(str(e))
        return 4
    except Exception as e:  # noqa: BLE001 — surface any runtime failure
        error(f"generation failed: {e}")
        if getattr(args, "verbose", False):
            raise
        return 2

    if dry_run:
        return 0

    result.circularity_warning = circ.warning
    if result.manifest_path is not None:
        # Rewrite manifest to capture the circularity warning line.
        generator._write_manifest(result, result.manifest_path)

    result_line(
        f"adversarial generate — {result.variants_generated}/{result.variants_requested} variants passed SHACL",
        result.variants_generated > 0,
    )
    if result.manifest_path:
        info(f"manifest: {result.manifest_path}")
    if result.total_llm_tokens_used:
        info(
            f"tokens: {result.total_llm_tokens_used:,} | "
            f"est. cost: ${result.total_cost_estimate:.4f}"
        )

    if result.variants_generated == 0:
        return 2
    if result.variants_generated < result.variants_requested:
        return 1
    return 0

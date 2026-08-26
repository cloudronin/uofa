"""In-process pipeline: drives uofa extract -> import-mapping -> check.

The Space never shells out to the CLI; it reuses the same functions the CLI
wraps. The one piece of new logic is `result_to_import_dict`, a thin adapter
from the extractor's `ExtractionResult` to the intermediate dict shape that
`excel_mapper.map_to_jsonld` consumes (the Excel round-trip is deliberately
skipped - it is fragile and lossy).

`analyze()` is the orchestration spine. It guarantees:
  * extraction runs in a child process with a hard wall-clock timeout, and a
    timed-out child is terminated (a hung Ollama call can't hold the slot);
  * every failure mode returns a typed `PipelineOutcome.failure(...)` rather
    than raising past the boundary;
  * the per-request temp dir and the extractor's /tmp debug file are torn down
    in `finally`, even on timeout/kill/exception.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import shutil
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from uofa_cli import paths
from uofa_cli.card_bundle import (
    MODEL_CREDIBILITY_RISK_ASSUMPTION,
    assign_factor_ids as _assign_factor_ids,
    result_to_import_dict,
    unwrap_fields as _unwrap,
    unwrap_value as _v,
)
from uofa_cli.document_reader import ExtractionCorpus, discover_files, read_corpus
from uofa_cli.excel_mapper import map_to_jsonld
from uofa_cli.llm.config import BUNDLED_MODEL
from uofa_cli.llm_extractor import extract as _real_extract

from space import solver_panel
from space import summary as summary_mod

# The extractor writes its raw response here for debugging - a content leak we
# must scrub on every request (see _save_debug_response in llm_extractor.py).
DEBUG_RESPONSE_FILE = Path("/tmp/uofa-extract-last-response.json")

# 12 min: above the ~7-min typical extract, below Ollama's 30-min default.
DEFAULT_EXTRACT_TIMEOUT = 720

# A pubkey path that does not exist, so check skips C1 integrity cleanly
# (the public Space never signs). Using the repo's real key would make
# run_structured attempt signature verification on an unsigned doc.
_NO_PUBKEY = Path("/nonexistent/uofa-space-unsigned.pub")


# ── Typed outcome ─────────────────────────────────────────────


class WeakenerEngineError(RuntimeError):
    """The Jena engine ran but aborted (e.g. a malformed literal) instead of
    emitting a valid JSON-LD result - distinct from the engine being absent."""


class FailureKind:
    EMPTY_FACTORS = "empty_factors"
    EXTRACT_TIMEOUT = "extract_timeout"
    READ_ERROR = "read_error"
    ROUTE_ERROR = "route_error"
    EXTRACT_ERROR = "extract_error"
    VALIDATE_ERROR = "validate_error"
    WEAKENER_ERROR = "weakener_error"
    NO_BACKEND = "no_backend"
    INTERNAL = "internal"


_USER_MESSAGES = {
    FailureKind.EMPTY_FACTORS: (
        "We couldn't read recognizable credibility factors from these "
        "documents. Check they're the right evidence, or try the sample."
    ),
    FailureKind.EXTRACT_TIMEOUT: (
        "Analysis took too long and was stopped. Try fewer or smaller "
        "documents, or retry."
    ),
    FailureKind.READ_ERROR: (
        "We couldn't read the uploaded documents. Check the file types and "
        "try again."
    ),
    FailureKind.ROUTE_ERROR: (
        "We couldn't determine which standard applies. Please pick one and "
        "retry."
    ),
    FailureKind.EXTRACT_ERROR: (
        "Something went wrong while reading your evidence. Please retry."
    ),
    FailureKind.VALIDATE_ERROR: (
        "We couldn't assemble a valid assurance bundle from the extraction. "
        "Please retry."
    ),
    FailureKind.WEAKENER_ERROR: (
        "The weakener analysis didn't complete on this bundle. Please retry."
    ),
    FailureKind.NO_BACKEND: (
        "This Space has no model backend configured, so it cannot read "
        "evidence. If you duplicated it, add your own API key under "
        "Settings -> Variables and secrets, or set UOFA_SPACE_MODEL=mock to "
        "explore the interface with canned data."
    ),
    FailureKind.INTERNAL: "Something went wrong. Please retry, or use the sample.",
}


@dataclass
class PipelineOutcome:
    ok: bool
    payload: dict | None = None
    kind: str | None = None
    user_message: str | None = None

    @classmethod
    def success(cls, payload: dict) -> "PipelineOutcome":
        return cls(ok=True, payload=payload)

    @classmethod
    def failure(cls, kind: str, message: str | None = None) -> "PipelineOutcome":
        return cls(
            ok=False,
            kind=kind,
            user_message=message or _USER_MESSAGES.get(kind, _USER_MESSAGES[FailureKind.INTERNAL]),
        )


# ── Subprocess-isolated extraction with a hard timeout ───────


def _silence_llm_logging() -> None:
    """Best-effort: stop litellm from echoing prompts/responses (which contain
    evidence content). Called in the extract child before any model call."""
    try:
        import litellm

        litellm.turn_off_message_logging = True
        litellm.suppress_debug_info = True
    except Exception:
        pass


def _extract_worker(q, extract_fn, corpus, model, pack, prompt_path, llm_config):
    _silence_llm_logging()
    try:
        result = extract_fn(
            corpus,
            model=model,
            pack_name=pack,
            pack_prompt_path=prompt_path,
            thinking=False,
            llm_config=llm_config,
        )
        q.put(("ok", result))
    except BaseException as exc:  # report any failure back to the parent
        q.put(("err", f"{type(exc).__name__}: {exc}"))


def _run_extract(corpus, model, pack, prompt_path, llm_config, timeout, extract_fn):
    """Run extract() in a child process; terminate it if it outlives `timeout`.

    Returns ("ok", ExtractionResult) | ("err", msg) | ("timeout", None).
    ExtractionResult is small (KBs) so the queue put never blocks the child.
    """
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    proc = ctx.Process(
        target=_extract_worker,
        args=(q, extract_fn, corpus, model, pack, prompt_path, llm_config),
    )
    proc.start()
    proc.join(timeout)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        if proc.is_alive():
            proc.kill()
        return ("timeout", None)
    try:
        return q.get_nowait()
    except Exception:
        return ("err", "extraction produced no result")


def extraction_label(llm_config=None) -> str:
    """How the evidence was read, for the reviewer readout and the payload.

    Rendered as "How assessed:". The upload path never set this, so the one
    flow that sends the user's OWN documents somewhere was the one that did not
    record where they went.
    """
    from space import llm_env

    if llm_config is None:
        return f"LLM extraction - {BUNDLED_MODEL} (local, in this Space)"
    return f"LLM extraction - {llm_env.provider_label(llm_config)}"


def _effective_model(model: str | None, llm_config=None) -> str:
    """The model that will actually run, for labels and provenance.

    `model or BUNDLED_MODEL` reported qwen3.5:4b while the call went to a hosted
    provider. That string reaches the reviewer readout as "How assessed:", so a
    stale default there is a false statement about how the evidence was read.
    """
    if model:
        return model
    if llm_config is not None:
        return llm_config.model
    return BUNDLED_MODEL


def _reading_message(llm_config=None) -> str:
    """In-flight copy, which must not promise privacy it is not providing.

    The local path reads documents inside this container and nothing leaves.
    The hosted path sends them to a third party, and saying "privately" there
    would be false at the exact moment the user is waiting on the request.
    """
    if llm_config is None:
        return ("Analyzing your evidence with the model. This runs privately in "
                "this Space and can take a few minutes...")
    from space import llm_env
    return (f"Analyzing your evidence with {llm_env.provider_label(llm_config)}. "
            "Your documents are sent there to be read, then discarded.")


def _prompt_path_for(pack: str) -> Path:
    """One definition, shared with the CLI.

    This used to resolve the pack directory and read its manifest here -- the
    correct logic, written out a second time. That duplication is why the CLI's
    routing bug survived: `paths.extract_prompt()` took no pack name and
    returned the V&V 40 prompt for every pack, so every NASA extraction through
    `uofa extract` asked for 13 V&V 40 factors. The Space was unaffected because
    it had its own copy, and nothing compared the two.

    A correct duplicate does not protect the codebase; it hides the broken
    original. Same shape as the two sentence segmenters found the same
    afternoon. See studies/nasa-prompt-routing/FINDINGS.md.
    """
    return paths.extract_prompt(pack)


def _has_usable_factors(result) -> bool:
    return bool(result.credibility_factors) and any(
        _v(f.get("factor_type")) for f in result.credibility_factors
    )


# ── Validation (SHACL + weakeners) ──────────────────────────


def _run_check(jsonld_path: Path, pack: str, pubkey: Path = _NO_PUBKEY):
    """Run SHACL (C2) + integrity (C1, skipped unsigned). Returns (conforms, violations).

    skip_rules=True: weakeners come from the dedicated jsonld pass below, so
    the check step needs no Java and never double-runs the rule engine.

    `pubkey` defaults to the nonexistent path that makes C1 skip cleanly. The
    signing path passes the real demo pubkey to re-check the package AFTER
    signing, so the Space validates the exact artifact it hands out.
    """
    from uofa_cli.commands import check as check_cmd

    args = argparse.Namespace(
        file=jsonld_path,
        pubkey=pubkey,
        context=None,
        rules=None,
        skip_rules=True,
        build=False,
        active_packs=[pack],
        enable_oos=False,
        disable_oos=False,
        enable_derivations=False,
        disable_derivations=False,
    )
    cr = check_cmd.run_structured(args)
    return cr.shacl.conforms, list(cr.shacl.violations)


def _run_weakeners(jsonld_path: Path, pack: str) -> list[dict]:
    """Rich weakener firings via the Jena engine in jsonld mode.

    Degrades to [] only when Java/JAR are *absent* (the headline still shows
    completeness; weakeners are best-effort where the jar isn't installed).

    A non-zero return code does NOT imply failure - the engine also exits
    non-zero when it successfully *detects* weakeners. The reliable signal that
    the engine aborted (e.g. a DatatypeFormatException on a malformed literal)
    is that stdout is not a valid JSON-LD document; a successful run always
    emits one with an `@graph`, even when zero weakeners fired. An abort raises
    WeakenerEngineError rather than silently reporting "no weakeners".
    """
    from uofa_cli.commands import rules as rules_mod

    args = argparse.Namespace(
        file=jsonld_path,
        rules=None,
        context=None,
        build=False,
        raw=False,
        format="jsonld",
        output=None,
        active_packs=[pack],
    )
    try:
        rr = rules_mod.run_structured(args)
    except (FileNotFoundError, RuntimeError):
        return []  # engine genuinely unavailable - degrade, don't fail

    stdout = rr.raw_stdout or ""
    try:
        doc = json.loads(stdout)
        valid = isinstance(doc, dict) and isinstance(doc.get("@graph"), list)
    except json.JSONDecodeError:
        valid = False
    if not valid:
        stderr_head = (rr.raw_stderr or "").strip().splitlines()
        detail = stderr_head[-1] if stderr_head else "no JSON-LD output"
        raise WeakenerEngineError(
            f"weakener engine aborted (rc={rr.returncode}): {detail}"
        )

    return rules_mod.parse_firings_jsonld(stdout)


_PACK_DISPLAY = {"vv40": "ASME V&V 40", "nasa-7009b": "NASA-STD-7009B", "model-credibility": "NIST AI RMF"}


SIGNER_LABEL = "UofA issuer (keys/uofa-issuer.pub)"

# Who produced the artifact, for prov:wasAttributedTo.
#
# `excel_mapper._operator_identity()` resolves UOFA_ASSESSOR -> `git config
# user.name` -> $USER, and correctly returns None when none of those identify
# anyone: inventing a name would be worse than omitting the field. In this
# container none of them resolve, so packages came out with wasAttributedTo
# missing and failed C2 on a field the CLI populates from the operator's git
# config. Same input, different document, purely because of the environment.
#
# It is also incoherent with signing: the package is signed by the demo issuer
# while declining to say who produced it, when the signature already asserts
# exactly that. PROV-O's agent may be "a piece of software", and here it is one.
#
# Set as a default, so a deployment that knows its operator can still override.
ASSESSOR_LABEL = "UofA Credibility Inspector (demo)"
os.environ.setdefault("UOFA_ASSESSOR", ASSESSOR_LABEL)

_UNSIGNED_STATEMENT = (
    "This evidence was assessed in an unsigned demo, so identity and "
    "tamper-evidence were not verified. A formally issued assurance "
    "package would carry a content hash and a cryptographic signature, "
    "shown here for a reviewer (or a technical colleague) to re-verify."
)

_SIGNED_STATEMENT = (
    "This package was signed by the UofA demonstration issuer key, not by a "
    "research or production key. A valid signature means only that the file is "
    "unmodified since this demo produced it. It is not a review, and it is not "
    "an acceptance decision: the credibility judgment stays with the reader."
)


def _authenticity_block(*, signed: bool = False, package_hash: str | None = None,
                        signer: str | None = None, integrity_checked: bool = False) -> dict:
    """What the reader may conclude about identity and tamper-evidence.

    Defaults to the unsigned demo statement, so callers that never sign (the
    CLI report path, any failure branch) keep today's behaviour with no
    argument. The signed branch names the key as a *demonstration* issuer,
    because a signature that reads as endorsement is a worse claim than no
    signature at all. The reviewer view branches on `signed`.
    """
    if not signed:
        return {
            "signed": False,
            "integrity_checked": False,
            "package_hash": None,
            "signer": None,
            "statement": _UNSIGNED_STATEMENT,
        }
    return {
        "signed": True,
        "integrity_checked": integrity_checked,
        "package_hash": package_hash,
        "signer": signer or SIGNER_LABEL,
        "statement": _SIGNED_STATEMENT,
    }


def _build_context(summary: dict, pack: str, authenticity: dict | None = None,
                   extraction_provenance: str | None = None) -> dict:
    """Reviewer-facing context, re-projected from already-extracted fields.

    `extraction_provenance` is rendered as "How assessed:" and is the
    machine-readable half of the disclosure: prose on the upload page tells the
    user where their documents go, this puts it in the payload and the readout,
    where a reviewer reading the output later can still see it. Only the card
    path set it before, so the upload path -- the one that sends the user's own
    documents -- was the one saying nothing.
    """
    ctx = {
        "project_name": summary.get("project_name"),
        "cou_name": summary.get("cou_name"),
        "cou_description": summary.get("cou_description"),
        "standard": _PACK_DISPLAY.get(pack, pack),
        "pack": pack,
        "model_risk_level": summary.get("model_risk_level"),
        "device_class": summary.get("device_class"),
        "assurance_level": summary.get("assurance_level"),
        "standards_reference": summary.get("standards_reference"),
        "authenticity": authenticity or _authenticity_block(),
    }
    if extraction_provenance:
        ctx["extraction_provenance"] = extraction_provenance
    if pack == "model-credibility":
        ctx["risk_assumption"] = MODEL_CREDIBILITY_RISK_ASSUMPTION
    return ctx


def _build_payload(pack, data, shacl_conforms, shacl_violations, firings, warnings,
                   doc=None, authenticity=None, extraction_provenance=None) -> dict:
    """Assemble the reviewer payload.

    `doc` is the JSON-LD bundle. It is passed so this supplies compute_findings
    with the SAME inputs the CLI report path does. Omitting them silently filed
    every package-level concern under documentation and left the evaluation
    section unable to see its own evidence: a caller that reconstructs the
    production call path with fewer arguments is not a lighter version of it,
    it is a different one that still returns a payload.
    """
    statuses = {f["factor_type"]: f["status"] for f in data["factors"]}
    doc = doc or {}
    eval_ids = frozenset(
        str(vr["id"]) if isinstance(vr, dict) and vr.get("id") else str(vr)
        for vr in (doc.get("hasValidationResult") or [])
        if (isinstance(vr, dict) and vr.get("id")) or isinstance(vr, str)
    )
    payload = summary_mod.compute(
        pack, statuses, {"conforms": shacl_conforms, "violations": shacl_violations}, firings,
        eval_ids, str(doc.get("id") or ""),
    )
    payload["context"] = _build_context(data["summary"], pack, authenticity,
                                        extraction_provenance)
    payload["warnings"] = warnings
    return payload


# ── Downloadable package (the thing the user actually takes away) ──
#
# The advisors' brief calls this "the signed pack (zip)". Nothing in this repo
# has ever produced a zip: the verifiable unit is a single .jsonld whose
# hash/signature fields are added in place. So the zip is packaging, and
# `uofa.jsonld` inside it is the artifact. `uofa verify` stays a single-file
# command; teaching the trust surface to parse archives would buy nothing and
# cost zip-slip handling in the one code path that must stay boring.

PACK_MEMBER_JSONLD = "uofa.jsonld"
PACK_MEMBER_REPORT = "report.md"
PACK_MEMBER_MANIFEST = "MANIFEST.json"
PACK_MEMBER_PUBKEY = "keys/uofa-issuer.pub"
PACK_MEMBER_VERIFY = "VERIFY.txt"

# PEM of the demo issuer's private key, supplied as a deployment secret. A path
# is accepted too, for local development. Neither may ever be a repo file:
# space/deploy_to_hf.py hard-refuses any *.key in its upload payload.
# The ISSUER secret: this path seals the measurement view. The demo secret
# keeps its name and changed its job -- it signs decisions now.
SIGNING_KEY_ENV = "UOFA_ISSUER_SIGNING_KEY"
SIGNING_KEY_FILE_ENV = "UOFA_ISSUER_SIGNING_KEY_FILE"

_VERIFY_TXT = """\
How to check this package
=========================

The file that carries the assurance is uofa.jsonld. Everything else in this zip
is a convenience copy of what that file already says.

    unzip <this-file>.zip
    uofa verify {jsonld} --pubkey {pubkey}
    uofa check  {jsonld} --pubkey {pubkey}

`verify` re-computes the content hash and checks the signature. `check` also runs
the structural (SHACL) rules. Neither needs a --pack flag: the package records
which standards profile validated it.

Expect `check` to report SHACL violations, and read them as findings about your
evidence rather than faults in this package. A model card carries no requirement
binding, no dataset binding and no validation results, so those are reported
missing: that gap is what the tool exists to name. The section that speaks to the
package itself is `C1 Integrity`, and that is the one that must pass.

What a valid signature here does and does not mean
--------------------------------------------------

It means: this file has not been modified since the demo produced it.

It does not mean the evidence was reviewed, accepted, or endorsed. The key that
signed it is a DEMONSTRATION issuer key held by the demo itself, not a research
or production key, and not anyone's decision key. The credibility judgment is
still the reader's to make.

About the public key in this zip
--------------------------------

{pubkey} is included so these commands work offline. A trust anchor shipped
inside the artifact it validates only proves the artifact is self-consistent. To
check it against a source this zip does not control, compare its fingerprint:

    sha256sum {pubkey}

against the fingerprint published at https://uofa.net and in the project repo.
If they differ, do not trust this package.

Notes
-----

- Package identifiers use the placeholder namespace {base_uri}. A formally
  issued package would be minted under the issuing organization's own namespace.
- MANIFEST.json lists a SHA-256 for every other file here, including this one's
  siblings, so you can tell whether the convenience copies match. MANIFEST.json
  is NOT itself signed: only uofa.jsonld is.
- contextSha256 in MANIFEST.json is the digest of the JSON-LD @context that was
  inlined into the hash. If `verify` reports a hash mismatch, compare that value
  first: over 98% of the signed bytes are the context, so a differing context is
  by far the most likely cause.
"""


def signing_key_material() -> tuple[Path | None, bytes | None]:
    """(key_path, key_pem) for the demo issuer, or (None, None) if unconfigured.

    Prefers the in-memory PEM: the hosted process serves user downloads out of a
    temp directory, and a private key on that filesystem is one path-traversal
    bug away from being one of them.
    """
    pem = os.environ.get(SIGNING_KEY_ENV)
    if pem and pem.strip():
        return None, pem.encode("utf-8")
    key_file = os.environ.get(SIGNING_KEY_FILE_ENV)
    if key_file:
        path = Path(key_file)
        if path.exists():
            return path, None
    return None, None


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _context_digest(doc: dict) -> str | None:
    """SHA-256 of the @context bytes that were inlined into the signed hash.

    Recorded because a future verification failure is otherwise undiagnosable:
    `uofa verify` can only say "Hash match: False", and the overwhelmingly
    likely cause is that the verifier's copy of the context differs from the
    one this package was signed against.
    """
    from uofa_cli.integrity import _local_context_for_url

    ref = doc.get("@context")
    if not isinstance(ref, str):
        return None
    local = _local_context_for_url(ref)
    return _sha256_file(local) if local and local.exists() else None


def _pack_filename(pack: str, package_hash: str) -> str:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"uofa-pack-{pack}-{stamp}-{package_hash[:8]}.zip"


def build_downloadable_pack(jsonld_path: Path, pack: str, payload: dict,
                            out_dir: Path, *, package_hash: str) -> dict | None:
    """Assemble the signed pack zip. Returns {zip_path, hash, filename} or None.

    Called only after `jsonld_path` has been signed, so the report rendered here
    describes the same bytes the signature covers.
    """
    from uofa_cli.commands.report import render_markdown
    from space.reviewer_state import build_reviewer_state

    doc = json.loads(jsonld_path.read_text(encoding="utf-8"))
    pubkey = paths.issuer_pubkey()
    if not pubkey.exists():
        return None

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    staging = out_dir / "staging"
    staging.mkdir(exist_ok=True)

    (staging / PACK_MEMBER_REPORT).write_text(
        render_markdown(build_reviewer_state(payload)), encoding="utf-8")
    (staging / PACK_MEMBER_VERIFY).write_text(
        _VERIFY_TXT.format(jsonld=PACK_MEMBER_JSONLD, pubkey=PACK_MEMBER_PUBKEY,
                           base_uri=str(doc.get("id", "")).rsplit("/", 1)[0] or "example.org"),
        encoding="utf-8")
    (staging / "keys").mkdir(exist_ok=True)
    (staging / PACK_MEMBER_PUBKEY).write_bytes(pubkey.read_bytes())

    members = {
        PACK_MEMBER_JSONLD: jsonld_path,
        PACK_MEMBER_REPORT: staging / PACK_MEMBER_REPORT,
        PACK_MEMBER_PUBKEY: staging / PACK_MEMBER_PUBKEY,
        PACK_MEMBER_VERIFY: staging / PACK_MEMBER_VERIFY,
    }
    manifest = {
        "packageHash": f"sha256:{package_hash}",
        "pack": pack,
        "validatedWithPacks": doc.get("validatedWithPacks"),
        "signatureAlg": doc.get("signatureAlg"),
        "canonicalizationAlg": doc.get("canonicalizationAlg"),
        "context": doc.get("@context") if isinstance(doc.get("@context"), str) else None,
        "contextSha256": _context_digest(doc),
        "toolVersion": _tool_version(),
        "signedBy": PACK_MEMBER_PUBKEY,
        "verifiableMember": PACK_MEMBER_JSONLD,
        "members": {name: f"sha256:{_sha256_file(p)}" for name, p in sorted(members.items())},
    }
    (staging / PACK_MEMBER_MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    members[PACK_MEMBER_MANIFEST] = staging / PACK_MEMBER_MANIFEST

    zip_path = out_dir / _pack_filename(pack, package_hash)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, src in sorted(members.items()):
            zf.write(src, arcname=name)
    shutil.rmtree(staging, ignore_errors=True)

    return {"zip_path": str(zip_path), "hash": package_hash, "filename": zip_path.name}


def _provenance_name(source_name: str) -> str:
    """Reduce a source label to something safe to publish inside a signed package.

    `map_to_jsonld` writes this straight into provenanceChain[].sourceFile, and
    that document is now signed and downloadable by anyone. A hosted service
    handed `/tmp/gradio/<uuid>/QuarterlyResults-CONFIDENTIAL.pdf` would publish
    both its own container layout and the uploader's filename.

    The Gradio callers already pass bare labels ("upload", "morrison-sample"),
    but `analyze()` passes `str(sources[0])` and any future caller passes
    whatever it likes. Enforcing it here means the guarantee holds for the
    document rather than for the callers that currently exist. The CLI is
    deliberately unchanged: `uofa import` records the real path a local operator
    ran against, which is provenance they want and control.
    """
    return Path(str(source_name)).name or "upload"


def _verify_as_shipped(jsonld_path: Path) -> bool:
    """Does the package we are about to hand out actually verify?

    Deliberately the same call `uofa verify` makes (commands/verify.py), against
    the same key that travels in the zip. Asserting "integrity checked" from
    anything else -- SHACL conformance, or merely the fact that we just signed --
    would put a claim in the reviewer readout that nobody had tested.
    """
    from uofa_cli.integrity import verify_file

    pubkey = paths.issuer_pubkey()
    if not pubkey.exists():
        return False
    try:
        hash_ok, sig_ok = verify_file(jsonld_path, pubkey)
    except Exception:
        return False
    return bool(hash_ok and sig_ok)


def _tool_version() -> str:
    try:
        from importlib.metadata import version
        return version("uofa")
    except Exception:
        return "unknown"


def _sign_and_pack(jsonld_path: Path, pack: str, data: dict, shacl_conforms,
                   shacl_violations, firings, warnings, doc, out_dir: Path | None,
                   extraction_provenance=None):
    """Sign, re-check what we signed, then build the payload and the zip.

    Ordering is load-bearing and easy to get wrong:
      1. weakeners have already run -- the Jena engine reads this file and has
         no reason to see hash/signature fields;
      2. sign;
      3. re-verify with the REAL pubkey, through the same call `uofa verify`
         makes, so "integrity_checked" is a fact about the artifact we hand out
         rather than a restatement of the fact that we signed it;
      4. build the payload LAST, so the reviewer readout can state the true
         hash and signer instead of claiming "signed" before signing happened.

    Returns (payload, download_or_None). A missing key is not an error: the
    Space degrades to the unsigned readout it has always shown.
    """
    from uofa_cli import package_policy

    key_path, key_bytes = signing_key_material()
    if key_path is None and key_bytes is None:
        payload = _build_payload(pack, data, shacl_conforms, shacl_violations,
                                 firings, warnings, doc,
                                 extraction_provenance=extraction_provenance)
        return payload, None

    package_hash, _sig = package_policy.sign_package(
        jsonld_path, key_path, key_bytes=key_bytes)

    integrity_ok = _verify_as_shipped(jsonld_path)

    signed_doc = json.loads(jsonld_path.read_text(encoding="utf-8"))
    authenticity = _authenticity_block(
        signed=True, package_hash=f"sha256:{package_hash}",
        integrity_checked=bool(integrity_ok),
    )
    payload = _build_payload(pack, data, shacl_conforms, shacl_violations,
                             firings, warnings, signed_doc, authenticity,
                             extraction_provenance)

    download = None
    if out_dir is not None:
        download = build_downloadable_pack(jsonld_path, pack, payload, out_dir,
                                           package_hash=package_hash)
    return payload, download


# ── Composable stages (the wizard drives these with pauses between) ──


class _StageError(Exception):
    """Internal: a stage failed with a known FailureKind."""

    def __init__(self, kind: str, message: str | None = None):
        super().__init__(kind)
        self.kind = kind
        self.message = message


def read_and_route(sources, on_progress=None):
    """Discover + read the corpus (streamed) and route to a primary pack.

    Returns (corpus, RouterDecision, warnings). Raises _StageError(READ_ERROR)
    when nothing readable is found. Cheap relative to extraction.
    """
    from space import router

    progress = on_progress or (lambda _m: None)
    try:
        file_paths, warnings = discover_files([Path(s) for s in sources])
    except Exception as exc:
        raise _StageError(FailureKind.READ_ERROR) from exc
    if not file_paths:
        raise _StageError(FailureKind.READ_ERROR, "No readable documents were found in the upload.")

    corpus = ExtractionCorpus()
    total = len(file_paths)
    for n, fp in enumerate(file_paths, 1):
        progress(f"Reading document {n} of {total}: {fp.name}")
        sub = read_corpus([fp])
        corpus.chunks.extend(sub.chunks)
        corpus.warnings.extend(sub.warnings)
        corpus.file_manifest.extend(sub.file_manifest)
    corpus.total_tokens = sum(c.token_estimate for c in corpus.chunks)
    if not corpus.chunks:
        raise _StageError(
            FailureKind.READ_ERROR, "We couldn't extract any text from the uploaded documents."
        )

    return corpus, router.route(corpus), warnings


def run_extract_stage(
    corpus,
    pack: str,
    *,
    model: str | None = None,
    llm_config=None,
    extract_timeout: int = DEFAULT_EXTRACT_TIMEOUT,
    extract_fn: Callable = _real_extract,
    on_progress=None,
):
    """Extract in an isolated subprocess with a hard timeout. Returns the
    ExtractionResult, or raises _StageError(EXTRACT_TIMEOUT/EXTRACT_ERROR/EMPTY_FACTORS)."""
    progress = on_progress or (lambda _m: None)

    # A deployment that declares a remote backend but has no key cannot read
    # anything, and with no local model in the image there is nothing to fall
    # back to. Say so by name: the generic extract error would send a
    # duplicator into a retry loop chasing a configuration problem.
    if llm_config is None and model is None:
        from space import llm_env
        missing = llm_env.missing_key_env()
        if missing:
            raise _StageError(
                FailureKind.NO_BACKEND,
                f"This Space has no model backend configured: the secret "
                f"{missing} is not set. If you duplicated this Space, add your "
                f"own key under Settings -> Variables and secrets, or set "
                f"UOFA_SPACE_MODEL=mock to explore the interface with canned data."
            )

    progress(_reading_message(llm_config))
    status, value = _run_extract(
        corpus, _effective_model(model, llm_config), pack, _prompt_path_for(pack),
        llm_config, extract_timeout, extract_fn,
    )
    if status == "timeout":
        raise _StageError(FailureKind.EXTRACT_TIMEOUT)
    if status != "ok":
        raise _StageError(FailureKind.EXTRACT_ERROR)
    if not _has_usable_factors(value):
        raise _StageError(FailureKind.EMPTY_FACTORS)
    return value


def factor_rows(result) -> list[dict]:
    """Confirm-step rows: one per factor with its extracted status (the only
    editable field) plus read-only context."""
    rows = []
    for raw in result.credibility_factors:
        f = _unwrap(raw)
        if not f.get("factor_type"):
            continue
        rows.append({
            "factor_type": f["factor_type"],
            "status": f.get("status") or "not-assessed",
            "required_level": f.get("required_level"),
            "achieved_level": f.get("achieved_level"),
            "rationale": f.get("rationale"),
        })
    return rows


def finalize_from_data(data, pack, work_dir, *, source_name="upload", warnings=None,
                       assess_sufficiency=True, pack_out_dir=None,
                       extraction_provenance=None) -> dict:
    """map -> SHACL -> (weakeners or skip) -> sign -> summary, from an import `data` dict.

    When `assess_sufficiency` is False the weakener engine is skipped (firings `[]`,
    no demotion) and the payload context is flagged so the readout reports completeness
    only and declines the sufficiency section -- the heuristic/no-card honesty rule.

    `pack_out_dir` is where the downloadable zip is written. It must NOT be
    `work_dir`: that directory is torn down the moment this returns, and the
    download has to outlive the request. When it is None, or no signing key is
    configured, the run behaves exactly as it did before downloads existed."""
    try:
        doc = map_to_jsonld(data, packs=[pack], source_path=Path(_provenance_name(source_name)))
        _assign_factor_ids(doc)
        jsonld_path = Path(work_dir) / PACK_MEMBER_JSONLD
        jsonld_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        shacl_conforms, shacl_violations = _run_check(jsonld_path, pack)
    except WeakenerEngineError:
        raise
    except Exception as exc:
        raise _StageError(FailureKind.VALIDATE_ERROR) from exc

    firings = _run_weakeners(jsonld_path, pack) if assess_sufficiency else []
    payload, download = _sign_and_pack(jsonld_path, pack, data, shacl_conforms,
                                       shacl_violations, firings, warnings or [],
                                       doc, pack_out_dir, extraction_provenance)
    if download:
        payload["download"] = download
    if not assess_sufficiency:
        payload["context"]["sufficiency_assessed"] = False
    return payload


def finalize(result, pack, factor_edits, work_dir, *, source_name="upload", warnings=None,
             pack_out_dir=None, llm_config=None) -> dict:
    """Adapt -> map -> SHACL -> weakeners -> sign -> summary. Returns the payload,
    or raises _StageError(VALIDATE_ERROR) / WeakenerEngineError."""
    data = result_to_import_dict(result, pack, factor_edits)
    return finalize_from_data(data, pack, work_dir, source_name=source_name,
                              warnings=warnings, pack_out_dir=pack_out_dir,
                              extraction_provenance=extraction_label(llm_config))


# ── Orchestration spine (all-in-one; used by the sample + spike) ──


def analyze(
    sources: list[Path],
    pack: str,
    *,
    model: str | None = None,
    llm_config=None,
    factor_edits: dict[str, str] | None = None,
    extract_timeout: int = DEFAULT_EXTRACT_TIMEOUT,
    on_progress: Callable[[str], None] | None = None,
    extract_fn: Callable = _real_extract,
    work_dir: Path | None = None,
) -> PipelineOutcome:
    """Run all stages end-to-end. Never raises for expected failures; always
    tears down the temp dir and the extractor's /tmp debug file."""
    progress = on_progress or (lambda _m: None)
    owns_work_dir = work_dir is None
    work_dir = work_dir or Path(tempfile.mkdtemp(prefix="uofa-space-"))

    try:
        corpus, _decision, warnings = read_and_route(sources, on_progress=progress)
        result = run_extract_stage(
            corpus, pack, model=model, llm_config=llm_config,
            extract_timeout=extract_timeout, extract_fn=extract_fn, on_progress=progress,
        )
        progress("Checking completeness and weakeners...")
        source_name = str(sources[0]) if sources else "upload"
        payload = finalize(result, pack, factor_edits, work_dir,
                            source_name=source_name, warnings=warnings)
        # Attached AFTER finalize, deliberately. finalize builds and signs the
        # package; this is display state only, so a change to the panel cannot
        # move a package hash and cannot trip the emittability guard.
        payload["solverEvidence"] = solver_panel.summarise(sources)
        return PipelineOutcome.success(payload)
    except _StageError as exc:
        return PipelineOutcome.failure(exc.kind, exc.message)
    except WeakenerEngineError:
        return PipelineOutcome.failure(FailureKind.WEAKENER_ERROR)
    except Exception:
        return PipelineOutcome.failure(FailureKind.INTERNAL)
    finally:
        DEBUG_RESPONSE_FILE.unlink(missing_ok=True)
        if owns_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)


# ── Card spine (live id path: fetch + extract + report, no confirm step) ──


def _card_extract(text, model_id, source_url, work_dir, *, model, deterministic,
                  on_progress, extract_timeout, llm_config=None):
    """(import_dict, provenance, sufficiency_assessed) for a fetched card. LLM-first via
    run_extract_stage (subprocess isolation + timeout); on failure, or when
    `deterministic`, falls back to the README scan (which declines sufficiency)."""
    from uofa_cli import card_bundle

    if not deterministic:
        try:
            (Path(work_dir) / "card.md").write_text(text, encoding="utf-8")
            corpus = read_corpus([Path(work_dir) / "card.md"])
            result = run_extract_stage(corpus, "model-credibility", model=model,
                                       llm_config=llm_config,
                                       extract_timeout=extract_timeout, on_progress=on_progress)
            data = result_to_import_dict(result, "model-credibility")
            data["summary"]["model_risk_level"] = card_bundle.MODEL_CREDIBILITY_ASSUMED_MRL
            data["summary"].setdefault("standards_reference", "NIST-AI-RMF-1.0")
            # Name the model that actually ran. `model or BUNDLED_MODEL` reported
            # "qwen3.5:4b" while the call went to a hosted provider, and this
            # string is rendered to the reviewer as "How assessed:".
            return data, f"{card_bundle.PROV_LLM} - {_effective_model(model, llm_config)}", True
        except _StageError:
            data = card_bundle.deterministic_import_dict(text, "model-credibility", model_id, source_url)
            return data, card_bundle.PROV_HEURISTIC_FALLBACK, False
    data = card_bundle.deterministic_import_dict(text, "model-credibility", model_id, source_url)
    return data, card_bundle.PROV_HEURISTIC, False


def card_report(
    model_id: str,
    *,
    revision: str | None = None,
    model: str | None = None,
    llm_config=None,
    deterministic: bool = False,
    on_progress: Callable[[str], None] | None = None,
    extract_timeout: int = DEFAULT_EXTRACT_TIMEOUT,
    work_dir: Path | None = None,
    pack_out_dir: Path | None = None,
) -> PipelineOutcome:
    """Live id path for the model-credibility pack: fetch the HF model card, extract factor
    statuses (LLM subprocess-isolated with a deterministic fallback), and produce a
    report payload. A gated/absent card yields an honest no-card payload (declining
    sufficiency) rather than failing. Always tears down its temp dir."""
    from uofa_cli import card_bundle, hf_card

    progress = on_progress or (lambda _m: None)
    owns_work_dir = work_dir is None
    work_dir = work_dir or Path(tempfile.mkdtemp(prefix="uofa-card-"))
    source_url = f"https://huggingface.co/{model_id}"

    try:
        progress("Fetching the public model card...")
        fetched = hf_card.fetch_card(model_id, revision)
        if fetched.status in ("gated", "error"):
            return PipelineOutcome.failure(
                FailureKind.READ_ERROR,
                fetched.detail or f"Could not fetch a model card for {model_id}.")

        if fetched.status in ("notfound", "empty"):
            data = card_bundle.deterministic_import_dict("", "model-credibility", model_id, source_url)
            provenance, doc_status, assess = "", "none", False
        else:
            data, provenance, assess = _card_extract(
                fetched.text, model_id, source_url, work_dir,
                model=model, llm_config=llm_config, deterministic=deterministic,
                on_progress=progress, extract_timeout=extract_timeout)
            doc_status = "present"

        payload = finalize_from_data(data, "model-credibility", work_dir, source_name=model_id,
                                     warnings=[], assess_sufficiency=assess,
                                     pack_out_dir=pack_out_dir)
        payload["context"]["extraction_provenance"] = provenance
        payload["context"]["documentation_status"] = doc_status
        return PipelineOutcome.success(payload)
    except _StageError as exc:
        return PipelineOutcome.failure(exc.kind, exc.message)
    except WeakenerEngineError:
        return PipelineOutcome.failure(FailureKind.WEAKENER_ERROR)
    except Exception:
        return PipelineOutcome.failure(FailureKind.INTERNAL)
    finally:
        DEBUG_RESPONSE_FILE.unlink(missing_ok=True)
        if owns_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)

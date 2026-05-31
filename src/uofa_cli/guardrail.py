"""Guardrail interface — the action-producing leg that consumes detection firings.

Pack-shaped architecture spec §6. A guardrail is a NEW consumer of detection
output: it reads the weakener firings exposed by
``check.run_structured(...).rules.firings`` and produces an **action** — a
recommendation or an engineer-commanded fix — in response. This is the inverse of
SIP: SIP measures and never decides; the guardrail acts.

**Firewall placement (§4), inherited at the interface.** A guardrail's output is
action/decision content, valid ONLY inside a signed **action-region** block
(``guardrailAction``), excluded from the measurement signature and signed in its
own ``"action"`` scope — exactly as ``engineerDecision`` is. The block is bound to
the *recomputed* measurement hash (tamper-evident) and verifies independently of
the measurement signature, which is unaffected. Any conforming guardrail pack
inherits this placement and cannot emit action content into the measurement
region. The two-scope signing machinery already exists
(``interrogate.signing.sign_scoped_block``, generalized in §4); this leg is "wire
a new consumer into the action-region scope."

**Interface + stub only.** This module ships the contract and a placeholder. The
basic guardrail's actual logic — the threshold trigger and the four
engineer-commanded fixes — is downstream and rides on this interface (spec §6,
"building that logic is downstream"); the stub deliberately decides nothing.
"""

from __future__ import annotations

import importlib
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# The guardrail's output is signed in this action-region scope (§4). The block
# key + scope are fixed so every guardrail pack signs identically.
ACTION_SCOPE_KEY = "action"
ACTION_SIGNATURE_FIELD = "actionSignature"


class Guardrail(ABC):
    """One contract: turn detection firings into an action-region block.

    Subclasses declare a ``capability_id`` and implement ``assess`` — consuming
    the firings list (``check.run_structured(...).rules.firings``) and returning
    the ``guardrailAction`` block *content* (without its signature). The content
    is action-region only; it is signed separately in the ``"action"`` scope and
    never enters the measurement region. Mirrors the ``ModelAdapter`` ABC style.
    """

    #: Stable capability identity, e.g. ``"guardrail:basic-threshold"``.
    capability_id: str = ""

    @abstractmethod
    def assess(self, firings: list[dict], *, context: dict | None = None) -> dict:
        """Return the ``guardrailAction`` block content for these firings (unsigned).

        ``firings`` is the list of ``{patternId, severity, hits, pack}`` dicts.
        ``context`` is optional caller-supplied state (the package, thresholds).
        The returned dict is action-region content — it MAY name an action; it
        MUST NOT be written into the measurement region.
        """
        raise NotImplementedError


class ThresholdGuardrailStub(Guardrail):
    """Open-core guardrail INTERFACE placeholder — decides nothing (spec §6).

    Summarizes the firings it was handed (counts + the packs that fired) and emits
    a structurally-valid action block with ``action: "none"``. The real basic
    guardrail (threshold trigger + the four engineer-commanded fixes) is the
    downstream build on this interface; the stub exists only to prove a guardrail
    can consume firings and emit a correctly-scoped action-region output.
    """

    capability_id = "guardrail:basic-threshold-stub"

    def assess(self, firings: list[dict], *, context: dict | None = None) -> dict:
        firings = firings or []
        packs = sorted({f.get("pack") for f in firings if f.get("pack")})
        return {
            "capabilityId": self.capability_id,
            "firingsConsidered": len(firings),
            "patternsFired": [f.get("patternId") for f in firings],
            "packsFired": packs,
            "action": "none",
            "note": "stub guardrail — interface only; no threshold or fix logic (spec §6, downstream)",
        }


def build_guardrail_action(
    guardrail: Guardrail, firings: list[dict], *, context: dict | None = None
) -> dict:
    """Assemble the ``guardrailAction`` block content (without its signature).

    Pack-attributes the firings first (§5/§7.3) — the guardrail is the
    evidence/action producer that records *which pack fired which weakener*, so
    attribution happens here rather than in the byte-stable core check report.
    Works on copies, so the caller's firings list is left untouched.
    """
    from uofa_cli.commands.rules import attribute_firings

    attributed = attribute_firings([dict(f) for f in (firings or [])])
    return guardrail.assess(attributed, context=context)


def sign_guardrail_action(package: dict, key_path: str | Path, block_without_signature: dict) -> dict:
    """Sign a guardrail action over the §4 action scope; return block + ``actionSignature``.

    Stamps ``attributedTo`` with the signing key's fingerprint (the action's
    author identity, like ``engineerDecision.decidedBy``) and signs over
    ``{measurementHash, action: block}`` via the generalized two-scope signer, so
    the action is tamper-evident and the measurement signature is unaffected.
    """
    from uofa_cli.interrogate import signing

    attributed = signing.fingerprint_from_private_key(Path(key_path))
    block = {**block_without_signature, "attributedTo": attributed}
    return signing.sign_scoped_block(
        package, key_path, block,
        scope_key=ACTION_SCOPE_KEY, signature_field=ACTION_SIGNATURE_FIELD,
    )


def verify_guardrail_action(package: dict, pubkey_path: str | Path) -> tuple[bool, str]:
    """Verify the ``guardrailAction`` signature over its action scope. Returns (ok, reason).

    A missing / unsigned / mis-scoped / unverifiable block, or an ``attributedTo``
    that doesn't match the supplied key, all resolve to ``(False, reason)`` — "no
    guardrail action", never package failure (mirrors ``verify_decision``).
    """
    from uofa_cli.interrogate import signing
    from uofa_cli.interrogate.forbidden import GUARDRAIL_BLOCK_KEY

    return signing.verify_scoped_block(
        package, pubkey_path,
        block_key=GUARDRAIL_BLOCK_KEY, scope_key=ACTION_SCOPE_KEY,
        signature_field=ACTION_SIGNATURE_FIELD, attributed_by_field="attributedTo",
    )


def load_guardrail(ref: str) -> Guardrail:
    """Resolve and instantiate a ``Guardrail`` from a reference string.

    Accepts ``"package.module:ClassName"`` or ``"/path/file.py:ClassName"``
    (mirrors ``adapter.load_adapter``). Raises ``ValueError`` if the target is not
    a ``Guardrail`` subclass.
    """
    cls = _resolve_class(ref)
    if not (isinstance(cls, type) and issubclass(cls, Guardrail)):
        raise ValueError(
            f"{ref!r} does not resolve to a Guardrail subclass (got {cls!r}). "
            f"Subclass uofa_cli.guardrail.Guardrail."
        )
    return cls()


def _resolve_class(ref: str):
    if ":" in ref and (ref.endswith(".py") or "/" in ref.split(":", 1)[0]):
        file_part, _, class_name = ref.partition(":")
        path = Path(file_part).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Guardrail file not found: {path}")
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load Guardrail module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    module_path, _, class_name = ref.rpartition(":") if ":" in ref else ref.rpartition(".")
    if not module_path:
        raise ValueError(
            f"Guardrail ref {ref!r} must be 'pkg.module:ClassName' or '/path/file.py:ClassName'."
        )
    return getattr(importlib.import_module(module_path), class_name)

"""Cross-family circularity check for judge ensembles (spec v1.5 §6.2).

Spec principle 1: every judge must come from a different family than the
generator. Spec principle 2: every judge must come from a different family
than the other judges in the ensemble.

This module mirrors the `circularity.py` exit-code idiom (used for the
generator-vs-extract check at spec v0.4 §7.2) but operates over a list of
roles rather than a pair, and resolves families through `FAMILY_MAP`
indirection rather than string normalization.

Exit code 5 is the spec-defined exit for cross-family violations
(`circularity.py` uses 4 for the generator-vs-extract check; the two are
deliberately different so CI logs disambiguate).
"""

from __future__ import annotations

from dataclasses import dataclass

from uofa_cli.adversarial.judge.providers import (
    UnknownFamilyError,
    resolve_family,
)


class FamilyCircularityViolation(Exception):
    """Raised when two roles in the ensemble share a family in blocking mode."""


@dataclass
class FamilyCheckResult:
    """Outcome of a cross-family check.

    `roles` is the input list of (role, model_id) pairs.
    `families` is the resolved per-role family.
    `violations` is a list of (role_a, role_b, family) tuples for every
        same-family pair found.
    `exit_code` is 0 (clean), 5 (violation), or 2 (unresolvable model id).
    `warning` is a user-facing message when allow_same_family was used.
    """

    roles: list[tuple[str, str]]
    families: dict[str, str]
    violations: list[tuple[str, str, str]]
    exit_code: int
    warning: str | None


def check_judge_ensemble(
    roles: list[tuple[str, str]],
    *,
    allow_same_family: bool = False,
) -> FamilyCheckResult:
    """Verify all roles in `roles` map to distinct families.

    `roles` is a list of (role_label, model_id) pairs, e.g.::

        [("generator", "anthropic"),
         ("judge_A", "openai"),
         ("judge_B", "google"),
         ("judge_C", "huggingface:meta-llama/Llama-3.3-70B-Instruct")]

    Behaviour:
        - All distinct families: exit 0, no warning.
        - Same family with allow_same_family=False: exit 5 with violation list.
        - Same family with allow_same_family=True: exit 0 with prominent warning
          (intended ONLY for Stage 0 smoke; never for full-corpus runs).
        - Any model_id unresolvable via FAMILY_MAP: exit 2; the caller should
          add a FAMILY_MAP entry.
    """
    if not roles:
        return FamilyCheckResult(
            roles=[],
            families={},
            violations=[],
            exit_code=0,
            warning=None,
        )

    # Resolve each role's family. An unresolvable model is exit 2 — distinct
    # from the cross-family violation exit code 5.
    families: dict[str, str] = {}
    for role, model in roles:
        try:
            families[role] = resolve_family(model)
        except UnknownFamilyError as e:
            return FamilyCheckResult(
                roles=roles,
                families=families,
                violations=[],
                exit_code=2,
                warning=str(e),
            )

    # Find every same-family pair. Stable order so test assertions and CI
    # diagnostics are deterministic.
    role_list = list(families.items())
    violations: list[tuple[str, str, str]] = []
    for i, (role_a, fam_a) in enumerate(role_list):
        for role_b, fam_b in role_list[i + 1 :]:
            if fam_a == fam_b:
                violations.append((role_a, role_b, fam_a))

    if not violations:
        return FamilyCheckResult(
            roles=roles,
            families=families,
            violations=[],
            exit_code=0,
            warning=None,
        )

    if allow_same_family:
        msg = (
            f"--allow-same-family-judge: ensemble has same-family pairs "
            f"({_format_violations(violations)}). Results may not "
            f"satisfy spec §6.2 cross-family independence. "
            f"Use only for Stage 0 smoke, never for full-corpus runs."
        )
        return FamilyCheckResult(
            roles=roles,
            families=families,
            violations=violations,
            exit_code=0,
            warning=msg,
        )

    msg = (
        f"family circularity: ensemble has same-family pair(s) "
        f"({_format_violations(violations)}). Pass --allow-same-family-judge "
        f"to override (smoke-test only) or change the model selection."
    )
    return FamilyCheckResult(
        roles=roles,
        families=families,
        violations=violations,
        exit_code=5,
        warning=msg,
    )


def _format_violations(violations: list[tuple[str, str, str]]) -> str:
    return ", ".join(f"{a}+{b}={fam}" for a, b, fam in violations)

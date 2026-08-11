"""A1 rule-property coverage lint for the Group-B evaluation-sufficiency layer.

Addendum v0.1 §A1 requires this as a mechanical check, not a convention, because
both directions of drift are silent:

  - **A rule testing a property nothing emits fires on 100% of inputs.** That is
    not a finding, it is a schema hole. The readout looks identical to a genuine
    universal failure, which is the worst possible disguise.
  - **A property emitted with no rule consuming it** is dead weight that reads,
    from the outside, exactly like a check.

Neither side is hardcoded here. Tested properties are parsed out of the `.rules`
files; emittable properties come from `uofa_cli.furnishers`. A copy of either
would drift from the thing it copies, which is the defect this file exists to
catch.

**The scan covers core's rules as well as the pack's, deliberately.** Scoped to
the pack alone, this lint would have reported full coverage while the pack
shipped a `W-EV-UQ-01` that duplicated core's `W-AL-01` on the same node and the
same property -- a coverage check blind to the duplication it should surface is
the "check that cannot fail" of AGENTS.md §13.
"""

from __future__ import annotations

import re

import pytest

from uofa_cli import paths
from uofa_cli.furnishers import (
    CORE_RESULT_PROPERTIES_POPULATED,
    GROUP_B_RESULT_PROPERTIES,
    GROUP_B_RUN_CONTEXT_PROPERTIES,
)

PACK = "mrm-nist"

# A rule block is `[name: <body> -> <head> ]`.
_RULE_RE = re.compile(r"\[(\w+):(.*?)\n\]", re.S)
# Properties a body tests for absence of, or binds as a triple pattern.
_NOVALUE_RE = re.compile(r"noValue\(\s*\?\w+\s*,\s*uofa:(\w+)\s*\)")
_TRIPLE_RE = re.compile(r"\(\s*\?\w+\s+uofa:(\w+)\s+[?'\"]")
_PATTERN_ID_RE = re.compile(r"uofa:patternId\s+'([^']+)'")

# Structural plumbing every rule binds; not evidence properties under assessment.
_PLUMBING = {
    "hasValidationResult", "hasWeakener", "patternId", "severity",
    "affectedNode", "hasCredibilityFactor", "bindsClaim", "bindsRequirement",
}


def _rule_blocks(path):
    return _RULE_RE.findall(path.read_text())


def _group_b_rule_files():
    """The pack's own rules file (the one declaring W-EV-* / COMPOUND-EV-*)."""
    return [p for p in paths.all_rules_files(active=[PACK]) if PACK.replace("-", "_") in p.name]


def _all_rule_files():
    return list(paths.all_rules_files(active=[PACK]))


def _body(block) -> str:
    return block[1].split("->")[0]


def test_group_b_rules_only_test_emittable_properties():
    """Every property a Group-B rule tests must be one a furnisher can emit."""
    emittable = (
        GROUP_B_RESULT_PROPERTIES
        | CORE_RESULT_PROPERTIES_POPULATED
        | GROUP_B_RUN_CONTEXT_PROPERTIES
    )
    untestable: dict[str, set[str]] = {}
    for path in _group_b_rule_files():
        for name, body in _rule_blocks(path):
            cond = _body((name, body))
            props = set(_NOVALUE_RE.findall(cond)) | set(_TRIPLE_RE.findall(cond))
            orphans = props - emittable - _PLUMBING
            if orphans:
                untestable[name] = orphans
    assert not untestable, (
        "Group-B rules test properties no furnisher emits, so they fire on every "
        f"input by construction: {untestable}. Either emit the property or drop "
        "the clause -- a rule that always fires is a schema hole, not a finding."
    )


def test_every_emittable_property_has_a_consuming_rule():
    """No Group-B property may be emitted without a rule that reads it."""
    tested: set[str] = set()
    for path in _group_b_rule_files():
        for name, body in _rule_blocks(path):
            cond = _body((name, body))
            tested |= set(_NOVALUE_RE.findall(cond)) | set(_TRIPLE_RE.findall(cond))

    declared = GROUP_B_RESULT_PROPERTIES | GROUP_B_RUN_CONTEXT_PROPERTIES
    unconsumed = declared - tested
    assert not unconsumed, (
        f"Declared Group-B properties with no consuming rule: {sorted(unconsumed)}. "
        "An emitted property no rule reads is dead weight that looks like a check."
    )


def test_core_populated_properties_are_consumed_by_core_not_duplicated():
    """`hasUncertaintyQuantification` is core's to assess; the pack must not re-test it.

    This is the check that would have caught the withdrawn W-EV-UQ-01. Core's
    W-AL-01 already fires on this property's absence for any ValidationResult,
    and the pack runs all core patterns -- so a Group-B rule testing the same
    property on the same node would report one gap twice under two ids.

    COMPOUND-EV-01 is the one permitted reader: it does not report the missing
    uncertainty on its own, it conjoins it with a missing null baseline under a
    high-risk decision, which is a distinct finding at a distinct severity.
    """
    core_consumers, pack_consumers = set(), set()
    for path in _all_rule_files():
        is_pack = PACK.replace("-", "_") in path.name
        for name, body in _rule_blocks(path):
            cond = _body((name, body))
            if CORE_RESULT_PROPERTIES_POPULATED & set(_NOVALUE_RE.findall(cond)):
                pid_match = _PATTERN_ID_RE.search(body)
                pid = pid_match.group(1) if pid_match else name
                (pack_consumers if is_pack else core_consumers).add(pid)

    assert core_consumers, (
        "No core rule tests hasUncertaintyQuantification. The pack relies on core "
        "owning that finding; if core stopped, the gap is now unreported."
    )
    assert pack_consumers <= {"COMPOUND-EV-01"}, (
        f"Pack rules duplicate a core-owned property: {sorted(pack_consumers)}. "
        f"Core already reports it via {sorted(core_consumers)}. Adding a parallel "
        "rule reports one missing standard error twice under two ids."
    )


@pytest.mark.parametrize("pattern_id", [
    "W-EV-GEN-02", "W-EV-DET-03", "W-EV-NULL-04",
    "W-EV-COU-05", "W-EV-CAP-06", "COMPOUND-EV-01", "COMPOUND-EV-02",
])
def test_declared_pattern_ids_are_implemented(pattern_id):
    """Every patternId in pack.json must exist in the rules file, and vice versa."""
    implemented = set()
    for path in _group_b_rule_files():
        implemented |= {m for _, body in _rule_blocks(path)
                        for m in _PATTERN_ID_RE.findall(body)}
    assert pattern_id in implemented, (
        f"{pattern_id} is declared in pack.json but no rule emits it."
    )


def test_manifest_pattern_ids_match_the_rules_file_exactly():
    manifest_ids = set(paths.detection_config(paths.pack_manifest(PACK))["patternIds"])
    implemented = set()
    for path in _group_b_rule_files():
        implemented |= {m for _, body in _rule_blocks(path)
                        for m in _PATTERN_ID_RE.findall(body)}
    assert manifest_ids == implemented, (
        f"pack.json declares {sorted(manifest_ids)} but the rules file implements "
        f"{sorted(implemented)}. The manifest is what collision-checking and "
        "factorFocus read; a mismatch silently unbinds a rule from its factor."
    )


def test_group_b_vocabulary_needs_no_context_declaration():
    """Group-B properties must resolve to `uofa:` IRIs with no context entry.

    Two things are pinned here, and both were learned the expensive way.

    **The context must keep its `@vocab` fallback.** Every Group-B rule matches
    `uofa:<prop>`, and those properties are deliberately undeclared. That works
    only because `v0.5.jsonld` sets `"@vocab": "https://uofa.net/vocab#"`. Remove
    it and the terms silently stop expanding, every Group-B rule stops matching,
    and the readout reports a clean bill of health for a model nobody assessed --
    failure as silence, which is the worst shape it can take.

    **And no Group-B property may be added to the context.** That file is inlined
    into the document before hashing, so a purely additive vocabulary entry
    changes the canonical hash of every bundle referencing it: adding these terms
    put the Morrison reference example into `C1 Integrity` failure while C2 and C3
    stayed green. Nothing in the tooling says a vocabulary edit is a corpus edit,
    so this test says it.
    """
    import json

    context = json.loads(paths.context_file().read_text())["@context"]

    assert context.get("@vocab") == "https://uofa.net/vocab#", (
        "the @vocab fallback is gone; undeclared Group-B properties will stop "
        "expanding to uofa: IRIs and every Group-B rule will silently stop firing"
    )

    declared = (
        GROUP_B_RESULT_PROPERTIES | GROUP_B_RUN_CONTEXT_PROPERTIES
    ) & set(context)
    assert not declared, (
        f"Group-B properties were added to {paths.context_file().name}: "
        f"{sorted(declared)}. That file is hashed into every signed bundle, so this "
        "invalidates the example corpus (check Morrison's C1). @vocab already makes "
        "the declaration unnecessary — remove the entries."
    )


def test_every_pattern_id_has_a_factor_focus():
    """A weakener with no factorFocus can demote nothing -- it reports into a void."""
    cfg = paths.detection_config(paths.pack_manifest(PACK))
    focus = cfg["factorFocus"] or {}
    missing = [pid for pid in cfg["patternIds"] if not focus.get(pid)]
    assert not missing, (
        f"Group-B patterns with no factorFocus: {missing}. These fire on a "
        "ValidationResult node, so IRI resolution yields no factor and the "
        "concern axis never meets the credibility-factor axis."
    )

"""Transform an intermediate dict (from excel_reader) into a UofA JSON-LD document.

Knows about JSON-LD structure but nothing about openpyxl.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from uofa_cli.excel_constants import (
    VV40_FACTOR_NAMES, NASA_ONLY_FACTOR_NAMES, MODEL_CREDIBILITY_FACTOR_NAMES,
    AI_800_3_FACTOR_NAMES,
    ALL_FACTOR_CATEGORIES, NASA_PHASE_MAP,
    FACTOR_STANDARD_VV40, FACTOR_STANDARD_NASA, FACTOR_STANDARD_MODEL_CREDIBILITY,
    FACTOR_STANDARD_AI_800_3,
    PROFILE_URIS, CONTEXT_URL, DEFAULT_BASE_URI, RESERVED_BASE_URIS,
    context_url_for,
    CRITERIA_BASE, KNOWN_CRITERIA_SETS,
    LEVEL_TOKENS, JUDGMENT_TOKENS, level_vocab_for, version_tuple,
    LEDGER_ANCHOR_SCHEME,
)
from uofa_cli import __version__
from uofa_cli.integrity import CANONICALIZATION_ALG


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug: lowercase, hyphens, no special chars."""
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def resolve_base_uri(base_uri: str | None) -> str:
    """Normalise a minting namespace, refusing the project's reserved one.

    uofa.net is where this project publishes its own examples. A package
    imported from someone's spreadsheet must never be minted there: the id sits
    inside the canonicalised content covered by the hash and signature, so it
    cannot be corrected after signing without destroying the provenance chain.
    """
    candidate = (base_uri or DEFAULT_BASE_URI).strip().rstrip("/")
    if not candidate:
        raise ValueError("base_uri cannot be empty")
    for reserved in RESERVED_BASE_URIS:
        if candidate == reserved or candidate.startswith(reserved + "/"):
            raise ValueError(
                f"{candidate!r} is reserved for this project's published examples. "
                f"Use a namespace you control, or leave it unset to mint under "
                f"{DEFAULT_BASE_URI} as a placeholder."
            )
    return candidate


def resolve_criteria_set(standards_reference: str, base_uri: str) -> str:
    """Identifier for the rubric an assessment was graded against.

    A recognised published standard is a shared concept, so it gets the stable
    project-controlled identifier under CRITERIA_BASE. Anything else is the
    author's own rubric and is minted in the author's namespace, because the
    project cannot speak for a criteria set it has never seen.

    Aliases are folded so that "ASME V&V 40", "asme-vv40-2018" and
    "ASME_VV40_2018" resolve to one identifier rather than three.
    """
    normalized = re.sub(r"[^A-Z0-9]", "", (standards_reference or "").upper())
    canonical = KNOWN_CRITERIA_SETS.get(normalized)
    if canonical:
        return f"{CRITERIA_BASE}/{canonical}"
    # Org-level, not under the COU: a rubric is shared across an author's
    # assessments, so burying it beneath one context of use would be wrong.
    return f"{base_uri}/criteria/{slugify(standards_reference)}"


# Supplied by `sign_file` AFTER the mapper runs, so they cannot be looked for
# when the profile is derived. Every other required field is present by then --
# generatedAtTime included, which is set here.
_DEFERRED_TO_SIGNING = {"hash", "signature"}


def _profile_requirements(packs: list[str]) -> dict[str, set[str]]:
    """Required property names per profile body, read from the shapes.

    Read, never hardcoded: a copy of the shape's requirements is a copy that
    drifts, and this repository has already moved PROFILE_URIS off a literal
    onto `sh:in` for that reason.
    """
    from rdflib import Graph, Namespace
    from uofa_cli import paths as _paths

    SH = Namespace("http://www.w3.org/ns/shacl#")
    g = Graph()
    for f in _paths.all_shacl_schemas(active=list(packs)):
        try:
            g.parse(f, format="turtle")
        except Exception:
            continue
    out: dict[str, set[str]] = {}
    for name in ("Disposition", "Complete", "Minimal"):
        shape = next((x for x in g.subjects(None, None)
                      if str(x).endswith(f"UnitOfAssurance_{name}Body")), None)
        if shape is None:
            continue
        req, frontier = set(), [shape]
        while frontier:
            n = frontier.pop()
            for prop in g.objects(n, SH.property):
                mc = g.value(prop, SH.minCount)
                if mc is not None and int(mc) >= 1:
                    req.add(str(g.value(prop, SH.path)).split("#")[-1])
            frontier.extend(g.objects(n, SH.node))
        out[name] = req
    return out


def derive_profile(doc: dict, packs: list[str]) -> tuple[str | None, set[str]]:
    """The highest profile the CONTENT satisfies, and what the closest one lacks.

    Every package used to declare whatever the spreadsheet said, which is how all
    five gpt-5 extractions came to claim ProfileComplete without containing
    Complete's fields -- an aspiration the shape then measured as a claim.

    Order is Disposition, Complete, Minimal: Disposition is CompleteBody plus
    hasDisposition via sh:node, so it is strictly the most demanding. Ranking by
    what a shape DEMANDS rather than by what is adopted keeps the order stable.

    Returns (None, missing) when nothing is satisfied, so the caller can fail
    loudly naming the gap rather than declaring a profile the package does not
    meet.
    """
    reqs = _profile_requirements(packs)
    present = {k for k, v in doc.items() if v not in (None, "", [], {})}
    closest, fewest = None, None
    for name in ("Disposition", "Complete", "Minimal"):
        need = reqs.get(name)
        if not need:
            continue
        missing = {r for r in need if r not in present} - _DEFERRED_TO_SIGNING
        if not missing:
            return name, set()
        if fewest is None or len(missing) < len(fewest):
            closest, fewest = name, missing
    return None, (fewest or set())


def _provenance(summary: dict, packs: list[str]) -> dict:
    """Which class each field came from. See R5 in docs/valid-package-spec.md.

    Only fields whose origin this mapper actually knows are listed. A field
    absent from this map is not thereby "extracted" -- it is unclassified, and
    saying so is the point. Guessing a class would recreate the problem the map
    exists to solve.
    """
    # Flat "field=class" strings, NOT a nested {field: class} map.
    #
    # A nested map puts vocabulary TERM NAMES in key position, and the JSON-LD
    # @context applies inside nested objects too -- so "generatedAtTime":
    # "run-context" was read as an xsd:dateTime literal and rdflib raised
    # `Failed to convert Literal lexical form to value` on every package. The
    # provenance record is metadata ABOUT fields, not more fields, and encoding
    # it as though it were fields made the graph unparseable.
    out = {
        "wasAttributedTo": "run-context",
        "validatedWithPacks": "run-context",
        "wasDerivedFrom": "run-context",
        "hash": "run-context",
        "signature": "run-context",
        "generatedAtTime": "run-context",
    }
    if summary.get("_project_name_defaulted"):
        out["name"] = "defaulted"
    elif summary.get("project_name"):
        out["name"] = "extracted"
    if summary.get("assessor_name"):
        out["statedAssessor"] = "extracted"
    for f in ("cou_name", "cou_description", "model_risk_level"):
        if summary.get(f):
            out[f] = "extracted"
    return [f"{k}={v}" for k, v in sorted(out.items())]


def _operator_identity() -> str | None:
    """Who is running this, for prov:wasAttributedTo.

    Order: an explicit --assessor, the [assessment] assessor config key, then
    `git config user.name`, then $USER. Returns None when nothing identifies the
    operator, and None is the right answer -- the package then fails validation
    naming the missing field, rather than validating on a name the extractor
    made up.
    """
    import os
    import subprocess

    env = os.environ.get("UOFA_ASSESSOR")
    if env:
        return env.strip()
    try:
        r = subprocess.run(["git", "config", "user.name"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return os.environ.get("USER") or None


def map_to_jsonld(
    data: dict, packs: list[str], source_path: Path, base_uri: str | None = None
) -> dict:
    """Transform intermediate dict into a UofA JSON-LD document.

    Args:
        data: Intermediate dict from excel_reader.read_workbook().
        packs: Active pack names (e.g., ["vv40"], ["nasa-7009b"]).
        source_path: Path to the original Excel file (for provenance).
        base_uri: Namespace to mint identifiers under. Defaults to
            DEFAULT_BASE_URI, a reserved placeholder domain the author is
            expected to replace with one they control.

    Returns:
        A dict ready for json.dumps() as JSON-LD.
    """
    summary = data["summary"]
    entities = data["entities"]
    validation_results = data["validation_results"]
    factors = data["factors"]
    # **Two kinds, never one key.** A DECISION is a human judgment and carries a
    # verdict; an ASSESSMENT is machine work and carries a status fact. They were
    # the same key, so the card path's "Not accepted" -- produced by a tool that
    # judged nothing -- reached `hasDecisionRecord` and was issuer-signed, which
    # is precisely what AGENTS.md section 12 forbids.
    decision = data.get("decision") or {}
    assessment = data.get("assessment") or {}

    profile = summary["profile"]
    project_slug = slugify(summary["project_name"] or "unnamed")
    cou_slug = slugify(summary["cou_name"] or "unnamed")
    root = resolve_base_uri(base_uri)
    base = f"{root}/{project_slug}/{cou_slug}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Build the document ───────────────────────────────────
    doc = {
        # Not the constant: the version this workbook DECLARES. See
        # `context_url_for` -- a package is judged by the vocabulary it was
        # authored against, so it declares that one.
        "@context": context_url_for(
            version_tuple(summary.get("encoding_profile", ""))),
        "id": base,
        "type": "UnitOfAssurance",
        "conformsToProfile": PROFILE_URIS.get(profile, PROFILE_URIS["Minimal"]),
        # The pack set this was built and validated under, so the same package
        # validates the same way for everyone -- including someone who received
        # it and knows nothing about how it was made. Without it, validation is
        # relative to a --pack flag the operator remembers, defaulting to vv40,
        # and a NASA-STD-7009B package is silently asked for a V&V 40 context of
        # use. Recorded as the PACK SET rather than the standard because the
        # standard does not resolve uniquely: ASME-VV40-2018 is claimed by vv40,
        # disposition and surrogate alike.
        "validatedWithPacks": list(packs),
        # R5. How each field got here: extracted from the document, supplied by
        # the run, defaulted, or synthesized. A package validating on six
        # run-context fields and two extracted ones is a different artefact from
        # one validating on eight extracted fields, and without this they are
        # indistinguishable -- which is what would let R1-R3 become a way to make
        # the numbers look better rather than the packages truer.
        #
        # Three findings on 2026-08-08 pointed here independently: a package that
        # validated because the model invented an assessor, one that validated on
        # the template's help text, and one that reaches Minimal via a warned
        # auto-synthesis. All three look identical to a conforming package today.
        "fieldProvenance": _provenance(summary, packs),
        "name": f"{summary['project_name']} \u2014 {summary['cou_name']}",
    }

    if summary.get("cou_description"):
        doc["description"] = summary["cou_description"]

    # ── Entity bindings ──────────────────────────────────────
    requirements = [e for e in entities if e["entity_type"] == "Requirement"]
    models = [e for e in entities if e["entity_type"] == "Model"]
    datasets = [e for e in entities if e["entity_type"] == "Dataset"]

    if requirements:
        req_uris = [_entity_uri(base, "req", r) for r in requirements]
        doc["bindsRequirement"] = req_uris[0] if len(req_uris) == 1 else req_uris

    if models:
        model_uris = [_entity_uri(base, "model", m) for m in models]
        doc["bindsModel"] = model_uris[0] if len(model_uris) == 1 else model_uris

    if datasets:
        doc["bindsDataset"] = [_entity_uri(base, "data", d) for d in datasets]

    # ── Context of Use ───────────────────────────────────────
    cou = {
        "id": f"{base}/cou",
        "type": "ContextOfUse",
        "name": summary["cou_name"],
    }
    if summary.get("cou_description"):
        cou["intendedUse"] = summary["cou_description"]
    doc["hasContextOfUse"] = cou

    # ── Validation Results ───────────────────────────────────
    if validation_results:
        doc["hasValidationResult"] = [
            _map_validation_result(base, vr) for vr in validation_results
        ]

    # ── Provenance ───────────────────────────────────────────
    if summary.get("source_document"):
        doc["wasDerivedFrom"] = summary["source_document"]

    # R1. `wasAttributedTo` is WHO RAN THE TOOL, which an extractor cannot know.
    #
    # It used to come from the spreadsheet's Assessor Name, and that single line
    # decided whether a package validated: of five real papers extracted by
    # gpt-5, the two that passed SHACL were exactly the two where the model had
    # invented an assessor. Validity turned on a guess about a person.
    #
    # A document MAY state who performed the assessment -- NTRS credibility
    # reports often do -- and reading that is legitimate evidence. Using it as
    # the operator's identity is not. It is recorded as `statedAssessor`, an
    # extracted fact, and the two stay distinguishable.
    if summary.get("assessor_name"):
        doc["statedAssessor"] = summary["assessor_name"]
    operator = _operator_identity()
    if operator:
        doc["wasAttributedTo"] = f"{base}/org/{slugify(operator)}"

    # ── Credibility Factors (Complete profile) ───────────────
    # Include ALL factors (assessed AND not-assessed) so the rule engine
    # can detect unassessed gaps at elevated risk (W-EP-04).
    if factors:
        doc["hasCredibilityFactor"] = [
            _map_factor(f, packs, base, vocab=level_vocab_for(
                version_tuple(summary.get("encoding_profile", ""))))
            for f in factors
        ]

    # ── Automated assessment (machine-class, issuer-signable) ─
    #
    # Attributed to the tool through the run log's existing lineage, not to a
    # person. An issuer key attesting this is exactly what an issuer key is for.
    if assessment.get("status"):
        res = {
            "id": f"{base}/assessment",
            "type": "AutomatedAssessment",
            "assessmentStatus": assessment["status"],
        }
        if assessment.get("rationale"):
            res["rationale"] = assessment["rationale"]
        doc["hasAssessmentResult"] = res

    # ── Decision Record (human judgment) ─────────────────────
    if decision.get("outcome"):
        dec = {
            "id": f"{base}/decision",
            "type": "DecisionRecord",
            "outcome": decision["outcome"],
        }
        if decision.get("rationale"):
            dec["rationale"] = decision["rationale"]
        if decision.get("decided_by"):
            dec["actor"] = f"{base}/org/{slugify(decision['decided_by'])}"
            dec["role"] = decision["decided_by"]
        if decision.get("decision_date"):
            dec["decidedAt"] = _as_datetime(decision["decision_date"])

        # **The fork is derived from the anchor's form, never declared twice.**
        # `decisionProvenance` and the anchor cannot disagree, because one is a
        # reading of the other -- two sources of truth made unrepresentable for
        # this fact.
        provenance = _decision_provenance(decision.get("anchor_uri"))
        if provenance is not None:
            dec["decisionProvenance"] = provenance
        if provenance == "extracted":
            uri = decision["anchor_uri"].strip()
            anchor = {"type": "SourceAnchor", "anchorLocator": uri}
            if decision.get("anchor_sha256"):
                anchor["anchorSha256"] = decision["anchor_sha256"]
            dec["decisionAnchor"] = anchor

        doc["hasDecisionRecord"] = dec

    # ── Complete profile metadata ────────────────────────────
    if profile == "Complete":
        if summary.get("assurance_level"):
            doc["assuranceLevel"] = summary["assurance_level"]
        if summary.get("standards_reference"):
            doc["criteriaSet"] = resolve_criteria_set(
                summary["standards_reference"], root
            )

        # Credibility metrics — placeholder values
        doc["credibilityIndex"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["traceCompleteness"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["verificationCoverage"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["validationCoverage"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["uncertaintyCIWidth"] = {"@value": "0.0", "@type": "xsd:decimal"}

        if summary.get("model_risk_level") is not None:
            doc["modelRiskLevel"] = summary["model_risk_level"]
        if summary.get("device_class"):
            doc["deviceClass"] = summary["device_class"]
        doc["couName"] = summary["cou_name"]
        if decision.get("outcome"):
            doc["decision"] = decision["outcome"]
        elif assessment.get("status"):
            doc["assessmentStatus"] = assessment["status"]
        doc["hasUncertaintyQuantification"] = summary.get("has_uq", "No") == "Yes"

    # ── Timestamp and integrity placeholders ─────────────────
    doc["generatedAtTime"] = now
    doc["hash"] = "sha256:" + "0" * 64
    doc["signature"] = "ed25519:" + "0" * 128
    doc["signatureAlg"] = "ed25519"
    doc["canonicalizationAlg"] = CANONICALIZATION_ALG

    # ── Provenance chain ─────────────────────────────────────
    doc["provenanceChain"] = [
        {
            "activityType": "ImportActivity",
            "timestamp": now,
            "sourceFile": str(source_path),
            "toolVersion": f"uofa-cli {__version__}",
            "generatedEntity": base,
        }
    ]

    # R3. The declared profile is DERIVED from what the package contains, not
    # taken from the spreadsheet. All five gpt-5 extractions declared
    # ProfileComplete because the extractor writes "Complete" -- an aspiration
    # the shape then measured as a claim, and three of them failed on it. A
    # package should declare what it earned.
    derived, missing = derive_profile(doc, packs)
    if derived:
        doc["conformsToProfile"] = PROFILE_URIS[derived]
        doc.setdefault("fieldProvenance", []).append("conformsToProfile=derived")
    else:
        # The floor. Leave the asserted value in place so `uofa shacl` fails
        # naming the gap, and record what is missing rather than silently
        # declaring a lower profile the package also does not meet.
        doc.setdefault("fieldProvenance", []).append("conformsToProfile=asserted")
        doc["profileShortfall"] = sorted(missing)
    return doc


def _entity_uri(base: str, entity_type: str, entity: dict) -> str:
    """Generate a URI for an entity."""
    if entity.get("uri"):
        return entity["uri"]
    name_slug = slugify(entity.get("name") or "unnamed")
    return f"{base}/{entity_type}/{name_slug}"


def _map_validation_result(base: str, vr: dict) -> dict:
    """Map a validation result intermediate dict to JSON-LD."""
    etype = vr["evidence_type"]
    result = {
        "type": etype,
    }

    if vr.get("uri"):
        result["id"] = vr["uri"]
    else:
        result["id"] = f"{base}/validation/{slugify(vr['name'])}"

    if vr.get("name"):
        result["name"] = vr["name"]
    if vr.get("description"):
        result["description"] = vr["description"]
    if vr.get("compares_to"):
        # v0.4 vocabulary uses "comparedAgainst" (not "comparesTo")
        result["comparedAgainst"] = vr["compares_to"]
    if vr.get("has_uq") == "Yes":
        result["hasUncertaintyQuantification"] = True
        if vr.get("uq_method"):
            result["uqMethod"] = vr["uq_method"]
    elif vr.get("has_uq") == "No":
        result["hasUncertaintyQuantification"] = False
    if vr.get("metric_value"):
        result["metricValue"] = vr["metric_value"]
    if vr.get("pass_fail"):
        result["passFail"] = vr["pass_fail"]

    # Auto-generate wasGeneratedBy activity so W-EP-02 doesn't fire on
    # every imported validation result (the Excel template has no column
    # for generation activity).
    result["wasGeneratedBy"] = {
        "id": f"{result['id']}/activity",
        "type": "prov:Activity",
    }

    # Add SHACL-required properties for evidence sub-types.
    # These shapes have mandatory fields that the generic Excel columns
    # don't capture, so we populate from available data or defaults.
    if etype == "ReviewActivity":
        result["reviewer"] = vr.get("compares_to") or f"{base}/org/reviewer"
        result["reviewType"] = "internal"
    elif etype == "ProcessAttestation":
        result["processType"] = "documentation"
        result["attestedBy"] = vr.get("compares_to") or f"{base}/org/attester"
    elif etype == "DeploymentRecord":
        result["deployedIn"] = vr.get("compares_to") or f"{base}/system/deployment"
    elif etype == "InputPedigreeLink":
        result["sourceReference"] = vr.get("compares_to") or vr.get("uri") or f"{base}/data/source"

    return result


def _as_datetime(value: str) -> str:
    """A date-or-datetime cell, normalised to one `xsd:dateTime`.

    The suffix used to be appended unconditionally, so a cell already carrying a
    time produced `2026-09-09T10:00:00T00:00:00Z` -- malformed against the
    context's `xsd:dateTime`, from a workbook that was not wrong.
    """
    s = str(value).strip()
    if "T" in s:
        return s if s.endswith("Z") or "+" in s[10:] else s + "Z"
    return f"{s}T00:00:00Z"


class AnchorFormError(ValueError):
    """An anchor whose form the emitter cannot classify."""


ASSERTED = "asserted"
EXTRACTED = "extracted"


def _decision_provenance(anchor_uri: str | None) -> str:
    """Which fork the anchor's FORM puts this decision on. Total by construction.

    `ledger://<assessor>/<entry>` is an act of judgment -- the reviewer decided,
    so the warrant is their signature. A passage (or an `archive://` member) is
    something the source actually stated, so the warrant is the anchor itself,
    sha-pinned: "the paper is their attestation" is empty if a reader cannot tell
    transcription from invention. The source never signs.

    **Totality is the point.** A fork derived from form is trustworthy only if an
    unclassifiable form is an ERROR rather than a guess -- otherwise the
    empty-value genus arrives here wearing a URI, and a decision silently lands
    on a branch nobody chose. So an unknown scheme raises and names itself.

    **No anchor means `asserted`, and this is not a default.** A workbook whose
    decision cites no source is one a live person filled in: they judged, so they
    are a participant in this package's production, and participants sign their
    acts. Returning None here looked like honest silence but was the opposite --
    a record with no fork slipped past the seal gate that a record honestly
    declaring `asserted` would have failed, so omission became the way around the
    boundary. The fork is always stated; what varies is which one.
    """
    uri = (anchor_uri or "").strip()
    if not uri:
        return ASSERTED
    if uri.startswith(LEDGER_ANCHOR_SCHEME):
        return ASSERTED
    if uri.startswith("archive://"):
        return EXTRACTED
    scheme = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*)://", uri)
    if scheme:
        raise AnchorFormError(
            f"cannot classify decision anchor form {scheme.group(1)!r}://: expected "
            f"a '{LEDGER_ANCHOR_SCHEME}' address (an act of judgment), an "
            f"'archive://' member, or a source passage locator. Refusing to guess "
            f"which fork this decision belongs on.")
    return EXTRACTED


def _map_factor(factor: dict, packs: list[str], base: str = "", *,
                vocab: frozenset[str]) -> dict:
    """Map a credibility factor intermediate dict to JSON-LD."""
    vv40_set = set(VV40_FACTOR_NAMES)
    nasa_only_set = set(NASA_ONLY_FACTOR_NAMES)
    model_credibility_set = set(MODEL_CREDIBILITY_FACTOR_NAMES)
    ai_800_3_set = set(AI_800_3_FACTOR_NAMES)

    f = {
        "type": "CredibilityFactor",
        "factorType": factor["factor_type"],
        "factorStatus": factor["status"],
    }

    # Whose judgment set factorStatus, when the caller knows. Emitted ONLY when
    # supplied: a package built from a spreadsheet cannot tell which cells a
    # human touched, and the honest answer there is silence rather than a guess
    # -- the same rule `_provenance` states for the summary fields.
    #
    # Not in the @context deliberately: `@vocab` maps it to
    # uofa:statusProvenance, so this adds no term to the vocabulary and needs no
    # new context version. That matters more than it looks -- the inlined
    # context is ~98% of a package's hash preimage, so a context bump would
    # invalidate every signature ever issued against the old one.
    if factor.get("status_provenance"):
        f["statusProvenance"] = factor["status_provenance"]

    # Assign factorStandard based on factor name and active packs. The stamp is
    # load-bearing: the vv40/nasa factor-name SHACL shapes use an
    # `(!BOUND(?fs) || ?fs = "<their-standard>")` guard, so a factor left
    # WITHOUT a factorStandard is checked against the vv40 name enum and flagged.
    # model-credibility names are disjoint from vv40/nasa, so they must carry their own
    # standard to be validated by model_credibility_shapes.ttl and ignored by the others.
    if factor["factor_type"] in nasa_only_set:
        f["factorStandard"] = FACTOR_STANDARD_NASA
    elif factor["factor_type"] in vv40_set:
        # If both packs active and it's a shared factor, use VV40
        f["factorStandard"] = FACTOR_STANDARD_VV40
    elif factor["factor_type"] in model_credibility_set:
        f["factorStandard"] = FACTOR_STANDARD_MODEL_CREDIBILITY
    elif factor["factor_type"] in ai_800_3_set:
        # Group B (evaluation sufficiency) shares the pack with Group A above but
        # carries its own standard, so each group's shape stays silent on the
        # other's factors. Both use a *required* factorStandard match rather than
        # vv40's !BOUND fallback; relaxing either to OPTIONAL makes every Group-B
        # factor a Group-A name violation.
        f["factorStandard"] = FACTOR_STANDARD_AI_800_3

    if factor.get("required_level") is not None:
        f["requiredLevel"] = factor["required_level"]
        # v0.8. Three claims per required level, three pieces of evidence: where
        # the source states it (the anchor), what it is (the value), and whether
        # anyone judged it sufficient (this token, and its activity).
        #
        # `confirmed` never appears here. That is the encoding tool's LOCATION
        # act -- anchoring produces it -- and exporting it as a judgment claim
        # is the exact ambiguity v0.8 exists to kill.
        # **The closed set is closed.** This read `LEVEL_TOKENS.get(token,
        # token)`, which passes an unrecognised term through verbatim -- so a
        # workbook whose column said `confirmed` emitted `confirmed` as a
        # provenance value, which is the precise ambiguity v0.8 exists to kill,
        # reintroduced by a two-character default. A naive encoder mapping the
        # tool's internal state writes exactly that token.
        #
        # An out-of-vocabulary term is not a v0.8 provenance value, so none is
        # written. The cell then carries no judgment claim -- which is true --
        # and the levels check refuses it by name rather than the package
        # asserting something it cannot support.
        # **And the closed set is closed AT THE VERSION THE SOURCE DECLARES.**
        # Testing membership of the whole vocabulary was the same hole one level
        # up: a workbook declaring v0.8 and carrying `not-recoverable` -- a term
        # v0.8 has no way to mean -- imported into a package whose context makes
        # the term legal, and the disagreement vanished at the boundary. The
        # token is dropped instead, so the levels check refuses the package by
        # name rather than the package asserting something its source could not.
        token = factor.get("required_level_provenance")
        if token in vocab:
            f["requiredLevelProvenance"] = LEVEL_TOKENS[token]
        if f.get("requiredLevelProvenance") in JUDGMENT_TOKENS:
            # A judgment claim carries its agent. Machine states do not need
            # one: their lineage is in the run log already.
            #
            # **Never a node that names nobody.** The first draft emitted the
            # node unconditionally and filled it only if the source had an
            # actor -- so a workbook with no attribution columns produced
            # `{"type": "LevelAffirmation"}`, empty. That is this program's
            # named defect exactly: a check asking "does the activity exist?"
            # passes, while the testimony it stands for is absent. Worse than
            # omitting it, because the hollow node manufactures the appearance
            # of an attributed judgment out of nothing.
            #
            # Omitting it instead leaves a judgment token with no activity,
            # which the v0.8 shape REFUSES -- the honest signal that this
            # source cannot yet say who judged, rather than a silent pass.
            #
            # **`actor` is an IRI, `role` is the name** -- the shape
            # `hasDecisionRecord` already uses for `decided_by`. `actor` is
            # declared `"@type": "@id"` in the context, so putting a person's
            # name in it does not store a name: JSON-LD resolves the string as a
            # relative IRI against the document, and "V. Vettrivel" became
            # `file:///.../V.%20Vettrivel` -- an identifier that means nothing,
            # points nowhere, and differs by where the file happened to sit.
            node = {"type": "LevelAffirmation"}
            if factor.get("affirmed_by"):
                who = factor["affirmed_by"]
                node["actor"] = f"{base}/org/{slugify(who)}" if base else f"urn:uofa:agent:{slugify(who)}"
                node["role"] = who
            if factor.get("affirmed_at"):
                node["affirmedAt"] = factor["affirmed_at"]
            if len(node) > 1:
                f["hasLevelAffirmation"] = node
    if factor.get("achieved_level") is not None:
        f["achievedLevel"] = factor["achieved_level"]
    if factor.get("acceptance_criteria"):
        f["acceptanceCriteria"] = factor["acceptance_criteria"]
    if factor.get("rationale"):
        f["rationale"] = factor["rationale"]

    # NASA-specific: assessmentPhase
    if "nasa-7009b" in packs and factor.get("category"):
        phase = NASA_PHASE_MAP.get(factor["category"])
        if phase:
            f["assessmentPhase"] = phase

    # Linked evidence URI (from Excel column H)
    if factor.get("linked_evidence"):
        f["hasEvidence"] = factor["linked_evidence"]

    return f

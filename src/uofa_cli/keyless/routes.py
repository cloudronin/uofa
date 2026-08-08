"""Pattern routes: regular expressions that beat a null model that reads nothing.

Moved here verbatim from the dev candidate scripts, which now import from this
module. One implementation, because twelve standalone scripts each re-reading
documents their own way is how two candidates came to be scored against binary
garbage and reported as failures.

## What each is worth, measured

| route | property | measured |
|---|---|---|
| definitional match (K7) | `hasContextOfUse` | first candidate 0.300; **restraint on 7009A 9/10 and 4/4** |
| risk table (K8) | `modelRiskLevel` | 5 of 6 real documents, one named failure |
| named entities (K3c) | `bindsModel` / `bindsDataset` | 0.418 / 0.088 against 0.075 / 0.000 |

**K7's restraint half is the valuable half.** NASA-STD-7009A defines no context of
use, so the correct answer on such a document is silence -- and K7 gives it on 9
of 10 and 4 of 4. Knowing a property does not apply is a different capability
from finding it, and it is the one a fabricating extractor cannot fake.

**K8 returns `not_derivable` rather than guessing.** The risk table is keyed only
on gradations the standard defines; a paper that renames an input or grades it
"deemed conservative" gets a named refusal, not a mapped-on value.
"""
from __future__ import annotations

import re


# ── context of use (K7) ───────────────────────────────

_ABOUT = re.compile(
    r"\b(context of use|COU)\b.{0,60}\b(is (presented|described|defined|given)|"
    r"section|table|figure|following|below|above|proposed context)\b|"
    r"^\s*(starting from|based on|according to)\b", re.I)


# The term, or a synonym, followed by a copula: a sentence DEFINING the context
# of use rather than referring to one. `_ABOUT` still removes the referring kind.
_DEFN = re.compile(
    r"\b(context of use|COU|intended (use|application)|question of interest)\b"
    r"[^.]{0,40}?\b(is|are|was|were|comprises?|covers?|will be|shall be)\b", re.I)


def find_context_of_use(sents: list[str], pool: list[int]) -> list[int]:
    """Sentence indices defining a context of use, best-first.

    Definitional statements first, since they carry it 15 times in 20 on the
    train set against 11 for naming the term alone. The shape route is NOT
    appended: it adds one hit and drops 7009A restraint from 9/10 to 3/10.
    """
    return [i for i in pool
            if _DEFN.search(" ".join(sents[i].split()))
            and not _ABOUT.search(" ".join(sents[i].split()))]


# ── model risk (K8) ──────────────────────────────────

# standard defines are keys -- a value it does not define must not be silently
# mapped onto one, which is the whole point of the `not_derivable` branch.
_RISK_TABLE: dict[tuple[str, str], str] = {}
_LEVELS = ("low", "medium", "high")
for _i, _inf in enumerate(_LEVELS):
    for _j, _dc in enumerate(_LEVELS):
        _RISK_TABLE[(_inf, _dc)] = _LEVELS[min(2, max(_i, _j))]

# The gradation is stated as a CONCLUSION after the rationale, not next to the
# label. Morrison:
#
#   ...will be identified from the CFD results -> Low
#   Decision Consequence: if the pump causes high levels of hemolysis while the
#   patient is in the surgical suite, then the pump can be replaced -> Medium
#   Model Risk: Low-medium (level 2)
#
# A first-match rule captured "high" from "high levels of hemolysis" -- the
# hazard being described, not the value being assigned -- and Morrison then
# scored agreement=match by coincidence. Take the LAST gradation before the next
# label instead, which is where the assignment sits.
_LABEL = r"(?:model influence|decision consequence|regulatory impact|model risk)"
_GRADE = re.compile(r"\b(low|medium|high)\b", re.I)

# Citations look like risk levels. "accounting for its risk level [3,4]" yielded
# a stated risk of "3" on Bologna, from a bibliography reference.
_CITATION = re.compile(r"\[[\d,\s-]+\]")

# Compound values the standard does not define -- Morrison's "Low-medium
# (level 2)", Nagaraja's "High-Medium". Recorded rather than resolved: picking
# one half would be inventing a gradation the authors declined to state.
_COMPOUND = re.compile(r"\b(low|medium|high)\s*[-/]\s*(low|medium|high)\b", re.I)


def _segment_after(text: str, label: str) -> str | None:
    """Text between this label and the next one -- where its value is assigned."""
    m = re.search(label + r"\s*:?", text, re.I)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(_LABEL, rest, re.I)
    return rest[:nxt.start()] if nxt else rest[:400]


def _graded(text: str, label: str) -> str | None:
    """The gradation assigned to `label`: the last one before the next label."""
    seg = _segment_after(text, label)
    if seg is None:
        return None
    hits = _GRADE.findall(_CITATION.sub(" ", seg))
    return hits[-1].lower() if hits else None

# Terms a paper may put in place of one of the two inputs. Detected so the
# substitution can be NAMED rather than guessed at or silently accepted.
_SUBSTITUTES = ("regulatory impact",)

# Values used where the standard expects a gradation.
_NON_GRADATION = re.compile(
    r"(?:model influence|decision consequence)[^.]{0,60}?\bdeemed (\w+)\b", re.I)


def _locate(label: str, sents: list[str], pool: list[int]) -> tuple[str | None, str | None]:
    """(gradation, the verbatim sentence carrying the label) or (None, None)."""
    for i in pool:
        s = " ".join(sents[i].split())
        if re.search(label, s, re.I):
            g = _graded(s, label)
            if g:
                return g, s
    return None, None


def assess(sents: list[str], pool: list[int]) -> dict:
    """The fixed output record. Every field is a verbatim span or null."""
    inf_v, inf_s = _locate(r"model influence", sents, pool)
    dc_v, dc_s = _locate(r"decision consequence", sents, pool)
    risk_v, risk_s = _locate(r"model risk|risk rating", sents, pool)
    # A compound stated risk is not a gradation the table can be compared to.
    compound = None
    if risk_s:
        m = _COMPOUND.search(_CITATION.sub(" ", risk_s))
        if m:
            compound = m.group(0).lower()
            risk_v = None

    sub = None
    for i in pool:
        low = " ".join(sents[i].split()).lower()
        for term in _SUBSTITUTES:
            if term in low and "model influence" not in low:
                sub = term
                break
        if sub:
            break
    # A non-gradation value given to a defined input is also a substitution --
    # of the value rather than the name.
    if sub is None:
        for i in pool:
            m = _NON_GRADATION.search(sents[i])
            if m and m.group(1).lower() not in _LEVELS:
                sub = m.group(1).lower()
                break

    derived = None
    if inf_v and dc_v:
        derived = _RISK_TABLE.get((inf_v, dc_v))

    if derived is None:
        agreement = "not_derivable"
    elif risk_v is None:
        agreement = "not_derivable"
    else:
        agreement = "match" if risk_v == derived else "mismatch"

    if compound and sub is None:
        sub = compound
    return {"stated_risk": risk_s, "decision_consequence": dc_s,
            "model_influence": inf_s, "substituted_term": sub,
            "derived_risk": derived, "agreement": agreement}


# ── named entities (K3c) ─────────────────────────────

_OVERLAP = 0.60


_FILLER = {"the", "of", "to", "a", "an", "and", "for", "in", "on", "with", "model",
           "models", "simulation", "framework"}


def _words(x: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{2,}", x.lower()) if w not in _FILLER}


# A MAJORITY of the longer name's words, not half. At exactly half,
# "knee simulator" matched "AMTI sixstation knee simulator" -- and the words it
# drops are the distinguishing ones, so it names a category rather than that rig.
# Genuine abbreviations are handled by the acronym path, which is why this can be
# strict without penalising "IO-ECM".
_OVERLAP = 0.60


def names_match(gold: str, proposed: str) -> bool:
    """Same entity, allowing for abbreviation and punctuation.

    Overlap is measured against the LONGER of the two, not as a subset test. A
    symmetric subset rule is fine for proper names and catastrophic for the long
    clauses gold records as requirement names: against

        "energy balance artifacts <=1% and maximum penetration <=0.02 mm
         support 8-10 on solver control"

    the bare word "balance" satisfied `p <= g` and counted as naming that
    requirement. Every short fragment did. bindsRequirement measured 0.387 that
    way, and the number was fragments.

    The acronym path survives, because it is the one case where a short proposal
    genuinely names a long entity: papers write "IO-ECM" far more often than
    "Implant-Only Explicit Contact Model", and both name the same model.
    """
    g, p = _words(gold), _words(proposed)
    if not g or not p:
        return False
    acro = {t for t in re.findall(r"\b([A-Z][A-Z0-9-]{2,})\b", gold)}
    if acro & {t.upper() for t in re.findall(r"[A-Za-z0-9-]{3,}", proposed)}:
        return True
    return len(g & p) / max(len(g), len(p)) >= _OVERLAP


# One pattern per kind, because the three are named differently in prose.
_PATTERNS = {
    "models": re.compile(
        r"\b([A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*){0,5}\s+"
        r"(?:Model|Simulation|Framework|Analysis))\b|"
        r"\b([A-Z][A-Z0-9]{2,}(?:-[A-Z0-9]+)*)\b"),
    "datasets": re.compile(
        r"\b([A-Z][A-Za-z0-9-]*(?:\s+[A-Za-z0-9-]+){0,4}\s+"
        r"(?:dataset|data\s?set|corpus|campaign|series|cohort|specimens?|"
        r"measurements?|tests?|trials?|bench(?:top)?|rig|study))\b|"
        r"\b(ISO\s?\d{3,5}[\w-]*|ASTM\s?[A-Z]?\d+[\w-]*)\b", re.I),
    "acceptance_criteria": re.compile(
        r"\b((?:within|below|above|less than|greater than|no more than|at least)\s+"
        r"[\d.]+\s*(?:%|mm|MPa|N|kPa|s|Hz|micro\w*|percent)?[\w\s-]{0,24})\b|"
        r"\b([A-Za-z][\w\s-]{2,28}\s+(?:criterion|criteria|requirement|"
        r"acceptance\s+limit|tolerance|threshold|target))\b", re.I),
}


def propose(kind: str, text: str, cap: int = 12) -> list[str]:
    """Names a keyless reader would put forward for this kind, most frequent first."""
    counts: dict[str, int] = {}
    for m in _PATTERNS[kind].finditer(text):
        name = next((g for g in m.groups() if g), "").strip()
        if len(name) > 2:
            counts[name] = counts.get(name, 0) + 1
    return [n for n, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:cap]]


def propose_models(text: str, cap: int = 12) -> list[str]:
    return propose("models", text, cap)

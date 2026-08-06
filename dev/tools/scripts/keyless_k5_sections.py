#!/usr/bin/env python3
"""K5: lift the decision and the acceptance criteria out of headed sections.

The last two properties with a plausible keyless route. Unlike a credibility
factor, a decision is *announced*: engineering documents put it under a heading
and state it in a sentence with a small, closed vocabulary. That is the kind of
structure a pattern can exploit and an embedding cannot improve on.

## The baseline is real here, unlike everywhere else

`control_constant_decision` answers "Accepted" always and scores **0.815** --
because 66 of 81 bundles were accepted, which is what a corpus of written-up
assessments looks like. That is beatable, unlike the 0.96 detection ceiling,
so this is the first candidate whose kill criterion is not a formality.

    KILL K5 if outcome accuracy <= 0.815

## Selection error, again

K5 has no fabrication immunity: lifting a sentence from the wrong section --
a decision about a *previous* revision, or a recommendation that was not
adopted -- is verbatim and therefore invisible to groundedness. Outcome
accuracy against `expected_decision.outcome` is what catches it, and rationale
keyword recall says whether the *reasoning* came from the right place too.

## The result: there is nothing to extract in 78% of bundles

K5 abstains on 44 of 49 and scores 0.061. That is not weak section-finding --
the rationale keywords land inside the section it chose 73% of the time, so it
is looking in the right place. The target is not there:

    documents containing ANY accept/reject wording   11/49  (22%)
    of those, a whole-document scan matches GT        9/11

In 38 of 49 bundles the outcome is stated nowhere in the source. These
documents have no decision section -- many have no markdown headings at all,
the slide format uses "Slide 7 --", reports use numbered sections. The
`expected_decision.outcome` in ground truth is the generator's **inference**,
not a span anyone could extract.

### And the LLM is inferring too

    sonnet emitted an outcome in                     35 bundles
    of which the source states no outcome at all     27  (77%)
    sonnet matches ground truth                      0.914
    control_constant_decision (always Accepted)      0.878

Sonnet invents the decision in three cases out of four and scores 0.036 above a
constant for it. `hasDecisionRecord` reads as 100% populated in the schema
coverage table; for most bundles that populated value is fabricated.

For a credibility tool this is worse than an empty field. An absent decision is
visibly absent; an invented one is indistinguishable from a recorded one, and
the whole point of the artefact is that a reader can tell which claims are
evidenced.

**The honest verdict on K5 is "unmeasurable, and the corpus is the reason" --
the same shape as detection, and it applies to the LLM as much as to keyless.**

## "Conditionally accepted" is Accepted

The shape allows only `Accepted` / `Not accepted`, and both extract prompts
used to offer a third value that 26 packages then failed validation for
emitting. An acceptance carrying conditions is `Accepted` with the conditions
in the rationale, so K5 maps it that way rather than reintroducing the defect.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_k2_extractive import sentences  # noqa: E402

_DECISION_HEAD = re.compile(
    r"^\s*#{1,6}\s*\d*\.?\s*(decision|disposition|conclusion|recommendation|"
    r"approval|acceptance|verdict|outcome|sign[- ]?off)\b.*$", re.I | re.M)

_CRITERIA_HEAD = re.compile(
    r"^\s*#{1,6}\s*\d*\.?\s*(acceptance criteri|success criteri|pass[/ ]fail|"
    r"adequacy criteri|acceptance threshold).*$", re.I | re.M)

# Ordered: a negation must be tested before the bare positive it contains.
_NOT_ACCEPTED = re.compile(
    r"\b(?:not accepted|not approved|rejected|declined|denied|"
    r"cannot be accepted|is not (?:accepted|approved|adequate|sufficient)|"
    r"do(?:es)? not (?:meet|satisfy)|insufficient for (?:the )?(?:intended )?use|"
    r"unfit|withheld)\b", re.I)
_ACCEPTED = re.compile(
    r"\b(?:accepted|approved|adequate for|sufficient for|fit for (?:the )?purpose|"
    r"cleared for|authoris?ed for|endorsed|conditionally accepted|"
    r"accepted with (?:conditions|caveats)|recommended for use)\b", re.I)


def section_after(text: str, head: re.Pattern) -> str | None:
    """Text between a matching heading and the next heading of any level."""
    m = head.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^\s*#{1,6}\s+\S", rest, re.M)
    return (rest[:nxt.start()] if nxt else rest).strip() or None


def extract_decision(text: str) -> tuple[str | None, str]:
    """(outcome, rationale text) from the decision section, or the whole doc."""
    sec = section_after(text, _DECISION_HEAD)
    scope = sec if sec else text[-4000:]      # fall back to the tail, where
                                              # a conclusion usually sits
    neg = _NOT_ACCEPTED.search(scope)
    pos = _ACCEPTED.search(scope)
    if neg and (not pos or neg.start() < pos.start()):
        return "Not accepted", scope
    if pos:
        return "Accepted", scope
    return None, scope


def extract_criteria(text: str) -> str | None:
    return section_after(text, _CRITERIA_HEAD)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=Path,
                    default=_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.glob("bundle_*"))
               if (b / "ground_truth.json").exists() and (b / "source").is_dir()]

    n = k5_right = const_right = abstained = 0
    kw_found = kw_total = 0
    crit_found = 0

    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        dec = gt.get("expected_decision") or {}
        want = dec.get("outcome")
        if not want:
            continue
        n += 1
        src = "\n".join(p.read_text(errors="ignore")
                        for p in sorted((b / "source").glob("*")))

        got, scope = extract_decision(src)
        if got is None:
            abstained += 1
        elif got == want:
            k5_right += 1
        if want == "Accepted":
            const_right += 1

        low = " ".join(scope.split()).lower()
        for kw in dec.get("rationale_keywords") or []:
            kw_total += 1
            if " ".join(str(kw).split()).lower() in low:
                kw_found += 1

        if extract_criteria(src):
            crit_found += 1

    acc = k5_right / n if n else 0.0
    const = const_right / n if n else 0.0
    print(f"\nK5 — headed-section extraction   ({n} bundles)\n")
    print(f"  decision outcome")
    print(f"    K5                        {acc:.3f}  ({k5_right}/{n}, "
          f"{abstained} abstained)")
    print(f"    control_constant_decision {const:.3f}  (always 'Accepted')")
    print(f"    delta                     {acc - const:+.3f}")
    print(f"\n  rationale keywords inside the section K5 chose")
    print(f"    {kw_found}/{kw_total} ({kw_found/max(kw_total,1):.3f}) — says whether the")
    print(f"    reasoning came from the same place as the outcome")
    print(f"\n  acceptance criteria section found in {crit_found}/{n} bundles")
    print(f"\n  KILL CRITERION: outcome accuracy > {const:.3f}")
    print(f"  -> {'PASSES' if acc > const else 'FAILS'}")
    print(f"\n  Synthetic only — real-document transfer unverified (V1 deferred).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

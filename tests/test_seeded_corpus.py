"""Guards on the seeded generator, and the contamination rules it enforces.

Nothing here makes an API call. The expensive failures this file exists to
prevent are the cheap ones to test: a held-back document used as a seed, gold and
its agreement check from one model family, a generator that stops withholding
factors, and prose that reaches LaTeX unescaped.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

pytest.importorskip("pdfplumber")

import generate_seeded_corpus as G  # noqa: E402
import latex_render as LR  # noqa: E402

PY = sys.executable
SCRIPT = _ROOT / "dev" / "tools" / "scripts" / "generate_seeded_corpus.py"


def _run(*flags, tmp):
    return subprocess.run(
        [PY, str(SCRIPT), "--count", "2", "--output-root", str(tmp), "--dry-run",
         *flags], capture_output=True, text=True, cwd=_ROOT)


# ------------------------------------------------------------------- guards

def test_held_back_documents_cannot_seed_generation(tmp_path):
    """elemance and morrison are the measurement surface, not training input.

    They are also valid seed names, so this must not fall through to "unknown
    seed" -- which is what happened when the membership check ran first and made
    this branch unreachable.
    """
    for name in G.HELD_BACK:
        r = _run("--seeds", name, tmp=tmp_path)
        assert r.returncode == 1
        assert "held back" in r.stderr + r.stdout
        assert "unknown seed" not in r.stderr + r.stdout


def test_gold_and_agreement_must_be_different_families(tmp_path):
    """Same family twice measures determinism, not reliability."""
    r = _run("--gold-model", "gpt-5", "--agreement-model", "gpt-5", tmp=tmp_path)
    assert r.returncode == 1
    assert "same family" in r.stderr + r.stdout

    ok = _run("--gold-model", "gpt-5", "--agreement-model", "claude-sonnet-4-6",
              tmp=tmp_path)
    assert ok.returncode == 0


def test_dry_run_makes_no_network_call_and_still_proves_the_render_path(tmp_path):
    """The lesson from the sparse campaign: a guard never dry-run cost a day."""
    r = _run(tmp=tmp_path)
    assert r.returncode == 0
    assert "no API calls made" in r.stdout
    assert (tmp_path / "_dryrun" / "paper.pdf").exists()


class _FakeBackend:
    """Records what generate() was handed, so the call can be inspected."""

    model_name = "gpt-5"

    def __init__(self, reply="{}"):
        self.reply, self.calls = reply, []

    def generate(self, prompt, options):
        self.calls.append((prompt, options))
        return self.reply


def test_ask_passes_the_step_timeout_not_the_prompt():
    """Pins the argument order.

    An edit once put the step name before the prompt at the call sites while the
    signature still took it second, so the entire prompt became the TIMEOUTS key
    and every paper died with a KeyError whose message was the prompt. Free to
    catch here, and it cost a whole run to notice.
    """
    b = _FakeBackend('{"ok": 1}')
    text, ti, to = G._ask(b, "write", "PROMPT BODY", max_tokens=999)
    prompt, opts = b.calls[0]
    assert prompt == "PROMPT BODY"
    assert opts.timeout_seconds == G.TIMEOUTS["write"]
    assert opts.max_tokens == 999
    assert text == '{"ok": 1}' and ti > 0 and to > 0


@pytest.mark.parametrize("step", ["plan", "write", "gold"])
def test_every_step_has_a_timeout(step):
    assert G.TIMEOUTS[step] >= 300.0
    G._ask(_FakeBackend(), step, "x")


def test_empty_response_fails_loudly():
    """gpt-5 returns "" when reasoning exhausts the completion budget.

    Passing that to the JSON parser produces a JSONDecodeError that names the
    wrong cause, so the budget never gets raised.
    """
    with pytest.raises(RuntimeError, match="empty response"):
        G._ask(_FakeBackend("   "), "write", "x")


def test_family_detection():
    assert G._family("gpt-5") == "openai"
    assert G._family("openai/gpt-5") == "openai"
    assert G._family("claude-sonnet-4-6") == "anthropic"
    assert G._family("anthropic/claude-opus-4-7") == "anthropic"


# ------------------------------------------------------- structural omission

def test_scope_withholds_a_real_fraction_of_the_checklist():
    """R5's mechanism. Asked in a prompt, the model omitted 8-21% against a 40%
    target however it was worded; naming the INCLUDED subset makes it structural.
    """
    for std in ("V&V40", "7009A"):
        facs = G._factors(std)
        scope = G.sparse_scope(facs, "bundle_seeded_000_bologna")
        withheld = len(facs) - len(scope)
        assert withheld / len(facs) >= 0.30, (
            f"{std}: only {withheld}/{len(facs)} withheld; the >=30%-absent "
            "guard downstream would have nothing to check")


def test_scope_varies_across_bundles_but_is_reproducible():
    """A fixed subset would leave the same factors unrepresented corpus-wide."""
    facs = G._factors("V&V40")
    a = G.sparse_scope(facs, "bundle_seeded_000_bologna")
    b = G.sparse_scope(facs, "bundle_seeded_001_bologna")
    assert a != b
    assert a == G.sparse_scope(facs, "bundle_seeded_000_bologna")


def test_domains_are_distinct_so_diversity_is_designed_in():
    """Five papers off one template scored 0.898 mean cosine against a real
    0.141. Prose style does not separate papers; subject matter does."""
    devices = [d[0] for d in G.DOMAINS]
    assert len(set(devices)) == len(devices)
    assert len(devices) >= 20, "fewer domains than the 40-paper target repeats"


# ------------------------------------------------------------ body assembly

def test_model_content_never_becomes_latex_markup():
    """The model returns plain text; every backslash is the renderer's."""
    sections = [{"heading": "Results & Discussion", "level": 1,
                 "paragraphs": [r"error was 5% with \alpha{2} and $x_i$"],
                 "rubric": {"factor": "Model form",
                            "rungs": ["no study", "partial {study}", "full study"]},
                 "figure": "Overview of the 100% case",
                 "table": {"caption": "Levels & basis",
                           "rows": [["Model form", "2", "50% of cases"]]}}]
    spec = dict(LR.demo_spec(0))
    spec["body"] = G.build_body(sections)
    assert LR.validate(LR.render(spec)) == []
    assert r"\textbackslash{}alpha" in spec["body"]
    assert r"5\%" in spec["body"]


def test_body_assembly_tolerates_absent_optional_blocks():
    body = G.build_body([{"heading": "Introduction", "level": 1,
                          "paragraphs": ["text"], "rubric": None,
                          "figure": None, "table": None}])
    assert r"\section{Introduction}" in body
    assert "tabular" not in body


def test_gold_is_given_the_standards_checklist():
    """Without it, gold invents labels that are not factors.

    One pilot bundle came back with "Credibility matrix", "Credibility rating"
    and "Model Risk Analysis (ASME V&V 40)" -- zero of ten names in common with
    the standard's list, because the prompt asked for factors without ever
    saying which factors exist.
    """
    assert "{factors}" in G.GOLD_PROMPT
    filled = G.GOLD_PROMPT.format(models="M", mechanisms="X", document="D",
                                  factors="\n".join(f"- {x}" for x in G._factors("V&V40")))
    assert "Model form" in filled
    assert "not on this list is not a credibility factor" in filled


def test_gold_gets_the_full_checklist_not_the_sparse_scope():
    """Otherwise selection agreement measures who knew the scope, not who read.

    The agreement annotator is offered the full standard; gold must be too, or
    gold holds the withheld subset and the comparison is rigged.
    """
    full = G._factors("V&V40")
    sparse = G.sparse_scope(full, "bundle_seeded_000_bologna")
    assert len(sparse) < len(full), "sparse_scope must actually withhold"
    # The call site passes _factors(standard); pin that it is not the scope.
    src = (_ROOT / "dev" / "tools" / "scripts" / "generate_seeded_corpus.py").read_text()
    assert "factors=\"\\n\".join(f\"- {x}\" for x in _factors(standard))" in src, \
        "gold must be handed the full checklist, not this paper's scope"


@pytest.mark.parametrize("standard,expect_names", [
    ("V&V40", "Model form"),
    ("7009A", None),
])
def test_each_standard_has_its_own_factor_vocabulary(standard, expect_names):
    """A 7009A paper annotated with V&V 40 names cannot agree with its own gold.

    This is D1's recorded lesson. Ignoring it produced a selection agreement of
    0.184 -- a vocabulary mismatch reported as a reading disagreement.
    """
    names = G._factors(standard)
    assert names
    if expect_names:
        assert expect_names in names
    else:
        assert set(names) != set(G._factors("V&V40"))


@pytest.mark.parametrize("v", ["3", "b", "Medium", "low-medium", "7/12", "Level 2",
                              "High-Medium", "0", "5", "6", "12", "3.5", "9-10"])
def test_gradations_are_accepted_including_R6_deviations(v):
    """R6 requires each paper to deviate somewhere, so compound levels and
    private numeric scales are legitimate and must not be filtered out.

    This was bounded to [0-5] and therefore REJECTED the deviation the spec
    mandates: a paper scoring on its own 0-12 "Explicit FEA Credibility Index"
    had 39 of its 64 table rows scored 6, the generator reported that as a
    coverage failure, and the paper was regenerated twice while the writer had
    produced the full grid correctly every time.
    """
    assert G._GRADATION.match(v), f"{v!r} is a gradation and was rejected"


@pytest.mark.parametrize("v", ["Global", "Gait", "Edge loading", "3.0 mm", "90 um",
                              "unspecified", "not stated", "", "mechanism-specific"])
def test_non_gradations_are_rejected(v):
    """Every one of these appeared in a pilot paper's level column."""
    assert not G._GRADATION.match(v), f"{v!r} is not a gradation and was accepted"


def test_levels_come_from_the_table_not_from_a_model_rereading_it():
    """And rows that do not carry a gradation are not levels at all.

    Three pilot papers produced, respectively, "Global" in every level cell, a
    device-parameter table ("Stent OD", "Strut thickness"), and no table. Gold
    reported those faithfully -- the fault was that the write prompt never
    defined the column, and nothing checked the result.
    """
    sections = [
        {"heading": "Results", "table": {"caption": "Credibility", "rows": [
            ["Model form - Model 1 - gait", "3", "basis"],
            ["Test samples - Model 1 - gait", "low-medium", "basis"],
            ["Governing choices - Model 1 - gait", "Global", "not a gradation"],
        ]}},
        {"heading": "Device", "table": {"caption": "Parameters", "rows": [
            ["Stent OD", "3.0 mm", "labeling size"],
            ["Strut thickness", "90 um", "measured"],
        ]}},
    ]
    lv = G.factor_levels(sections)
    assert lv == {"model form - model 1 - gait": "3",
                  "test samples - model 1 - gait": "low-medium"}


def test_a_paper_without_a_usable_factor_table_is_rejected():
    """R3 and R8 were in the spec and absent from the prompt actually sent."""
    thin = [{"heading": "R", "table": {"caption": "c",
                                       "rows": [["Model form", "3", "b"]]}}]
    # 1 gradation row against a paper assessing, say, 2 models x 3 mechanisms
    # x 7 factors is nowhere near the coverage R8 asks for.
    assert len(G.factor_levels(thin)) / (2 * 3 * 7) < G._MIN_TABLE_COVERAGE


def test_seed_reading_never_touches_ground_truth(monkeypatch):
    """Generation may see a seed's DOCUMENT and never its labels."""
    opened: list[str] = []
    real_read = pathlib.Path.read_text

    def spy(self, *a, **k):
        opened.append(self.name)
        return real_read(self, *a, **k)

    monkeypatch.setattr(pathlib.Path, "read_text", spy)
    G._seed_text("bologna", chars=500)
    assert not any("ground_truth" in n or "extracted" in n for n in opened), opened


@pytest.mark.parametrize("bad,note", [
    ('{"a": "x \\sep y", "sections": [1]}', "invalid escape"),
    ('{"a": 1, "sections": [1, 2,]}', "trailing comma in array"),
    ('{"sections": [1], "b": {"c": 1,},}', "trailing comma in object"),
])
def test_common_model_json_slips_are_repaired_without_loss(bad, note):
    """Both cost a whole paper, and the second cost it silently.

    An invalid escape killed 66,000 chars of otherwise perfect JSON over two
    characters. A trailing comma was worse: the salvage path truncates at the
    last position that parses, and the comma sat just before the credibility
    table, so recovery returned a document whose only surviving table was device
    parameters -- the artefact the run existed to produce was in the discarded
    half, and nothing said so.
    """
    got, lost = G.parse_or_salvage(bad)
    assert got.get("sections"), note
    assert lost == 0, f"{note}: repaired content should not need truncating"


def test_salvage_still_truncates_genuinely_incomplete_json():
    """Repair must not paper over a response that really was cut off."""
    truncated = '{"title": "t", "sections": [{"heading": "a"}, {"heading": "b"'
    got, lost = G.parse_or_salvage(truncated)
    assert [s["heading"] for s in got["sections"]] == ["a"]
    assert lost >= 0


def test_table_coverage_is_measured_against_what_the_paper_assesses():
    """An absolute row floor cannot catch a partial table.

    Measured on the pilot: bologna 42 rows over 39 combinations (1.08),
    nagaraja 63/56 (1.12), opensim 11/73 (0.15). A floor of 6 passed all three.
    Every missing row is a finding with no gradation to read, which is precisely
    where the residual N/A rate came from -- opensim contributed almost all of
    it.
    """
    assert 0.5 < G._MIN_TABLE_COVERAGE <= 1.0
    for rows, combos, want in ((42, 39, True), (63, 56, True), (11, 73, False)):
        assert (rows / combos >= G._MIN_TABLE_COVERAGE) is want, (
            f"{rows}/{combos} should {'pass' if want else 'be regenerated'}")


def test_gold_and_the_annotator_are_asked_the_same_question():
    """Otherwise the agreement score measures the prompts, not the papers.

    Gold enumerates (model x mechanism x factor); D1's annotator judges what the
    paper reports. Left asymmetric, gold labelled factors the papers never
    assess -- 13 of 39 findings on one bundle -- and none of them appeared in
    the authored summary table, so the papers had stayed in scope and gold was
    over-attributing. That depresses selection agreement for a reason that has
    nothing to do with the corpus.

    The discipline D1's prompt carries must therefore be in gold's too.
    """
    from d1_annotator_agreement import PROMPT as ANNOTATOR_PROMPT

    for phrase, why in [
        ("what THIS study did", "the definition of a finding"),
        ("row label", "headings and row labels name a factor without assessing it"),
        ("gradation", "the standard's level definitions are not findings"),
    ]:
        assert phrase.lower() in G.GOLD_PROMPT.lower(), f"gold prompt lacks {why}"
        assert phrase.lower() in ANNOTATOR_PROMPT.lower(), f"annotator prompt lacks {why}"


def test_gold_findings_outside_the_papers_scope_are_dropped():
    """They are wrong, not merely out of scope.

    The plan forbids the factor and the authored summary table does not contain
    it, so the paper demonstrably makes no claim about it. Gold reaches these by
    mapping incidental prose onto the full checklist it is handed: 11 of 34
    findings on one pilot bundle, and all 11 also came back with no gradation --
    there is no table row to read one from. So the N/A residual and the
    out-of-scope residual were the same eleven findings.

    Dropping them removes provably wrong entries from the answer key. It is NOT
    the same as handing gold the scope, which would let gold find things the
    annotator cannot and rig the measure in the flattering direction.
    """
    src = (_ROOT / "dev" / "tools" / "scripts" / "generate_seeded_corpus.py").read_text()
    assert 'dropped_reason["factor-out-of-scope"] += 1' in src
    # and the scope must still be withheld from the gold PROMPT
    assert "{factors}" in G.GOLD_PROMPT
    filled = G.GOLD_PROMPT.format(models="M", mechanisms="X", document="D",
                                  factors="\n".join(G._factors("V&V40")))
    full = G._factors("V&V40")
    assert all(f in filled for f in full), "gold must still see the FULL checklist"


def test_gold_is_multi_reference():
    """A finding carries every sentence that independently evidences it.

    Measured on the pilot: same-sentence agreement 0.509, and every disagreement
    inspected was two DEFENSIBLE picks rather than a gold error -- the same
    finding stated once in the methods and again in the results, or two
    mechanisms each with their own test conditions. A single-span key marks a
    reader who cites the other one wrong, so a router finding a valid
    alternative would have been scored as a miss and every routing result on
    this corpus would have been understated.
    """
    assert '"spans"' in G.GOLD_PROMPT
    assert "List EVERY sentence that independently evidences" in G.GOLD_PROMPT
    src = (_ROOT / "dev" / "tools" / "scripts" / "generate_seeded_corpus.py").read_text()
    assert 'f["spans"] = valid' in src
    assert 'f["span"] = valid[0]' in src, "keep a single-span view for old readers"
    agree = (_ROOT / "dev" / "tools" / "scripts" / "seeded_agreement.py").read_text()
    assert '.extend(spans)' in agree, "the check must credit any valid reference"

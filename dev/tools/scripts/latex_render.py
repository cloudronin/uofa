#!/usr/bin/env python3
r"""LaTeX -> PDF, producing the extraction pathologies on purpose.

The five reader fixes -- column detection, unwrapping, x_tolerance,
dehyphenation, rubric removal -- each rest on one or two real documents. This
renders papers that exhibit the same faults, so those fixes acquire regression
tests and the routing evaluation acquires documents that are hard in the way
real ones are.

## The model writes CONTENT; this file writes every backslash

The plan had the generator emit a whole LaTeX file and budgeted a repair pass for
compile failures. A first attempt here split the difference -- renderer preamble,
model-authored body markup -- and it does not hold up: no regex reliably
separates a model's stray `}` from the renderer's own
`\begin{tabular}{p{0.3\linewidth}}`, and escaping conservatively corrupts one
while escaping liberally corrupts the other. The version that tried it failed to
compile on its own factor table.

So the boundary moved. The model returns a structured spec -- sections, headings,
paragraphs, table rows, rubric rungs -- and every LaTeX token is emitted here.
Prose is escaped aggressively because it is known to contain no markup, which
makes `sanitize()` correct instead of heuristic. Compile failures on model output
effectively disappear, and structural variety survives: the model still chooses
how many sections, what they are called, their order, and where tables, rubrics
and figures fall.

## Why the rubric is NOT the standard's verbatim text

R4 asks for the gradation rubric reproduced, because those definitions survive
segmentation as standalone sentences and outrank findings. Nagaraja carries 45
of them and that is where the pathology was found.

Reproducing ASME's ladder verbatim in every generated paper would put ~45
IDENTICAL sentences in all forty -- which inflates inter-paper similarity
directly against the diversity gate that `corpus_profile.py` just started
enforcing, and needlessly republishes the standard forty times. The pathology is
structural: a bare gradation letter alone on a line, followed by a definition
sentence, in a ladder of increasing rigour. `rubric_block()` generates that shape
with paper-specific wording.

## Pathology rates are asserted, not hoped for

`measure()` reads the compiled PDF back through the project's own reader and
`check()` fails a paper that came out too clean. A paper that compiles without
the faults is a failed generation and is regenerated, not shipped.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

# Per-paper floors, and they answer a DIFFERENT question from corpus_profile's
# bands. Here: did this pathology occur at all -- did the renderer break, did it
# emit markdown. There: is the corpus rate the real rate.
#
# Confusing the two set three of these wrong in a row, always the same way: a
# floor picked from what a typical real paper does, which then rejects the
# atypical real papers. Measured per paper, the five are
#
#     two-column   1.000  0.917  0.875  0.750  0.089   (elemance is 1-column)
#     hyphenation  0.083  0.070  0.059  0.026  0.007
#
# so a floor at the middle of either range fails two of the five documents the
# whole corpus is anchored to. A per-paper criterion that rejects real papers is
# measuring the wrong thing. These floors sit below every real value; the corpus
# mean is what checks the rate.
TARGETS = {
    "two_col_pages": 0.50,   # real per paper: 0.089-1.000; corpus mean 0.726
    "hyphen_lines": 0.005,   # real per paper: 0.007-0.083; corpus mean 0.049
    "rubric_sents": 20,      # real 0, 4, 11, 24, 45
    # Lost inter-word spaces. Measured at pdfplumber's DEFAULT tolerance, where
    # the fault must be present -- reading through the project's own reader
    # measures whether the x_tolerance=1.2 fix works, which is the opposite
    # question. The plan expected to need a special font for one paper in ten;
    # elsarticle's narrow two-column setting produces it unaided at 9.0%, against
    # 10-11% on the two real APL PDFs that were nearly discarded over it. So
    # every generated paper regression-tests that fix rather than one in ten.
    "run_together_default": 0.020,
}
# And the other half of that assertion: the reader must still fix it. Checked as
# a ceiling in `check()`, not a floor.
_MAX_AFTER_FIX = 0.005

# Ceilings, because a pathology can also be too STRONG. These mirror
# corpus_profile.BANDS: without them the renderer called a paper shippable at
# 15.0% hyphenation that the corpus gate then rejected at its 0.12 ceiling, so
# the failure surfaced two steps after the cause and after the paper was paid
# for. A per-paper check that disagrees with the corpus gate is worse than none.
CEILINGS = {"hyphen_lines": 0.12}

_PREAMBLE = r"""\documentclass[5p,times]{elsarticle}
\usepackage[T1]{fontenc}
\usepackage{booktabs}
\usepackage{fancyhdr}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{textcomp}
% Hyphenation is a REQUIRED pathology, and the target is the REAL rate, not the
% maximum one: real papers hyphenate 0.7-8.3% of lines, mean 4.9%.
%
% microtype was originally left out on the reasoning that it would suppress
% hyphenation. That was backwards. Measured on a real generated paper (7,435
% words), without it the rate floors at 10.2% even at \hyphenpenalty=9999 --
% above the real maximum and past corpus_profile's ceiling. Real journal papers
% use microtype, and it is what puts them in range:
%
%     no microtype, pen=500        15.0%   run-together @default  7.6%
%     microtype,    pen=500         8.0%                         16.6%
%     microtype,    pen=2000        6.0%   <- chosen             15.7%
%
% It also strengthens the lost-inter-word-space pathology, because character
% expansion tightens the spacing -- the same mechanism as the two real APL PDFs.
\usepackage{microtype}
\hyphenpenalty=2000
\exhyphenpenalty=2000
\tolerance=1000
\emergencystretch=4em
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\small @@runhead@@}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\journal{Journal of Verification and Validation in Computational Modelling}
\begin{document}
\begin{frontmatter}
\title{@@title@@}
@@authors@@
\begin{abstract}
@@abstract@@
\end{abstract}
\begin{keyword}
@@keywords@@
\end{keyword}
\end{frontmatter}
"""

_END = "\n\\end{document}\n"

# Models reliably emit these unescaped. `{` `}` `~` `^` and bare `\` are here
# because a round-trip test that fed raw document text through an earlier version
# -- which escaped only & % _ # -- produced a silently mangled PDF rather than a
# compile error: a stray `$` opened math mode and swallowed the rest of a
# section. Silent corruption is the bad outcome, since the paper still compiles
# and still measures plausibly.
_ESCAPES = ((re.compile(r"&"), r"\\&"), (re.compile(r"%"), r"\\%"),
            (re.compile(r"_"), r"\\_"), (re.compile(r"#"), r"\\#"),
            (re.compile(r"\$"), r"\\$"), (re.compile(r"\{"), r"\\{"),
            (re.compile(r"\}"), r"\\}"),
            (re.compile(r"~"), r"\\textasciitilde{}"),
            (re.compile(r"\^"), r"\\textasciicircum{}"))
# Applied LAST, after escaping, so the commands introduced here are not
# themselves escaped. Text-mode commands only -- an earlier version mapped to
# `$\leq$`, whose dollars were then escaped into literal text, leaving the
# document with an odd number of them and a `validate()` failure.
_UNICODE = {"\u2014": "---", "\u2013": "--", "\u2018": "`", "\u2019": "'",
            "\u201c": "``", "\u201d": "''", "\u00a0": " ",
            "\u2264": r"\ensuremath{\leq}", "\u2265": r"\ensuremath{\geq}",
            "\u00b1": r"\textpm{}", "\u00d7": r"\texttimes{}",
            "\u00b7": r"\textperiodcentered{}",
            "\u00b5": r"\textmu{}", "\u03bc": r"\textmu{}",
            "\u00b0": r"\textdegree{}",
            "\u03b1": r"\ensuremath{\alpha}", "\u03b2": r"\ensuremath{\beta}",
            "\u03c3": r"\ensuremath{\sigma}", "\u0394": r"\ensuremath{\Delta}"}

# Greek, built from the code points rather than listed. An explicit table caught
# alpha, beta, sigma and Delta and then a real paper used phi, which is a fatal
# pdflatex error -- so the whole alphabet is covered at once instead of one
# letter per failed run.
for _cp, _nm in ((0x3B1, "alpha"), (0x3B2, "beta"), (0x3B3, "gamma"),
                 (0x3B4, "delta"), (0x3B5, "epsilon"), (0x3B6, "zeta"),
                 (0x3B7, "eta"), (0x3B8, "theta"), (0x3B9, "iota"),
                 (0x3BA, "kappa"), (0x3BB, "lambda"), (0x3BC, "mu"),
                 (0x3BD, "nu"), (0x3BE, "xi"), (0x3C0, "pi"), (0x3C1, "rho"),
                 (0x3C3, "sigma"), (0x3C4, "tau"), (0x3C5, "upsilon"),
                 (0x3C6, "phi"), (0x3C7, "chi"), (0x3C8, "psi"),
                 (0x3C9, "omega"), (0x393, "Gamma"), (0x394, "Delta"),
                 (0x398, "Theta"), (0x39B, "Lambda"), (0x3A0, "Pi"),
                 (0x3A3, "Sigma"), (0x3A6, "Phi"), (0x3A8, "Psi"),
                 (0x3A9, "Omega")):
    _UNICODE.setdefault(chr(_cp), rf"\ensuremath{{\{_nm}}}")

# Anything still non-ASCII after the map. A single unmapped character is a FATAL
# pdflatex error, so the default cannot be to pass it through and hope.
_NON_ASCII = re.compile(r"[^\x00-\x7f]")

# `\` cannot be replaced in place: its replacement contains braces, which the
# brace rules would then escape into `\textbackslash\{\}`. Park it first and
# restore it after the escape pass.
_BS = "\x00BACKSLASH\x00"


def sanitize(text: str) -> str:
    """Escape PROSE. Not markup -- prose is never expected to contain any.

    Because the caller guarantees there is no LaTeX here, every special character
    is escaped unconditionally. That is what makes this correct rather than
    heuristic: there is no legitimate `\\command` to preserve, and therefore no
    judgement call about which brace belongs to whom.

    Order is load-bearing. Escaping introduces backslashes and braces, so the
    literal backslash is parked first and the unicode map runs last; doing either
    in the obvious order corrupts its own output.
    """
    text = text.replace("\\", _BS)
    for pat, rep in _ESCAPES:
        text = pat.sub(rep, text)
    text = text.replace(_BS, r"\textbackslash{}")
    for k, v in _UNICODE.items():
        text = text.replace(k, v)
    # Whatever is left: decompose accents to their ASCII base where that works
    # (e.g. e-acute -> e), and drop the rest. Lossy by design -- losing one glyph
    # beats a fatal compile error that discards a paper already paid for.
    if _NON_ASCII.search(text):
        import unicodedata
        text = _NON_ASCII.sub(
            lambda m: unicodedata.normalize("NFKD", m.group(0))
                                 .encode("ascii", "ignore").decode() or "",
            text)
    return text


def validate(tex: str) -> list[str]:
    """Structural problems that make a document compile into the wrong thing."""
    bad = []
    # Unescaped only -- a properly escaped `\$` is literal text, not a delimiter.
    if len(re.findall(r"(?<!\\)\$", tex)) % 2:
        bad.append("unbalanced $")
    depth = 0
    for m in re.finditer(r"(?<!\\)([{}])", tex):
        depth += 1 if m.group(1) == "{" else -1
        if depth < 0:
            bad.append("unmatched }")
            break
    if depth > 0:
        bad.append(f"{depth} unclosed {{")
    for env in set(re.findall(r"\\begin\{(\w+\*?)\}", tex)):
        if tex.count(rf"\begin{{{env}}}") != tex.count(rf"\end{{{env}}}"):
            bad.append(f"unbalanced {env} environment")
    return bad


def rubric_block(factor: str, rungs: list[str]) -> str:
    r"""A gradation ladder in the shape that breaks segmentation.

    Each rung renders as a bare letter alone on its line, then the definition as
    its own sentence -- which is what makes `document_furniture` see a standalone
    rubric definition rather than a finding. `\\` after the letter forces the
    line break inside the narrow column, where a normal list would keep them
    together.
    """
    lines = [rf"\noindent\textit{{{sanitize(factor)} --- gradation.}}",
             r"\begin{quote}\small"]
    for letter, text in zip("abcde", rungs):
        lines.append(rf"{letter}.\\")
        lines.append(rf"{sanitize(text)}\par")
    lines.append(r"\end{quote}")
    return "\n".join(lines)


def factor_table(rows: list[tuple[str, str, str]], caption: str) -> str:
    """The per-factor summary table. R3: the same finding also appears in prose."""
    body = "\n".join(rf"{sanitize(f)} & {sanitize(lvl)} & {sanitize(why)} \\"
                     for f, lvl, why in rows)
    return "\n".join([r"\begin{table}[t]", r"\centering", r"\small",
                      rf"\caption{{{sanitize(caption)}}}",
                      r"\begin{tabular}{p{0.30\linewidth}cp{0.42\linewidth}}",
                      r"\toprule", r"Credibility factor & Level & Basis \\", r"\midrule",
                      body, r"\bottomrule", r"\end{tabular}", r"\end{table}"])


def wide_figure(caption: str) -> str:
    """A full-width float in a two-column paper -- crosses the gutter."""
    return "\n".join([r"\begin{figure*}[t]", r"\centering",
                      r"\rule{0.92\textwidth}{38mm}",
                      rf"\caption{{{sanitize(caption)}}}", r"\end{figure*}"])


def keywords(raw) -> str:
    r"""Keyword list -> `a \sep b \sep c`, with each keyword escaped.

    This was the one field passed through unescaped, because it is the only one
    that legitimately carries a command (`\sep`). Two of three papers in a pilot
    then failed to compile on `ASME V&V 40` as a keyword -- "Misplaced alignment
    tab character &", a fatal error, from a field nobody thought of as prose.

    The separator is now the renderer's, like every other token: split whatever
    the model sent, escape the pieces, rejoin.
    """
    parts = ([str(x) for x in raw] if isinstance(raw, (list, tuple))
             else re.split(r"\\sep|;|,", str(raw)))
    clean = [sanitize(p.strip()) for p in parts if p and p.strip()]
    return r" \sep ".join(clean) or "verification \\sep validation"


def section(heading: str, paragraphs: list[str], level: int = 1) -> str:
    """A heading and its prose. The model supplies both as plain text."""
    cmd = {1: "section", 2: "subsection", 3: "subsubsection"}[level]
    return "\n\n".join([rf"\{cmd}{{{sanitize(heading)}}}",
                        *(sanitize(p) for p in paragraphs)])


def render(spec: dict) -> str:
    """Assemble the full document.

    `spec["body"]` is already LaTeX, built from the helpers above, each of which
    escaped its own text. It is NOT re-sanitised -- doing so was the bug that
    escaped the factor table's own column specification and stopped the document
    compiling.
    """
    auth = "\n".join(rf"\author[{i+1}]{{{sanitize(a)}}}"
                     for i, a in enumerate(spec["authors"]))
    auth += "\n" + "\n".join(rf"\affiliation[{i+1}]{{organization={{{sanitize(o)}}}}}"
                             for i, o in enumerate(spec["affiliations"]))
    head = _PREAMBLE
    for k, v in (("runhead", sanitize(spec["runhead"])),
                 ("title", sanitize(spec["title"])), ("authors", auth),
                 ("abstract", sanitize(spec["abstract"])),
                 ("keywords", keywords(spec["keywords"]))):
        head = head.replace(f"@@{k}@@", v)   # not %-format: the preamble is full
                                             # of LaTeX % comments
    return head + spec["body"] + _END


def compile_pdf(tex: str, out: pathlib.Path, keep: bool = False) -> pathlib.Path:
    """pdflatex twice -- the running head and refs need the second pass."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "paper.tex").write_text(tex)
        for _ in range(2):
            # errors="replace": pdflatex emits the offending bytes of a bad
            # input verbatim, so a strict decode turns a readable LaTeX error
            # into a UnicodeDecodeError from the error handler itself.
            r = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "paper.tex"],
                cwd=d, capture_output=True, text=True, errors="replace")
        if not (d / "paper.pdf").exists():
            log = (d / "paper.log").read_text(errors="replace") if (d / "paper.log").exists() else r.stdout
            err = [ln for ln in log.splitlines() if ln.startswith("!")][:6]
            if keep:
                shutil.copy(d / "paper.tex", out.with_suffix(".failed.tex"))
            raise RuntimeError("pdflatex failed:\n  " + "\n  ".join(err or ["(no ! lines)"]))
        shutil.copy(d / "paper.pdf", out)
    return out


def measure(pdf: pathlib.Path) -> dict:
    """Read the PDF back through the project's own reader and count the faults."""
    import pdfplumber

    from document_furniture import strip_furniture
    from keyless_k2_extractive import sentences
    from uofa_cli import excel_constants as ec
    from uofa_cli.readers.pdf_reader import _find_gutter, read_pdf

    names = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})
    text = "\n".join(c.text for c in read_pdf(pdf))
    ss = sentences(text)
    _, _, reasons = strip_furniture(ss, names)
    pages = split = lines = hy = 0
    with pdfplumber.open(pdf) as doc:
        for pg in doc.pages:
            pages += 1
            if _find_gutter(pg.extract_words(), pg.bbox[0], pg.bbox[2]) is not None:
                split += 1
            ls = [x for x in (pg.extract_text(x_tolerance=1.2) or "").split("\n") if x.strip()]
            lines += len(ls)
            hy += sum(1 for x in ls if re.search(r"[A-Za-z]{2,}-\s*$", x))
    def _rt(tol: float) -> float:
        with pdfplumber.open(pdf) as doc:
            t = "\n".join((pg.extract_text(x_tolerance=tol) or "") for pg in doc.pages)
        w = re.findall(r"[A-Za-z-]+", t)
        return sum(1 for x in w if len(x) > 20) / max(len(w), 1)

    toks = re.findall(r"[A-Za-z-]+", text)
    return {"pages": pages, "sentences": len(ss), "words": len(text.split()),
            "two_col_pages": split / max(pages, 1),
            "hyphen_lines": hy / max(lines, 1),
            "rubric_sents": reasons.get("rubric-definition", 0),
            # The fault as a naive reader sees it...
            "run_together_default": _rt(3.0),
            # ...and as this project's reader sees it, which must be near zero.
            "run_together": sum(1 for w in toks if len(w) > 20) / max(len(toks), 1)}


def check(m: dict) -> list[str]:
    """Which pathology targets this paper missed. Empty means shippable."""
    miss = [f"{k}={m[k]:.3f} < {v}" if isinstance(v, float) else f"{k}={m[k]} < {v}"
            for k, v in TARGETS.items() if m[k] < v]
    miss += [f"{k}={m[k]:.3f} > {v} (too strong; real papers do not do this)"
             for k, v in CEILINGS.items() if m[k] > v]
    if m["run_together"] > _MAX_AFTER_FIX:
        miss.append(f"run_together={m['run_together']:.4f} > {_MAX_AFTER_FIX} "
                    "after the reader fix -- the fix is not holding")
    return miss


# ---------------------------------------------------------------- demo content

_TERMS = ("mesh density", "solver tolerance", "material model", "contact stiffness",
          "boundary condition", "load path", "element type", "time step",
          "friction", "damping", "gap size", "yield stress", "flow rate",
          "inlet profile", "wall roughness", "bone density", "cement mantle")
_OBJ = ("cortical strain", "contact pressure", "hemolysis index", "shear stress",
        "head displacement", "outlet velocity", "peak force", "fatigue life",
        "stress range", "flow split", "rib deflection", "chest compression")
_VERB = ("was measured", "was recorded", "was compared", "was checked",
         "was fixed", "was varied", "was held", "was traced", "was scaled")

# Deliberately varied in length. A pool of only long words over-hyphenates in a
# narrow column regardless of the TeX settings, which is what made an earlier
# demo report 31.9% against a real 0.7-8.3% and read as a renderer fault.
_SHORT = ("The", "A", "This", "Each", "Both", "One", "No", "Two", "All")


def _prose(rng, n: int) -> str:
    """Technical filler with mixed word lengths, figures and citations."""
    out = []
    for _ in range(n):
        t, o, v = rng.choice(_TERMS), rng.choice(_OBJ), rng.choice(_VERB)
        out.append(rng.choice([
            f"{rng.choice(_SHORT)} {t} {v} at {rng.randint(2, 90)} Hz and the "
            f"{o} fell within {rng.randint(3, 18)}\\% of the bench value "
            f"[{rng.randint(1, 40)}].",
            f"Mesh refinement gave a change in {o} of less than "
            f"{rng.randint(1, 9)}\\%, so the {t} was held fixed for all runs.",
            f"Uncertainty in {t} was propagated and reported as an interval on "
            f"{o} of {rng.randint(2, 25)} to {rng.randint(26, 60)} units.",
            f"{rng.choice(_SHORT)} model was run over the range of {t} seen in "
            f"use, and {o} {v} against {rng.randint(3, 12)} test articles.",
            f"Sensitivity of {o} to {t} was ranked {rng.randint(1, 9)} of "
            f"{rng.randint(10, 20)} across the operating envelope.",
            f"Agreement between predicted and measured {o} was satisfactory for "
            f"the key comparisons but not for all of them [{rng.randint(1, 40)}].",
        ]))
    return " ".join(out)


def demo_spec(seed: int = 0) -> dict:
    """A paper built without an API key, to validate the renderer itself."""
    import random
    rng = random.Random(seed)
    facs = ["Code verification", "Calculation verification", "Model form",
            "Model inputs", "Test samples", "Test conditions",
            "Output comparison", "Input pedigree", "Results uncertainty"]
    body = [section("Introduction", [_prose(rng, 11), _prose(rng, 11)]),
            section("Computational model", [_prose(rng, 10), _prose(rng, 10)]),
            wide_figure("Geometry and boundary conditions for both mechanisms, "
                        "shown across the full page width."),
            section("Credibility assessment", [_prose(rng, 16)])]
    for f in facs:
        body.append(section(f, [_prose(rng, 5)], level=2))
        body.append(rubric_block(f, [
            f"No {f.lower()} activity was undertaken for either mechanism.",
            f"A limited {f.lower()} activity was undertaken on a single nominal configuration.",
            f"A comprehensive {f.lower()} activity spanned the expected operating range.",
            f"The {f.lower()} activity spanned the entire parameter range and was independently reviewed.",
        ]))
    body.append(factor_table(
        [(f, rng.choice("0123"), _prose(rng, 1)[:110]) for f in facs],
        "Credibility factor levels for the primary context of use."))
    body.append(r"\section{Discussion}")
    body.append(_prose(rng, 24))
    return {"title": "Credibility assessment of a computational model of the "
                     "implanted proximal femur under physiological loading",
            "runhead": "Credibility assessment of an implanted femur model",
            "authors": ["A. Practitioner", "B. Reviewer"],
            "affiliations": ["Department of Mechanical Engineering"],
            "abstract": _prose(rng, 6),
            "keywords": "verification \\sep validation \\sep credibility",
            "body": "\n\n".join(body)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--demo", action="store_true",
                    help="render a canned paper and report pathology rates")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path("/tmp/latex_render_demo.pdf"))
    args = ap.parse_args()
    if not args.demo:
        raise SystemExit("nothing to do; --demo renders a canned paper")

    pdf = compile_pdf(render(demo_spec(args.seed)), args.out, keep=True)
    m = measure(pdf)
    print(f"\n  {pdf}  ({m['pages']} pages, {m['words']:,} words, "
          f"{m['sentences']} sentences)\n")
    for k, v in TARGETS.items():
        got = m[k]
        ok = got >= v
        shown = f"{got:.3f}" if isinstance(v, float) else f"{got}"
        tgt = f"{v:.3f}" if isinstance(v, float) else f"{v}"
        print(f"  {'PASS' if ok else 'FAIL'}  {k:16s} {shown:>8s}  target >= {tgt}")
    print(f"        {'  ':4s}  {'run_together':16s} {m['run_together']:>8.4f}  "
          f"after the reader fix, must stay <= {_MAX_AFTER_FIX}")
    miss = check(m)
    print(f"\n  {'shippable' if not miss else 'TOO CLEAN: ' + '; '.join(miss)}")
    return 1 if miss else 0


if __name__ == "__main__":
    raise SystemExit(main())

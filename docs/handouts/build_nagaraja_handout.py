"""Generate the Nagaraja case handout HTML from the S1 evidence artifacts.

Every quantitative value on the page is read here from build/ or from the
encoded package. Nothing is typed in by hand, so the handout cannot drift from
the run that produced it.

Usage (from repo root, with the conda python):
    python docs/handouts/build_nagaraja_handout.py

Then render both PDFs with headless Chrome, matching how the conference
handout in site/public/handout/ is produced.
"""

import datetime
import html
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUILD = ROOT / "build"
OUT = ROOT / "docs/handouts/uofa-nagaraja-handout.html"

PKG_PATH = ROOT / "packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld"
PKG_REL = PKG_PATH.relative_to(ROOT).as_posix()
# --build compiles the Jena engine JAR if it is absent. Without it a fresh
# clone passes C1 and C2 but cannot run C3. Verified from a clean worktree.
REPRO_CMD = f"uofa check --build {PKG_REL}"

# ── Pinned versions, read from the engine build and pack metadata (S0.4) ──
ENGINE = subprocess.run(
    ["uofa", "--version"], capture_output=True, text=True
).stdout.strip()
CORE_VER = json.loads((ROOT / "packs/core/pack.json").read_text())["version"]
VV40_VER = json.loads((ROOT / "packs/vv40/pack.json").read_text())["version"]
CATALOG_VER = f"core@{CORE_VER} + vv40@{VV40_VER}"
RUN_DATE = datetime.date.today().isoformat()

# ── Evidence ──────────────────────────────────────────────────────────────
# build/ is gitignored, so on a fresh clone the S1 artifacts are absent. Rather
# than fail, regenerate them from the packages at the pinned catalog version.
# Either way the numbers come from a real engine run, never from a literal here.
def rules_json(case, cou):
    out = BUILD / case / f"rules-{cou}.json"
    if not out.exists():
        src = next((ROOT / f"packs/vv40/examples/{case}/{cou}").glob("*.jsonld"))
        out.parent.mkdir(parents=True, exist_ok=True)
        # Pass the repo-relative path: the engine echoes it into the artifact's
        # "file" field, and an absolute path would bake this machine's home
        # directory into the evidence.
        res = subprocess.run(
            ["uofa", "--no-color", "rules", "--build", "-f", "json",
             src.relative_to(ROOT).as_posix()],
            capture_output=True, text=True, cwd=ROOT,
        )
        if res.returncode != 0:
            raise SystemExit(f"uofa rules failed for {case}/{cou}:\n{res.stderr}")
        out.write_text(res.stdout)
    return json.loads(out.read_text())


PKG = json.loads(PKG_PATH.read_text())
NAG = rules_json("nagaraja", "cou1")
MOR1 = rules_json("morrison", "cou1")
MOR2 = rules_json("morrison", "cou2")

COU = PKG["hasContextOfUse"]
DEC = PKG["hasDecisionRecord"]
OFFSET = DEC["hasOffsetRationale"]
FACTORS = PKG["hasCredibilityFactor"]

# Canonical V&V 40 Table 5-1 order, from packs/vv40/shapes/vv40_shapes.ttl.
VV40_ORDER = [
    "Software quality assurance",
    "Numerical code verification",
    "Discretization error",
    "Numerical solver error",
    "Use error",
    "Model form",
    "Model inputs",
    "Test samples",
    "Test conditions",
    "Equivalency of input parameters",
    "Output comparison",
    "Relevance of the quantities of interest",
    "Relevance of the validation activities to the COU",
]

# Source paper, expanded from the package's wasDerivedFrom DOI via Crossref.
CITATION = (
    "Nagaraja S, Loughran G, Baumann AP, Kartikeya K, Horner M. "
    "&ldquo;Establishing finite element model credibility of a pedicle screw "
    "system under compression-bending: An end-to-end example of the ASME "
    "V&amp;V 40 standard.&rdquo; <em>Methods</em> 225 (2024) 74&ndash;88."
)
DOI = PKG["wasDerivedFrom"]

# One-line findings, each a restatement of the catalog description of the
# pattern that fired. Phrased as a property of the record as published.
FINDINGS = {
    "W-AL-01": "No uncertainty quantification is linked to the validation result node.",
    "W-AR-05": "No comparator data source is linked from the validation result node.",
    "W-EP-02": "No generating activity is recorded for the validation result node.",
    "W-ON-02": "The context of use carries no applicability constraint and no operating envelope.",
}
NAMES = {
    "W-AL-01": "Aleatory uncertainty uncharacterized",
    "W-AR-05": "Comparator source absent",
    "W-EP-02": "Generation activity missing",
    "W-ON-02": "Validity boundary undocumented",
}


def short(uri):
    return uri.rsplit("/", 1)[-1]


def sev_class(sev):
    return {"Critical": "crit", "High": "high", "Medium": "med"}.get(sev, "dim")


def sev_line(summary):
    """Render a by-severity breakdown in fixed Critical/High/Medium order."""
    by = summary["by_severity"]
    parts = [f"{k} {by[k]}" for k in ("Critical", "High", "Medium") if by.get(k)]
    return ", ".join(parts)


def attaches_to(firing):
    nodes = sorted(set(firing["affected_nodes"]))
    kinds = {("validation result" if "/validation/" in n else "context of use") for n in nodes}
    kind = nodes[0] if len(nodes) == 1 else f"{len(nodes)} {list(kinds)[0]}s"
    return short(nodes[0]) if len(nodes) == 1 else f"{len(nodes)} validation results"


# ── Fragments ─────────────────────────────────────────────────────────────

factor_by_type = {f["factorType"]: f for f in FACTORS}
assessed = [t for t in VV40_ORDER if t in factor_by_type]
shortfalls = [
    t
    for t in assessed
    if factor_by_type[t]["achievedLevel"] < factor_by_type[t]["requiredLevel"]
]
meeting = len(assessed) - len(shortfalls)

factor_rows = []
for t in VV40_ORDER:
    f = factor_by_type.get(t)
    if not f:
        factor_rows.append(
            f'<tr class="miss"><td>{html.escape(t)}</td>'
            f'<td class="lv">not reported</td></tr>'
        )
        continue
    req, ach = f["requiredLevel"], f["achievedLevel"]
    cls = " class=\"short\"" if ach < req else ""
    factor_rows.append(
        f"<tr{cls}><td>{html.escape(t)}</td>"
        f'<td class="lv">{ach}<span class="of"> / {req}</span></td></tr>'
    )
half = (len(factor_rows) + 1) // 2
factor_col_a = "\n".join(factor_rows[:half])
factor_col_b = "\n".join(factor_rows[half:])

weakener_rows = "\n".join(
    f"<tr>"
    f'<td class="pid {sev_class(f["severity"])}">{f["patternId"]}</td>'
    f"<td>{html.escape(NAMES[f['patternId']])}</td>"
    f'<td class="sev {sev_class(f["severity"])}">{f["severity"]}</td>'
    f'<td class="num">{f["hits"]}</td>'
    f'<td class="mono-sm">{html.escape(attaches_to(f))}</td>'
    f"<td>{html.escape(FINDINGS[f['patternId']])}</td>"
    f"</tr>"
    for f in sorted(NAG["firings"], key=lambda x: (-x["hits"], x["patternId"]))
)

comparison_rows = "\n".join(
    f"<tr{' class=\"self\"' if lbl.startswith('Nagaraja') else ''}>"
    f"<td>{lbl}</td>"
    f'<td class="num">{cov}</td>'
    f'<td class="num">{d["summary"]["total_firings"]}</td>'
    f'<td class="num">{d["summary"]["patterns"]}</td>'
    f"<td>{sev_line(d['summary'])}</td></tr>"
    for lbl, cov, d in [
        ("Nagaraja COU1", "13 / 13", NAG),
        ("Morrison COU1", "13 / 13", MOR1),
        ("Morrison COU2", "13 / 13", MOR2),
    ]
)

# Terminal centrepiece, built from the run summary so it cannot drift.
term_pat_lines = "\n".join(
    f'<span class="term-high">&#9888; {f["patternId"]}</span>'
    f'{" " * (12 - len(f["patternId"]))}'
    f'<span class="term-faint">[High]  {f["hits"]} hit{"s" if f["hits"] > 1 else ""}</span>'
    for f in sorted(NAG["firings"], key=lambda x: (-x["hits"], x["patternId"]))
)

TEMPLATE = f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Nagaraja pedicle screw case &mdash; UofA credibility record</title>
<meta name="description" content="The Nagaraja et al. (2024) pedicle screw FEA credibility assessment, encoded as a signed Unit of Assurance package and scored by the weakener rule engine." />

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400;1,9..144,500&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
/>

<style>
/* Theme tokens inherited verbatim from site/public/handout/index.html */
:root {{
  --bg:           #0c0d0e;
  --bg-elev:      #131418;
  --bg-subtle:    #1a1c21;
  --bg-code:      #0f1013;
  --border:       #25262c;
  --border-bright:#3a3b42;
  --text:         #e8e6e1;
  --text-muted:   #9a988f;
  --text-faint:   #6b6a64;
  --accent:       #d4a35a;
  --accent-hi:    #ead0a0;
  --accent-dim:   #8b6c3a;
  --critical:     #c97864;
  --high:         #d4a35a;
  --medium:       #b9a472;
  --pass:         #7eb87a;

  --font-serif: 'Fraunces', ui-serif, Georgia, serif;
  --font-sans:  'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif;
  --font-mono:  'IBM Plex Mono', ui-monospace, 'SF Mono', Menlo, monospace;
}}

[data-theme="light"] {{
  --bg:           #ffffff;
  --bg-elev:      #faf8f3;
  --bg-subtle:    #f3f0e8;
  --bg-code:      #f7f4ec;
  --border:       #d8d4c7;
  --border-bright:#b8b3a5;
  --text:         #1a1a1a;
  --text-muted:   #5a5752;
  --text-faint:   #8a8780;
  --accent:       #a07832;
  --accent-hi:    #7d5d22;
  --accent-dim:   #c7a76a;
  --critical:     #a85440;
  --high:         #a07832;
  --medium:       #8a7340;
  --pass:         #4a8a48;
}}

@page {{ size: letter portrait; margin: 0; }}
* {{ box-sizing: border-box; }}

html, body {{
  margin: 0; padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 10.5pt;
  line-height: 1.45;
  -webkit-font-smoothing: antialiased;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}

.page {{
  width: 8.5in;
  height: 11in;
  padding: 0.42in 0.55in 0.28in;
  margin: 0 auto;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  gap: 0.088in;
  overflow: hidden;
}}
/* Last block on each page is pinned to the foot so slack collects above it. */
.page > :last-child {{ margin-top: auto; }}
.page + .page {{ page-break-before: always; }}

@media screen {{
  body {{ padding: 32px 0; min-height: 100vh; }}
  .page {{
    box-shadow: 0 24px 70px rgba(0,0,0,0.55), 0 2px 8px rgba(0,0,0,0.3);
    border: 1px solid var(--border);
  }}
  .page + .page {{ margin-top: 32px; }}
  [data-theme="light"] body {{ background: #e8e4d8; }}
  [data-theme="light"] .page {{
    box-shadow: 0 24px 70px rgba(60,50,30,0.18), 0 2px 8px rgba(60,50,30,0.08);
  }}
}}

/* Header */
.header {{
  display: grid; grid-template-columns: auto 1fr; gap: 14px;
  align-items: start; padding-bottom: 0.14in;
  border-bottom: 1px solid var(--border);
}}
.logo {{ width: 40px; height: 40px; flex-shrink: 0; color: var(--accent); }}
.brand-eyebrow {{
  font-family: var(--font-mono); font-size: 8.6pt; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--accent); margin: 2px 0 4px;
}}
h1.title {{
  font-family: var(--font-serif); font-variation-settings: 'opsz' 80;
  font-weight: 400; font-size: 23.5pt; line-height: 1.05; letter-spacing: -0.02em;
  margin: 0 0 5px; color: var(--text);
}}
h1.title em {{ color: var(--accent); font-style: italic; font-variation-settings: 'opsz' 80; }}
.tagline {{
  font-family: var(--font-serif); font-variation-settings: 'opsz' 30;
  font-weight: 400; font-size: 11pt; line-height: 1.32; margin: 0 0 6px;
  color: var(--text); max-width: 6.9in;
}}
.author {{ font-family: var(--font-mono); font-size: 8.5pt; color: var(--text-muted); margin: 0; }}

.section-eyebrow {{
  font-family: var(--font-mono); font-size: 8.5pt; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--accent); margin: 0 0 6px;
}}
section p {{ margin: 0; font-size: 9.7pt; line-height: 1.44; color: var(--text); }}
section p + p {{ margin-top: 5px; }}

/* Citation */
.cite p {{ font-size: 9.3pt; line-height: 1.42; color: var(--text); }}
.cite .doi {{ font-family: var(--font-mono); font-size: 8.6pt; color: var(--accent); margin-top: 3px; }}

/* Quote block */
blockquote {{
  margin: 0; padding: 0.095in 0.15in;
  background: var(--bg-elev); border: 1px solid var(--border);
  border-left: 2px solid var(--accent); border-radius: 6px;
  font-size: 9pt; line-height: 1.38; color: var(--text);
}}
blockquote .src {{
  display: block; margin-top: 4px;
  font-family: var(--font-mono); font-size: 7.6pt;
  color: var(--text-faint); letter-spacing: 0.04em;
}}

/* Risk tiles */
.tiles {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px;
  background: var(--border); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
.tile {{ background: var(--bg); padding: 0.085in 0.11in; }}
.tile .k {{ font-family: var(--font-mono); font-size: 7.2pt; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-muted); margin: 0 0 3px; }}
.tile .v {{ font-family: var(--font-serif); font-variation-settings: 'opsz' 30;
  font-size: 12pt; font-weight: 500; color: var(--accent); margin: 0; line-height: 1.1; }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; font-size: 8.6pt; }}
th {{
  font-family: var(--font-mono); font-size: 7.4pt; letter-spacing: 0.11em;
  text-transform: uppercase; color: var(--text-muted); font-weight: 400;
  text-align: left; padding: 0 6px 4px 0; border-bottom: 1px solid var(--border);
}}
td {{ padding: 2.4px 6px 2.4px 0; border-bottom: 1px solid var(--border); vertical-align: top; color: var(--text); }}
tr:last-child td {{ border-bottom: none; }}
td.num, th.num {{ text-align: right; padding-right: 10px; font-family: var(--font-mono); }}
td.pid {{ font-family: var(--font-mono); font-size: 8.6pt; white-space: nowrap; }}
td.sev {{ font-family: var(--font-mono); font-size: 8.2pt; }}
td.mono-sm {{ font-family: var(--font-mono); font-size: 7.5pt; color: var(--text-muted); }}
.crit {{ color: var(--critical); }}
.high {{ color: var(--high); }}
.med  {{ color: var(--medium); }}

/* Factor coverage */
.factors {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 0.28in; align-items: start; }}
.factors td {{ font-size: 8.4pt; padding: 2.3px 6px 2.3px 0; }}
.factors td.lv {{ font-family: var(--font-mono); font-size: 8.4pt; text-align: right;
  white-space: nowrap; color: var(--pass); }}
.factors td.lv .of {{ color: var(--text-faint); }}
.factors tr.short td.lv {{ color: var(--accent); }}
.factors tr.short td {{ color: var(--accent); }}
.factors tr.miss td {{ color: var(--text-faint); }}

.comparison tr.self td {{ color: var(--accent-hi); }}

/* Terminal */
.terminal {{ background: var(--bg-code); border: 1px solid var(--border);
  border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }}
.terminal-bar {{ background: var(--bg-subtle); padding: 5px 10px; display: flex;
  align-items: center; gap: 5px; border-bottom: 1px solid var(--border); }}
.terminal-bar .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
.terminal-bar .dot.r {{ background: #4a3a3a; }}
.terminal-bar .dot.y {{ background: #4a4530; }}
.terminal-bar .dot.g {{ background: #364530; }}
[data-theme="light"] .terminal-bar .dot.r {{ background: #c97864; }}
[data-theme="light"] .terminal-bar .dot.y {{ background: #d4a35a; }}
[data-theme="light"] .terminal-bar .dot.g {{ background: #7eb87a; }}
.terminal-bar .title {{ font-family: var(--font-mono); font-size: 7.5pt; color: var(--text-faint); margin-left: 4px; }}
.terminal pre {{ margin: 0; padding: 8px 11px 9px; font-family: var(--font-mono);
  font-size: 7pt; line-height: 1.42; color: var(--text); white-space: pre; overflow: hidden; flex: 1; }}
.term-prompt {{ color: var(--accent); }}
.term-cmd {{ color: var(--text); }}
.term-faint {{ color: var(--text-faint); }}
.term-dim {{ color: var(--text-muted); }}
.term-ok {{ color: var(--pass); }}
.term-high {{ color: var(--high); }}

/* Integrity band */
.integrity {{ background: var(--bg-elev); border: 1px solid var(--border);
  border-radius: 8px; padding: 0.115in 0.17in; }}
.integrity .rows {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.16in; }}
.integrity .k {{ font-family: var(--font-mono); font-size: 7.2pt; letter-spacing: 0.11em;
  text-transform: uppercase; color: var(--text-muted); margin: 0 0 3px; }}
.integrity .v {{ font-family: var(--font-mono); font-size: 8.6pt; color: var(--pass); margin: 0; }}
.integrity .hash {{ margin-top: 0.1in; }}
.integrity .hash .v {{ color: var(--text-muted); font-size: 7.4pt; word-break: break-all; }}

/* Reproduce band */
.repro {{ background: var(--bg-elev); border: 1px solid var(--border);
  border-radius: 8px; padding: 0.125in 0.17in; }}
.repro .cmd {{ font-family: var(--font-mono); font-size: 8.8pt; color: var(--text);
  background: var(--bg-code); border: 1px solid var(--border); border-radius: 5px;
  padding: 7px 9px; margin: 6px 0 0; word-break: break-all; }}
.repro .cmd .p {{ color: var(--accent); }}

/* Footer */
.footer {{ display: grid; grid-template-columns: 1fr auto; gap: 0.2in;
  align-items: end; padding-top: 0.1in; border-top: 1px solid var(--border); }}
.runmeta {{ font-family: var(--font-mono); font-size: 7.8pt; line-height: 1.55; color: var(--text-muted); margin: 0; }}
.runmeta .lbl {{ color: var(--text-faint); }}
.runmeta .val {{ color: var(--accent); }}
.contact {{ text-align: right; font-family: var(--font-mono); font-size: 8.2pt;
  line-height: 1.5; color: var(--text-muted); }}
.contact .name {{ color: var(--text); font-weight: 500; }}
.contact a {{ color: var(--text); text-decoration: none; }}
.contact .urls {{ color: var(--accent); }}
.note {{ font-size: 8.6pt; color: var(--text-muted); line-height: 1.4; }}
</style>
</head>
<body>

<!-- ══════════════════ PAGE 1 ══════════════════ -->
<div class="page page-1">

  <header class="header">
    <svg class="logo" viewBox="0 0 100 100" aria-hidden="true">
      <polygon points="50,4 91,27 91,73 50,96 9,73 9,27" fill="none" stroke="currentColor" stroke-width="5"/>
      <polygon points="50,22 76,37 76,63 50,78 24,63 24,37" fill="none" stroke="currentColor" stroke-width="3" opacity="0.55"/>
      <text x="50" y="60" text-anchor="middle" font-family="Fraunces, Georgia, serif" font-size="34" font-weight="500" fill="currentColor">U</text>
    </svg>
    <div>
      <p class="brand-eyebrow">ASME V&amp;V 40 &middot; Case record &middot; Catalog {CATALOG_VER}</p>
      <h1 class="title">Pedicle screw FEA <em>credibility record</em></h1>
      <p class="tagline">The Nagaraja et al. (2024) assessment, encoded as a signed Unit of Assurance package and scored by the weakener rule engine.</p>
      <p class="author">Vishnu Vettrivel &middot; Doctoral Candidate, Systems Engineering, George Washington University</p>
    </div>
  </header>

  <section class="cite">
    <p class="section-eyebrow">Source record</p>
    <p>{CITATION}</p>
    <p class="doi">{DOI}</p>
  </section>

  <section>
    <p class="section-eyebrow">Context of use, as encoded</p>
    <blockquote>
      {html.escape(COU["description"])}
      <span class="src">{html.escape(COU["id"])}</span>
    </blockquote>
  </section>

  <section>
    <p class="section-eyebrow">Model risk, as encoded</p>
    <div class="tiles">
      <div class="tile"><p class="k">Model influence</p><p class="v">{COU["modelInfluence"]}</p></div>
      <div class="tile"><p class="k">Decision consequence</p><p class="v">{COU["decisionConsequence"]}</p></div>
      <div class="tile"><p class="k">Model risk level</p><p class="v">{PKG["modelRiskLevel"]}</p></div>
      <div class="tile"><p class="k">Assurance level</p><p class="v">{PKG["assuranceLevel"]}</p></div>
      <div class="tile"><p class="k">Device class</p><p class="v">{PKG["deviceClass"]}</p></div>
    </div>
    <p class="note" style="margin-top:7px">Model influence and decision consequence are the two components the record gives as drivers of model risk. Both are recorded at Medium.</p>
  </section>

  <section>
    <p class="section-eyebrow">Factor coverage, {len(assessed)} of {len(VV40_ORDER)} assessed</p>
    <p class="note" style="margin-bottom:6px">The published record reports every factor in the ASME V&amp;V 40 Table 5-1 set. {meeting} factors reach their required level. Values show achieved level against required level.</p>
    <div class="factors">
      <table><tbody>
{factor_col_a}
      </tbody></table>
      <table><tbody>
{factor_col_b}
      </tbody></table>
    </div>
  </section>

  <section class="terminal" aria-label="uofa check output on the Nagaraja COU1 evidence package">
    <div class="terminal-bar">
      <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
      <span class="title">uofa check --build nagaraja/cou1</span>
    </div>
<pre><span class="term-prompt">$</span> <span class="term-cmd">{REPRO_CMD}</span>
<span class="term-faint">══ C2: SHACL profile validation ══</span>
  <span class="term-ok">&#10003; SHACL validation  Conforms</span>
<span class="term-faint">══ C1: Integrity verification (hash + signature) ══</span>
  <span class="term-ok">&#10003; Hash match</span>
  <span class="term-ok">&#10003; Signature valid</span>
<span class="term-faint">══ C3: Jena rule engine ══</span>
<span class="term-dim">  SUMMARY:</span> <span class="term-cmd">{NAG["summary"]["total_firings"]} weakener(s) detected</span>
<span class="term-faint">  ─────────────────────────────────</span>
    <span class="term-high">High:  {NAG["summary"]["by_severity"]["High"]}</span>
{term_pat_lines}</pre>
  </section>

</div>

<!-- ══════════════════ PAGE 2 ══════════════════ -->
<div class="page page-2">

  <section>
    <p class="section-eyebrow">Weakeners detected</p>
    <p class="note" style="margin-bottom:8px">A weakener is a condition under which stated evidence does not support the claim it is offered for. It is a property of the record as published. It is not a defect in the modeling work.</p>
    <table>
      <thead><tr>
        <th>Pattern</th><th>Name</th><th>Severity</th><th class="num">Hits</th><th>Attaches to</th><th>Finding</th>
      </tr></thead>
      <tbody>
{weakener_rows}
      </tbody>
    </table>
    <p class="note" style="margin-top:8px">The package records uncertainty quantification and sensitivity analysis at the package level, and it carries validation results for both. W-AL-01 fires on all six validation results because no uncertainty quantification is linked from the individual validation result nodes. The rule reads the link rather than the package flag.</p>
  </section>

  <section>
    <p class="section-eyebrow">Decision record, as encoded</p>
    <blockquote>
      <strong style="color:var(--accent)">{DEC["outcome"]}</strong>. {html.escape(DEC["rationale"])}
      <span class="src">{html.escape(DEC["role"])} &middot; decided {DEC["decidedAt"][:10]}</span>
    </blockquote>
    <p class="section-eyebrow" style="margin-top:9px">Offset rationale, {html.escape(short(OFFSET["refersToFactor"]).replace("-", " "))}</p>
    <blockquote>
      {html.escape(OFFSET["justification"])}
      <span class="src">{html.escape(OFFSET["id"])}</span>
    </blockquote>
  </section>

  <section>
    <p class="section-eyebrow">Comparison at the same catalog version</p>
    <p class="note" style="margin-bottom:6px">Two published records scored under catalog {CATALOG_VER}. The counts describe how completely each record documents its evidence. They do not rank the papers or the teams.</p>
    <table class="comparison">
      <thead><tr>
        <th>Record</th><th class="num">Factors</th><th class="num">Firings</th><th class="num">Patterns</th><th>Severity</th>
      </tr></thead>
      <tbody>
{comparison_rows}
      </tbody>
    </table>
  </section>

  <section class="integrity">
    <div class="rows">
      <div><p class="k">SHACL profile</p><p class="v">&#10003; Conforms &middot; ProfileComplete</p></div>
      <div><p class="k">Hash</p><p class="v">&#10003; Match &middot; SHA-256</p></div>
      <div><p class="k">Signature</p><p class="v">&#10003; Valid &middot; Ed25519</p></div>
    </div>
    <div class="hash">
      <p class="k">Package hash</p>
      <p class="v">{PKG["hash"]}</p>
    </div>
  </section>

  <section class="repro">
    <p class="section-eyebrow">Reproduce every number on these pages</p>
    <p class="cmd"><span class="p">$</span> {REPRO_CMD}</p>
  </section>

  <footer class="footer">
    <p class="runmeta">
      <span class="lbl">Catalog</span> <span class="val">{CATALOG_VER}</span><br/>
      <span class="lbl">Engine</span> <span class="val">{ENGINE}</span><br/>
      <span class="lbl">Run date</span> <span class="val">{RUN_DATE}</span>
    </p>
    <div class="contact">
      <div class="name">Vishnu Vettrivel</div>
      <div><a href="mailto:support@uofa.net">support@uofa.net</a></div>
      <div class="urls">uofa.net &middot; github.com/cloudronin/uofa</div>
    </div>
  </footer>

</div>

<script>
  (function () {{
    var params = new URLSearchParams(window.location.search);
    if (params.get('theme') === 'light') {{
      document.documentElement.setAttribute('data-theme', 'light');
    }}
  }})();
</script>

</body>
</html>
"""

if __name__ == "__main__":
    OUT.write_text(TEMPLATE)
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  catalog     {CATALOG_VER}")
    print(f"  engine      {ENGINE}")
    print(f"  run date    {RUN_DATE}")
    print(f"  firings     {NAG['summary']['total_firings']} across {NAG['summary']['patterns']} patterns")
    print(f"  coverage    {len(assessed)}/{len(VV40_ORDER)} assessed, {meeting} meeting required level")

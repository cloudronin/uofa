# Vocabulary-to-CLI wiring spec v0.1

Proposed target path: `docs/vocabulary-cli-wiring-spec.md`

Companion to [vocabulary-status.md](vocabulary-status.md) (what the vocabulary
now says), [vocabulary-authoring-spec.md](vocabulary-authoring-spec.md) (how
definitions get written) and [vocabulary-cleanup-audit.md](vocabulary-cleanup-audit.md).
Those three describe the vocabulary as a published artifact. This one describes
making it load-bearing inside the tool.

State verified against `113c651b` (local working copy and origin/main agree).

## 1. The question this spec protects

*When a new user runs a UofA command and it tells them something is wrong, can
they tell what the tool is asking for?*

Every line below is held or dropped on that question. Anything that is only
about vocabulary tidiness is out of scope and marked as such.

## 2. Current state, verified

**The definitions are unreachable from the CLI.** All 288 labels and 240
comments live in seven Turtle files (`spec/schemas/uofa_shacl.ttl` plus
`packs/*/shapes/*.ttl`). The only reader is
`site/scripts/lib/vocab-extract.mjs`, a regex extractor in the Node site build.
No Python module in `src/uofa_cli/` reads `rdfs:label`, `rdfs:comment`,
`rdfs:domain` or `rdfs:range`. The 122 core definitions currently reach users
only through a web page.

**The CLI carries a hand-maintained shadow copy instead.**
`src/uofa_cli/shacl_friendly.py` defines `_FIX_SUGGESTIONS` (20 entries) and
`_PROPERTY_SEVERITY` (6 entries), keyed on property IRI, written by hand. This
is the same hardcoded-versus-derived shape as the `PROFILE_URIS` bug recorded in
the status doc: a sibling map that must be updated in lockstep with a source of
truth it has no link to.

**Coverage on the path that matters.** 108 distinct `sh:path` IRIs appear across
all shapes. These are exactly the properties that can surface in a violation
message, so they are the set a new user can actually collide with.

| Namespace | `sh:path` terms | Have `rdfs:comment` | Missing |
|---|---|---|---|
| core | 66 | 66 | **0** |
| iso42001 (aims) | 27 | 4 | 23 |
| surrogate | 10 | 4 | 6 |
| external (prov, dcterms, schema) | 5 | 0 | 5 |
| **total** | **108** | **74** | **34** |

Core is complete on this path. The 14 undefined core terms cannot appear here,
because they have no shape. The gap is 23 aims terms, 6 surrogate terms, and 5
terms UofA does not own.

**Fallbacks available.** 80 of the 108 paths carry at least one `sh:message` on
a property shape. 20 carry a hand-written fix string. Neither is a definition.

**rdflib parses all seven shapes files cleanly** (2250 triples, no errors), and
`shacl_friendly` already imports rdflib and constructs `Graph` objects. No new
dependency.

## 3. Design principle

One reader, three consumers. Every consumer derives from the same index. No
second hand-maintained map is created, and the one that exists shrinks to the
part that is genuinely not derivable.

Definitions say what a term **means**. Fix strings say what to **do**. They are
different registers and both belong in the output. Core definitions are
standard-agnostic by authoring rule, so a definition can never carry the
`--pack`-specific instruction a fix string carries. Keep both.

## 4. Work items

Sizing assumes paired spec-driven execution, not solo hand-writing. Solo
estimates in brackets for calibration only.

Dependency order is the only ordering in this table. W0, W3 and W5 have no
predecessor and are **parallel-now**.

| ID | Item | Depends on | Hours | Status |
|---|---|---|---|---|
| W0 | `uofa_cli/vocab.py` term index | none | 1.5 [4] | parallel-now |
| W1 | `Means:` line on violations | W0 | 0.75 [2] | blocked on W0 |
| W2 | `uofa define` / `uofa vocab` | W0 | 1.0 [3] | blocked on W0 |
| W3 | Describe 23 aims + 6 surrogate terms | none | 2.0 [5] | parallel-now |
| W4 | Excel template definitions | W0, I1 | 1.5 [4] | blocked on I1 |
| W5 | External-term gloss (5 terms) | none | 0.25 [0.5] | parallel-now |
| W6 | Collapse the Node extractor onto W0 | W0 | 1.0 [2] | blocked on W0 |

Total 8.0 paired hours [20.5 solo], of which W0+W1 is 2.25 and delivers the
whole user-visible benefit on the core namespace.

### W0. `src/uofa_cli/vocab.py`

A lazily built, process-cached index over the shapes graph.

```python
@dataclass(frozen=True)
class Term:
    iri: str
    name: str              # local part
    namespace: str         # core | aims | surrogate | external
    kind: str              # Class | Property
    label: str | None
    comment: str | None    # the definition
    domain: str | None     # rdfs:domain IRI
    range: str | None      # rdfs:range IRI
    subclass_of: tuple[str, ...]
    deprecated: bool
    json_key: str | None   # from the active context
    since: str | None      # first context version carrying it
    dropped_in: str | None # first context version that does not
    packs: tuple[str, ...] # packs whose shapes reference it
    messages: tuple[str, ...]  # sh:message on shapes with this path

def index(packs: Sequence[str] | None = None) -> dict[str, Term]: ...
def lookup(name_or_iri: str) -> Term | None: ...   # resolves bare local names
```

Parse with rdflib rather than porting the Node regex. Version ordering is
numeric on both components, not lexicographic, per the `v0.10`-sorts-before-`v0.2`
bug already recorded.

**Done-gate:** `index()` returns 108 entries whose IRI appears as an `sh:path`,
with `comment` populated for exactly the count in the §2 table, asserted in a
new `tests/test_vocab_index.py`. The test asserts counts derived from the graph,
not literals, so it does not need editing when W3 lands.

### W1. Definition on the violation path

In `shacl_friendly.py`, the violation dict gains a `means` key populated from
`vocab.lookup(path_iri).comment`. `print_violations` renders it first, because a
user who does not know what the field is cannot evaluate Required or Actual.

```
  [High] hasContextOfUse
         Means:    <rdfs:comment, wrapped>
         Required: minCount 1
         Actual:   absent
         Fix:      Every UofA must declare a V&V 40 Context of Use.
```

Resolution order for `Means:`: `rdfs:comment`, then the local gloss from W5 for
external terms, then omit the line. Never `sh:message`, which already renders as
Required. Omitting is correct and honest when nothing is known; do not
substitute a name-derived guess, for the same reason the authoring spec forbids
one.

`--explain --explain-format json` envelopes carry `means` as a sibling of `fix`
so the interpretation layer and any downstream consumer get it too.

`_FIX_SUGGESTIONS` stays, reduced to its imperative half. Delete any entry whose
text merely restates the definition.

**Done-gate:** a test asserting that for a fixture package failing on a core
property, stdout contains the exact `rdfs:comment` string read from the graph at
test time. Comparing against the graph rather than a literal is what stops the
shadow copy from re-forming.

### W2. `uofa define` and `uofa vocab`

New subcommand module `src/uofa_cli/commands/define.py`, registered in the
`modules` dict in `cli.py`.

- `uofa define hasContextOfUse` prints label, definition, kind, domain, range,
  JSON key, `since`, deprecation, the packs that constrain it, and its SHACL
  constraints. Accepts bare local name, full IRI, or JSON key.
- `uofa define --search "context of use"` matches over label and comment.
- `uofa vocab --pack vv40` lists in-scope terms with one-line labels.
- `--format json` on both, per the existing CLI convention.

Terms dropped in v0.7 resolve and print `not in the current context (v0.4 to
v0.6)`, matching the site. Deprecated terms print their `owl:deprecated` note.

**Done-gate:** `uofa define` resolves every one of the 108 `sh:path` local names
without a miss, and every dropped term prints the marker, asserted in the same
test module.

### W3. Pack descriptions

Run the batch treatment core got on 23 aims and 6 surrogate terms, against
repository evidence only, per the authoring spec. These are the terms behind
every `Means:` line the packs cannot currently produce.

The aims 23 cluster into audit and approval (`auditDate`, `auditFindings`,
`auditedFunction`, `approvalDate`, `approvalSignatory`), assessment
(`assessmentDate`, `assessmentScope`, `assessor`), risk (`identifiedRisk`,
`mitigationStrategy`, `mappedToControl`, `nonconformityDescription`),
model and data (`dataResource`, `dataType`, `evaluatedModelVersion`,
`testSetCoverage`, `deployedConfiguration`), and governance (`policyText`,
`objectiveStatement`, `roleName`, `monitoringMethodology`, `nextReviewDate`,
`provenanceStage`). The surrogate 6 are one coherent bounds-and-coordinates
feature.

This is not documentation hygiene once W1 lands. It is the difference between an
aims user seeing a definition and seeing nothing.

**Done-gate:** the §2 table reads 108 of 108 for the three UofA namespaces, and
the site vocabulary pages regenerate without a new dead anchor.

### W4. Excel template definitions

`uofa init` hands a new user an `.xlsx` and that is where they actually type.
Add a `Definitions` sheet plus per-header cell comments sourced from W0.

`excel_writer.py` already imports `openpyxl.comments.Comment` and sets cell
comments for extraction source attribution, so the mechanism exists. Blocked on
I1 below because it is not established that the seven checked-in
`packs/*/templates/*.xlsx` blobs have a generator.

**Done-gate:** every column header in the generated template whose mapped term
has a definition carries it as a cell comment, asserted by reading the workbook
back.

### W5. External-term gloss

Five paths belong to prov, dcterms and schema.org: `generatedAtTime`,
`wasDerivedFrom`, `wasAttributedTo`, `identifier`, `description`. UofA cannot
define other people's terms in its own namespace. A five-entry local gloss in
`vocab.py`, marked as such in output (`Means (PROV-O):`), with the upstream IRI
shown. Three already have fix strings; this adds the meaning register.

**Done-gate:** all five render a `Means:` line and none claims a `uofa:` IRI.

### W6. Collapse the Node extractor

`site/scripts/lib/vocab-extract.mjs` regex-parses the same TTL that W0 parses
with rdflib. Two readers of one source will drift, and the regex is the fragile
one: it throws on any label line it cannot parse, which is safe but brittle.

`.github/workflows/deploy-site.yml` already runs `pip install -e .` before
`npm ci`, so the site build can call the CLI with no workflow change. Replace
the regex extraction inside `gen-vocab-pages.mjs` with a call to
`uofa vocab --format json`, keeping the render layer and its dead-anchor test
untouched.

Fallback if the site must build without the Python package: keep both readers
and add a parity test. That is strictly worse and should only be taken if the
constraint turns out to be real.

**Done-gate:** the generated vocabulary pages are byte-identical before and
after the swap.

## 5. Investigation items

Not asserted. The execution agent confirms these before building on them.

**I1. Are `packs/*/templates/*.xlsx` generated or hand-built?** No generator
script was found under `dev/tools/scripts/`, and the only Python that references
those paths is test code. `excel_writer.py` builds workbooks programmatically,
but for extraction output rather than blank templates. If the blanks are
hand-built, W4 is a template-generator project, not a comment-injection patch,
and should be re-sized before it starts.

**I2. Does the extract prompt benefit from vocabulary definitions?**
`llm_extractor.py` already assembles pack-specific factor definitions from a
pack prompt file plus `excel_constants`. Its fields are Excel column names, not
vocabulary IRIs, and the join runs through `excel_mapper.py`. The
`extract-vocab-mismatch` regression fixture is about non-canonical enum values,
which is a different failure from an undefined term. Confirm the header-to-IRI
join is total before assuming definitions would reduce that error class. If the
join is partial, this is not a W-item.

**I3. Should `uofa define` resolve the 19 dropped terms and the 14 undefined
ones?** W2 assumes yes for dropped terms, matching the site. The 14 undefined
core terms have no definition to print. Printing a term with an empty definition
may be more useful than a miss, or may look broken. Decide at build time; it is
one branch either way.

## 6. Non-goals

- Writing definitions for the 14 undefined core terms. The repository cannot
  evidence them and the authoring spec forbids guesses. They are dropped from
  v0.7 and cannot appear in a violation.
- Resolving the `rdfs:range uofa:ValidationResult` question. That is a shape-fit
  decision, held by `tests/test_validation_result_taxonomy.py`, and independent
  of everything here.
- Moving the toolchain off v0.5. `CONTEXT_URL` pinning affects which context
  newly authored packages carry. W0 reads shapes, not the emitted context, so
  the two are unrelated. Do not couple them.
- Deciding the fate of the disposition line.

## 7. Regression surface

Every change here is additive to output and inert to validation. No shape, rule
or context file is modified by W0, W1, W2, W4, W5 or W6. W3 adds `rdfs:comment`
triples only, which the status doc establishes cannot change what validates,
since no `pyshacl.validate` call site passes `ont_graph` or enables inference
and the Jena engine never loads the shapes.

The tests most likely to move are snapshot or golden-output tests over CLI
stdout. Enumerate them before W1 rather than discovering them at the gate.

## 8. Recommended cut if the budget shrinks

W0 plus W1 plus W5, at 2.5 paired hours, delivers a definition on every core
violation and the five external ones, which is 71 of the 108 paths a user can
hit. W3 raises that to 108. W2 and W4 are discovery surfaces and matter less
than the failure path, because a confused user is looking at a violation, not
browsing a glossary.

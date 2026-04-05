# Domain Packs

A **domain pack** bundles the SHACL shapes, Jena rules, Excel templates, examples, and LLM extraction prompt for a specific credibility assessment domain. The CLI loads assets from the active pack (default: `vv40`) and supports switching via `--pack <name>`.

## Directory Structure

Every pack follows this layout. Only `pack.json` and `shapes/` are required — all other directories are optional:

```
packs/
  <pack-name>/
    pack.json                   # Pack manifest (required)
    shapes/
      <shapes>.ttl              # SHACL shapes for validation (C2)
    rules/
      <rules>.rules             # Jena forward-chaining rules (C3)
    templates/
      <template>.xlsx           # Excel template (for uofa import)
      <skeleton>.jsonld         # JSON-LD skeleton (for uofa init)
      <starter-filled>.xlsx     # Pre-filled example workbook
    examples/
      <case-study>/             # Working example UofA files
        cou1/<file>.jsonld
        cou2/<file>.jsonld
      starters/                 # Real-world starter examples
    prompts/
      <prompt>.txt              # LLM extraction prompt (for uofa extract)
```

### Installed Packs

```
packs/
  core/                         # Base pack — standards-agnostic core shapes + rules
    pack.json
    shapes/uofa_shacl.ttl       # Core SHACL (always loaded, all packs extend this)
    rules/uofa_weakener.rules   # 9 core + 2 compound weakener rules
    templates/
      uofa-template.xlsx        # Generic Excel template
      uofa-minimal-skeleton.jsonld
      uofa-complete-skeleton.jsonld

  vv40/                         # ASME V&V 40-2018 (13 credibility factors)
    pack.json
    shapes/vv40_shapes.ttl      # Factor name enum + level range 1-5
    templates/
      vv40-template.xlsx        # VV40-specific Excel template
      uofa-starter-filled.xlsx  # Pre-filled wind turbine blade example
    examples/
      morrison/                 # FDA blood pump case study (2 COUs)
      starters/                 # Starter .jsonld files
    prompts/

  nasa-7009b/                   # NASA-STD-7009B (19 factors, 6 NASA-only)
    pack.json
    shapes/nasa_7009b_shapes.ttl  # Factor name enum + level range 0-4 + phase
    rules/nasa_7009b_weakener.rules  # 6 NASA-specific weakener rules
    templates/                  # (uses core template)
    examples/
      aerospace/                # TPS thermal protection system example
      starters/                 # HPT blade thermal + aero fatigue starters
    prompts/
```

## Pack Manifest (`pack.json`)

Every pack must have a `pack.json` with at minimum `name`, `version`, and `shapes`:

```json
{
  "name": "vv40",
  "version": "0.4.0",
  "description": "ASME V&V 40-2018 credibility factor taxonomy (13 factors).",
  "standards": ["ASME-VV40-2018", "FDA-2023-CMS"],
  "shapes": "shapes/vv40_shapes.ttl",
  "rules": null,
  "template": "templates/vv40-template.xlsx",
  "prompt": "prompts/vv40_extract_prompt.txt",
  "factors": 13,
  "weakener_patterns": 0,
  "author": "Vishnu Vettrivel",
  "license": "CC0-1.0"
}
```

## Domain Pack Contract

1. **Must have `pack.json`** with at minimum: `name`, `version`, `shapes`.
2. **Shapes extend, never replace, the core shapes.** A domain pack's SHACL file adds domain-specific constraints. The CLI loads core + pack shapes together.
3. **Rules are additive.** Domain rules file is loaded *after* core rules. Domain patterns use a pack-specific prefix (e.g., `W-NASA-xx`) to avoid ID collisions.
4. **Template is standalone.** A domain template includes all core fields plus domain-specific ones.
5. **Examples are self-contained.** Each example `.jsonld` file uses a relative `@context` path to `spec/context/v0.4.jsonld`. The `uofa validate` command auto-discovers examples across all packs.

## Using Packs

```bash
# List installed packs
uofa packs

# Inspect a specific pack
uofa packs vv40

# Use a specific pack for validation
uofa check my-file.jsonld --pack vv40

# Import from Excel using a pack's factor taxonomy
uofa import assessment.xlsx --pack nasa-7009b

# Use multiple packs (shapes + rules from both are loaded)
uofa check my-file.jsonld --pack vv40 --pack nasa-7009b

# Validate all examples across all packs
uofa validate
```

### Excel Templates

Each pack can include Excel templates in `templates/`. The `uofa import` command uses the active pack to determine valid factor names, level ranges, and evidence types. The `core` and `vv40` packs ship with pre-populated templates; see `packs/vv40/templates/uofa-starter-filled.xlsx` for a complete filled example.

When running `uofa init my-project --pack vv40`, the init command copies the pack's template into the new project directory.

## Creating a Domain Pack

### 1. Create the directory

```
packs/
  cardio-cfd/
    pack.json
    shapes/
      cardio_cfd_shapes.ttl
    rules/
      cardio_cfd_weakener.rules
    templates/
      cardio-cfd-template.xlsx
    examples/
      blood-pump/
        uofa-blood-pump-cou1.jsonld
    prompts/
      cardio_cfd_extract_prompt.txt
```

### 2. Extend the core shapes

```turtle
# packs/cardio-cfd/shapes/cardio_cfd_shapes.ttl

@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix uofa: <https://uofa.net/vocab#> .

# Domain constraint: hemolysis metric required for blood-contacting devices
uofa:CardioValidationResultShape a sh:NodeShape ;
    sh:targetClass uofa:ValidationResult ;
    sh:property [
        sh:path uofa:metricType ;
        sh:hasValue "hemolysis-index" ;
        sh:message "Cardiovascular CFD pack requires hemolysis index metric." ;
    ] .
```

### 3. Add domain rules

```
# packs/cardio-cfd/rules/cardio_cfd_weakener.rules

[W-CARDIO-01:
    (?uofa rdf:type uofa:UnitOfAssurance)
    (?uofa uofa:hasValidationResult ?vr)
    (?vr uofa:resultType 'hemolysis-comparison')
    noValue(?vr, uofa:comparedAgainst)
    makeSkolem(?ann, ?uofa, 'W-CARDIO-01', ?vr)
    ->
    (?ann rdf:type uofa:WeakenerAnnotation)
    (?ann uofa:patternId 'W-CARDIO-01')
    (?ann uofa:severity 'High')
    (?ann uofa:affectedNode ?vr)
    (?ann schema:description 'Hemolysis comparison has no comparator — in vitro hemolysis data not linked.')
    (?uofa uofa:hasWeakener ?ann)
]
```

### 4. Write the manifest

```json
{
  "name": "cardio-cfd",
  "version": "0.1.0",
  "description": "Cardiovascular CFD credibility pack for blood-contacting devices.",
  "standards": ["ASME-VV40-2018", "FDA-2023-CMS"],
  "shapes": "shapes/cardio_cfd_shapes.ttl",
  "rules": "rules/cardio_cfd_weakener.rules",
  "template": "templates/cardio-cfd-template.xlsx",
  "prompt": "prompts/cardio_cfd_extract_prompt.txt",
  "factors": 13,
  "weakener_patterns": 3,
  "author": "Your Name",
  "license": "CC0-1.0"
}
```

### 5. Test your pack

```bash
uofa packs cardio-cfd                         # verify manifest loads
uofa shacl my-file.jsonld --pack cardio-cfd    # test SHACL shapes
uofa rules my-file.jsonld --pack cardio-cfd    # test Jena rules
uofa validate                                  # verify examples pass
```

# Domain Packs

A **domain pack** bundles the SHACL shapes, Jena rules, Excel template, and LLM extraction prompt for a specific credibility assessment domain. The CLI loads assets from the active pack (default: `core`) and supports switching via `--pack <name>`.

## Directory Structure

Every pack follows this layout:

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
    prompts/
      <prompt>.txt              # LLM extraction prompt (for uofa extract)
```

## Pack Manifest (`pack.json`)

Every pack must have a `pack.json` with at minimum `name`, `version`, `shapes`, and `rules`:

```json
{
  "name": "core",
  "version": "0.4.0",
  "description": "Core credibility assessment rules.",
  "standards": [],
  "shapes": "shapes/uofa_shacl.ttl",
  "rules": "rules/uofa_weakener.rules",
  "template": "templates/uofa-template.xlsx",
  "prompt": "prompts/extract_prompt.txt",
  "factors": 13,
  "weakener_patterns": 13,
  "author": "Your Name",
  "license": "CC0-1.0"
}
```

## Domain Pack Contract

1. **Must have `pack.json`** with at minimum: `name`, `version`, `shapes`, `rules`.
2. **Shapes extend, never replace, the core shapes.** A domain pack's SHACL file imports the core shapes and adds domain-specific constraints. The CLI loads both.
3. **Rules are additive.** Domain rules file is loaded *after* core rules. Domain patterns use a `W-DOM-xx` prefix to avoid ID collisions.
4. **Template is standalone.** A domain template includes all core fields plus domain-specific ones. It is a superset, not a delta.
5. **Prompt extends the core prompt.** Domain prompts include the base V&V 40 extraction instructions plus domain-specific terminology and factor definitions.

## Using Packs

```bash
# List installed packs
uofa packs

# Inspect a specific pack
uofa packs core

# Use a specific pack for validation
uofa check my-file.jsonld --pack cardio-cfd

# Import from Excel using a pack's factor taxonomy
uofa import assessment.xlsx --pack cardio-cfd

# The --pack flag works with all commands
uofa shacl my-file.jsonld --pack cardio-cfd
uofa rules my-file.jsonld --pack cardio-cfd
```

### Excel Templates

Each pack can include an Excel template in `templates/`. The `uofa import` command uses the active pack to determine valid factor names, level ranges, and evidence types. The `core` and `vv40` packs ship with pre-populated templates; see `examples/starters/uofa-starter-filled.xlsx` for a complete filled example.

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
    prompts/
      cardio_cfd_extract_prompt.txt
```

### 2. Extend the core shapes

```turtle
# packs/cardio-cfd/shapes/cardio_cfd_shapes.ttl

@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix uofa: <https://uofa.net/schema/> .

# Import core shapes (pyshacl --imports flag, or concatenate at load time)

# Add domain constraint: hemolysis metric required
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

# Domain rule: hemolysis comparison missing for blood-contacting devices
[W-DOM-01:
    (?uofa rdf:type uofa:UnitOfAssurance)
    (?uofa uofa:hasValidationResult ?vr)
    (?vr uofa:resultType 'hemolysis-comparison')
    noValue(?vr, uofa:comparesTo)
    ->
    ... WeakenerAnnotation with patternId 'W-DOM-01' ...
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
uofa packs cardio-cfd              # verify manifest loads
uofa shacl my-file.jsonld --pack cardio-cfd   # test SHACL shapes
uofa rules my-file.jsonld --pack cardio-cfd   # test Jena rules
```

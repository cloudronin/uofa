# Contributing to UofA

Thanks for helping make the **Unit of Assurance (UofA)** better!

## Quick Start

1. **Fork** the repo and create a feature branch.
2. If adding examples, put them in `/examples` and open a PR — CI will run SHACL validation.

## Adding Examples

Start from a template in `packs/core/templates/`, import from an Excel workbook (`uofa import`), or customize manually. Your example should:

- Use the v0.5 JSON-LD context:
  ```json
  "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"
  ```
- Conform to either Minimal or Complete profile
- Include a signed hash and signature (see [Getting Started Guide](docs/getting-started.md))

## Validating Before Submitting

```bash
# Install the CLI
pip install -e .

# Validate your example passes SHACL
uofa check packs/your-pack/examples/your-uofa.jsonld

# Or validate all examples at once
uofa validate
```

CI runs `uofa validate` and `uofa check` on the Morrison example for every PR.

## Questions?

If you are preparing a CM&S-supported regulatory submission and want to explore UofA packaging for your evidence, please reach out at [crediblesimulation.com](https://crediblesimulation.com).

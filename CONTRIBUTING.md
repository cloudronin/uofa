# Contributing to UofA

Thanks for helping make the **Unit of Assurance (UofA)** better!

## Quick Start

1. **Fork** the repo and create a feature branch.
2. If adding examples, put them in `/examples` and open a PR — CI will run SHACL validation.

## Adding Examples

Start from a template in `examples/templates/` and customize it for your domain. Your example should:

- Use the v0.2 JSON-LD context:
  ```json
  "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.2.jsonld"
  ```
- Conform to either Minimal or Complete profile
- Include a signed hash and signature (see [Getting Started Guide](docs/getting-started.md))

## Validating Before Submitting

```bash
# Install dependencies
pip install pyshacl rdflib cryptography

# Validate your example passes SHACL
make check FILE=examples/your-example/your-uofa.jsonld

# Or validate all examples at once
make validate
```

CI runs `make validate` and `make morrison` on every PR.

## Questions?

If you are preparing a CM&S-supported regulatory submission and want to explore UofA packaging for your evidence, please reach out at [crediblesimulation.com](https://crediblesimulation.com).

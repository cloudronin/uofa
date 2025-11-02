# Contributing to UoFA

Thanks for helping make the **Unit of Assurance (UoFA)** better!

## Quick Start

1. **Fork** the repo and create a feature branch.
2. If adding examples, put them in `/examples` and open a PR — CI will run SHACL validation.

## Examples Guidelines (`/examples`)

Your example should model a **Minimal Profile UoFA**:

- Use the canonical JSON-LD context:
  ```json
  "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.1.jsonld"

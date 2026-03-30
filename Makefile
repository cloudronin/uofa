# ── UofA Makefile (compatibility shim) ──────────────────────
# The primary CLI is now `uofa`. Install it: pip install -e .
# These targets delegate to `uofa` commands for backward compatibility.

MORRISON = examples/morrison-cou1/uofa-morrison-cou1.jsonld
ENG_DIR  = weakener-engine

FILE ?=
KEY  ?= keys/research.key

.PHONY: all validate morrison morrison-shacl morrison-rules morrison-verify morrison-build clean
.PHONY: check shacl verify rules sign build

# ── Primary targets ─────────────────────────────────────────

all: clean validate morrison
	@echo "\n✓ All checks passed."

# ── Generic targets (delegate to uofa CLI) ──────────────────

check:
	uofa check $(FILE) --build

shacl:
	uofa shacl $(FILE)

verify:
	uofa verify $(FILE)

rules:
	uofa rules $(FILE) --build

sign:
	uofa sign $(FILE) --key $(KEY)

# ── SHACL validation (all examples) ─────────────────────────

validate:
	uofa validate

# ── Morrison COU1: full pipeline ────────────────────────────

morrison:
	uofa check $(MORRISON) --build

morrison-shacl:
	uofa shacl $(MORRISON)

morrison-verify:
	uofa verify $(MORRISON)

morrison-rules:
	uofa rules $(MORRISON) --build

morrison-build:
	@if [ ! -f $(ENG_DIR)/target/uofa-weakener-engine-0.1.0.jar ]; then \
		echo "══ Building Jena rule engine ══"; \
		cd $(ENG_DIR) && mvn package -q; \
	fi

morrison-sign:
	uofa sign $(MORRISON) --key keys/research.key

clean:
	cd $(ENG_DIR) && mvn clean -q
	@echo "✓ Clean."

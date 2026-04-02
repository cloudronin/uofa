# ── UofA Makefile (compatibility shim) ──────────────────────
# The primary CLI is now `uofa`. Install it: pip install -e .
# These targets delegate to `uofa` commands for backward compatibility.

MORRISON_COU1 = examples/morrison/cou1/uofa-morrison-cou1.jsonld
MORRISON_COU2 = examples/morrison/cou2/uofa-morrison-cou2.jsonld
ENG_DIR       = weakener-engine

FILE ?=
KEY  ?= keys/research.key

.PHONY: all test validate morrison morrison-shacl morrison-rules morrison-verify morrison-diff
.PHONY: morrison-build morrison-sign clean check shacl verify rules sign

# ── Primary targets ─────────────────────────────────────────

all: clean test validate morrison morrison-diff
	@echo "\n✓ All checks passed."

# ── Generic targets (delegate to uofa CLI) ──────────────────

check:
	uofa check $(FILE) --build

shacl:
	uofa shacl $(FILE)

test:
	pytest tests/test_integration.py -v

verify:
	uofa verify $(FILE)

rules:
	uofa rules $(FILE) --build

sign:
	uofa sign $(FILE) --key $(KEY)

# ── SHACL validation (all examples) ─────────────────────────

validate:
	uofa validate --verify

# ── Morrison: full pipeline (COU1) ──────────────────────────

morrison:
	uofa check $(MORRISON_COU1) --build

morrison-shacl:
	uofa shacl $(MORRISON_COU1)

morrison-verify:
	uofa verify $(MORRISON_COU1)

morrison-rules:
	uofa rules $(MORRISON_COU1) --build

morrison-diff:
	uofa diff $(MORRISON_COU1) $(MORRISON_COU2)

morrison-build:
	@if [ ! -f $(ENG_DIR)/target/uofa-weakener-engine-0.1.0.jar ]; then \
		echo "══ Building Jena rule engine ══"; \
		cd $(ENG_DIR) && mvn package -q; \
	fi

morrison-sign:
	uofa sign $(MORRISON_COU1) --key keys/research.key

clean:
	cd $(ENG_DIR) && mvn clean -q
	@echo "✓ Clean."

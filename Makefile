SHACL      = spec/schemas/uofa_shacl.ttl
CONTEXT    = spec/context/v0.2.jsonld
MORRISON   = examples/morrison-cou1/uofa-morrison-cou1.jsonld
RULES_DIR  = examples/morrison-cou1
ENG_DIR    = weakener-engine
RULES_FILE = $(RULES_DIR)/uofa_weakener.rules
JAR        = $(ENG_DIR)/target/uofa-weakener-engine-0.1.0.jar
PUBKEY     = keys/research.pub

# User-overridable: make check FILE=my-project.jsonld
FILE       ?=
KEY        ?= keys/research.key

# ── Primary targets ─────────────────────────────────────────

.PHONY: all validate morrison morrison-shacl morrison-rules morrison-verify morrison-build clean
.PHONY: check shacl verify rules sign build

all: clean validate morrison
	@echo "\n✓ All checks passed."

# ── Generic targets (any UofA file) ─────────────────────────
# Usage: make check FILE=path/to/your-uofa.jsonld
#        make sign  FILE=path/to/your-uofa.jsonld KEY=keys/your.key

check: _require-file shacl verify rules
	@echo "\n══════════════════════════════════════════════════════════"
	@echo "  ✓ $(FILE): C1 (integrity) + C2 (SHACL) + C3 (rules)"
	@echo "══════════════════════════════════════════════════════════"

shacl: _require-file
	@echo "══ C2: SHACL profile validation ══"
	pyshacl -s $(SHACL) -df json-ld -d $(FILE) -f human

verify: _require-file
	@echo "\n══ C1: Integrity verification (hash + signature) ══"
	python scripts/sign_uofa.py $(FILE) --verify --pubkey $(PUBKEY) --context $(CONTEXT)

rules: _require-file build
	@echo "\n══ C3: Jena rule engine — weakener detection ══"
	java -jar $(JAR) $(FILE) --rules $(RULES_FILE) --context $(CONTEXT)

sign: _require-file build
	@echo "══ Signing $(FILE) ══"
	python scripts/sign_uofa.py $(FILE) --key $(KEY) --context $(CONTEXT)

build:
	@if [ ! -f $(JAR) ]; then \
		echo "══ Building Jena rule engine ══"; \
		cd $(ENG_DIR) && mvn package -q; \
	fi

_require-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE is required. Usage: make check FILE=path/to/your-uofa.jsonld"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: $(FILE) not found."; \
		exit 1; \
	fi

# ── SHACL validation (all examples) ─────────────────────────

validate:
	@echo "══ SHACL validation: all examples ══"
	@for f in $$(find examples -name '*.jsonld' -o -name '*.json' | grep -v deprecated | grep -v templates | sort); do \
		echo "  → $$f"; \
		pyshacl -s $(SHACL) -df json-ld -d $$f -f human || exit 1; \
	done
	@echo "✓ All examples conform.\n"

# ── Morrison COU1: full pipeline ────────────────────────────

morrison: morrison-shacl morrison-verify morrison-rules
	@echo "\n══════════════════════════════════════════════════════════"
	@echo "  ✓ Morrison COU1: C1 (integrity) + C2 (SHACL) + C3 (rules)"
	@echo "══════════════════════════════════════════════════════════"

morrison-shacl:
	@echo "══ C2: SHACL Complete profile validation ══"
	pyshacl -s $(SHACL) -df json-ld -d $(MORRISON) -f human

morrison-verify:
	@echo "\n══ C1: Integrity verification (hash + signature) ══"
	python scripts/sign_uofa.py $(MORRISON) --verify --pubkey $(PUBKEY) --context $(CONTEXT)

morrison-rules: morrison-build
	@echo "\n══ C3: Jena rule engine — weakener detection ══"
	java -jar $(JAR) $(MORRISON) --rules $(RULES_FILE) --context $(CONTEXT)

# ── Jena build ──────────────────────────────────────────────

morrison-build:
	@if [ ! -f $(JAR) ]; then \
		echo "══ Building Jena rule engine ══"; \
		cd $(ENG_DIR) && mvn package -q; \
	fi

# ── Utility targets ─────────────────────────────────────────

morrison-sign:
	@echo "══ Signing Morrison COU1 ══"
	python scripts/sign_uofa.py $(MORRISON) --key keys/research.key --context $(CONTEXT)

clean:
	cd $(ENG_DIR) && mvn clean -q
	@echo "✓ Clean."




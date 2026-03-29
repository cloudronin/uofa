SHACL      = spec/schemas/uofa_shacl.ttl
CONTEXT    = spec/context/v0.2.jsonld
MORRISON   = examples/morrison-cou1/uofa-morrison-cou1.jsonld
RULES_DIR  = examples/morrison-cou1
ENG_DIR    = weakener-engine
RULES_FILE = $(RULES_DIR)/uofa_weakener.rules
JAR        = $(ENG_DIR)/target/uofa-weakener-engine-0.1.0.jar
PUBKEY     = keys/research.pub

# ── Primary targets ─────────────────────────────────────────

.PHONY: all validate morrison morrison-shacl morrison-rules morrison-verify morrison-build clean

all: clean validate morrison
	@echo "\n✓ All checks passed."

# ── SHACL validation (all examples) ─────────────────────────

validate:	
	@echo "══ SHACL validation: all examples ══"
	@for f in $$(find examples -name '*.jsonld' -o -name '*.json' | grep -v deprecated | sort); do \
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




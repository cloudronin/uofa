# ── UofA Makefile (compatibility shim) ──────────────────────
# The primary CLI is now `uofa`. Install it: pip install -e .
# These targets delegate to `uofa` commands for backward compatibility.

MORRISON_COU1 = packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
MORRISON_COU2 = packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
ENG_DIR       = src/weakener-engine

FILE ?=
KEY  ?= keys/research.key

.PHONY: all test validate morrison morrison-shacl morrison-rules morrison-verify morrison-diff
.PHONY: morrison-build morrison-sign clean check shacl verify rules sign corpus corpus-clean
.PHONY: clean-bundled

# ── Primary targets ─────────────────────────────────────────

all: clean morrison-build test validate morrison morrison-diff
	@echo "\n✓ All checks passed."

# ── Generic targets (delegate to uofa CLI) ──────────────────

check:
	uofa check $(FILE) --build

shacl:
	uofa shacl $(FILE)

test:
	pytest tests/ -v

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

# Recovery target for the dev-shadowing failure mode: if you ever build a
# wheel locally with UOFA_KEEP_BUNDLE=1 (or interrupt a build mid-flight),
# the staged JAR + JRE remain under src/uofa_cli/_engine and _runtime/.
# paths.bundled_jre_executable() will then prefer those staged binaries
# over system Java for every subsequent test run — and a wrong-architecture
# JRE causes "Exec format error". This target wipes the staged artifacts.
clean-bundled:
	rm -rf src/uofa_cli/_engine/uofa-weakener-engine-0.1.0.jar
	rm -rf src/uofa_cli/_runtime/jre
	rm -f  src/uofa_cli/_runtime/PLATFORM
	rm -f  src/uofa_cli/_runtime/JRE_VERSION
	@echo "✓ Bundled wheel artifacts removed from source tree."

# ── Pre-Tester QA Corpus v2 ─────────────────────────────────
# Builds 18 deterministic test fixtures under tests/corpus/{edge-cases,import-tests}.
# Requires the [corpus] optional deps: pip install -e '.[corpus]'

corpus:
	python tests/corpus/build.py

corpus-clean:
	rm -rf tests/corpus/edge-cases tests/corpus/import-tests
	@echo "✓ Corpus cleaned."

# ── UofA Makefile (compatibility shim) ──────────────────────
# The primary CLI is now `uofa`. Install it: pip install -e .
# These targets delegate to `uofa` commands for backward compatibility.
#
# Phase E (post-Phase-D) moved this file from repo root to build-config/.
# Most recipes still want to run from repo root, so each recipe is a
# single shell pipeline that begins with `cd $(ROOT)`. Invoke via the
# root-level `make <target>` shim or with `make -C build-config <target>`
# directly — both work.

# Resolve the repo root from this Makefile's location (build-config/Makefile).
ROOT := $(realpath $(dir $(firstword $(MAKEFILE_LIST))))/..

MORRISON_COU1 = packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld
MORRISON_COU2 = packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld
ENG_DIR       = src/weakener-engine

FILE ?=
KEY  ?= keys/research.key

.PHONY: all test validate morrison morrison-shacl morrison-rules morrison-verify morrison-diff
.PHONY: morrison-build morrison-sign clean check shacl verify rules sign corpus corpus-clean
.PHONY: clean-bundled firewall-guard

# ── Primary targets ─────────────────────────────────────────

all: clean morrison-build firewall-guard test validate morrison morrison-diff
	@echo "\n✓ All checks passed."

# ── Interrogation firewall guard (SIP measures, never judges) ─
# Fails the build if the SIP evidence bundle schema whitelists a verdict
# field, its denylist drifts from FORBIDDEN_TOKENS, a committed bundle carries
# a forbidden field, or the wheel stops force-including specs/. See AGENTS.md §12.

firewall-guard:
	cd $(ROOT) && python dev/tools/scripts/firewall_guard.py

# ── Generic targets (delegate to uofa CLI) ──────────────────

check:
	cd $(ROOT) && uofa check $(FILE) --build

shacl:
	cd $(ROOT) && uofa shacl $(FILE)

test:
	cd $(ROOT) && pytest tests/ -v

verify:
	cd $(ROOT) && uofa verify $(FILE)

rules:
	cd $(ROOT) && uofa rules $(FILE) --build

sign:
	cd $(ROOT) && uofa sign $(FILE) --key $(KEY)

# ── SHACL validation (all examples) ─────────────────────────

validate:
	cd $(ROOT) && uofa validate --verify

# ── Morrison: full pipeline (COU1) ──────────────────────────

morrison:
	cd $(ROOT) && uofa check $(MORRISON_COU1) --build

morrison-shacl:
	cd $(ROOT) && uofa shacl $(MORRISON_COU1)

morrison-verify:
	cd $(ROOT) && uofa verify $(MORRISON_COU1)

morrison-rules:
	cd $(ROOT) && uofa rules $(MORRISON_COU1) --build

morrison-diff:
	cd $(ROOT) && uofa diff $(MORRISON_COU1) $(MORRISON_COU2)

morrison-build:
	@cd $(ROOT) && \
	if [ ! -f $(ENG_DIR)/target/uofa-weakener-engine-0.1.0.jar ]; then \
		echo "══ Building Jena rule engine ══"; \
		cd $(ENG_DIR) && mvn package -q; \
	fi

morrison-sign:
	cd $(ROOT) && uofa sign $(MORRISON_COU1) --key keys/research.key

clean:
	cd $(ROOT)/$(ENG_DIR) && mvn clean -q
	@echo "✓ Clean."

# Recovery target for the dev-shadowing failure mode: if you ever build a
# wheel locally with UOFA_KEEP_BUNDLE=1 (or interrupt a build mid-flight),
# the staged JAR + JRE remain under src/uofa_cli/_engine and _runtime/.
# paths.bundled_jre_executable() will then prefer those staged binaries
# over system Java for every subsequent test run — and a wrong-architecture
# JRE causes "Exec format error". This target wipes the staged artifacts.
clean-bundled:
	cd $(ROOT) && \
	rm -rf src/uofa_cli/_engine/uofa-weakener-engine-0.1.0.jar && \
	rm -rf src/uofa_cli/_runtime/jre && \
	rm -f  src/uofa_cli/_runtime/PLATFORM && \
	rm -f  src/uofa_cli/_runtime/JRE_VERSION
	@echo "✓ Bundled wheel artifacts removed from source tree."

# ── Pre-Tester QA Corpus v2 ─────────────────────────────────
# Builds 18 deterministic test fixtures under tests/corpus/{edge-cases,import-tests}.
# Requires the [corpus] optional deps: pip install -e '.[corpus]'

corpus:
	cd $(ROOT) && python tests/corpus/build.py

# ── Interrogation eval corpus (AirfRANS, pull-on-demand) ────
# AirfRANS is ODbL share-alike and never vendored. Install the extra, then pull
# on demand into UOFA_AIRFRANS_DIR; the eval harness skips when it is absent.
UOFA_AIRFRANS_DIR ?= $(ROOT)/dev/build/airfrans

interrogate-corpus:
	@echo "AirfRANS eval corpus (ODbL; never committed to the repo)."
	@echo "  1) pip install -e '.[interrogate-corpus]'"
	@echo "  2) set UOFA_AIRFRANS_DIR (current: $(UOFA_AIRFRANS_DIR))"
	@echo "  3) pull AirfRANS into that dir; the harness reads it on demand."
	@echo "See packs/surrogate/README.md and tests/fixtures/interrogate/pdebench/LICENSE.md."

corpus-clean:
	cd $(ROOT) && rm -rf tests/corpus/edge-cases tests/corpus/import-tests
	@echo "✓ Corpus cleaned."

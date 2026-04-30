# Repo-root Makefile shim — delegates to build-config/Makefile.
#
# The real targets (morrison-build, corpus, test, validate, …) live in
# build-config/Makefile so the repo root stays free of build clutter.
# This shim preserves the `cd repo && make <target>` UX so contributors
# don't have to type `make -C build-config <target>`.
#
# Phase E (post-Phase-D) introduced this split. To bypass the shim,
# invoke `make -C build-config <target>` directly.

.DEFAULT_GOAL := all

%:
	@$(MAKE) -C build-config $@

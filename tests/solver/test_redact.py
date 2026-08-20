"""Redaction: protect the operator, keep the evidence.

Every sample here is the shape of something actually present in the OSF
archives, with the real names replaced.
"""

from __future__ import annotations

import pytest

from uofa_cli.solver import redact
from uofa_cli.solver.redact import Redactor

LOGHISTORY = r"TESTUSER@EXAMPLEPC:C:\Users\testuser\AppData\Local\Temp\WorkbenchLogs\CoreEvents1.log"
STRIPPED = (r"1. E:\Projects\Example\Mesh_Refinement\Example_files\dp0\SYS\MECH\ds.dat "
            r"2. E:\Projects\Example\Mesh_Refinement\Example_files\dp0\SYS\MECH\solve.out")


def test_the_stripped_filenames_survive():
    """The completeness argument is the filenames.

    The archive's own record names `ds.dat`, `file.rst` and `solve.out` as
    absent, and that list is the strongest completeness evidence in the folder.
    Redacting the basename would protect the operator by deleting the finding.
    """
    out = redact.redact(STRIPPED)
    assert out.endswith("solve.out")
    assert "ds.dat" in out and "solve.out" in out
    assert "Projects" not in out and "Mesh_Refinement" not in out


def test_username_and_host_are_removed():
    out = redact.redact(LOGHISTORY)
    assert "testuser" not in out.lower()
    assert "examplepc" not in out.lower()
    assert out.endswith("CoreEvents1.log")


def test_same_directory_gets_the_same_token():
    """Two files from one directory must stay visibly co-located."""
    r = Redactor()
    out = r.redact(STRIPPED)
    tokens = {p.split(">")[0] + ">" for p in out.split() if p.startswith("<redacted-path")}
    assert len(tokens) == 1, out


def test_different_directories_get_different_tokens():
    r = Redactor()
    out = r.redact(r"C:\Users\a\one.txt and D:\Other\two.txt")
    assert "<redacted-path-1>" in out and "<redacted-path-2>" in out


def test_tokens_are_deterministic_across_runs():
    """Canonicalisation hashes this output; a salted or random token would make
    the same input produce two different signed packages."""
    assert Redactor().redact(LOGHISTORY) == Redactor().redact(LOGHISTORY)


def test_urls_are_never_touched():
    """A source URL is the entire point of a re-derivable pin."""
    text = "fetched from https://osf.io/n4pjz/files/osfstorage/abc123 at 09:00"
    assert redact.redact(text) == text


def test_url_with_a_path_shaped_tail_survives():
    text = "see file:///home/x/y or https://example.invalid/C:/Users/x"
    out = redact.redact(text)
    assert "https://example.invalid/C:/Users/x" in out


@pytest.mark.parametrize("text", [
    r"C:\Users\alice\project\model.wbpj",
    "/home/alice/project/model.wbpj",
    "/Users/alice/project/model.wbpj",
    "/tmp/wb-4821/scratch.dat",
    "/var/folders/xy/abc/T/scratch.dat",
    "alice@buildbox:/home/alice/x.log",
])
def test_looks_redacted_is_false_before_and_true_after(text):
    assert not redact.looks_redacted(text)
    assert redact.looks_redacted(redact.redact(text))


def test_ordinary_email_is_not_mistaken_for_user_at_host():
    """`USER@HOST:` in logHistory is followed by a colon; an address in prose
    is not, and rewriting it would corrupt a contact line for no benefit."""
    text = "correspondence to author@example.org about the study"
    assert redact.redact(text) == text


def test_relative_paths_are_left_alone():
    """Only absolute operator paths are private. `dp0/SYS/MECH/ds.dat` is
    archive-internal structure and is evidence."""
    text = "dp0/SYS/MECH/ds.dat and mini_files/dp0/act.dat"
    assert redact.redact(text) == text


def test_counts_are_reported_by_class():
    r = Redactor()
    r.redact(LOGHISTORY)
    r.redact(STRIPPED)
    assert r.counts == {"user": 1, "host": 1, "path": 2}
    assert r.total == 4
    assert "redacted" in r.summary()


def test_empty_and_clean_text_are_pass_through():
    r = Redactor()
    assert r.redact("") == ""
    assert r.redact("nothing private here") == "nothing private here"
    assert r.total == 0
    assert r.summary() == "no operator paths or identities found"


def test_directory_with_trailing_separator_is_fully_redacted():
    """No basename to preserve, so nothing is kept."""
    out = redact.redact("C:\\Users\\alice\\project\\ ")
    assert "alice" not in out and "project" not in out


def test_identity_embedded_in_a_preserved_basename_is_scrubbed():
    """Regression: preserving basenames leaked the hostname.

    Workbench names its cleanup scripts after the machine, so a
    results-stripped archive lists `cleanup-ansys-<hostname>-16148.bat`. The
    basename is kept on purpose -- it is part of the completeness record -- so
    the hostname rode out inside it even though every `USER@HOST:` and every
    absolute path had been replaced. Found against the real OSF archive, where
    the host survived 40-odd times after a clean-looking redaction pass.

    The fix scrubs learned identities as literals wherever they appear. The
    filename keeps its shape; only the name goes.
    """
    r = Redactor()
    r.redact(LOGHISTORY)                       # teaches EXAMPLEPC
    out = r.redact(r"C:\x\MECH\cleanup-ansys-examplepc-100172.bat")
    assert "examplepc" not in out.lower()
    assert out.endswith("-100172.bat"), "the filename must keep its shape"
    assert "cleanup-ansys-" in out


def test_identity_is_scrubbed_case_insensitively():
    """One project file spells the same host `PUNKKARTIKEPC` and
    `punkkartikepc`; a case-sensitive scrub catches only one of them."""
    r = Redactor()
    r.redact("alice@BUILDBOX:/home/alice/x.log")
    out = r.redact("see buildbox-12.log and BUILDBOX-13.log")
    assert "buildbox" not in out.lower()


def test_short_identities_are_not_scrubbed_as_literals():
    """A two-letter username would mangle unrelated words. Below the length
    floor the path and USER@HOST rewrites still apply; only the literal sweep
    is skipped."""
    r = Redactor()
    r.redact("ab@pc:/home/ab/x.log")
    assert "fabric" in r.redact("the fabric of the mesh")


def test_username_is_learned_from_a_path_alone():
    """A username can appear in a path with no `USER@HOST:` anywhere."""
    r = Redactor()
    out = r.redact(r"C:\Users\alice\p\model.wbpj and log-alice-1.txt")
    assert "alice" not in out.lower()

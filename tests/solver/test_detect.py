"""Content sniffing: the suffix must never be the only thing consulted.

Every case here is drawn from the real OSF archives, because every one of them
is a case where suffix routing gives the wrong answer.
"""

from __future__ import annotations

import pytest

from uofa_cli.solver import detect

HDF5 = b"\x89HDF\r\n\x1a\n" + b"\x00" * 64
ZIP = b"PK\x03\x04" + b"\x00" * 64


def test_act_dat_is_hdf5_not_text():
    """`dp0/act.dat` is an HDF5 container.

    document_reader._READERS maps `.dat` to the plain-text reader, so under
    suffix routing this 266 KB binary is decoded with errors="replace" and
    shipped to an extractor as mojibake.
    """
    assert detect.sniff("act.dat", HDF5) == detect.HDF5_CONTAINER
    assert not detect.is_readable(detect.HDF5_CONTAINER)


def test_named_binary_beats_hdf5_magic():
    """`.mechdb` and `.agdb` are HDF5 too; the specific label must win."""
    assert detect.sniff("SYS-15.mechdb", HDF5) == detect.MECHANICAL_DB
    assert detect.sniff("SYS-15.agdb", HDF5) == detect.GEOMETRY_DB


def test_scdoc_is_a_zip_but_is_not_an_archive_to_descend():
    """SpaceClaim documents are zips. Reporting one as an undescended archive
    would read as a tooling failure rather than a deliberate seal-only call."""
    assert detect.sniff("SYS-31.scdoc", ZIP) == detect.GEOMETRY_DB


def test_wbpz_needs_member_names_to_be_a_workbench_archive():
    assert detect.sniff("x.wbpz", ZIP) == detect.ZIP_ARCHIVE
    assert detect.sniff("x.wbpz", ZIP, zip_names=["p.wbpj"]) == detect.WORKBENCH_ARCHIVE
    assert detect.sniff("x.zip", ZIP, zip_names=["a.txt"]) == detect.ZIP_ARCHIVE


def test_wbdp_and_wbpj_share_a_marker_and_must_still_be_separated():
    """Both carry `<Project Version=`, so the design-point table has to be
    ruled out by name before the project test runs."""
    body = b'<?xml version="1.0"?><Storage><Project Version="9.1" /></Storage>'
    assert detect.sniff("designPoint.wbdp", body) == detect.DESIGN_POINT_TABLE
    proj = b'<?xml version="1.0"?><Storage><Project Version="9.1">' \
           b'<framework-build-version valType="String">23.2.142.0</framework-build-version>'
    assert detect.sniff("mini.wbpj", proj) == detect.WORKBENCH_PROJECT


def test_engineering_data_recognised_under_both_its_names():
    body = b'<?xml version="1.0"?><EngineeringData version="23.2.0.230">'
    assert detect.sniff("EngineeringData.xml", body) == detect.ENGINEERING_DATA
    assert detect.sniff("material.engd", body) == detect.ENGINEERING_DATA


def test_utf16_log_decodes_via_bom_not_replacement_characters():
    """The real `optiSLang_protocol.log` is UTF-16LE.

    A naive utf-8 read does not raise on it -- it yields interleaved
    replacement characters, i.e. it fails silently. The BOM branch is what
    stops that.
    """
    raw = b"\xff\xfe" + "Error: unload failed\n".encode("utf-16-le")
    text, encoding = detect.decode_head(raw)
    assert encoding == "utf-16-le"
    assert text.startswith("Error: unload failed")
    assert "\x00" not in text


def test_figure_captures_are_named_as_images_not_unknown_binaries():
    """Workbench saves result screenshots under `Figures and Images/`.

    The 405 MB FDA archive holds twelve of them. Reporting a PNG as
    "unrecognised binary" in a completeness manifest says we did not know what
    it was when we did -- and these are evidence, being saved contour plots of a
    solved model. They are still sealed and not read: there is no text in them
    this tool can extract.
    """
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    assert detect.sniff("StaticFigure136.png", png) == detect.RASTER_IMAGE
    assert not detect.is_readable(detect.RASTER_IMAGE)
    assert "image" in detect.unreadable_reason(detect.RASTER_IMAGE)
    # Magic wins over a missing or wrong extension.
    assert detect.sniff("figure", png) == detect.RASTER_IMAGE
    assert detect.sniff("x.jpg", b"\xff\xd8\xff" + b"\x00" * 64) == detect.RASTER_IMAGE


@pytest.mark.parametrize("kind", sorted(detect.READABLE))
def test_readable_kinds_have_no_unreadable_reason(kind):
    assert detect.unreadable_reason(kind) == ""


def test_every_unreadable_kind_states_why():
    """An artifact sealed but not read must always carry a reason.

    This is the honest-blank contract from keyless_extractor applied to bytes:
    a blank with no explanation is indistinguishable from a bug.
    """
    for kind in (detect.MECHANICAL_DB, detect.GEOMETRY_DB, detect.RESULT_BINARY,
                 detect.HDF5_CONTAINER, detect.OPAQUE_BINARY, detect.EMPTY,
                 detect.ZIP_ARCHIVE):
        assert detect.unreadable_reason(kind)

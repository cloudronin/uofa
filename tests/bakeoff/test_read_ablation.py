"""The pre-registered primary verdict must partition outcomes as committed in
PREREGISTRATION-2026-05-31-ablation-n60.md — and FALSIFY must be reachable, or the
pre-registration is toothless.
"""
from harness.bakeoff import read_ablation as ra


def test_confirm_fires_when_fired_flag_clearly_worse():
    assert ra.verdict(0.083, 0.0).startswith("CONFIRM")   # the n=24 result
    assert ra.verdict(0.04, 0.0).startswith("CONFIRM")     # boundary Δ=+0.04
    assert ra.verdict(0.10, 0.03).startswith("CONFIRM")    # Δ=+0.07 from a nonzero base


def test_falsify_fires_when_they_converge():
    assert ra.verdict(0.0, 0.0).startswith("FALSIFY")      # identical
    assert ra.verdict(0.02, 0.0).startswith("FALSIFY")     # boundary |Δ|=0.02
    assert ra.verdict(0.05, 0.04).startswith("FALSIFY")    # both nonzero, |Δ|=0.01


def test_inconclusive_in_the_gap():
    assert ra.verdict(0.03, 0.0).startswith("INCONCLUSIVE")   # Δ=0.03 in (0.02, 0.04)
    assert ra.verdict(0.039, 0.0).startswith("INCONCLUSIVE")  # just under the CONFIRM bar


def test_confirm_requires_a_real_fired_flag_danger():
    # Δ≥0.04 can only arise with danger_fired_flag>0 (danger rates are >=0), so the
    # guard is belt-and-suspenders — but a zero-danger fired_flag never CONFIRMs.
    assert not ra.verdict(0.0, 0.0).startswith("CONFIRM")

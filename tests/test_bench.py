"""Benchmark metrics: intervals, counts and blast radius bounds."""

import pytest

from handoffpact.bench import mean_ci, run_bench, wilson
from handoffpact.faults import FAULTS


def test_wilson_known_values():
    lo, hi = wilson(0, 200)
    assert lo == 0.0 and 0.018 < hi < 0.0190
    lo, hi = wilson(50, 100)
    assert lo == pytest.approx(0.4038, abs=1e-3) and hi == pytest.approx(0.5962, abs=1e-3)
    assert wilson(0, 0) == (0.0, 0.0)


def test_mean_ci_contains_mean():
    m, lo, hi = mean_ci([0, 1, 2, 3, 4] * 20, seed=1)
    assert lo <= m <= hi and m == 2


@pytest.fixture(scope="module")
def small():
    return run_bench(faults=140, clean=40, seed=11)


def test_bench_counts_and_mix(small):
    assert small["meta"]["fault_runs"] == 140
    assert small["meta"]["fault_mix"] == {k: 20 for k in FAULTS}
    assert small["false_alarms"]["n"] == 40


def test_blast_radius_bounds(small):
    for r in small["runs"]:
        k = r["edge_index"]
        assert 0 <= r["blast_on"] <= r["blast_off"] <= 4 - k
        if r["detected_at_edge"]:
            assert r["blast_on"] == 0


def test_contracts_shrink_blast_radius(small):
    o = small["overall"]
    assert o["blast_on"][0] < o["blast_off"][0]
    assert o["wrong_delivered_on"]["rate"] < o["wrong_delivered_off"]["rate"]


def test_bench_is_seeded():
    a = run_bench(faults=14, clean=5, seed=3)
    b = run_bench(faults=14, clean=5, seed=3)
    assert a["runs"] == b["runs"]

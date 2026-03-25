import pytest
import numpy as np
from backend.services.analysis import (
    group_into_rows,
    detect_method_mistakes,
    compute_ideal_times,
    compute_striking_errors,
    compute_summary_stats,
    compute_per_bell_stats,
    analyse_performance,
)


def make_timing_data(n_bells=4, n_rows=10, start=10000.0, interval=200.0, noise=0.0):
    """Create synthetic timing data: bells in order 1..n_bells."""
    data = []
    t = start
    for row in range(n_rows):
        for bell in range(1, n_bells + 1):
            data.append((bell, t + noise * (bell - 1)))
            t += interval
        t += interval
    return data


def test_group_into_rows_basic():
    data = [(i % 4 + 1, float(i)) for i in range(12)]
    rows = group_into_rows(data, 4)
    assert len(rows) == 3
    assert len(rows[0]) == 4


def test_group_into_rows_discards_incomplete():
    data = [(i % 4 + 1, float(i)) for i in range(10)]
    rows = group_into_rows(data, 4)
    assert len(rows) == 2  # 10 / 4 = 2 complete rows


def test_detect_method_mistakes_no_mistakes():
    actual = [[1, 2, 3, 4], [2, 1, 4, 3]]
    expected = [[1, 2, 3, 4], [2, 1, 4, 3]]
    assert detect_method_mistakes(actual, expected) == []


def test_detect_method_mistakes_with_mistake():
    actual = [[1, 2, 3, 4], [3, 1, 4, 2]]
    expected = [[1, 2, 3, 4], [2, 1, 4, 3]]
    mistakes = detect_method_mistakes(actual, expected)
    assert 1 in mistakes


def test_compute_ideal_times_basic():
    # 4 rows of 4 bells, perfect timing
    rows_data = [
        [(1, 0.0), (2, 200.0), (3, 400.0), (4, 600.0)],
        [(1, 800.0), (2, 1000.0), (3, 1200.0), (4, 1400.0)],
        [(1, 1600.0), (2, 1800.0), (3, 2000.0), (4, 2200.0)],
        [(1, 2400.0), (2, 2600.0), (3, 2800.0), (4, 3000.0)],
    ]
    ideal = compute_ideal_times(rows_data, set())
    assert len(ideal) == 4
    assert len(ideal[0]) == 4


def test_compute_striking_errors_zero_error():
    rows_data = [
        [(1, 100.0), (2, 300.0), (3, 500.0)],
    ]
    ideal_times = [[100.0, 300.0, 500.0]]
    errors = compute_striking_errors(rows_data, ideal_times)
    assert len(errors) == 1
    assert errors[0][0]["error_ms"] == pytest.approx(0.0)


def test_compute_striking_errors_with_error():
    rows_data = [
        [(1, 110.0), (2, 300.0), (3, 490.0)],
    ]
    ideal_times = [[100.0, 300.0, 500.0]]
    errors = compute_striking_errors(rows_data, ideal_times)
    assert errors[0][0]["error_ms"] == pytest.approx(10.0)
    assert errors[0][2]["error_ms"] == pytest.approx(-10.0)


def test_compute_summary_stats_basic():
    all_errors = [
        {"error_ms": 10.0, "is_inaudible": True},
        {"error_ms": -10.0, "is_inaudible": True},
        {"error_ms": 100.0, "is_inaudible": False},
    ]
    stats = compute_summary_stats(all_errors)
    assert "mean_error" in stats
    assert "pct_inaudible" in stats
    assert stats["pct_inaudible"] == pytest.approx(200.0 / 3)


def test_compute_per_bell_stats_basic():
    striking_errors = [
        [{"bell": 1, "error_ms": 10.0, "is_inaudible": True, "actual": 100.0, "ideal": 90.0},
         {"bell": 2, "error_ms": -5.0, "is_inaudible": True, "actual": 200.0, "ideal": 205.0}],
        [{"bell": 1, "error_ms": 20.0, "is_inaudible": True, "actual": 400.0, "ideal": 380.0},
         {"bell": 2, "error_ms": -15.0, "is_inaudible": True, "actual": 600.0, "ideal": 615.0}],
    ]
    stats = compute_per_bell_stats(striking_errors, 2)
    assert 1 in stats
    assert 2 in stats
    assert "mean_error" in stats[1]
    assert stats[1]["mean_error"] == pytest.approx(15.0)


def test_analyse_performance_basic(sample_method_content, sample_timing_content):
    result = analyse_performance(sample_method_content, sample_timing_content)
    assert "n_bells" in result
    assert result["n_bells"] == 8
    assert "striking_errors" in result
    assert "summary_stats" in result
    assert "per_bell_stats" in result
    assert result["total_rows"] > 0


@pytest.fixture
def sample_method_content():
    rounds = "12345678\n" * 4
    changes = ["21436587\n", "12345678\n"] * 8
    return rounds + "".join(changes)


@pytest.fixture
def sample_timing_content(sample_method_content):
    import random
    random.seed(42)
    from backend.services.parser import parse_method_file
    method_rows = parse_method_file(sample_method_content)
    bell_chars = "1234567890ET"
    lines = ["Bell No,Actual Time"]
    n_bells = 8
    n_rows = min(20, len(method_rows))
    current_time = 10000.0
    interval = 200.0
    for row_idx in range(n_rows):
        row_bells = method_rows[row_idx]
        for pos, bell in enumerate(row_bells):
            t = current_time + pos * interval + random.gauss(0, 10)
            bell_char = bell_chars[bell - 1]
            lines.append(f"{bell_char},{t:.1f}")
        current_time += n_bells * interval + interval
    return "\n".join(lines) + "\n"

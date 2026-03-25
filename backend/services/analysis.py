import numpy as np
from scipy.ndimage import uniform_filter1d
from .parser import parse_method_file, parse_timing_file, detect_n_bells, separate_rounds_and_changes


def group_into_rows(timing_data: list[tuple[int, float]], n_bells: int) -> list[list[tuple[int, float]]]:
    """Group timing data into rows of n_bells entries each. Discard incomplete final row."""
    rows = []
    n = len(timing_data)
    for i in range(0, n - n_bells + 1, n_bells):
        row = timing_data[i:i + n_bells]
        if len(row) == n_bells:
            rows.append(row)
    return rows


def detect_method_mistakes(actual_rows: list[list[int]], expected_rows: list[list[int]]) -> list[int]:
    """Return list of row indices where actual order != expected."""
    mistakes = []
    for i, (actual, expected) in enumerate(zip(actual_rows, expected_rows)):
        if actual != expected:
            mistakes.append(i)
    return mistakes


def compute_ideal_times(rows_data: list[list[tuple[int, float]]], mistake_rows: set[int]) -> list[list[float]]:
    """
    Compute ideal strike times:
    1. For each row: center_time = mean of actual times, interval = (max-min)/(n_bells-1)
    2. Smooth center times and intervals using rolling window (size 8), excluding mistake rows
    3. ideal_time[row][pos] = smoothed_center[row] + (pos - (n_bells-1)/2) * smoothed_interval[row]
    """
    n_rows = len(rows_data)
    if n_rows == 0:
        return []
    n_bells = len(rows_data[0])
    center_times = np.array([np.mean([t for _, t in row]) for row in rows_data])
    if n_bells > 1:
        intervals = np.array([(max(t for _, t in row) - min(t for _, t in row)) / (n_bells - 1) for row in rows_data])
    else:
        intervals = np.zeros(n_rows)

    # Mask mistake rows and interpolate
    good_mask = np.array([i not in mistake_rows for i in range(n_rows)])
    indices = np.arange(n_rows)
    if good_mask.any():
        good_indices = indices[good_mask]
        center_times_smooth = np.interp(indices, good_indices, center_times[good_mask])
        intervals_smooth = np.interp(indices, good_indices, intervals[good_mask])
    else:
        center_times_smooth = center_times.copy()
        intervals_smooth = intervals.copy()

    win = min(8, n_rows)
    center_times_smooth = uniform_filter1d(center_times_smooth, size=win, mode="nearest")
    intervals_smooth = uniform_filter1d(intervals_smooth, size=win, mode="nearest")

    ideal = []
    half = (n_bells - 1) / 2.0
    for r in range(n_rows):
        row_ideal = [center_times_smooth[r] + (pos - half) * intervals_smooth[r] for pos in range(n_bells)]
        ideal.append(row_ideal)
    return ideal


def compute_striking_errors(rows_data: list[list[tuple[int, float]]], ideal_times: list[list[float]]) -> list[list[dict]]:
    """Returns per-row, per-bell: {bell, actual, ideal, error_ms, is_inaudible}. is_inaudible = abs(error) <= 50ms"""
    result = []
    for row_data, row_ideal in zip(rows_data, ideal_times):
        row_errors = []
        for pos, ((bell, actual), ideal) in enumerate(zip(row_data, row_ideal)):
            error_ms = actual - ideal
            row_errors.append({
                "bell": bell,
                "actual": actual,
                "ideal": ideal,
                "error_ms": error_ms,
                "is_inaudible": bool(abs(error_ms) <= 50),
            })
        result.append(row_errors)
    return result


def compute_summary_stats(all_errors: list[dict]) -> dict:
    """Compute mean_error, std_error, mean_abs_error, pct_inaudible from flat list of error dicts."""
    if not all_errors:
        return {"mean_error": 0, "std_error": 0, "mean_abs_error": 0, "pct_inaudible": 0}
    errors = np.array([e["error_ms"] for e in all_errors])
    inaudible = np.array([e["is_inaudible"] for e in all_errors])
    return {
        "mean_error": float(np.mean(errors)),
        "std_error": float(np.std(errors)),
        "mean_abs_error": float(np.mean(np.abs(errors))),
        "pct_inaudible": float(np.mean(inaudible) * 100),
    }


def compute_per_bell_stats(striking_errors: list[list[dict]], n_bells: int) -> dict:
    """
    Per-bell stats: {bell: {mean_error, std_error, mean_abs_error,
                            backstroke_mean, handstroke_mean, backstroke_std, handstroke_std,
                            pct_inaudible}}
    Backstroke = odd rows (1-indexed), handstroke = even rows.
    """
    bell_errors: dict[int, list[float]] = {b: [] for b in range(1, n_bells + 1)}
    bell_bs: dict[int, list[float]] = {b: [] for b in range(1, n_bells + 1)}
    bell_hs: dict[int, list[float]] = {b: [] for b in range(1, n_bells + 1)}
    bell_inaudible: dict[int, list[bool]] = {b: [] for b in range(1, n_bells + 1)}

    for row_idx, row_errors in enumerate(striking_errors):
        is_backstroke = (row_idx % 2 == 0)  # 0-indexed: row 0 = first row = backstroke (1-indexed odd)
        for entry in row_errors:
            bell = entry["bell"]
            if bell not in bell_errors:
                bell_errors[bell] = []
                bell_bs[bell] = []
                bell_hs[bell] = []
                bell_inaudible[bell] = []
            bell_errors[bell].append(entry["error_ms"])
            bell_inaudible[bell].append(entry["is_inaudible"])
            if is_backstroke:
                bell_bs[bell].append(entry["error_ms"])
            else:
                bell_hs[bell].append(entry["error_ms"])

    per_bell = {}
    for bell in range(1, n_bells + 1):
        errs = np.array(bell_errors[bell]) if bell_errors[bell] else np.array([0.0])
        bs = np.array(bell_bs[bell]) if bell_bs[bell] else np.array([0.0])
        hs = np.array(bell_hs[bell]) if bell_hs[bell] else np.array([0.0])
        inaud = bell_inaudible[bell]
        per_bell[bell] = {
            "mean_error": float(np.mean(errs)),
            "std_error": float(np.std(errs)),
            "mean_abs_error": float(np.mean(np.abs(errs))),
            "backstroke_mean": float(np.mean(bs)),
            "handstroke_mean": float(np.mean(hs)),
            "backstroke_std": float(np.std(bs)),
            "handstroke_std": float(np.std(hs)),
            "pct_inaudible": float(np.mean(inaud) * 100) if inaud else 0.0,
        }
    return per_bell


def compute_tempo_data(rows_data: list[list[tuple[int, float]]]) -> list[dict]:
    """Return [{row_index, center_time_ms, interval_ms}] for each row."""
    result = []
    for i, row in enumerate(rows_data):
        times = [t for _, t in row]
        center = float(np.mean(times))
        n = len(times)
        interval = float((max(times) - min(times)) / (n - 1)) if n > 1 else 0.0
        result.append({"row_index": i, "center_time_ms": center, "interval_ms": interval})
    return result


def analyse_performance(method_content: str, timing_content: str) -> dict:
    """Full analysis."""
    method_rows = parse_method_file(method_content)
    timing_data = parse_timing_file(timing_content)
    if not method_rows or not timing_data:
        return {"error": "No data to analyse"}
    n_bells = detect_n_bells(method_rows)
    rows_data = group_into_rows(timing_data, n_bells)
    if not rows_data:
        return {"error": "Could not group timing data into rows"}
    rounds_end, changes_start = separate_rounds_and_changes(method_rows, n_bells)
    total_rows = len(rows_data)
    # Align expected rows to actual data rows
    expected_rows = method_rows[:total_rows] if len(method_rows) >= total_rows else method_rows + [method_rows[-1]] * (total_rows - len(method_rows))
    actual_rows = [[bell for bell, _ in row] for row in rows_data]
    mistake_rows_list = detect_method_mistakes(actual_rows, expected_rows)
    mistake_rows_set = set(mistake_rows_list)
    ideal_times = compute_ideal_times(rows_data, mistake_rows_set)
    striking_errors = compute_striking_errors(rows_data, ideal_times)
    all_errors = [entry for row in striking_errors for entry in row]
    summary_stats = compute_summary_stats(all_errors)
    per_bell_stats = compute_per_bell_stats(striking_errors, n_bells)
    tempo_data = compute_tempo_data(rows_data)
    return {
        "n_bells": n_bells,
        "total_rows": total_rows,
        "rounds_rows": rounds_end,
        "changes_rows": total_rows - rounds_end,
        "mistake_rows": mistake_rows_list,
        "striking_errors": striking_errors,
        "summary_stats": summary_stats,
        "tempo_data": tempo_data,
        "per_bell_stats": per_bell_stats,
    }


def analyse_multiple_performances(performances: list[dict]) -> dict:
    """Analyse multiple performances."""
    results = []
    for p in performances:
        r = analyse_performance(p["method_content"], p["timing_content"])
        r["label"] = p["label"]
        results.append(r)
    # Build trend: per bell, list of {label, mean_error, std_error}
    trend: dict[int, list[dict]] = {}
    for r in results:
        per_bell_stats = r.get("per_bell_stats", {})
        for bell, stats in per_bell_stats.items():
            trend.setdefault(bell, []).append({
                "label": r.get("label"),
                "mean_error": stats.get("mean_error"),
                "std_error": stats.get("std_error"),
            })
    return {"performances": results, "trend": trend}

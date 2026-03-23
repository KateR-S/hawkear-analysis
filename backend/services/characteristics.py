import numpy as np


def compute_characteristics(per_bell_errors: dict) -> dict:
    """
    per_bell_errors: {bell: [error_ms per strike in order]}
    For each bell, compute characteristics.
    """
    result = {}
    bells = sorted(per_bell_errors.keys())
    for i, bell in enumerate(bells):
        errors = np.array(per_bell_errors[bell], dtype=float)
        n = len(errors)
        # lag-1 autocorrelation
        if n > 2:
            lag1 = float(np.corrcoef(errors[:-1], errors[1:])[0, 1])
            if np.isnan(lag1):
                lag1 = 0.0
        else:
            lag1 = 0.0
        # backstroke = even indices (0, 2, 4...), handstroke = odd indices
        backstroke_errors = errors[0::2]
        handstroke_errors = errors[1::2]
        backstroke_mean = float(np.mean(backstroke_errors)) if len(backstroke_errors) > 0 else 0.0
        handstroke_mean = float(np.mean(handstroke_errors)) if len(handstroke_errors) > 0 else 0.0
        mean_abs = float(np.mean(np.abs(errors))) if n > 0 else 0.0
        std = float(np.std(errors)) if n > 0 else 0.0
        low_confidence = bool(mean_abs < 30 and std > 60)
        # Correlation with previous bell's errors
        if i > 0:
            prev_errors = np.array(per_bell_errors[bells[i - 1]], dtype=float)
            min_len = min(len(errors), len(prev_errors))
            if min_len > 2:
                corr = float(np.corrcoef(prev_errors[:min_len], errors[:min_len])[0, 1])
                if np.isnan(corr):
                    corr = 0.0
            else:
                corr = 0.0
        else:
            corr = 0.0
        result[bell] = {
            "slow_tempo_reaction": lag1,
            "backstroke_tendency": backstroke_mean,
            "handstroke_tendency": handstroke_mean,
            "low_confidence": low_confidence,
            "influenced_by_previous": corr,
        }
    return result

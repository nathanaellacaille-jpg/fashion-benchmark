# scoring.py
# Proper scoring rules for binary predictions.
#
# WHY LOG SCORE PUNISHES RARE EVENTS MORE HARSHLY THAN BRIER SCORE:
#   The Brier score uses squared error: (p - outcome)^2.
#   For a rare TRUE event (outcome=1) where you assigned p=0.05,
#   Brier penalty = (0.05 - 1)^2 = 0.9025 — bounded and moderate.
#
#   The log score uses -log(p) when the event occurs.
#   For the same p=0.05: log penalty = -log(0.05) ≈ 3.00 — and it
#   grows to +∞ as p → 0. A forecaster who says "1% chance" and is
#   wrong gets a finite Brier hit but an extreme (potentially infinite)
#   log hit. This makes the log score incentive-compatible for
#   well-calibrated probabilities on low-base-rate events: you cannot
#   shrug off a rare TRUE outcome the way Brier lets you.

import math


def compute_brier_score(predicted_prob: float, outcome: int) -> float:
    """
    Brier score for a single binary forecast.

    Args:
        predicted_prob: forecast probability of outcome=1, in [0, 1]
        outcome: realised outcome, 0 or 1

    Returns:
        Brier score in [0, 1]; lower is better (0 = perfect).
    """
    if not (0.0 <= predicted_prob <= 1.0):
        raise ValueError(f"predicted_prob must be in [0,1], got {predicted_prob}")
    if outcome not in (0, 1):
        raise ValueError(f"outcome must be 0 or 1, got {outcome}")
    return (predicted_prob - outcome) ** 2


def compute_log_score(predicted_prob: float, outcome: int) -> float:
    """
    Log score (negative log-likelihood) for a single binary forecast.

    Args:
        predicted_prob: forecast probability of outcome=1, in (0, 1]
                        (clipped to 1e-15 to avoid log(0))
        outcome: realised outcome, 0 or 1

    Returns:
        Log score ≥ 0; lower is better (0 = perfect certainty, correct).
    """
    if not (0.0 <= predicted_prob <= 1.0):
        raise ValueError(f"predicted_prob must be in [0,1], got {predicted_prob}")
    if outcome not in (0, 1):
        raise ValueError(f"outcome must be 0 or 1, got {outcome}")

    epsilon = 1e-15
    p = max(epsilon, min(1 - epsilon, predicted_prob))

    if outcome == 1:
        return -math.log(p)
    else:
        return -math.log(1 - p)


# ── Unit tests ────────────────────────────────────────────────────────────────

def _run_tests():
    tol = 1e-9

    # Perfect prediction
    assert abs(compute_brier_score(1.0, 1)) < tol,  "brier: perfect TRUE"
    assert abs(compute_brier_score(0.0, 0)) < tol,  "brier: perfect FALSE"
    assert abs(compute_log_score(1.0, 1))   < tol,  "log: perfect TRUE"
    assert abs(compute_log_score(0.0, 0))   < tol,  "log: perfect FALSE"

    # Worst prediction
    assert abs(compute_brier_score(0.0, 1) - 1.0) < tol, "brier: worst TRUE"
    assert abs(compute_brier_score(1.0, 0) - 1.0) < tol, "brier: worst FALSE"

    # Known values
    assert abs(compute_brier_score(0.7, 1) - 0.09) < tol, "brier: 0.7 TRUE"
    assert abs(compute_brier_score(0.3, 0) - 0.09) < tol, "brier: 0.3 FALSE"
    assert abs(compute_log_score(0.5, 1) - math.log(2)) < tol, "log: 0.5 TRUE"
    assert abs(compute_log_score(0.5, 0) - math.log(2)) < tol, "log: 0.5 FALSE"

    # Log score grows for low-prob TRUE events
    log_5pct  = compute_log_score(0.05, 1)
    log_50pct = compute_log_score(0.50, 1)
    assert log_5pct > log_50pct, "log score should punish rare correct event more"

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()

    # Demo
    print("\n-- Demo --")
    for p, o in [(0.9, 1), (0.5, 1), (0.1, 1), (0.9, 0)]:
        print(
            f"  p={p:.1f}, outcome={o}"
            f"  brier={compute_brier_score(p, o):.4f}"
            f"  log={compute_log_score(p, o):.4f}"
        )

"""Bayesian blending of live data with priors."""

from typing import Optional, Tuple


def blend_with_prior(
    live_value: Optional[float],
    prior: float,
    live_weight: float = 0.70,
) -> float:
    """
    Blend live observed value with prior.
    If live_value is None, use prior.
    live_weight: how much to trust live data (0-1).
    """
    if live_value is None:
        return prior
    return live_weight * live_value + (1 - live_weight) * prior


def bayesian_credible_interval(
    successes: Optional[int],
    trials: Optional[int],
    alpha: float = 0.05,
) -> Optional[Tuple[float, float]]:
    """
    Compute Bayesian credible interval using Beta-Binomial model.
    Returns (lower, upper) bounds, or None if data missing.
    alpha: confidence level (0.05 -> 95% CI).
    """
    if successes is None or trials is None:
        return None

    try:
        from scipy import stats

        # Beta prior: uniform (1, 1)
        prior_a, prior_b = 1, 1
        posterior_a = prior_a + successes
        posterior_b = prior_b + (trials - successes)

        lower = stats.beta.ppf(alpha / 2, posterior_a, posterior_b)
        upper = stats.beta.ppf(1 - alpha / 2, posterior_a, posterior_b)
        return (lower, upper)
    except ImportError:
        # Fallback if scipy not available
        return None

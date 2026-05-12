import numpy as np

# -----------------------------
# Regime definitions
# -----------------------------
REGIMES = ["normal", "bull", "bear", "crash"]

def sample_regime(current_regime="normal"):
    """
    Markov-style regime transition (simple version)
    """

    if current_regime == "normal":
        return np.random.choice(
            REGIMES,
            p=[0.70, 0.15, 0.10, 0.05]
        )

    if current_regime == "bull":
        return np.random.choice(
            REGIMES,
            p=[0.60, 0.25, 0.10, 0.05]
        )

    if current_regime == "bear":
        return np.random.choice(
            REGIMES,
            p=[0.60, 0.10, 0.25, 0.05]
        )

    if current_regime == "crash":
        return np.random.choice(
            REGIMES,
            p=[0.50, 0.10, 0.10, 0.30]
        )

    return "normal"


def get_regime_params(regime):
    """
    Returns expected return parameters per regime
    """

    if regime == "normal":
        return dict(
            equity_mean=0.07,
            equity_vol=0.15,
            bond_mean=0.03,
            bond_vol=0.05
        )

    if regime == "bull":
        return dict(
            equity_mean=0.12,
            equity_vol=0.12,
            bond_mean=0.02,
            bond_vol=0.04
        )

    if regime == "bear":
        return dict(
            equity_mean=-0.02,
            equity_vol=0.18,
            bond_mean=0.03,
            bond_vol=0.06
        )

    if regime == "crash":
        return dict(
            equity_mean=-0.15,
            equity_vol=0.30,
            bond_mean=0.01,
            bond_vol=0.10
        )

    return get_regime_params("normal")
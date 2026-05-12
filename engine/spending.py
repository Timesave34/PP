import numpy as np

def inflate(value, inflation, years):
    """
    Applies compound inflation over time.
    """
    return value * ((1 + inflation) ** years)

def spending_path_factory(
    go_spend,
    slow_spend,
    no_spend,
    state_pension,
    inflation=0.02
):
    """
    Returns a spending function used inside simulation.
    """

    def spending(age, start_age):

        years = age - start_age

        # -----------------------------
        # 1. Life phase spending level
        # -----------------------------
        if age < start_age + 10:
            base = go_spend
        elif age < start_age + 25:
            base = slow_spend
        else:
            base = no_spend

        # -----------------------------
        # 2. Behavioural variation
        # -----------------------------
        drift = np.random.normal(1.0, 0.05)  # lifestyle variation
        base *= drift

        # -----------------------------
        # 3. Inflation adjustment
        # -----------------------------
        # spending already assumed real terms

        # -----------------------------
        # 4. State pension offset
        # -----------------------------
        #net_spend = max(0, base - state_pension)
        net_spend = base

        # -----------------------------
        # 5. Random spending shocks
        # (care costs / car repairs / health events)
        # -----------------------------
        shock = np.random.choice(
            [0, 0, 0, 2000, 5000],
            p=[0.70, 0.15, 0.10, 0.04, 0.01]
        )

        return net_spend + shock

    return spending
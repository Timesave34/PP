import numpy as np

from engine.state import FinancialState
from engine.spending import spending_path_factory
from engine.withdrawals import withdraw
from engine.regimes import sample_regime, get_regime_params


# ------------------------------------------------
# TAX MODEL (simplified UK)
# ------------------------------------------------
def calculate_income_tax(income, allowance=12570, basic_rate=0.20, higher_rate=0.40):

    taxable = max(0, income - allowance)

    if taxable <= 37700:
        return taxable * basic_rate

    basic = 37700 * basic_rate
    higher = (taxable - 37700) * higher_rate

    return basic + higher


# ------------------------------------------------
# MONTE CARLO ENGINE
# ------------------------------------------------
def run_simulation(initial_state, years, spending_path, sims=1000, inflation=0.02):

    results = np.zeros((sims, years))

    for s in range(sims):

        # --- clone state per simulation path ---
        state = FinancialState(
            age=initial_state.age,
            pension=initial_state.pension,
            isa=initial_state.isa,
            taxable=initial_state.taxable,
            cash=initial_state.cash
        )

        regime = "normal"

        for y in range(years):

            # 1. age
            age = state.age + y

            # 2. regime + returns
            regime = sample_regime(regime)
            params = get_regime_params(regime)

            equity_return = np.random.normal(params["equity_mean"], params["equity_vol"])
            bond_return   = np.random.normal(params["bond_mean"], params["bond_vol"])

            # 3. update assets
            state.pension *= (1 + equity_return)
            state.isa *= (1 + equity_return)
            state.taxable *= (1 + bond_return)
            state.cash *= 1.01

            # 4. spending
            gross_spend = spending_path(age, initial_state.age)
            state_pension_income = 0
            if age >= 67:
                state_pension_income = 14364

            # 5. withdrawal (NOW STRUCTURED)
            #withdrawal = withdraw(state, gross_spend)
            required_withdrawal = max(
                0,
                gross_spend - state_pension_income
            )

            withdrawal_breakdown = withdraw(
                state,
                required_withdrawal
            )

            # 6. taxable income (advisor logic)
            taxable_income = withdrawal_breakdown["pension"] + withdrawal_breakdown["taxable"]

            tax = calculate_income_tax(taxable_income)

            # 7. net cashflow into buffer
            net_income = (
                withdrawal_breakdown["cash"] +
                withdrawal_breakdown["isa"] +
                (taxable_income - tax)
            )

            state.cash += net_income

            # ------------------------------------------------
            # 8. Track total wealth
            # ------------------------------------------------
            results[s, y] = state.total_value()

            # ------------------------------------------------
            # 9. Ruin condition
            # ------------------------------------------------
            if state.total_value() <= 0:
                results[s, y:] = 0
                break

    return results
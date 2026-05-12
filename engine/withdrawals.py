from engine.state import FinancialState

def withdraw(state: FinancialState, gross_spending: float):
    """
    Advisor-grade withdrawal engine.

    Returns a structured breakdown of where money was taken from.
    Order:
    1. Cash
    2. Taxable
    3. ISA
    4. Pension
    """

    remaining = gross_spending

    breakdown = {
        "cash": 0.0,
        "taxable": 0.0,
        "isa": 0.0,
        "pension": 0.0
    }

    # 1. Cash
    take = min(state.cash, remaining)
    state.cash -= take
    remaining -= take
    breakdown["cash"] = take

    # 2. Taxable
    if remaining > 0:
        take = min(state.taxable, remaining)
        state.taxable -= take
        remaining -= take
        breakdown["taxable"] = take

    # 3. ISA
    if remaining > 0:
        take = min(state.isa, remaining)
        state.isa -= take
        remaining -= take
        breakdown["isa"] = take

    # 4. Pension
    if remaining > 0:
        take = min(state.pension, remaining)
        state.pension -= take
        remaining -= take
        breakdown["pension"] = take

    return breakdown
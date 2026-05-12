import pandas as pd
import numpy as np

from engine.state import FinancialState

# ------------------------------------------------
# UK TAX MODEL (simplified)
# ------------------------------------------------
def calculate_income_tax(
    taxable_income,
    allowance=12570
):

    taxable = max(0, taxable_income - allowance)

    basic_band = 37700

    if taxable <= basic_band:
        return taxable * 0.20

    basic_tax = basic_band * 0.20
    higher_tax = (taxable - basic_band) * 0.40

    return basic_tax + higher_tax


# ------------------------------------------------
# DETERMINISTIC CASHFLOW LEDGER
# ------------------------------------------------
def build_cashflow_ledger(
    state,
    years,
    spending,
    growth=0.05,
    inflation=0.02,
    state_pension=14364,
    state_pension_age=67
):

    rows = []

    # local copies
    pension = state.pension
    isa = state.isa
    taxable = state.taxable
    cash = state.cash

    for y in range(years):

        age = state.age + y

        # ------------------------------------------------
        # START VALUES
        # ------------------------------------------------
        pension_start = pension
        isa_start = isa
        taxable_start = taxable
        cash_start = cash

        # ------------------------------------------------
        # STATE PENSION (inflation linked)
        # ------------------------------------------------
        if age >= state_pension_age:

            years_on_sp = age - state_pension_age

            current_state_pension = (
                state_pension *
                ((1 + inflation) ** years_on_sp)
            )

        else:
            current_state_pension = 0

        # ------------------------------------------------
        # SPENDING NEED
        # ------------------------------------------------
        gross_spend = spending(age, state.age)

        # ------------------------------------------------
        # REQUIRED PORTFOLIO WITHDRAWAL
        # ------------------------------------------------
        required = max(
            0,
            gross_spend - current_state_pension
        )

        remaining = required

        # ------------------------------------------------
        # WITHDRAWAL ORDER
        # ------------------------------------------------
        cash_wdl = min(cash, remaining)
        cash -= cash_wdl
        remaining -= cash_wdl

        taxable_wdl = min(taxable, remaining)
        taxable -= taxable_wdl
        remaining -= taxable_wdl

        isa_wdl = min(isa, remaining)
        isa -= isa_wdl
        remaining -= isa_wdl

        pension_wdl = min(pension, remaining)
        pension -= pension_wdl
        remaining -= pension_wdl

        total_withdrawal = (
            cash_wdl +
            taxable_wdl +
            isa_wdl +
            pension_wdl
        )
        
        # ------------------------------------------------
        # FUNDING GAP / SHORTFALL
        # ------------------------------------------------
        available_income = (
            current_state_pension +
            total_withdrawal
        )
        shortfall = max(
            0,
            gross_spend - available_income
        )

        # ------------------------------------------------
        # TAX CALCULATION
        # Pension = 25% tax free
        # ------------------------------------------------
        tax_free_cash = pension_wdl * 0.25

        taxable_pension = pension_wdl * 0.75

        taxable_income = (
            current_state_pension +
            taxable_wdl +
            taxable_pension
        )

        tax_paid = calculate_income_tax(
            taxable_income
        )

        # ------------------------------------------------
        # GROWTH
        # ------------------------------------------------
        pension_growth = pension * growth
        isa_growth = isa * growth
        taxable_growth = taxable * 0.03
        cash_growth = cash * 0.01

        pension += pension_growth
        isa += isa_growth
        taxable += taxable_growth
        cash += cash_growth

        # ------------------------------------------------
        # END VALUES
        # ------------------------------------------------
        total_end = (
            pension +
            isa +
            taxable +
            cash
        )

        rows.append({

            "Age": age,

            "Gross Spend":
                round(gross_spend, 0),

            "State Pension":
                round(current_state_pension, 0),

            "Required Wdl":
                round(required, 0),

            "Cash Wdl":
                round(cash_wdl, 0),

            "Taxable Wdl":
                round(taxable_wdl, 0),

            "ISA Wdl":
                round(isa_wdl, 0),

            "Pension Wdl":
                round(pension_wdl, 0),

            "Tax Free 25%":
                round(tax_free_cash, 0),

            "Taxable Income":
                round(taxable_income, 0),

            "Tax Paid":
                round(tax_paid, 0),
                
            "Shortfall":
                round(shortfall, 0),

            "Pension Start":
                round(pension_start, 0),

            "Pension Growth":
                round(pension_growth, 0),

            "Pension End":
                round(pension, 0),

            "ISA End":
                round(isa, 0),

            "Taxable End":
                round(taxable, 0),

            "Cash End":
                round(cash, 0),

            "Total Portfolio":
                round(total_end, 0)
        })

    return pd.DataFrame(rows)

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from engine.state import FinancialState
from engine.simulation import run_simulation
from engine.spending import spending_path_factory
from engine.spending import spending_path_factory
from engine.input_loader import load_inputs
from engine.cashflow import build_cashflow_ledger

excel = load_inputs()
# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(page_title="Retirement Adviser", layout="wide")

st.title("Retirement Planning Dashboard (v8)")

#new css start
st.markdown("""
<style>

/* Reduce sidebar top padding */
section[data-testid="stSidebar"] > div {
    padding-top: 0.2rem;
}

/* Reduce spacing between widgets */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.1rem;
}

/* Reduce slider spacing */
.stSlider {
    padding-top: 0rem;
    padding-bottom: 0rem;
}

/* Reduce markdown/caption spacing */
p {
    margin-bottom: 0.1rem;
}

/* Reduce overall container padding */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# SIDEBAR INPUTS (clean + grouped)
# ------------------------------------------------
st.sidebar.header("Client Inputs")

#-----------------------------------
age = st.sidebar.slider("Current Age",40,75,int(excel["Current Age"]))
life = st.sidebar.slider("Life Expectancy",75,105,int(excel["Life Expectancy"]))
pension_value = st.sidebar.number_input("Pension Value",0,5000000,int(excel["Pension Value"]),step=1000)
isa_value = st.sidebar.number_input("ISA Value",0,5000000,int(excel["ISA Value"]),step=500)
taxable_value = st.sidebar.number_input("Taxable Account",0,5000000,int(excel["Taxable Account"]),step=500)
cash_reserve = st.sidebar.number_input("Cash Reserve",0,5000000,int(excel["Cash Reserve"]),step=500)

formatted_pv = f"{pension_value:,}"
formatted_iv = f"{isa_value:,}"
formatted_tv = f"{taxable_value:,}"
formatted_cv = f"{cash_reserve:,}"
st.info(f"Date entry: SIPP pot=£{formatted_pv}, ISA=£{formatted_iv}, Taxable=£{formatted_tv} & Cash=£{formatted_cv}.") 
#---------------------------------
#age = st.sidebar.slider("Current Age", 40, 75, 60)
#age = st.sidebar.slider("Age",50,75,int(excel["1 Current Age"]))
#life = st.sidebar.slider("Life Expectancy", 75, 100, 90)
#portfolio = st.sidebar.slider("Total Portfolio", 100000, 2000000, 500000, step=10000)
#portfolio = st.sidebar.number_input("Portfolio",100000,5000000,int(excel["4 Current Savings"]),step=10000)

spend_gogo = st.sidebar.number_input("Go-Go Spending", 10000, 100000, int(excel["Base Expenses Go-Go"]), step=500)
spend_goslow = st.sidebar.number_input("Slow-Go Spending", 10000, 100000, int(excel["Base Expenses Slow-Go"]), step=500)
spend_nogo = st.sidebar.number_input("No-Go Spending", 5000, 80000, int(excel["Base Expenses No-Go"]), step=500)

state_pension = st.sidebar.number_input("State Pension", 0, 25000, 12000, step=500)

sims = st.sidebar.slider("Simulations", 100, 2000, 500, step=100)

# ------------------------------------------------
# BUILD INITIAL STATE
# ------------------------------------------------
#state = FinancialState(age=age,pension=portfolio * 0.5,isa=portfolio * 0.3,taxable=portfolio * 0.1,cash=portfolio * 0.1)
state = FinancialState(
    age=age,
    pension=pension_value,
    isa=isa_value,
    taxable=taxable_value,
    cash=cash_reserve
)

# ------------------------------------------------
# SPENDING PATH
#    state_pension=state_pension
# ------------------------------------------------
#spending_path = spending_path_factory(go_spend=spend_gogo,slow_spend=spend_goslow,no_spend=spend_nogo,state_pension=12000,inflation=0.02)
spending_path = spending_path_factory(
    go_spend=float(excel["Base Expenses Go-Go"]),
    slow_spend=float(excel["Base Expenses Slow-Go"]),
    no_spend=float(excel["Base Expenses No-Go"]),
    state_pension=float(excel["State Pension"]),
    inflation=0.02
)

years = life - age

# ------------------------------------------------
# RUN SIMULATION
# ------------------------------------------------
results = run_simulation(
    initial_state=state,
    years=years,
    spending_path=spending_path,
    sims=sims
)
# ------------------------------------------------
#new table showing taxflow
# ------------------------------------------------
cashflow_df = build_cashflow_ledger(
    state=state,
    years=life - age,
    spending=spending_path,
    growth=0.05,
    inflation=0.02,
    state_pension=float(excel["State Pension"]),
    state_pension_age=int(excel["State Pension Start Age"])
)

# ------------------------------------------------
# DERIVED METRICS
# ------------------------------------------------
median = np.percentile(results, 50, axis=0)
p10 = np.percentile(results, 10, axis=0)
p90 = np.percentile(results, 90, axis=0)

final_values = results[:, -1]

success_rate = (final_values > 0).mean() * 100

# ------------------------------------------------
# TOP SUMMARY STRIP (IFA STYLE)
# ------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Success Probability", f"{success_rate:.1f}%")
col2.metric("Median Final Wealth", f"£{int(median[-1]):,}")
col3.metric("Worst Case (10%)", f"£{int(np.percentile(final_values,10)):,}")

st.markdown("---")

# ------------------------------------------------
# TAB LAYOUT (Voyant-style structure)
# ------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Wealth Projection", "Risk Analysis", "Cashflow View"])

ages = np.arange(age, life)

# ------------------------------------------------
# TAB 1: WEALTH PROJECTION (fan chart)
# ------------------------------------------------
with tab1:

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=ages,
        y=p90,
        line=dict(width=0),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=ages,
        y=p10,
        fill='tonexty',
        name="10–90% Range",
        opacity=0.3
    ))

    fig.add_trace(go.Scatter(
        x=ages,
        y=median,
        name="Median Outcome",
        line=dict(width=3)
    ))

    fig.update_layout(
        title="Projected Wealth Over Time",
        xaxis_title="Age",
        yaxis_title="Portfolio Value (£)"
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# TAB 2: RISK (ruin probability curve)
# ------------------------------------------------
with tab2:

    ruin_curve = []

    for y in range(results.shape[1]):
        ruin_curve.append((results[:, y] <= 0).mean() * 100)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=ages,
        y=ruin_curve,
        name="Probability of Ruin"
    ))

    fig.update_layout(
        title="Risk of Depletion Over Time",
        xaxis_title="Age",
        yaxis_title="Failure Probability (%)"
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# TAB 3: CASHFLOW STYLE VIEW (simplified)
# ------------------------------------------------
with tab3:

    st.subheader("Portfolio Distribution at Retirement")

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=final_values,
        nbinsx=40
    ))

    fig.update_layout(
        title="Distribution of Final Wealth",
        xaxis_title="Final Portfolio (£)",
        yaxis_title="Frequency"
    )

    st.plotly_chart(fig, use_container_width=True)


# new charts
fig = go.Figure()

fig.add_bar(
    x=cashflow_df["Age"],
    y=cashflow_df["State Pension"],
    name="State Pension",
    marker=dict(color='#0D1763')
)

fig.add_bar(
    x=cashflow_df["Age"],
    y=cashflow_df["Cash Wdl"],
    name="Cash"
)

fig.add_bar(
    x=cashflow_df["Age"],
    y=cashflow_df["Taxable Wdl"],
    name="Taxable",
    marker=dict(color='#FF0000')
)

fig.add_bar(
    x=cashflow_df["Age"],
    y=cashflow_df["ISA Wdl"],
    name="ISA", 
    marker=dict(color='#08C77E')
)

fig.add_bar(
    x=cashflow_df["Age"],
    y=cashflow_df["Pension Wdl"],
    name="Pension",
    marker=dict(color='#0D6348')
)

fig.add_bar(
    x=cashflow_df["Age"],
    y=cashflow_df["Shortfall"],
    name="Shortfall",
    marker=dict(color="#F5279F")
)

fig.add_trace(
    go.Scatter(
        x=cashflow_df["Age"],
        y=cashflow_df["Gross Spend"],
        name="Total Need",
        mode="lines",
        line=dict(color="black", width=3)
    )
)

fig.update_layout(
    barmode="stack",
    title="Retirement Cashflow Plan",
    xaxis_title="Age",
    yaxis_title="£ per year"
)
st.plotly_chart(fig, use_container_width=True)

# display the chart
st.markdown("""
<style>

/* dataframe header */
thead tr th {
    font-size: 11px !important;
    padding: 2px !important;
}

/* dataframe cells */
tbody tr td {
    font-size: 11px !important;
    padding: 2px !important;
}

</style>
""", unsafe_allow_html=True)
st.subheader("Retirement Cashflow Ledger")
st.dataframe(cashflow_df, hide_index=True)

# ------------------------------------------------
# RAW STATS (optional debug)
# ------------------------------------------------
with st.expander("Debug Stats"):
    st.write("Shape:", results.shape)
    st.write("Median final:", np.median(final_values))
    st.write("Mean final:", np.mean(final_values))

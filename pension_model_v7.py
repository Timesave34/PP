#v7 adds improvement spliting csh2/cash to equities.
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os
import copy

EXCEL_PATH=r"C:\Users\ianbe\PyPen1\pension_inputs.xlsm"

# ------------------------------------------------
# LOAD INPUTS
# ------------------------------------------------

def load_inputs():

    df=pd.read_excel(EXCEL_PATH,sheet_name="Inputs")

    vals={}
    for _,r in df.iterrows():

        label=str(r["Label"])
        label=label.split(" ",1)[1] if label[0].isdigit() else label
        vals[label.strip()]=r["Data"]

    return vals

excel=load_inputs()

# ------------------------------------------------
# PARSE GIFTS
# ------------------------------------------------

def parse_gifts(text):

    gifts={}
    if isinstance(text,str):

        items=text.split(",")

        for i in items:

            val,age=i.split("-")
            gifts[int(age)]=float(val)

    return gifts

# ------------------------------------------------
# PARSE INFLATION SCHEDULE
# ------------------------------------------------

def parse_inflation(text,yrs):

    rates=[float(x) for x in text.split(",")]
    out=[]

    for r in rates:
        for _ in range(yrs):
            out.append(r)

    return out

# ------------------------------------------------
# MONTE CARLO
# ------------------------------------------------

def simulate(i):

    sims=i["sims"]
    years=i["life"]-i["age"]+1

    balances=np.zeros((sims,years))
    withdrawals=np.zeros((sims,years))
    ruin=np.zeros((sims,years))

    inflation_schedule=parse_inflation(i["infl_text"],i["infl_years"])
    gifts=parse_gifts(i["gifts"])

    for s in range(sims):

        #portfolio=i["portfolio"]
        cash=min(90000,i["portfolio"])
        equity=i["portfolio"]-cash

        for y in range(years):

            age=i["age"]+y

            if age<i["go_end"]:
                spend=i["go"]
            elif age<i["slow_end"]:
                spend=i["slow"]
            else:
                spend=i["no"]

            if age>=i["sp_age"]:
                spend-=i["sp"]

            spend=max(spend,0)

            if age in gifts:
                spend+=gifts[age]

            withdrawals[s,y]=spend

            r=np.random.normal(i["return"],i["vol"])

            #inflation=inflation_schedule[min(y,len(inflation_schedule)-1)]
            base_infl=inflation_schedule[min(y,len(inflation_schedule)-1)]
            inflation=np.random.normal(base_infl,i["infl_vol"])

            real_return=((1+r)/(1+inflation))-1

            #portfolio=portfolio*(1+real_return)-spend
            equity=equity*(1+real_return)

            # draw from cash first
            if cash>=spend:
                cash-=spend
            else:
                spend_left=spend-cash
                cash=0
                equity-=spend_left

            # refill cash ONLY after good returns
            target_cash=90000

            if real_return>0 and cash<target_cash:
                refill=min(target_cash-cash,equity)
                equity-=refill
                cash+=refill

            portfolio=cash+equity
            #

            balances[s,y]=portfolio

            if portfolio<=0:
                ruin[s,y]=1
                break

    final=balances[:,-1]

    return{
        "balances":balances,
        "withdrawals":withdrawals,
        "ruin":ruin,
        "success":np.mean(final>0)*100,
        "median":np.median(final)
    }

# ------------------------------------------------
# SPENDING OPTIMISER
# ------------------------------------------------
def optimise(i, target):

    low = 0.5
    high = 2
    best = 1

    for _ in range(25):

        mid = (low + high) / 2

        test = copy.deepcopy(i)

        test["go"] = i["go"] * mid
        test["slow"] = i["slow"] * mid
        test["no"] = i["no"] * mid

        r = simulate(test)

        success = r["success"]

        if success >= target:
            best = mid
            low = mid
        else:
            high = mid

    return best


# ------------------------------------------------
# CHARTS
# ------------------------------------------------

def percentile_chart(r,i):

    ages=np.arange(i["age"],i["life"]+1)

    p10,p50,p90=np.percentile(r["balances"],[10,50,90],axis=0)

    fig=go.Figure()

    fig.add_trace(go.Scatter(x=ages,y=p90,line=dict(width=0)))
    fig.add_trace(go.Scatter(x=ages,y=p10,fill="tonexty",name="10-90% range"))
    fig.add_trace(go.Scatter(x=ages,y=p50,name="Median"))

    st.plotly_chart(fig,use_container_width=True)

def failure_chart(r,i):

    ages=np.arange(i["age"],i["life"]+1)

    fail=[np.mean(r["ruin"][:,y])*100 for y in range(r["ruin"].shape[1])]

    fig=go.Figure()
    fig.add_trace(go.Scatter(x=ages,y=fail,name="Failure probability"))

    st.plotly_chart(fig,use_container_width=True)

def withdrawal_chart(r,i):

    ages=np.arange(i["age"],i["life"]+1)

    med=np.median(r["withdrawals"],axis=0)

    fig=go.Figure()
    fig.add_trace(go.Scatter(x=ages,y=med,name="Withdrawals"))

    st.plotly_chart(fig,use_container_width=True)

# ------------------------------------------------
# STREAMLIT UI
# ------------------------------------------------

st.markdown("<h3 style='font-size:24px'>Retirement Planner</h3>",unsafe_allow_html=True)

sb=st.sidebar

inputs={}

inputs["age"]=sb.slider("Current Age",40,75,int(excel["Current Age"]))
inputs["life"]=sb.slider("Life Expectancy",80,100,int(excel["Life Expectancy"]))

inputs["portfolio"]=sb.slider("Portfolio",100000,2000000,int(excel["Current Savings"]),step=10000)

inputs["go"]=sb.slider("Go-Go Spending",10000,80000,int(excel["Base Expenses Go-Go"]),step=1000)
inputs["slow"]=sb.slider("Slow-Go Spending",10000,70000,int(excel["Base Expenses Slow-Go"]),step=1000)
inputs["no"]=sb.slider("No-Go Spending",5000,60000,int(excel["Base Expenses No-Go"]),step=1000)

inputs["sp"]=sb.slider("State Pension",0,25000,int(excel["State Pension"]),step=500)
inputs["sp_age"]=sb.slider("State Pension Age",60,75,int(excel["State Pension Start Age"]))

inputs["return"]=excel["Expected Return"]
inputs["vol"]=excel["Return Volatility"]

inputs["infl_text"]=excel["Inflation Rates"]
inputs["infl_years"]=int(excel["Years per rate"])

inputs["gifts"]=excel["Gifts"]

inputs["sims"]=int(excel["Num Simulations"])

#inputs["go_end"]=68
#inputs["slow_end"]=80
inputs["go_end"]=inputs["age"]+11
inputs["slow_end"]=85

inputs["infl_vol"]=excel["Inflation Volatility"]

# ------------------------------------------------
# RUN SIMULATION
# ------------------------------------------------

base=simulate(inputs)

#scale=optimise(inputs,90) #scale=optimise(inputs,excel["Final Balance"])
target_success=sb.slider("Target Success %",70,99,90)
scale=optimise(inputs,target_success)

opt=copy.deepcopy(inputs)

opt["go"]*=scale
opt["slow"]*=scale
opt["no"]*=scale

comp=simulate(opt)

#charts
def cashflow_chart(r,i):

    ages=np.arange(i["age"],i["life"]+1)

    withdrawals=np.median(r["withdrawals"],axis=0)

    income=[]
    spending=[]

    for y in range(len(ages)):

        age=ages[y]

        if age<i["go_end"]:
            spend=i["go"]
        elif age<i["slow_end"]:
            spend=i["slow"]
        else:
            spend=i["no"]

        spending.append(spend)

        if age>=i["sp_age"]:
            income.append(i["sp"])
        else:
            income.append(0)

    fig=go.Figure()

    fig.add_bar(x=ages,y=spending,name="Spending Need")
    fig.add_bar(x=ages,y=income,name="Income")
    fig.add_bar(x=ages,y=withdrawals,name="Portfolio Withdrawal")

    st.plotly_chart(fig,use_container_width=True)
    
def assets_chart(r,i):

    ages=np.arange(i["age"],i["life"]+1)

    median=np.percentile(r["balances"],50,axis=0)

    fig=go.Figure()

    fig.add_trace(go.Scatter(
        x=ages,
        y=median,
        name="Total Assets"
    ))

    st.plotly_chart(fig,use_container_width=True)
    
def income_vs_needs_chart(r,i):

    ages=np.arange(i["age"],i["life"]+1)

    needs=[]
    income=[]

    for age in ages:

        if age<i["go_end"]:
            spend=i["go"]
        elif age<i["slow_end"]:
            spend=i["slow"]
        else:
            spend=i["no"]

        needs.append(spend)

        if age>=i["sp_age"]:
            income.append(i["sp"])
        else:
            income.append(0)

    fig=go.Figure()

    fig.add_trace(go.Bar(x=ages,y=needs,name="Spending Need"))
    fig.add_trace(go.Bar(x=ages,y=income,name="Income"))

    st.plotly_chart(fig,use_container_width=True)
    
def dual_view(r,i):

    ages=np.arange(i["age"],i["life"]+1)

    withdrawals=np.median(r["withdrawals"],axis=0)
    assets=np.percentile(r["balances"],50,axis=0)

    fig=go.Figure()

    fig.add_trace(go.Bar(
        x=ages,
        y=withdrawals,
        name="Withdrawals"
    ))

    fig.add_trace(go.Scatter(
        x=ages,
        y=assets,
        name="Assets",
        yaxis="y2"
    ))

    fig.update_layout(
        yaxis=dict(title="Cash Flow"),
        yaxis2=dict(title="Assets",overlaying="y",side="right")
    )

    st.plotly_chart(fig,use_container_width=True)

# ------------------------------------------------
# DISPLAY
# ------------------------------------------------

tab1,tab2=st.tabs(["Current Plan","Optimised Plan"])

with tab1:

    st.write(f"Success rate: {base['success']:.1f}%")
    st.write(f"Median final balance: £{int(base['median']):,}")

    percentile_chart(base,inputs)

    cashflow_chart(base,inputs)

    assets_chart(base,inputs)

    income_vs_needs_chart(base,inputs)

    dual_view(base,inputs)

with tab2:

    st.write(f"Spending adjustment: {(scale-1)*100:.1f}%")

    st.write(
        f"Go-Go £{int(opt['go']):,} "
        f"Slow-Go £{int(opt['slow']):,} "
        f"No-Go £{int(opt['no']):,}"
    )

    st.write(f"Success rate: {comp['success']:.1f}%")
    st.write(f"Median final balance: £{int(comp['median']):,}")

    percentile_chart(comp,opt)

    cashflow_chart(comp,opt)

    assets_chart(comp,opt)

    income_vs_needs_chart(comp,opt)

    dual_view(comp,opt)
    
#report button
if st.button("Generate Adviser Report"):

    file=create_pdf_report(base,comp,inputs)

    with open(file,"rb") as f:

        st.download_button(
            "Download PDF Report",
            f,
            file_name="retirement_plan.pdf"
        )
    
    
    
#reports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import matplotlib.pyplot as plt

def create_pdf_report(base,comp,inputs):

    file="retirement_plan_report.pdf"

    styles=getSampleStyleSheet()
    elements=[]

    elements.append(Paragraph("Retirement Plan Report",styles['Title']))
    elements.append(Spacer(1,20))

    elements.append(Paragraph(
        f"Current Age: {inputs['age']}<br/>"
        f"Life Expectancy: {inputs['life']}<br/>"
        f"Portfolio Value: £{inputs['portfolio']:,}",
        styles['Normal']
    ))

    elements.append(Spacer(1,20))

    elements.append(Paragraph(
        f"Success Rate: {base['success']:.1f}%<br/>"
        f"Median Final Balance: £{int(base['median']):,}",
        styles['Normal']
    ))

    elements.append(Spacer(1,20))

    # Create fan chart image
    ages=np.arange(inputs["age"],inputs["life"]+1)
    p10,p50,p90=np.percentile(base["balances"],[10,50,90],axis=0)

    plt.figure()
    plt.fill_between(ages,p10,p90,alpha=0.3)
    plt.plot(ages,p50)
    plt.title("Portfolio Projection")
    plt.xlabel("Age")
    plt.ylabel("Portfolio Value")

    chart_file="fan_chart.png"
    plt.savefig(chart_file)
    plt.close()

    elements.append(Image(chart_file,6*inch,3*inch))

    elements.append(Spacer(1,20))

    # Cashflow table
    withdrawals=np.median(base["withdrawals"],axis=0)

    data=[["Age","Withdrawal"]]

    for i,age in enumerate(ages):
        data.append([age,f"£{int(withdrawals[i]):,}"])

    table=Table(data)

    elements.append(table)

    doc=SimpleDocTemplate(file,pagesize=A4)
    doc.build(elements)

    return file
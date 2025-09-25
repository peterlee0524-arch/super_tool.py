import streamlit as st
import pandas as pd
from super_tool import TaxParams, SuperParams, MLSParams, ScenarioInput, run_scenario

st.title("Super Balance & Tax Simulator (AU)")

# --- Sidebar inputs ---
salary = st.sidebar.number_input("Annual Salary (AUD)", value=100000.0, step=1000.0)
negative_gearing = st.sidebar.number_input("Negative Gearing Deduction (AUD)", value=30000.0, step=1000.0)
salary_sacrifice = st.sidebar.number_input("Salary Sacrifice (AUD)", value=8400.0, step=1000.0)
start_balance = st.sidebar.number_input("Starting Super Balance (AUD)", value=100000.0, step=10000.0)
years = st.sidebar.slider("Projection Years", min_value=5, max_value=40, value=20, step=1)
annual_return = st.sidebar.number_input("Annual Return (e.g., 0.06 = 6%)", value=0.06, step=0.01, format="%.2f")
fees_rate = st.sidebar.number_input("Annual Fee Rate (e.g., 0.0075 = 0.75%)", value=0.0075, step=0.001, format="%.4f")

# --- Run scenario ---
tp = TaxParams()
sp = SuperParams(annual_return=annual_return, fees_rate=fees_rate)
mls = MLSParams(enabled=False, private_insured=True)

si = ScenarioInput(
    salary=salary,
    negative_gearing=negative_gearing,
    salary_sacrifice=salary_sacrifice,
    start_super_balance=start_balance,
    years=years,
    private_insured=True
)

res = run_scenario(si, tp, sp, mls)

# --- Caps Table ---
st.subheader("Caps")
cap_df = pd.DataFrame({
    "ITEM": ["SG", "TOTAL CAP", "USED", "MAX SALARY SACRIFICE", "OVER BY"],
    "AMOUNT": [
        f"{res.cap['sg']:,.2f}",
        f"{res.cap['total_cap']:,.2f}",
        f"{res.cap['used']:,.2f}",
        f"{res.cap['max_salary_sacrifice']:,.2f}",
        f"{res.cap['over_by']:,.2f}",
    ]
})
st.table(cap_df)

# --- Projection Table ---
st.subheader("Projection")
proj_df = pd.DataFrame(res.projection)

# Capitalize headers
proj_df.columns = [c.upper() for c in proj_df.columns]

# Round and format numbers with accounting style
for col in proj_df.columns:
    if col != "YEAR":
        proj_df[col] = proj_df[col].map(lambda x: f"{x:,.2f}")

st.dataframe(proj_df)

# --- Download CSV ---
csv = proj_df.to_csv(index=False).encode("utf-8")
st.download_button("Download Projection CSV", csv, "projection.csv", "text/csv")

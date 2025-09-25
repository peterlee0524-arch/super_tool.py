import streamlit as st
import pandas as pd
import super_tool as sim  # 调用你的 super_tool.py

st.set_page_config(page_title="Super Balance & Tax Simulator", layout="wide")

st.title("🇦🇺 Super Balance & Tax Simulator")

# --- Sidebar Inputs ---
st.sidebar.header("Inputs")
salary = st.sidebar.number_input("Annual salary (AUD)", 0, 5_000_000, 175000, step=1000)
neg = st.sidebar.number_input("Negative gearing deduction (AUD)", 0, 5_000_000, 60000, step=1000)
ss = st.sidebar.number_input("Salary sacrifice (annual, AUD)", 0, 30_000, 8400, step=100)
sg = st.sidebar.number_input("SG rate", 0.00, 0.20, 0.12, step=0.005, format="%.3f")
cap = st.sidebar.number_input("Concessional cap", 0, 100_000, 30000, step=1000)
carry = st.sidebar.number_input("Carry-forward available", 0, 1_000_000, 0, step=1000)
start_bal = st.sidebar.number_input("Start super balance", 0, 10_000_000, 200000, step=1000)
years = st.sidebar.slider("Projection years", 1, 40, 10)
annual_ret = st.sidebar.number_input("Annual gross return", 0.00, 0.20, 0.06, step=0.005, format="%.3f")
fees_rate = st.sidebar.number_input("Annual fee rate", 0.00, 0.05, 0.0075, step=0.0005, format="%.4f")
private_insured = st.sidebar.checkbox("Private hospital insurance", value=True)
mls_enabled = st.sidebar.checkbox("Enable MLS (simplified)", value=True)
mls_threshold = st.sidebar.number_input("MLS threshold", 0, 1_000_000, 90000, step=1000)
mls_rate = st.sidebar.number_input("MLS rate", 0.00, 0.03, 0.01, step=0.001, format="%.3f")

# --- Params ---
tp = sim.TaxParams()
sp = sim.SuperParams(
    cap_concessional=cap,
    sg_rate=sg,
    carry_forward_available=carry,
    earnings_tax_rate=0.15,
    fees_rate=fees_rate,
    annual_return=annual_ret
)
mls = sim.MLSParams(
    enabled=mls_enabled,
    threshold=mls_threshold,
    rate=mls_rate,
    private_insured=private_insured
)
si = sim.ScenarioInput(
    salary=salary,
    negative_gearing=neg,
    salary_sacrifice=ss,
    other_concessional=0.0,
    start_super_balance=start_bal,
    years=years,
    private_insured=private_insured
)

# --- Run calculation ---
res = sim.run_scenario(si, tp, sp, mls)

# --- Display results ---
col1, col2, col3 = st.columns(3)
col1.metric("Taxable income", f"AUD {res.taxable_income:,.0f}")
col2.metric("Take-home cash", f"AUD {res.take_home_cash:,.0f}")
col3.metric("Super net in (after 15%)", f"AUD {res.super_net_in:,.0f}")

st.subheader("Caps")
st.write(res.cap)

st.subheader("Projection")
df = pd.DataFrame(res.projection)
st.dataframe(df, use_container_width=True)

st.download_button("Download Projection CSV", df.to_csv(index=False), "projection.csv", "text/csv")

import streamlit as st
import pandas as pd
from super_tool import (
    TaxParams, SuperParams, MLSParams, ScenarioInput, run_scenario
)

st.set_page_config(page_title="Super Balance & Tax Simulator", layout="wide")
st.title("🇦🇺 Super Balance & Tax Simulator (AU)")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("Inputs")

# Income & deductions
salary = st.sidebar.number_input("Annual Salary (AUD)", min_value=0.0, value=100000.0, step=1000.0, format="%.2f")
negative_gearing = st.sidebar.number_input("Negative Gearing Deduction (AUD)", min_value=0.0, value=30000.0, step=1000.0, format="%.2f")
salary_sacrifice = st.sidebar.number_input("Salary Sacrifice (AUD, per year)", min_value=0.0, value=8400.0, step=500.0, format="%.2f")

# Super settings
sg_rate = st.sidebar.number_input("Employer SG Rate (e.g., 0.12 = 12%)", min_value=0.00, max_value=0.20, value=0.12, step=0.005, format="%.3f")
cap = st.sidebar.number_input("Concessional Cap (AUD)", min_value=0.0, value=30000.0, step=1000.0, format="%.2f")
carry_forward = st.sidebar.number_input("Carry-forward Available (AUD)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
start_balance = st.sidebar.number_input("Starting Super Balance (AUD)", min_value=0.0, value=100000.0, step=10000.0, format="%.2f")

years = st.sidebar.slider("Projection Years", min_value=5, max_value=40, value=20, step=1)
annual_return = st.sidebar.number_input("Annual Return (e.g., 0.06 = 6%)", min_value=0.00, max_value=0.20, value=0.06, step=0.005, format="%.3f")
fees_rate = st.sidebar.number_input("Annual Fee Rate (e.g., 0.0075 = 0.75%)", min_value=0.00, max_value=0.05, value=0.0075, step=0.0005, format="%.4f")

# Medicare Levy Surcharge (simplified)
st.sidebar.markdown("---")
private_insured = st.sidebar.checkbox("Private Hospital Insurance", value=True)
mls_enabled = st.sidebar.checkbox("Enable MLS (Simplified)", value=False)
mls_threshold = st.sidebar.number_input("MLS Threshold (AUD)", min_value=0.0, value=90000.0, step=5000.0, format="%.2f")
mls_rate = st.sidebar.number_input("MLS Rate (e.g., 0.01 = 1%)", min_value=0.00, max_value=0.03, value=0.01, step=0.001, format="%.3f")

# -----------------------------
# Build params & run
# -----------------------------
tp = TaxParams()
sp = SuperParams(
    cap_concessional=cap,
    sg_rate=sg_rate,
    carry_forward_available=carry_forward,
    earnings_tax_rate=0.15,
    fees_rate=fees_rate,
    annual_return=annual_return,
)
mls = MLSParams(
    enabled=mls_enabled,
    threshold=mls_threshold,
    rate=mls_rate,
    private_insured=private_insured,
)
si = ScenarioInput(
    salary=salary,
    negative_gearing=negative_gearing,
    salary_sacrifice=salary_sacrifice,
    other_concessional=0.0,
    start_super_balance=start_balance,
    years=years,
    private_insured=private_insured,
)

res = run_scenario(si, tp, sp, mls)

# -----------------------------
# Top KPIs
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("TAXABLE INCOME", f"AUD {res.taxable_income:,.2f}")
c2.metric("TAKE-HOME CASH", f"AUD {res.take_home_cash:,.2f}")
c3.metric("SUPER NET IN (AFTER 15%)", f"AUD {res.super_net_in:,.2f}")
c4.metric("DIVISION 293 TAX", f"AUD {res.division293:,.2f}")

# -----------------------------
# Caps table (pretty)
# -----------------------------
st.subheader("Caps")
cap_table = pd.DataFrame({
    "ITEM": ["SG", "TOTAL CAP", "USED", "MAX SALARY SACRIFICE", "OVER BY"],
    "AMOUNT": [
        res.cap["sg"],
        res.cap["total_cap"],
        res.cap["used"],
        res.cap["max_salary_sacrifice"],
        res.cap["over_by"],
    ],
    "DESCRIPTION": [
        "Employer contributions at SG rate",
        "Annual concessional cap incl. carry-forward",
        "SG + salary sacrifice + other concessional",
        "Remaining headroom for salary sacrifice",
        "Excess over cap (if any)",
    ],
})
# 格式化 AMOUNT 为会计数字样式（两位小数）
cap_table["AMOUNT"] = cap_table["AMOUNT"].map(lambda x: f"{x:,.2f}")
st.table(cap_table)

# -----------------------------
# Projection table & chart
# -----------------------------
st.subheader("Projection")

# 用于下载的原始数值 DataFrame
df_raw = pd.DataFrame(res.projection)

# 展示：表头大写 + 两位小数格式
df_show = df_raw.copy()
df_show.columns = [c.upper() for c in df_show.columns]
for col in df_show.columns:
    if col != "YEAR":
        df_show[col] = df_show[col].map(lambda x: f"{x:,.2f}")

st.dataframe(df_show, use_container_width=True)

# 简单余额走势图（使用原始数值）
st.line_chart(df_raw.set_index("year")["end_balance"], height=260)

# 下载按钮（导出未格式化数值，便于再计算）
csv_bytes = df_raw.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Projection CSV",
    data=csv_bytes,
    file_name="projection.csv",
    mime="text/csv",
)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Super Balance & Tax Simulator (Australia)
Author: You (FCPA) + ChatGPT
License: MIT

Features
- Income tax (2024–25 brackets) + Medicare Levy (2%)
- Optional Medicare Levy Surcharge (MLS) with user-set thresholds/rates
- Negative gearing deduction
- Concessional cap logic (cap=30k, SG default 12%), carry-forward
- Division 293 tax check
- Salary sacrifice optimiser helper
- Super accumulation projection (accumulation-phase tax model)
- CLI for quick scenarios; can be imported as a library
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
from typing import List, Dict
import csv

# -----------------------------
# Tax models (updateable params)
# -----------------------------

@dataclass
class TaxParams:
    # 2024–25 resident tax brackets (exclusive of Medicare/MLS)
    # Using ATO stage 3 settings.
    brackets: List[Dict[str, float]] = None
    medicare_levy_rate: float = 0.02

    def __post_init__(self):
        if self.brackets is None:
            # piecewise linear via thresholds:
            # 0–18,200: 0
            # 18,201–45,000: 19%
            # 45,001–135,000: 30%
            # 135,001–190,000: 37%
            # 190,001+: 45%
            self.brackets = [
                {"min": 0.0, "rate": 0.0,  "base": 0.0},
                {"min": 18200.0, "rate": 0.19, "base": 0.0},
                {"min": 45000.0, "rate": 0.30, "base": (45000.0-18200.0)*0.19},
                {"min": 135000.0, "rate": 0.37, "base": (45000.0-18200.0)*0.19 + (135000.0-45000.0)*0.30},
                {"min": 190000.0, "rate": 0.45, "base": (45000.0-18200.0)*0.19 + (135000.0-45000.0)*0.30 + (190000.0-135000.0)*0.37},
            ]

@dataclass
class MLSParams:
    enabled: bool = False
    # Simple one-threshold model (user can refine):
    threshold: float = 0.0
    rate: float = 0.0
    # If family thresholds are needed, extend here.
    private_insured: bool = True  # if True, MLS not applied


def income_tax_resident_2024_25(taxable_income: float, tax: TaxParams) -> float:
    """Income tax excluding Medicare/MLS."""
    if taxable_income <= 18200:
        return 0.0
    applicable = max([b for b in tax.brackets if taxable_income > b["min"]], key=lambda x: x["min"])
    return applicable["base"] + (taxable_income - applicable["min"]) * applicable["rate"]


def medicare_levy(taxable_income: float, tax: TaxParams) -> float:
    return max(0.0, taxable_income * tax.medicare_levy_rate)


def mls_surcharge(taxable_income: float, mls: MLSParams) -> float:
    if not mls.enabled or mls.private_insured:
        return 0.0
    if taxable_income <= mls.threshold:
        return 0.0
    return (taxable_income - mls.threshold) * mls.rate


# -----------------------------
# Super & caps
# -----------------------------

@dataclass
class SuperParams:
    cap_concessional: float = 30000.0
    sg_rate: float = 0.12  # 12%
    carry_forward_available: float = 0.0  # user-provided, requires TSB<500k
    division293_threshold: float = 250000.0
    # accumulation phase tax on earnings:
    earnings_tax_rate: float = 0.15
    cgt_discount_long_term: float = 1.0/3.0  # not explicitly modelled by asset split
    fees_rate: float = 0.0  # annual % fee on balance (user set)
    # Assumption for projection:
    annual_return: float = 0.06  # gross return in accumulation phase


def concessional_capacity(salary: float, salary_sacrifice: float, other_cc: float, sp: SuperParams):
    sg = salary * sp.sg_rate
    total_cap = sp.cap_concessional + sp.carry_forward_available
    used = sg + other_cc + salary_sacrifice
    remaining = max(0.0, total_cap - (sg + other_cc))
    max_sacrifice = max(0.0, total_cap - (sg + other_cc))
    over_by = max(0.0, used - total_cap)
    return {
        "sg": sg,
        "total_cap": total_cap,
        "used": used,
        "remaining_cap_excl_ss": remaining,
        "max_salary_sacrifice": max_sacrifice,
        "over_by": over_by
    }


def division_293_extra_tax(taxable_income: float, concessional_contributions: float, sp: SuperParams) -> float:
    income_for_div293 = taxable_income + concessional_contributions
    if income_for_div293 <= sp.division293_threshold:
        return 0.0
    excess = max(0.0, income_for_div293 - sp.division293_threshold)
    base = min(concessional_contributions, excess)
    return base * 0.15


@dataclass
class ScenarioInput:
    salary: float
    negative_gearing: float = 0.0
    salary_sacrifice: float = 0.0
    other_concessional: float = 0.0
    start_super_balance: float = 0.0
    years: int = 0  # projection horizon
    # toggles:
    private_insured: bool = True


@dataclass
class ScenarioResult:
    taxable_income: float
    income_tax: float
    medicare: float
    mls: float
    concessional_contributions: float
    division293: float
    super_net_in: float
    take_home_cash: float
    combined_net_effect: float
    cap: dict
    projection: list


def run_scenario(si: ScenarioInput, tp: TaxParams, sp: SuperParams, mls: MLSParams) -> ScenarioResult:
    # Taxable income
    taxable_income = max(0.0, si.salary - si.negative_gearing - si.salary_sacrifice)

    # CCs
    sg = si.salary * sp.sg_rate
    cc = sg + si.salary_sacrifice + si.other_concessional

    # Cap info
    cap_info = concessional_capacity(
        salary=si.salary,
        salary_sacrifice=si.salary_sacrifice,
        other_cc=si.other_concessional,
        sp=sp
    )

    # Taxes
    base_tax = income_tax_resident_2024_25(taxable_income, tp)
    medicare = medicare_levy(taxable_income, tp)
    mls_effective = MLSParams(
        enabled=mls.enabled,
        threshold=mls.threshold,
        rate=mls.rate,
        private_insured=si.private_insured
    )
    mls_tax = mls_surcharge(taxable_income, mls_effective)

    # Div 293
    div293 = division_293_extra_tax(taxable_income, cc, sp)

    # Super net inflow after 15% contrib tax (fund level)
    super_net_in = cc * (1.0 - 0.15)

    # Take-home cash (salary minus sacrifice minus taxes minus MLS minus Div293)
    take_home_cash = si.salary - si.salary_sacrifice - base_tax - medicare - mls_tax - div293

    combined_net_effect = take_home_cash + super_net_in

    # Projection (simple accumulation model)
    projection = []
    bal = si.start_super_balance
    annual_cc_net = super_net_in  # assume constant each year for now
    for yr in range(1, max(1, si.years) + 1):
        start_bal = bal
        # add net contributions
        bal += annual_cc_net
        # grow
        gross_earn = bal * sp.annual_return
        # earnings tax in accumulation
        earn_tax = gross_earn * sp.earnings_tax_rate
        # fees on balance
        fees = bal * sp.fees_rate
        # apply taxes & fees, then add net earnings
        bal += (gross_earn - earn_tax - fees)
        projection.append({
            "year": yr,
            "start_balance": float(start_bal),
            "net_cc_in": float(annual_cc_net),
            "gross_earnings": float(gross_earn),
            "earnings_tax": float(earn_tax),
            "fees": float(fees),
            "end_balance": float(bal),
        })

    return ScenarioResult(
        taxable_income=taxable_income,
        income_tax=base_tax,
        medicare=medicare,
        mls=mls_tax,
        concessional_contributions=cc,
        division293=div293,
        super_net_in=super_net_in,
        take_home_cash=take_home_cash,
        combined_net_effect=combined_net_effect,
        cap=cap_info,
        projection=projection
    )


def format_currency(x: float) -> str:
    return f"AUD {x:,.0f}"


def print_summary(res: ScenarioResult):
    print("=== SUMMARY ===")
    print(f"Taxable income:            {format_currency(res.taxable_income)}")
    print(f"Income tax:                {format_currency(res.income_tax)}")
    print(f"Medicare levy:             {format_currency(res.medicare)}")
    print(f"MLS:                       {format_currency(res.mls)}")
    print(f"Div 293 extra tax:         {format_currency(res.division293)}")
    print(f"Concessional contrib (CC): {format_currency(res.concessional_contributions)}")
    print(f"Super net in (after 15%):  {format_currency(res.super_net_in)}")
    print(f"Take-home cash:            {format_currency(res.take_home_cash)}")
    print(f"Combined net effect:       {format_currency(res.combined_net_effect)}")
    print("--- Caps ---")
    print(f"  SG (at {int(100*0.12)}%):                {format_currency(res.cap['sg'])}")
    print(f"  Total cap (incl CF):      {format_currency(res.cap['total_cap'])}")
    print(f"  Used (incl SS):           {format_currency(res.cap['used'])}")
    print(f"  Max SS available:         {format_currency(res.cap['max_salary_sacrifice'])}")
    if res.cap['over_by'] > 0:
        print(f"  WARNING: Over cap by      {format_currency(res.cap['over_by'])}")


def write_projection_csv(res: ScenarioResult, path: str):
    fieldnames = ["year","start_balance","net_cc_in","gross_earnings","earnings_tax","fees","end_balance"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in res.projection:
            w.writerow(row)


def main():
    p = argparse.ArgumentParser(description="Super Balance & Tax Simulator (AU)")
    # Income & deductions
    p.add_argument("--salary", type=float, required=True, help="Annual salary (AUD)")
    p.add_argument("--negative-gearing", type=float, default=0.0, help="Annual negative gearing deduction (AUD)")
    # Super
    p.add_argument("--sg-rate", type=float, default=0.12, help="Employer SG rate (default 0.12)")
    p.add_argument("--cap", type=float, default=30000.0, help="Concessional cap (default 30,000)")
    p.add_argument("--carry-forward", type=float, default=0.0, help="Carry-forward concessional cap available")
    p.add_argument("--salary-sacrifice", type=float, default=0.0, help="Annual salary sacrifice (AUD)")
    p.add_argument("--other-cc", type=float, default=0.0, help="Other concessional contributions (AUD)")
    # Tax toggles
    p.add_argument("--private-insured", action="store_true", help="Has private hospital cover (suppresses MLS)")
    p.add_argument("--mls-enabled", action="store_true", help="Enable MLS simple model")
    p.add_argument("--mls-threshold", type=float, default=0.0, help="MLS threshold (simple)")
    p.add_argument("--mls-rate", type=float, default=0.0, help="MLS rate (simple)")
    # Projection
    p.add_argument("--start-balance", type=float, default=0.0, help="Starting super balance")
    p.add_argument("--years", type=int, default=10, help="Projection years")
    p.add_argument("--return", dest="annual_return", type=float, default=0.06, help="Annual gross return (e.g., 0.06)")
    p.add_argument("--fees-rate", type=float, default=0.0, help="Annual fee rate on balance (e.g., 0.0075)")
    # Output
    p.add_argument("--csv", type=str, default="", help="Write projection to CSV path")

    args = p.parse_args()

    tp = TaxParams()
    sp = SuperParams(
        cap_concessional=args.cap,
        sg_rate=args.sg_rate,
        carry_forward_available=args.carry_forward,
        earnings_tax_rate=0.15,
        fees_rate=args.fees_rate,
        annual_return=args.annual_return
    )
    mls = MLSParams(
        enabled=args.mls_enabled,
        threshold=args.mls_threshold,
        rate=args.mls_rate,
        private_insured=args.private_insured
    )
    si = ScenarioInput(
        salary=args.salary,
        negative_gearing=args.negative_gearing,
        salary_sacrifice=args.salary_sacrifice,
        other_concessional=args.other_cc,
        start_super_balance=args.start_balance,
        years=args.years,
        private_insured=args.private_insured
    )

    res = run_scenario(si, tp, sp, mls)
    print_summary(res)

    if args.csv:
        write_projection_csv(res, args.csv)
        print(f"Projection CSV written to: {args.csv}")

if __name__ == "__main__":
    main()

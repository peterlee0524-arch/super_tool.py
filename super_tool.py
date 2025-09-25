#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Super Balance & Tax Simulator (Australia)
Author: You (FCPA) + ChatGPT
License: MIT
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict


# -----------------------------
# Tax models (updateable params)
# -----------------------------
@dataclass
class TaxParams:
    brackets: List[Dict[str, float]] = None
    medicare_levy_rate: float = 0.02

    def __post_init__(self):
        if self.brackets is None:
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
    threshold: float = 0.0
    rate: float = 0.0
    private_insured: bool = True


def income_tax_resident_2024_25(taxable_income: float, tax: TaxParams) -> float:
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
    sg_rate: float = 0.12
    carry_forward_available: float = 0.0
    division293_threshold: float = 250000.0
    earnings_tax_rate: float = 0.15
    fees_rate: float = 0.0
    annual_return: float = 0.06


def concessional_capacity(salary: float, salary_sacrifice: float, other_cc: float, sp: SuperParams):
    sg = salary * sp.sg_rate
    total_cap = sp.cap_concessional + sp.carry_forward_available
    used = sg + other_cc + salary_sacrifice
    max_sacrifice = max(0.0, total_cap - (sg + other_cc))
    over_by = max(0.0, used - total_cap)
    return {
        "sg": sg,
        "total_cap": total_cap,
        "used": used,
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
    years: int = 0
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
    taxable_income = max(0.0, si.salary - si.negative_gearing - si.salary_sacrifice)
    sg = si.salary * sp.sg_rate
    cc = sg + si.salary_sacrifice + si.other_concessional
    cap_info = concessional_capacity(si.salary, si.salary_sacrifice, si.other_concessional, sp)
    base_tax = income_tax_resident_2024_25(taxable_income, tp)
    medicare = medicare_levy(taxable_income, tp)
    mls_tax = mls_surcharge(taxable_income, mls)
    div293 = division_293_extra_tax(taxable_income, cc, sp)
    super_net_in = cc * (1.0 - 0.15)
    take_home_cash = si.salary - si.salary_sacrifice - base_tax - medicare - mls_tax - div293
    combined_net_effect = take_home_cash + super_net_in

    projection = []
    bal = si.start_super_balance
    annual_cc_net = super_net_in
    for yr in range(1, max(1, si.years) + 1):
        start_bal = bal
        bal += annual_cc_net
        gross_earn = bal * sp.annual_return
        earn_tax = gross_earn * sp.earnings_tax_rate
        fees = bal * sp.fees_rate
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

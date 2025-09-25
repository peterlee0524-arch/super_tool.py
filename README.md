# Super Balance & Tax Simulator (AU)

A command-line / library tool for modelling Australian superannuation (super) and personal tax scenarios.  

## Features
- Personal income tax (2024–25 tax rates) + Medicare Levy (2%)  
- Optional **Medicare Levy Surcharge (MLS)** (user-defined thresholds and rates; toggle for private health insurance)  
- **Negative gearing** deductions  
- **Concessional cap** logic (default 30,000), **SG default 12%**, carry-forward input  
- **Division 293** check and additional tax  
- **Salary sacrifice** allowance calculation and validation  
- **Super accumulation phase** investment tax (15%) and fee rate  
- Balance projection and CSV export  

## Installation & Usage
```bash
python super_tool.py --salary 175000 --negative-gearing 60000 \
  --salary-sacrifice 8400 --sg-rate 0.12 --cap 30000 --carry-forward 0 \
  --start-balance 200000 --years 10 --return 0.06 --fees-rate 0.0075 \
  --private-insured --mls-enabled --mls-threshold 90000 --mls-rate 0.01 \
  --csv projection.csv

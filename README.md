# Super Balance & Tax Simulator (AU)

An interactive Streamlit tool (with a reusable Python library) for modelling Australian superannuation (super) and personal tax scenarios.  

## Features
- Personal income tax (2024–25 tax rates) + Medicare Levy (2%)  
- Optional **Medicare Levy Surcharge (MLS)** (user-defined thresholds and rates; toggle for private health insurance)  
- **Negative gearing** deductions  
- **Concessional cap** logic (default 30,000), **SG default 12%**, carry-forward input  
- **Division 293** check and additional tax  
- **Salary sacrifice** allowance calculation and validation  
- **Super accumulation phase** investment tax (15%) and fee rate  
- Balance projection and CSV export  

## Installation
Clone the repo and install dependencies:
```bash
git clone https://github.com/yourname/super-simulator.git
cd super-simulator
pip install -r requirements.txt
## Usage
Run the Streamlit app:
```bash
streamlit run streamlit_app.py

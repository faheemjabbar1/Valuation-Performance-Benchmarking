# One‑Week Equity Valuation & Peer Comparison

This repository contains a **one‑week** project that automates data collection, computes valuation & performance metrics, compares a peer set, and exports a polished **Excel** report. It is designed to be portfolio‑ready and extensible.

## Scope & Constraints
- **Universe:** ~15–20 public companies in one sector (default: *Software & Cloud*).
- **Horizon:** Last 4 years (daily prices; annual/quarterly fundamentals when available).
- **Outputs:** One Excel workbook in `reports/` + Python scripts in `src/` (+ optional dashboard stub).
- **Tech:** Python (pandas, yfinance), Excel (via `pandas.ExcelWriter`).

## Quickstart
```bash
# (optional) create env and install deps
pip install -r requirements.txt

# run the pipeline
python src/main.py
```
The Excel file will be created at: `reports/peer_comparison.xlsx`.

## Default Peer Set (Software & Cloud)
Tickers are editable in `src/config.py`.
- MSFT, ORCL, SAP, ADBE, CRM, NOW, INTU, ADSK, ANSS, SNOW, DDOG, MDB, TEAM, SHOP, PANW, CRWD

## What’s Included
- Automated price fetching (Yahoo Finance via `yfinance`).
- Fundamentals placeholders for FMP/SEC with clear TODOs (so you can add an API key later).
- Metric engine for: **P/E, P/B, EV/Revenue, EV/EBITDA (if available), ROE, margins, YoY growth, 3‑yr CAGR**.
- Clean export to Excel with raw sheets, calculations, peer medians, rankings, and charts (stubbed).
- Optional **Streamlit** dashboard stub.

## Folder Structure
```
equity-valuation-week/
  ├─ data/                  # cached CSVs (prices, fundamentals)
  ├─ notebooks/             # (optional) analysis notebooks
  ├─ reports/               # Excel output
  ├─ src/
  │   ├─ config.py
  │   ├─ data_fetch.py
  │   ├─ cleaning.py
  │   ├─ metrics.py
  │   ├─ export_excel.py
  │   ├─ charts.py
  │   └─ main.py
  └─ requirements.txt
```

## How to Extend in Week‑2
- Replace placeholder fundamentals with real FMP/SEC pulls.
- Add EV (enterprise value) and net debt to compute **EV/EBIT** and **EV/EBITDA** robustly.
- Add scenario/sensitivity tabs in Excel (e.g., margin shocks, growth decel).
- Ship the Streamlit app for interactive filtering & charts.

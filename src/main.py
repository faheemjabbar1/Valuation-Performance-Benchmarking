# src/main.py
import os
from pathlib import Path
# --- Robust imports: package mode first, script mode fallback ---
try:
    from .config import TICKERS, REPORT_PATH
    from . import data_fetch, metrics as m, export_excel
except ImportError:
    import sys
    THIS_DIR = Path(__file__).resolve().parent          # .../project/src
    PROJECT_ROOT = THIS_DIR.parent                      # .../project
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from src.config import TICKERS, REPORT_PATH
    from src import data_fetch, metrics as m, export_excel

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH_ABS = BASE_DIR / REPORT_PATH

def run():
    os.chdir(BASE_DIR)

    print("Fetching prices & snapshot...")
    prices = data_fetch.load_or_fetch_prices(TICKERS)
    snapshot = data_fetch.load_or_fetch_snapshot(TICKERS)

    print("Fetching fundamentals (annual) from FMP...")
    fund_annual = data_fetch.load_or_fetch_fmp_fundamentals(TICKERS)

    print("Computing metrics...")
    peer_simple = m.compute_simple_valuation(snapshot)
    peer_final  = m.compute_final_peer_table(snapshot, fund_annual)

    print("Exporting to Excel (v2)...")
    REPORT_PATH_ABS.parent.mkdir(parents=True, exist_ok=True)
    export_excel.export_to_excel_v2(prices, snapshot, peer_simple, fund_annual, peer_final, str(REPORT_PATH_ABS))
    print(f"Done. Report saved to {REPORT_PATH_ABS}")

if __name__ == "__main__":
    run()

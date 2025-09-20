# src/data_fetch.py
import os
import time
from typing import List
import pandas as pd
import yfinance as yf

# ---- Robust config import: package first, script fallback ----
try:
    from .config import START_DATE, END_DATE, DATA_DIR, TICKERS, FMP_API_KEY
except ImportError:
    from config import START_DATE, END_DATE, DATA_DIR, TICKERS, FMP_API_KEY

# ------------------ Yahoo Finance fetchers ------------------

def fetch_prices_yf(tickers: List[str]) -> pd.DataFrame:
    """
    Fetch adjusted close prices from Yahoo Finance for a list of tickers.
    Returns a DataFrame indexed by date with one column per ticker.
    """
    df = yf.download(
        tickers,
        start=START_DATE,
        end=END_DATE,
        auto_adjust=True,
        progress=False,
    )
    # With auto_adjust=True, adjusted prices are in the "Close" column.
    # If multiple tickers, df is a column MultiIndex; select "Close" level.
    if isinstance(df.columns, pd.MultiIndex):
        df = df["Close"].copy()

    # If a single ticker was passed (string), yfinance returns a Series.
    if isinstance(df, pd.Series):
        df = df.to_frame(name=tickers if isinstance(tickers, str) else tickers[0])

    df = df.sort_index()
    return df

def fetch_info_yf(tickers: List[str]) -> pd.DataFrame:
    """
    Fetch snapshot-style fields using yfinance.Ticker().info (best-effort).
    Some fields may be missing/None for certain tickers—expected.
    """
    records = []
    for t in tickers:
        info_subset = {"symbol": t}
        try:
            tk = yf.Ticker(t)
            info = tk.info or {}
            for k in [
                "shortName","marketCap","enterpriseValue","trailingPE","forwardPE",
                "priceToBook","profitMargins","returnOnEquity","ebitdaMargins",
                "grossMargins","operatingMargins","beta","sector","industry","fullTimeEmployees"
            ]:
                info_subset[k] = info.get(k)
        except Exception:
            # Keep defaults/None if yfinance hiccups
            pass
        records.append(info_subset)
        time.sleep(0.15)
    return pd.DataFrame.from_records(records)

def _cache_csv(df: pd.DataFrame, name: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, name)
    df.to_csv(path, index=True)
    return path

def load_or_fetch_prices(tickers: List[str]) -> pd.DataFrame:
    """
    Load prices from cache if present; otherwise fetch and cache.
    """
    path = os.path.join(DATA_DIR, "prices.csv")
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True)
    df = fetch_prices_yf(tickers)
    _cache_csv(df, "prices.csv")
    return df

def load_or_fetch_snapshot(tickers: List[str]) -> pd.DataFrame:
    """
    Load snapshot from cache if present; otherwise fetch and cache.
    """
    path = os.path.join(DATA_DIR, "snapshot.csv")
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0)
    snap = fetch_info_yf(tickers)
    _cache_csv(snap, "snapshot.csv")
    return snap

# ------------------ FMP Annual Fundamentals (Day-2) ------------------

def _fetch_fmp_statement(ticker: str, statement_type: str, period: str) -> pd.DataFrame:
    """
    Fetch a financial statement from FMP API and return as DataFrame.
    statement_type: "income-statement", "balance-sheet-statement", or "cash-flow-statement"
    period: "annual" or "quarter"
    """
    import requests
    base_url = f"https://financialmodelingprep.com/api/v3/{statement_type}/{ticker}"
    params = {
        "apikey": FMP_API_KEY,
        "period": period
    }
    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "financials" in data:
            data = data["financials"]
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def _std_annual_fundamentals(ticker: str) -> pd.DataFrame:
    """
    Merge income + balance to produce a tidy annual fundamentals table
    with fields needed for EV multiples and basic growth/quality.
    """
    inc = _fetch_fmp_statement(ticker, "income-statement", "annual")
    bal = _fetch_fmp_statement(ticker, "balance-sheet-statement", "annual")
    # cfs = _fetch_fmp_statement(ticker, "cash-flow-statement", "annual")  # not strictly needed Day-2

    if inc.empty or bal.empty:
        return pd.DataFrame()

    cols_inc = [
        "date","calendarYear","revenue","netIncome","ebitda","operatingIncome",
        "incomeBeforeTax","incomeTaxExpense","weightedAverageShsOut","weightedAverageShsOutDil"
    ]
    inc = inc[[c for c in cols_inc if c in inc.columns]].copy()

    cols_bal = [
        "date","calendarYear","totalAssets","totalStockholdersEquity","cashAndCashEquivalents",
        "shortTermDebt","longTermDebt","totalDebt","totalCurrentAssets","totalCurrentLiabilities"
    ]
    bal = bal[[c for c in cols_bal if c in bal.columns]].copy()

    on_cols = [c for c in ["date","calendarYear"] if c in inc.columns and c in bal.columns]
    if not on_cols:
        return pd.DataFrame()

    df = pd.merge(inc, bal, on=on_cols, how="inner", suffixes=("","_bal"))
    df["ticker"] = ticker

    # Shares (prefer diluted)
    df["shares"] = df.get("weightedAverageShsOutDil", pd.Series(index=df.index)).fillna(df.get("weightedAverageShsOut"))

    # Total debt fallback
    if "totalDebt" not in df.columns or df["totalDebt"].isna().all():
        df["totalDebt"] = df.get("shortTermDebt", 0).fillna(0) + df.get("longTermDebt", 0).fillna(0)

    want = [
        "ticker","date","calendarYear","revenue","netIncome","ebitda","operatingIncome",
        "incomeBeforeTax","incomeTaxExpense","shares",
        "totalAssets","totalStockholdersEquity","cashAndCashEquivalents","totalDebt",
        "totalCurrentAssets","totalCurrentLiabilities",
    ]
    out = df[[c for c in want if c in df.columns]].copy()

    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out = out.sort_values("date", ascending=False)

    return out

# ------------------ FMP Fundamentals Loader ------------------

def load_or_fetch_fmp_fundamentals(tickers: List[str]) -> pd.DataFrame:
    """
    Load FMP fundamentals from cache if present; otherwise fetch and cache.
    """
    path = os.path.join(DATA_DIR, "fmp_fundamentals.csv")
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=["date"])
    frames = []
    for t in tickers:
        df = _std_annual_fundamentals(t)
        if not df.empty:
            frames.append(df)
        time.sleep(0.15)
    if frames:
        out = pd.concat(frames, ignore_index=True)
        _cache_csv(out, "fmp_fundamentals.csv")
        return out
    return pd.DataFrame()

# ------------------ Optional CLI self-test ------------------

if __name__ == "__main__":
    print("Testing price & snapshot fetch...")
    prices = load_or_fetch_prices(TICKERS)
    snap = load_or_fetch_snapshot(TICKERS)
    print("Prices shape:", prices.shape)
    print("Snapshot shape:", snap.shape)

    if FMP_API_KEY:
        print("Testing FMP fundamentals...")
        fund = load_or_fetch_fmp_fundamentals(TICKERS)
        print("Fundamentals rows:", fund.shape)

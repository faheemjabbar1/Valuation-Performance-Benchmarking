# src/metrics.py
import numpy as np
import pandas as pd

# ---------- Utilities ----------
def safe_div(a, b):
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    return np.where(pd.notna(b) & (b != 0), a / b, np.nan)

# ---------- SIMPLE METRICS (snapshot-only) ----------
def compute_simple_valuation(snapshot: pd.DataFrame) -> pd.DataFrame:
    """
    Build a peer table from snapshot fields:
      PE_TTM, PE_FWD, P_B, ROE, NetMargin, EBITDA_Margin, GrossMargin, OpMargin
    + per-metric ranks and a CompositeRank (lower is better).
    """
    if snapshot is None or snapshot.empty:
        return pd.DataFrame()

    df = snapshot.copy()

    # Make sure we have an identifier column
    if "symbol" not in df.columns and "ticker" in df.columns:
        df["symbol"] = df["ticker"]

    # Normalize column names
    df = df.rename(columns={
        "trailingPE": "PE_TTM",
        "forwardPE": "PE_FWD",
        "priceToBook": "P_B",
        "marketCap": "MarketCap",
        "enterpriseValue": "EV",
        "profitMargins": "NetMargin",
        "returnOnEquity": "ROE",
        "ebitdaMargins": "EBITDA_Margin",
        "grossMargins": "GrossMargin",
        "operatingMargins": "OpMargin",
    })

    # Create ranks (only when data exists)
    low_better  = ["PE_TTM", "PE_FWD", "P_B"]
    high_better = ["ROE", "NetMargin", "EBITDA_Margin", "GrossMargin", "OpMargin"]

    for c in low_better:
        if c in df and df[c].notna().any():
            df[c + "_rank"] = df[c].rank(ascending=True, method="min")
    for c in high_better:
        if c in df and df[c].notna().any():
            df[c + "_rank"] = df[c].rank(ascending=False, method="min")

    rank_cols = [c for c in df.columns if c.endswith("_rank")]
    if rank_cols:
        df["CompositeRank"] = df[rank_cols].mean(axis=1)
        df = df.sort_values("CompositeRank")

    return df

# ---------- ADVANCED METRICS (snapshot + annual fundamentals) ----------
def _latest_annual(fund: pd.DataFrame) -> pd.DataFrame:
    """Take the latest annual row per ticker."""
    if fund is None or fund.empty:
        return pd.DataFrame()
    fund = fund.copy()
    if "date" in fund.columns:
        fund["date"] = pd.to_datetime(fund["date"], errors="coerce")
        fund = fund.sort_values(["ticker", "date"], ascending=[True, False])
    latest = fund.groupby("ticker", as_index=False).first()
    return latest

def _growth_annual(fund: pd.DataFrame) -> pd.DataFrame:
    """
    Compute YoY and an up-to-3Y CAGR for revenue per ticker.
    Requires >= 2 rows for YoY and >= 4 rows for 3Y CAGR.
    """
    if fund is None or fund.empty:
        return pd.DataFrame(columns=["ticker", "Rev_YoY", "Rev_CAGR_3Y"])

    fund = fund.copy()
    if "date" in fund.columns:
        fund["date"] = pd.to_datetime(fund["date"], errors="coerce")
        fund = fund.sort_values(["ticker", "date"])

    out = []
    for t, g in fund.groupby("ticker"):
        g = g.dropna(subset=["revenue"])
        if g.empty:
            out.append({"ticker": t, "Rev_YoY": np.nan, "Rev_CAGR_3Y": np.nan})
            continue

        rev = g["revenue"].to_numpy()
        # YoY
        yoy = np.nan
        if len(rev) >= 2 and pd.notna(rev[-2]) and rev[-2] != 0:
            yoy = (rev[-1] - rev[-2]) / rev[-2]

        # 3Y CAGR (use last 4 observations if available; otherwise fall back)
        if len(rev) >= 4:
            years = 3  # approximate 3 intervals
            start = rev[-(years + 1)]
            end = rev[-1]
            cagr = (end / start) ** (1 / years) - 1 if start and start > 0 else np.nan
        else:
            cagr = np.nan

        out.append({"ticker": t, "Rev_YoY": yoy, "Rev_CAGR_3Y": cagr})

    return pd.DataFrame(out)

def compute_final_peer_table(snapshot: pd.DataFrame, fund_annual: pd.DataFrame) -> pd.DataFrame:
    """
    Merge snapshot + fundamentals to compute advanced metrics:
      EV, EV/EBITDA, EV/Revenue, ROE_fund, NetMargin_fund, Rev_YoY, Rev_CAGR_3Y
    Then rank and build CompositeRank_All across all available metrics.
    Works even if fund_annual is empty or columns are missing.
    """
    if snapshot is None or snapshot.empty:
        return pd.DataFrame()

    # Normalize snapshot and rename
    snap = snapshot.rename(columns={
        "trailingPE": "PE_TTM",
        "forwardPE": "PE_FWD",
        "priceToBook": "P_B",
        "marketCap": "MarketCap",
        "enterpriseValue": "EV_snap",
        "profitMargins": "NetMargin",
        "returnOnEquity": "ROE",
        "ebitdaMargins": "EBITDA_Margin",
        "grossMargins": "GrossMargin",
        "operatingMargins": "OpMargin",
        "symbol": "ticker",
    }).copy()

    # Ensure identifier
    if "ticker" not in snap.columns:
        # last resort: try to use 'symbol' if it exists, else make a row index id
        if "symbol" in snapshot.columns:
            snap["ticker"] = snapshot["symbol"]
        else:
            snap["ticker"] = snap.index.astype(str)

    df = snap.copy()

    # Merge latest annual & growth only if those frames exist and have 'ticker'
    latest = _latest_annual(fund_annual) if (fund_annual is not None and not fund_annual.empty) else pd.DataFrame()
    if latest is not None and not latest.empty and ("ticker" in latest.columns):
        df = pd.merge(df, latest, on="ticker", how="left", suffixes=("", "_ann"))

    growth = _growth_annual(fund_annual) if (fund_annual is not None and not fund_annual.empty) else pd.DataFrame()
    if growth is not None and not growth.empty and ("ticker" in growth.columns):
        df = pd.merge(df, growth, on="ticker", how="left")

    # Helper: always return a pandas Series aligned to df.index
    def _as_series(column_name: str) -> pd.Series:
        if column_name in df.columns:
            return pd.to_numeric(df[column_name], errors="coerce")
        else:
            return pd.Series(np.nan, index=df.index)

    # EV = MarketCap + totalDebt - cash; fallback to EV_snap if any part missing
    mcap   = _as_series("MarketCap")
    debt   = _as_series("totalDebt")
    cash   = _as_series("cashAndCashEquivalents")
    ev_fallback = _as_series("EV_snap")

    mask = mcap.notna() & debt.notna() & cash.notna()
    ev_calc = mcap + debt - cash
    df["EV"] = ev_calc.where(mask, ev_fallback)

    # Fund-based ROE and net margin
    if "netIncome" in df.columns and "totalStockholdersEquity" in df.columns:
        df["ROE_fund"] = safe_div(df["netIncome"], df["totalStockholdersEquity"])
    if "netIncome" in df.columns and "revenue" in df.columns:
        df["NetMargin_fund"] = safe_div(df["netIncome"], df["revenue"])

    # EV multiples
    if "ebitda" in df.columns:
        df["EV_EBITDA"] = safe_div(df["EV"], df["ebitda"])
    if "revenue" in df.columns:
        df["EV_Revenue"] = safe_div(df["EV"], df["revenue"])

    # Ranking (only rank on columns that exist & have numbers)
    low_better  = ["PE_TTM", "PE_FWD", "P_B", "EV_EBITDA", "EV_Revenue"]
    high_better = ["ROE", "ROE_fund", "NetMargin", "NetMargin_fund",
                   "EBITDA_Margin", "GrossMargin", "OpMargin", "Rev_YoY", "Rev_CAGR_3Y"]

    for c in low_better:
        if c in df and pd.to_numeric(df[c], errors="coerce").notna().any():
            df[c + "_rank"] = df[c].rank(ascending=True, method="min")
    for c in high_better:
        if c in df and pd.to_numeric(df[c], errors="coerce").notna().any():
            df[c + "_rank"] = df[c].rank(ascending=False, method="min")

    rank_cols = [c for c in df.columns if c.endswith("_rank")]
    if rank_cols:
        df["CompositeRank_All"] = df[rank_cols].mean(axis=1)
        df = df.sort_values("CompositeRank_All")

    return df

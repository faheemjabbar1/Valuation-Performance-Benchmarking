import pandas as pd
from pandas import ExcelWriter

def export_to_excel(prices: pd.DataFrame, snapshot: pd.DataFrame, metrics: pd.DataFrame, report_path: str):
    with ExcelWriter(report_path, engine="openpyxl") as xw:
        prices.to_excel(xw, sheet_name="Raw_Prices")
        snapshot.to_excel(xw, sheet_name="Raw_Snapshot")
        metrics.to_excel(xw, sheet_name="Peer_Metrics")
        # Summary sheet (top 5 by CompositeRank if available)
        summary = metrics.head(5) if "CompositeRank" in metrics else metrics
        summary.to_excel(xw, sheet_name="Summary")

def export_to_excel_v2(prices: pd.DataFrame,
                       snapshot: pd.DataFrame,
                       peer_simple: pd.DataFrame,
                       fundamentals_annual: pd.DataFrame,
                       peer_final: pd.DataFrame,
                       report_path: str):
    with ExcelWriter(report_path, engine="openpyxl") as xw:
        prices.to_excel(xw, sheet_name="Raw_Prices")
        snapshot.to_excel(xw, sheet_name="Raw_Snapshot")
        if fundamentals_annual is not None and not fundamentals_annual.empty:
            fundamentals_annual.to_excel(xw, sheet_name="Fundamentals_Annual", index=False)
        peer_simple.to_excel(xw, sheet_name="Peer_Metrics")
        if peer_final is not None and not peer_final.empty:
            peer_final.to_excel(xw, sheet_name="Peer_Final", index=False)

            # Summary: Top 5 by CompositeRank_All if present; else fallback to simple CompositeRank
            if "CompositeRank_All" in peer_final.columns:
                summary = peer_final[["ticker","CompositeRank_All"]].sort_values("CompositeRank_All").head(5)
            elif "CompositeRank" in peer_simple.columns:
                summary = peer_simple[["symbol","CompositeRank"]].head(5)
            else:
                summary = peer_simple.head(5)
            summary.to_excel(xw, sheet_name="Summary", index=False)
        else:
            # fallback summary from simple metrics
            summary = peer_simple.head(5) if "CompositeRank" in peer_simple.columns else peer_simple.head(5)
            summary.to_excel(xw, sheet_name="Summary", index=False)

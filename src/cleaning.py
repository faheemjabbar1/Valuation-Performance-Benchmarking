import pandas as pd

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna(how="all")

def resample_annual(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.resample("A").last()

def resample_quarterly(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.resample("Q").last()

def yoy_growth(series: pd.Series) -> pd.Series:
    return series.pct_change(periods=1)

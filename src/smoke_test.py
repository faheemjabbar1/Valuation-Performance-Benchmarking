import sys
sys.path.append(r"C:\Users\Faheem\Desktop\projects\test")

from src.config import TICKERS
from src import data_fetch

prices = data_fetch.load_or_fetch_prices(TICKERS)
snap   = data_fetch.load_or_fetch_snapshot(TICKERS)

print("Prices shape:", prices.shape)
print("Snapshot columns:", list(snap.columns)[:12], "...")
print(snap.head(3))

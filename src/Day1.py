import pandas as pd

prices = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
snap   = pd.read_csv("data/snapshot.csv", index_col=0)

print("✅ Prices shape:", prices.shape)
print(prices.head(3), "\n")

key_cols = ["symbol","marketCap","trailingPE","priceToBook","profitMargins","returnOnEquity"]
existing = [c for c in key_cols if c in snap.columns]
print("✅ Snapshot shape:", snap.shape)
print("Nulls (selected):")
print(snap[existing].isna().sum().sort_values(ascending=False), "\n")

peer = pd.read_excel("reports/peer_comparison.xlsx", sheet_name="Peer_Metrics")
print("Top 5 by CompositeRank:")
print(peer[["symbol","CompositeRank"]].head(5), "\n")

print("Bottom 5 by CompositeRank:")
print(peer[["symbol","CompositeRank"]].tail(5))

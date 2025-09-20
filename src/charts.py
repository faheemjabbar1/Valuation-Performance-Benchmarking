import io
import pandas as pd
import matplotlib.pyplot as plt

def plot_price_trends(prices: pd.DataFrame, tickers: list, outfile: str = None):
    plt.figure(figsize=(10,6))
    prices[tickers].plot(ax=plt.gca())
    plt.title("Price (Adj Close) – 4 Years")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.tight_layout()
    if outfile:
        plt.savefig(outfile, dpi=150)
    return outfile

def plot_scatter(df: pd.DataFrame, x: str, y: str, label_col: str = "symbol", outfile: str = None):
    plt.figure(figsize=(7,6))
    plt.scatter(df[x], df[y])
    for _, row in df.iterrows():
        plt.text(row[x], row[y], str(row[label_col])[:8], fontsize=8)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.title(f"{y} vs {x}")
    plt.tight_layout()
    if outfile:
        plt.savefig(outfile, dpi=150)
    return outfile

import os
import argparse
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import ticker
from pymongo import MongoClient
import pandas as pd

# Config
MONGO_URL = "mongodb://192.168.1.58:27018/"
DB_NAME = "bsc_pools"
OUTPUT_DIR = "charts"
COLORS = ["blue", "orange", "green", "red", "purple"]


parser = argparse.ArgumentParser()
parser.add_argument("--pair", required=True, nargs='+', help="Token pair(s)")
parser.add_argument(
    "--chart", choices=["block", "timestamp", "both"], default="both")
args = parser.parse_args()
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = MongoClient(MONGO_URL)
price_col = client[DB_NAME]["token_prices"]


def fetch_data(pair, key):
    cursor = price_col.find({"pair_name": pair}).sort(key, 1)
    return [(doc[key], doc["price_token1_in_token0"]) for doc in cursor]


def plot_line_chart(xlabel, title, key):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    axes = [ax1]

    for i, pair in enumerate(args.pair):
        data = fetch_data(pair, key)
        if not data:
            continue
        x, y = zip(*data)
        color = COLORS[i % len(COLORS)]
        ax = ax1 if i == 0 else ax1.twinx()
        if i > 0:
            ax.spines["right"].set_position(("outward", 60 * (i - 1)))
        ax.plot(x, y, color=color, label=pair)
        ax.set_ylabel(f"Price ({pair})", color=color)
        ax.tick_params(axis="y", labelcolor=color)
        axes.append(ax)

    ax1.set_xlabel(xlabel)
    ax1.set_title(title)
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
    if key == "timestamp":
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=30)
    else:
        ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))
        plt.xticks(rotation=45, ha='right')

    plt.grid(True, axis="x")
    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, f"{'_'.join(args.pair)}_{key}.png")
    plt.savefig(path)
    print(f"{key.title()} chart saved to {path}")
    plt.close()


def write_summary(p1, p2, df):
    summary = f"""Price Analysis Report for {p1} and {p2}
=============================================
Block Range: {df['block_number'].min()} to {df['block_number'].max()} ({df['block_number'].nunique()} blocks)
Time Range: {df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S')} to {df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')}

{p1} Price: 
- Min={df['price1'].min():.8f} 
- Max={df['price1'].max():.8f} 
- Avg={df['price1'].mean():.8f} 
- Std={df['price1'].std():.8f}

{p2} Price: 
- Min={df['price2'].min():.8f} 
- Max={df['price2'].max():.8f} 
- Avg={df['price2'].mean():.8f} 
- Std={df['price2'].std():.8f}

Deviation (%): 
- Min={df['deviation_pct'].min():.4f} 
- Max={df['deviation_pct'].max():.4f} 
- Avg={df['deviation_pct'].mean():.4f} 
- Std={df['deviation_pct'].std():.4f}
"""
    path = os.path.join(
        OUTPUT_DIR, f"{p1}_{p2}_price_analysis.txt".replace("/", "_"))
    with open(path, "w") as f:
        f.write(summary)
    print(f"Summary file saved to {path}")


def build_deviation_df(p1, p2):
    docs1 = list(price_col.find({"pair_name": p1}))
    docs2 = list(price_col.find({"pair_name": p2}))

    if not docs1 or not docs2:
        print("⚠️ No data for one of the pairs.")
        return None

    df1 = pd.DataFrame([(d["block_number"], d["timestamp"], d["price_token1_in_token0"])
                        for d in docs1], columns=["block_number", "timestamp", "price1"])
    df2 = pd.DataFrame([(d["block_number"], d["timestamp"], d["price_token1_in_token0"])
                        for d in docs2], columns=["block_number", "timestamp", "price2"])

    df = pd.merge(df1, df2, on=["block_number", "timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["deviation_pct"] = 100 * \
        abs(df["price1"] - df["price2"]) / ((df["price1"] + df["price2"]) / 2)
    return df


def plot_deviation(df: pd.DataFrame, key: str):
    plt.figure(figsize=(12, 6))
    plt.plot(df[key], df["deviation_pct"],
             label="Deviation (%)", color="green")
    plt.xlabel(key.replace("_", " ").title())
    plt.ylabel("Deviation (%)")
    plt.title(f"Price Deviation by {key.title()}")
    if key == "timestamp":
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=30, ha="right")
    plt.grid(True)
    plt.tight_layout()
    fname = f"{args.pair[0]}_{args.pair[1]}_deviation_by_{key}.png".replace(
        "/", "_")
    plt.savefig(os.path.join(OUTPUT_DIR, fname))
    print(f"📈 Deviation chart saved to {fname}")
    plt.close()


def main():
    if args.chart in ["block", "both"]:
        plot_line_chart("Block Number", "Price by Block", "block_number")
    if args.chart in ["timestamp", "both"]:
        plot_line_chart("Timestamp", "Price by Timestamp", "timestamp")

    df = build_deviation_df(*args.pair)
    if df is not None:
        plot_deviation(df, key="block_number")
        plot_deviation(df, key="timestamp")
        write_summary(args.pair[0], args.pair[1], df)


if __name__ == "__main__":
    main()

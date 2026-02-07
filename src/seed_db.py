import os

import duckdb
import yfinance as yf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "investments.duckdb")


def seed_database():
    db_name = "investments.duckdb"

    print("Fetching historical S&P 500 data from Yahoo Finance...")
    ticker = "^GSPC"

    df = yf.download(ticker, period="max")

    df = df[["Close"]].reset_index()
    df.columns = ["date", "price"]

    df = df.dropna()
    df["date"] = df["date"].dt.date

    print(f"Connecting to {db_name} and inserting {len(df)} rows...")
    con = duckdb.connect(DB_PATH)

    con.execute("CREATE OR REPLACE TABLE snp500 AS SELECT * FROM df")

    count = con.execute("SELECT COUNT(*) FROM snp500").fetchone()
    print(f"Success! Database seeded with {count} records.")
    con.close()


if __name__ == "__main__":
    seed_database()

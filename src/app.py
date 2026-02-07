import os

import duckdb
import plotly.express as px
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "investments.duckdb")


st.set_page_config(page_title="S&P 500 Investment Simulator", layout="wide")


def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


# --- SIDEBAR INPUTS ---
st.sidebar.header("Investment Parameters")
start_year = st.sidebar.number_input(
    "Start Year", min_value=1900, max_value=2024, value=2000
)
init_amount = st.sidebar.number_input("Starting Amount ($)", value=10000)
monthly_contrib = st.sidebar.number_input("Monthly Contribution ($)", value=500)
years_to_invest = st.sidebar.slider("Years of Investment", 1, 50, 20)

st.title("📈 S&P 500 Historical Simulator")
st.markdown(
    f"Simulating a **{years_to_invest} year** investment starting in **{start_year}**."
)


def run_simulation():
    conn = get_connection()

    query = f"""
    WITH RECURSIVE first_dates AS (
        SELECT 
            date, 
            price,
            ROW_NUMBER() OVER(PARTITION BY date_trunc('month', date) ORDER BY date ASC) as day_idx
        FROM snp500
        WHERE date >= '{start_year}-01-01'
    ),
    monthly_data AS (
        SELECT
            date,
            price,
            price / LAG(price) OVER(ORDER BY date) as monthly_return
        FROM first_dates
        WHERE day_idx = 1
        LIMIT {years_to_invest * 12} 
    ),
    simulation AS (
        SELECT * FROM (
        SELECT
            date,
            {init_amount}::DOUBLE AS capital,
            0 as month_idx
        FROM monthly_data
        WHERE monthly_return IS NULL
        LIMIT 1)

        UNION ALL

        SELECT * FROM (
        SELECT 
            m.date,
            (s.capital * m.monthly_return) + {monthly_contrib} AS capital,
            s.month_idx + 1
        FROM simulation s
        JOIN monthly_data m ON m.date > s.date
        -- This subquery ensures we only grab the next sequential month from our data
        WHERE m.date = (SELECT MIN(date) FROM monthly_data WHERE date > s.date))
    )
    SELECT * FROM simulation;
    """
    return conn.execute(query).df()


try:
    df_sim = run_simulation()

    final_val = df_sim["capital"].iloc[-1]
    total_invested = init_amount + (monthly_contrib * len(df_sim))
    profit = final_val - total_invested

    col1, col2, col3 = st.columns(3)
    col1.metric("Final Capital", f"${final_val:,.2f}")
    col2.metric("Total Invested", f"${total_invested:,.2f}")
    col3.metric(
        "Net Profit", f"${profit:,.2f}", delta=f"{(profit/total_invested)*100:.1f}%"
    )

    fig = px.line(
        df_sim,
        x="date",
        y="capital",
        title="Capital Growth Over Time",
        labels={"capital": "Portfolio Value ($)", "date": "Year"},
    )
    st.plotly_chart(fig, width="stretch")

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Check if the table is named 'snp500' and columns are 'date' and 'close'.")

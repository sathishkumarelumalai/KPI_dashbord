"""Shared KPI definitions used by both the Streamlit app and the PDF export."""
import pandas as pd

def kpis(d: pd.DataFrame) -> dict:
    rev, orders = d.revenue.sum(), d.orders.sum()
    newc, spend = d.new_customers.sum(), d.marketing_spend.sum()
    return {"Revenue": rev,
            "CAC": spend / newc if newc else 0.0,                       # marketing spend / new customers
            "Churn": d.churned_customers.sum() / d.active_customers.sum() if d.active_customers.sum() else 0.0,
            "AOV": rev / orders if orders else 0.0}                      # revenue / orders

def delta(cur: dict, prev: dict) -> dict:
    return {k: (cur[k] - prev[k]) / prev[k] if prev.get(k) else None for k in cur}

def grain_col(d: pd.DataFrame, grain: str) -> pd.Series:
    if grain == "Year": return d.month.dt.year.astype(str)
    if grain == "Quarter": return d.month.dt.to_period("Q").astype(str)
    return d.month.dt.to_period("M").dt.to_timestamp()

def trend(d: pd.DataFrame, grain: str) -> pd.DataFrame:
    g = d.assign(period=grain_col(d, grain)).groupby("period").agg(
        revenue=("revenue", "sum"), orders=("orders", "sum"), new=("new_customers", "sum"),
        spend=("marketing_spend", "sum"), active=("active_customers", "sum"),
        churned=("churned_customers", "sum")).reset_index()
    g["AOV"], g["CAC"], g["Churn"] = g.revenue / g.orders, g.spend / g.new, g.churned / g.active
    return g

def money(x): return f"${x/1e6:,.2f}M" if x >= 1e6 else f"${x:,.0f}"

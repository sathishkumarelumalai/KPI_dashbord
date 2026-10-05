"""Generates a reproducible synthetic e-commerce dataset (monthly x country x category x channel)."""
import numpy as np, pandas as pd

COUNTRIES = {"USA": "United States", "GBR": "United Kingdom", "DEU": "Germany", "FRA": "France",
             "IND": "India", "BRA": "Brazil", "CAN": "Canada", "AUS": "Australia",
             "JPN": "Japan", "ZAF": "South Africa", "MEX": "Mexico", "ARE": "UAE"}
SIZE = {"USA": 1.0, "GBR": .55, "DEU": .5, "FRA": .4, "IND": .7, "BRA": .35,
        "CAN": .3, "AUS": .28, "JPN": .45, "ZAF": .12, "MEX": .2, "ARE": .1}
CATS = {"Electronics": ["Phones", "Laptops", "Audio"], "Fashion": ["Apparel", "Footwear", "Accessories"],
        "Home & Living": ["Furniture", "Kitchen", "Decor"], "Beauty": ["Skincare", "Makeup", "Fragrance"]}
AOV = {"Electronics": 240, "Fashion": 70, "Home & Living": 130, "Beauty": 45}
CHANNELS = {"Organic Search": 8, "Paid Search": 42, "Social Ads": 36, "Email": 12, "Referral": 18}

def generate(seed=42):
    rng = np.random.default_rng(seed)
    months = pd.date_range("2024-01-01", "2026-09-01", freq="MS")
    rows = []
    for i, m in enumerate(months):
        season = 1 + .25 * np.sin((m.month - 3) / 12 * 2 * np.pi) + (.35 if m.month in (11, 12) else 0)
        growth = 1 + .025 * i
        for c, cn in COUNTRIES.items():
            for cat, subs in CATS.items():
                for sub in subs:
                    for ch, cac in CHANNELS.items():
                        base = 14 * SIZE[c] * growth * season * rng.uniform(.8, 1.2)
                        base *= {"Organic Search": 1.4, "Paid Search": 1.2, "Social Ads": 1.0, "Email": .7, "Referral": .5}[ch]
                        orders = max(int(rng.poisson(base)), 0)
                        aov = AOV[cat] * rng.uniform(.88, 1.12) * (1 + .004 * i)
                        revenue = orders * aov
                        new_c = int(orders * rng.uniform(.30, .45))
                        spend = new_c * cac * rng.uniform(.85, 1.2) * (1 + .003 * i)
                        active = int(orders * rng.uniform(3.2, 4.2))
                        churn = int(active * rng.uniform(.035, .065) * (1.15 - .004 * i))
                        rows.append((m, cn, c, cat, sub, ch, orders, round(revenue, 2), new_c,
                                     round(spend, 2), active, churn))
    return pd.DataFrame(rows, columns=["month", "country", "iso3", "category", "subcategory", "channel",
                                       "orders", "revenue", "new_customers", "marketing_spend",
                                       "active_customers", "churned_customers"])

if __name__ == "__main__":
    df = generate(); df.to_csv("data/sales_data.csv", index=False); print(df.shape)

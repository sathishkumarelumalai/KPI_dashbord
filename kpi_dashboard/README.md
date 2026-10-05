# Interactive Dashboard & KPI Visualizations (Streamlit + Plotly)

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Optional: `python data_gen.py` regenerates `data/sales_data.csv`; `python export_pdf.py` regenerates `exports/Dashboard_Export.pdf`.

## Executive KPIs
| KPI | Definition |
|---|---|
| Revenue | Sum of order revenue |
| Customer Acquisition Cost | Marketing spend / new customers |
| Churn Rate | Churned customers / active customers |
| Average Order Value | Revenue / orders |

Each KPI card shows the % change vs. the previous period of equal length (CAC and churn use inverse colouring: lower is better).

## Features
- **Dashboard cards** (top row) -> **trend area charts** (revenue + switchable CAC/Churn/AOV) -> **geographic heatmap** (choropleth, colour by Revenue/AOV/CAC/Churn) -> **categorical drill-down** -> channel scorecard (visual hierarchy: summary first, detail last).
- **Slicers** (sidebar): date range, country, category, channel.
- **Drill-down**: temporal Year -> Quarter -> Month toggle; categorical Category -> Sub-category (or channel) selector.
- Data: synthetic, reproducible (seeded) e-commerce data, Jan 2024 - Sep 2026 (`data/sales_data.csv`).

## Deploy (for a shareable link)
Push this folder to GitHub, then deploy free on https://share.streamlit.io (main file: `app.py`).

## Files
`app.py` dashboard · `kpis.py` KPI logic · `data_gen.py` data · `export_pdf.py` PDF export · `exports/Dashboard_Export.pdf` · `data/sales_data.csv`

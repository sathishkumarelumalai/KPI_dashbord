"""Exports a static PDF snapshot of the dashboard (all filters = full dataset). Run: python export_pdf.py"""
import pandas as pd, plotly.express as px, plotly.graph_objects as go
from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from data_gen import generate
from kpis import kpis, delta, trend, money

OUT = Path("exports"); OUT.mkdir(exist_ok=True)
df = pd.read_csv("data/sales_data.csv", parse_dates=["month"]) if Path("data/sales_data.csv").exists() else generate()
P, A = "#1F4E79", "#E07A1F"
cur_df = df[df.month >= "2025-10-01"]; prev_df = df[(df.month >= "2024-10-01") & (df.month < "2025-10-01")]
cur = kpis(cur_df); dl = delta(cur, kpis(prev_df))   # last 12 months vs prior 12 months
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#C9D1DC"})
def save(fig, name): fig.tight_layout(); fig.savefig(OUT / name, dpi=200); plt.close(fig)
usd = FuncFormatter(lambda v, _: f"${v/1e6:.1f}M" if abs(v) >= 1e6 else f"${v:,.0f}")

t = trend(df, "Month"); fig, ax = plt.subplots(figsize=(15, 4.6))
ax.fill_between(t.period, t.revenue, color=P, alpha=.18); ax.plot(t.period, t.revenue, color=P, lw=2.5)
ax.yaxis.set_major_formatter(usd); ax.grid(axis="y", color="#EEF1F6"); save(fig, "_trend.png")
q = trend(df, "Quarter")
fig, ax = plt.subplots(figsize=(7.2, 4.6)); ax.bar(q.period, q.CAC, color=A)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:.0f}")); ax.tick_params(axis="x", rotation=45); ax.grid(axis="y", color="#EEF1F6"); save(fig, "_cac.png")
fig, ax = plt.subplots(figsize=(7.2, 4.6)); ax.fill_between(q.period, q.Churn, color="#B3261E", alpha=.15); ax.plot(q.period, q.Churn, color="#B3261E", lw=2.5)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=1)); ax.tick_params(axis="x", rotation=45); ax.grid(axis="y", color="#EEF1F6"); save(fig, "_churn.png")
# Geographic heat map: country-centroid bubble map (no external map files needed -> works offline)
LL = {"USA": (-98, 39), "GBR": (-2, 54), "DEU": (10, 51), "FRA": (2, 47), "IND": (79, 22), "BRA": (-52, -10),
      "CAN": (-100, 58), "AUS": (134, -25), "JPN": (138, 36), "ZAF": (25, -29), "MEX": (-102, 23), "ARE": (54, 24)}
geo = pd.DataFrame([{"iso3": i, "country": n, "Revenue": g.revenue.sum()} for (i, n), g in df.groupby(["iso3", "country"])])
fig, ax = plt.subplots(figsize=(11, 5.2)); ax.set_facecolor("#F4F7FB")
sc = ax.scatter([LL[i][0] for i in geo.iso3], [LL[i][1] for i in geo.iso3], s=geo.Revenue / geo.Revenue.max() * 2600 + 80,
                c=geo.Revenue, cmap="Blues", edgecolor=P, alpha=.9, vmin=-1)
for _, r in geo.iterrows(): ax.annotate(r.iso3, LL[r.iso3], ha="center", va="center", fontsize=8, color="#1B2437", weight="bold")
ax.set_xlim(-130, 160); ax.set_ylim(-45, 70); ax.set_xticks([]); ax.set_yticks([]); ax.grid(color="white", lw=1.2)
cb = fig.colorbar(sc, ax=ax, shrink=.8); cb.ax.yaxis.set_major_formatter(usd); save(fig, "_geo.png")
cat = df.groupby("category").revenue.sum().sort_values()
fig, ax = plt.subplots(figsize=(7, 5.2)); ax.barh(cat.index, cat.values, color=P); ax.xaxis.set_major_formatter(usd); ax.grid(axis="x", color="#EEF1F6"); save(fig, "_cat.png")
ch = df.groupby("channel").apply(lambda g: pd.Series(kpis(g))).reset_index().sort_values("Revenue", ascending=False)

# ---------------- Page 1: executive overview ----------------
pw, ph = landscape(A4); c = canvas.Canvas(str(OUT / "Dashboard_Export.pdf"), pagesize=(pw, ph))
c.setTitle("Executive KPI Dashboard"); c.setAuthor("KPI Dashboard Project")
def header(title, sub):
    c.setFillColor(colors.HexColor(P)); c.rect(0, ph - 22*mm, pw, 22*mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 20); c.drawString(14*mm, ph - 13*mm, title)
    c.setFont("Helvetica", 10); c.drawString(14*mm, ph - 18.5*mm, sub)
def footer(n):
    c.setFillColor(colors.HexColor("#8A94A6")); c.setFont("Helvetica", 8)
    c.drawString(14*mm, 7*mm, "Source: synthetic e-commerce dataset (Jan 2024 - Sep 2026). KPIs: Revenue, CAC = spend/new customers, Churn = churned/active, AOV = revenue/orders.")
    c.drawRightString(pw - 14*mm, 7*mm, f"Page {n}")
header("Executive KPI Dashboard", "Last 12 months (Oct 2025 - Sep 2026) vs. prior 12 months | all countries, categories & channels")
cards = [("REVENUE", money(cur["Revenue"]), dl["Revenue"], True), ("CUSTOMER ACQUISITION COST", f"${cur['CAC']:.2f}", dl["CAC"], False),
         ("CHURN RATE", f"{cur['Churn']*100:.2f}%", dl["Churn"], False), ("AVERAGE ORDER VALUE", f"${cur['AOV']:.2f}", dl["AOV"], True)]
cw, gap, x0, y0, chh = (pw - 28*mm - 3*8*mm) / 4, 8*mm, 14*mm, ph - 22*mm - 12*mm - 28*mm, 28*mm
for i, (lab, val, dd, up_good) in enumerate(cards):
    x = x0 + i * (cw + gap)
    c.setFillColor(colors.white); c.setStrokeColor(colors.HexColor("#E3E8EF")); c.roundRect(x, y0, cw, chh, 3*mm, fill=1, stroke=1)
    c.setFillColor(colors.HexColor(P)); c.rect(x, y0, 1.6*mm, chh, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#5B6577")); c.setFont("Helvetica-Bold", 8); c.drawString(x + 6*mm, y0 + chh - 7*mm, lab)
    c.setFillColor(colors.HexColor(P)); c.setFont("Helvetica-Bold", 24); c.drawString(x + 6*mm, y0 + 12*mm, val)
    good = (dd >= 0) == up_good
    c.setFillColor(colors.HexColor("#1E8E3E" if good else "#B3261E")); c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 6*mm, y0 + 3*mm, f"{'+' if dd >= 0 else ''}{dd*100:.1f}% YoY")
c.setFillColor(colors.HexColor("#1B2437")); c.setFont("Helvetica-Bold", 12); c.drawString(14*mm, y0 - 8*mm, "Monthly revenue trend")
iw = pw - 28*mm; th = y0 - 12*mm - 14*mm
c.drawImage(str(OUT / "_trend.png"), 14*mm, 14*mm, iw, th, preserveAspectRatio=True, anchor="c")
footer(1); c.showPage()

# ---------------- Page 2: drivers ----------------
header("Drivers & Geography", "Acquisition efficiency, retention, geographic distribution and category mix")
hw = (pw - 28*mm - 8*mm) / 2; top = ph - 22*mm - 8*mm
def block(title, img, x, y, w, h):
    c.setFillColor(colors.HexColor("#1B2437")); c.setFont("Helvetica-Bold", 11); c.drawString(x, y, title)
    c.drawImage(str(OUT / img), x, y - 3*mm - h, w, h, preserveAspectRatio=True, anchor="nw")
block("Quarterly CAC", "_cac.png", 14*mm, top - 4*mm, hw, 62*mm)
block("Quarterly churn rate", "_churn.png", 14*mm + hw + 8*mm, top - 4*mm, hw, 62*mm)
block("Revenue by country (heatmap)", "_geo.png", 14*mm, top - 76*mm, hw, 62*mm)
block("Revenue by category", "_cat.png", 14*mm + hw + 8*mm, top - 76*mm, hw, 62*mm)
footer(2); c.showPage()

# ---------------- Page 3: channel scorecard + insights ----------------
header("Channel Scorecard & Insights", "Drill-down by marketing channel (full period)")
y = ph - 40*mm; cols = [("Channel", 14*mm, "l"), ("Revenue", 80*mm, "r"), ("AOV", 120*mm, "r"), ("CAC", 155*mm, "r"), ("Churn", 190*mm, "r")]
c.setFillColor(colors.HexColor("#EEF3F9")); c.rect(14*mm, y - 3*mm, pw - 28*mm, 9*mm, fill=1, stroke=0)
c.setFillColor(colors.HexColor(P)); c.setFont("Helvetica-Bold", 10)
for n, x, al in cols: (c.drawString if al == "l" else c.drawRightString)(x if al == "l" else x + 12*mm, y, n)
c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#1B2437")); y -= 9*mm
for _, r in ch.iterrows():
    vals = [r.channel, money(r.Revenue), f"${r.AOV:.2f}", f"${r.CAC:.2f}", f"{r.Churn*100:.2f}%"]
    for (n, x, al), v in zip(cols, vals): (c.drawString if al == "l" else c.drawRightString)(x if al == "l" else x + 12*mm, y, v)
    y -= 8*mm
top_c = geo.sort_values("Revenue", ascending=False).iloc[0]; best = ch.sort_values("CAC").iloc[0]; worst = ch.sort_values("CAC").iloc[-1]
y -= 6*mm; c.setFont("Helvetica-Bold", 12); c.drawString(14*mm, y, "Key insights"); c.setFont("Helvetica", 10.5)
for s in [f"Revenue reached {money(cur['Revenue'])} over the last 12 months ({dl['Revenue']*100:+.1f}% vs prior 12 months).",
          f"{top_c.country} is the largest market with {money(top_c.Revenue)} of lifetime revenue ({top_c.Revenue/geo.Revenue.sum()*100:.0f}% of total).",
          f"{best.channel} is the cheapest channel (CAC ${best.CAC:.2f}); {worst.channel} is the most expensive (${worst.CAC:.2f}).",
          f"Churn is {cur['Churn']*100:.2f}% ({dl['Churn']*100:+.1f}% YoY) - retention is improving." if dl['Churn'] < 0 else
          f"Churn is {cur['Churn']*100:.2f}% ({dl['Churn']*100:+.1f}% YoY) - retention needs attention.",
          "Q4 seasonality is visible each year; plan acquisition budget ahead of Nov-Dec."]:
    y -= 7*mm; c.drawString(18*mm, y, "-  " + s)
footer(3); c.save()
for p in OUT.glob("_*.png"): p.unlink()
print("PDF written:", OUT / "Dashboard_Export.pdf")

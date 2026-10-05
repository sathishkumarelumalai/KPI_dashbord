
import pandas as pd, plotly.express as px, plotly.graph_objects as go, streamlit as st
from pathlib import Path
from data_gen import generate
from kpis import kpis, delta, trend, money

st.set_page_config(page_title="Executive KPI Dashboard", page_icon="📊", layout="wide")
PRIMARY, ACCENT, MUTED = "#1F4E79", "#E07A1F", "#8A94A6"
st.markdown("""<style>
.block-container{padding-top:1.4rem}
div[data-testid="stMetric"]{background:#fff;border:1px solid #E3E8EF;border-left:5px solid #1F4E79;
 padding:14px 18px;border-radius:10px;box-shadow:0 1px 3px rgba(16,24,40,.06)}
div[data-testid="stMetricValue"]{font-size:2rem;color:#1F4E79}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load():
    p = Path(__file__).parent / "data" / "sales_data.csv"
    df = pd.read_csv(p, parse_dates=["month"]) if p.exists() else generate()
    return df
df = load()

# ---------------- Sidebar slicers ----------------
st.sidebar.header("🎛️ Slicers")
lo, hi = df.month.min().date(), df.month.max().date()
dr = st.sidebar.slider("Date range", lo, hi, (lo, hi), format="MMM YYYY")
countries = st.sidebar.multiselect("Country", sorted(df.country.unique()), default=sorted(df.country.unique()))
cats = st.sidebar.multiselect("Category", sorted(df.category.unique()), default=sorted(df.category.unique()))
chans = st.sidebar.multiselect("Channel", sorted(df.channel.unique()), default=sorted(df.channel.unique()))
grain = st.sidebar.radio("Time drill-down", ["Year", "Quarter", "Month"], index=2, horizontal=True,
                         help="Switch the trend charts between Year → Quarter → Month.")
f = df[(df.month >= pd.Timestamp(dr[0])) & (df.month <= pd.Timestamp(dr[1])) & df.country.isin(countries)
       & df.category.isin(cats) & df.channel.isin(chans)]
if f.empty: st.warning("No data for the selected filters."); st.stop()

# previous period of equal length for deltas
span = (pd.Timestamp(dr[1]).to_period("M") - pd.Timestamp(dr[0]).to_period("M")).n + 1
ps = pd.Timestamp(dr[0]) - pd.DateOffset(months=span); pe = pd.Timestamp(dr[0]) - pd.DateOffset(months=1)
prev = df[(df.month >= ps) & (df.month <= pe) & df.country.isin(countries) & df.category.isin(cats) & df.channel.isin(chans)]
cur = kpis(f); dl = delta(cur, kpis(prev)) if not prev.empty else {k: None for k in cur}
def d(k, pct=True): return None if dl[k] is None else f"{dl[k]*100:+.1f}%"

# ---------------- Header + KPI cards ----------------
st.title("📊 Executive KPI Dashboard")
st.caption(f"{dr[0]:%b %Y} – {dr[1]:%b %Y} · {len(countries)} countries · {len(cats)} categories · vs. previous {span} months")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", money(cur["Revenue"]), d("Revenue"))
c2.metric("Customer Acquisition Cost", f"${cur['CAC']:,.2f}", d("CAC"), delta_color="inverse")
c3.metric("Churn Rate", f"{cur['Churn']*100:.2f}%", d("Churn"), delta_color="inverse")
c4.metric("Average Order Value", f"${cur['AOV']:,.2f}", d("AOV"))

# ---------------- Trend (area) + KPI selector ----------------
t = trend(f, grain)
left, right = st.columns([2, 1])
with left:
    st.subheader(f"Revenue trend ({grain.lower()}ly)")
    fig = go.Figure(go.Scatter(x=t.period, y=t.revenue, fill="tozeroy", mode="lines+markers" if grain != "Month" else "lines",
                               line=dict(color=PRIMARY, width=2.5), fillcolor="rgba(31,78,121,.18)",
                               hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>"))
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0), yaxis_tickprefix="$", plot_bgcolor="white",
                      yaxis=dict(gridcolor="#EEF1F6"), xaxis=dict(showgrid=False))
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("Efficiency KPIs")
    k = st.selectbox("Metric", ["CAC", "Churn", "AOV"], label_visibility="collapsed")
    fig = go.Figure(go.Scatter(x=t.period, y=t[k], fill="tozeroy", line=dict(color=ACCENT, width=2.5),
                               fillcolor="rgba(224,122,31,.18)"))
    fig.update_layout(height=290, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white",
                      yaxis=dict(gridcolor="#EEF1F6", tickformat=".1%" if k == "Churn" else "$,.0f"),
                      xaxis=dict(showgrid=False))
    st.plotly_chart(fig, width="stretch")

# ---------------- Geographic heatmap ----------------
st.subheader("Geographic heatmap")
gm = st.radio("Colour by", ["Revenue", "AOV", "CAC", "Churn"], horizontal=True)
rows = []
for (iso, name), g in f.groupby(["iso3", "country"]):
    rows.append({"iso3": iso, "country": name, **kpis(g)})
geo = pd.DataFrame(rows)
fig = px.choropleth(geo, locations="iso3", color=gm, hover_name="country",
                    color_continuous_scale="Blues" if gm in ("Revenue", "AOV") else "OrRd",
                    hover_data={"iso3": False, "Revenue": ":$,.0f", "AOV": ":$.2f", "CAC": ":$.2f", "Churn": ":.2%"})
fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth", bgcolor="rgba(0,0,0,0)")
fig.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, width="stretch")

# ---------------- Categorical drill-down ----------------
st.subheader("Categorical drill-down")
a, b = st.columns(2)
with a:
    by_cat = f.groupby("category").revenue.sum().sort_values().reset_index()
    fig = px.bar(by_cat, x="revenue", y="category", orientation="h", color_discrete_sequence=[PRIMARY],
                 title="Revenue by category")
    fig.update_layout(height=320, plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0), xaxis_tickprefix="$")
    st.plotly_chart(fig, width="stretch")
with b:
    pick = st.selectbox("Drill into a category →", ["All (by channel)"] + sorted(f.category.unique()))
    if pick.startswith("All"):
        sub = f.groupby("channel").revenue.sum().reset_index(); xcol, ttl = "channel", "Revenue by channel"
    else:
        sub = f[f.category == pick].groupby("subcategory").revenue.sum().reset_index()
        xcol, ttl = "subcategory", f"{pick}: revenue by sub-category"
    fig = px.bar(sub.sort_values("revenue", ascending=False), x=xcol, y="revenue", title=ttl,
                 color_discrete_sequence=[ACCENT])
    fig.update_layout(height=320, plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0), yaxis_tickprefix="$")
    st.plotly_chart(fig, width="stretch")

# ---------------- Detail table ----------------
with st.expander("📋 Channel scorecard (CAC & churn by channel)"):
    sc = pd.DataFrame([{"Channel": c, **kpis(g)} for c, g in f.groupby("channel")])
    st.dataframe(sc.style.format({"Revenue": "${:,.0f}", "CAC": "${:,.2f}", "Churn": "{:.2%}", "AOV": "${:,.2f}"}),
                 width="stretch", hide_index=True)
    st.download_button("Download filtered data (CSV)", f.to_csv(index=False), "filtered_data.csv")

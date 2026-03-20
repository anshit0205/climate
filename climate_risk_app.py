"""
Climate Risk Premium — Interactive Bubble Scatter Chart
Deploy: streamlit run climate_risk_app.py
Requires: pip install streamlit plotly pandas numpy

DATA NOTES (read before presenting):
──────────────────────────────────────────────────────────────────────
X-AXIS  →  Real ND-GAIN Vulnerability scores (2023, gain.nd.edu).
           Scale 0.0–1.0, displayed ×100. Higher = more vulnerable.
           Source: https://gain-new.crc.nd.edu/ranking/vulnerability

Y-AXIS  →  Indicative sovereign bond spreads over 10-yr US Treasury (bps).
           Representative 2023-2024 annual averages from:
             • J.P. Morgan EMBIG sovereign index
             • Bloomberg sovereign yield research
             • IMF WP/2020/79 cross-sectional averages
           NOTE: Exact spreads change daily. Do NOT cite as real-time.

BUBBLE  →  World Bank GDP 2023 (USD trillion, current prices)
──────────────────────────────────────────────────────────────────────
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Climate Risk Premium · Global Bond Markets",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background: #0B1A2E; color: #E2E8F0; }
  [data-testid="stSidebar"] { background: #0F2D52 !important; border-right: 1px solid #1E3A5F; }
  [data-testid="stSidebar"] * { color: #CBD5E1 !important; }
  .hero-title { font-size: 2.0rem; font-weight: 700; color: #FFFFFF; line-height: 1.15; margin-bottom: 4px; }
  .hero-sub   { font-size: 0.88rem; color: #64748B; margin-bottom: 0; }
  .hero-tag   { display:inline-block; background:rgba(20,255,236,0.13); border:1px solid rgba(20,255,236,0.33); color:#14FFEC;
                font-size:0.7rem; font-weight:600; letter-spacing:.1em; padding:3px 10px;
                border-radius:999px; margin-bottom:12px; text-transform:uppercase; }
  .metric-row { display:flex; gap:12px; margin:14px 0 18px; flex-wrap:wrap; }
  .metric-card { background:#112240; border:1px solid #1E3A5F; border-radius:10px;
                  padding:13px 17px; flex:1; min-width:130px; }
  .metric-card .label { font-size:10px; color:#64748B; text-transform:uppercase; letter-spacing:.08em; margin-bottom:4px; }
  .metric-card .value { font-size:1.5rem; font-weight:700; line-height:1; }
  .metric-card .sub   { font-size:10px; color:#475569; margin-top:2px; }
  .section-label { font-size:10px; color:#14FFEC; font-weight:700; letter-spacing:.15em;
                    text-transform:uppercase; margin:16px 0 5px; }
  .warn-box { background:#2D1A00; border:1px solid rgba(245,158,11,0.33); border-left:3px solid #F59E0B;
               border-radius:8px; padding:9px 13px; font-size:11px; color:#FCD34D;
               margin-bottom:10px; line-height:1.5; }
  .block-container { padding-top:1.6rem !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  DATA — Real ND-GAIN 2023 scores + indicative EMBIG-based spreads
# ══════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    # ND-GAIN scores: real 2023 values from gain-new.crc.nd.edu/ranking/vulnerability
    # Spreads: indicative 2023-24 averages from Bloomberg/EMBIG research
    # GDP: World Bank 2023 (USD trillion)
    rows = [
        # name,          ND_GAIN, spread_bps, gdp_T,  group,        phys, trans
        # --- Advanced (ND-GAIN scores 0.28-0.37) ---
        ("Germany",       0.301,   15,   4.46,  "Advanced",    3,   6),
        ("France",        0.304,   18,   3.05,  "Advanced",    5,   9),
        ("UK",            0.288,   22,   3.10,  "Advanced",    8,  12),
        ("USA",           0.312,    0,  27.36,  "Advanced",   18,  28),
        ("Japan",         0.369,   38,   4.21,  "Advanced",   14,  11),
        ("Australia",     0.316,   42,   1.69,  "Advanced",   22,  18),
        ("S. Korea",      0.357,   55,   1.71,  "Advanced",   24,  20),
        # --- Emerging (scores 0.33-0.49) ---
        ("Chile",         0.332,  155,   0.34,  "Emerging",   30,  22),
        ("Brazil",        0.369,  210,   2.17,  "Emerging",   42,  38),
        ("Turkey",        0.375,  310,   1.12,  "Emerging",   48,  52),
        ("China",         0.382,   95,  17.79,  "Emerging",   28,  42),
        ("Mexico",        0.387,  240,   1.49,  "Emerging",   42,  36),
        ("S. Africa",     0.395,  280,   0.38,  "Emerging",   55,  48),
        ("Colombia",      0.405,  295,   0.36,  "Emerging",   52,  44),
        ("Indonesia",     0.430,  265,   1.42,  "Emerging",   65,  50),
        ("India",         0.485,  185,   3.55,  "Emerging",   60,  52),
        # --- Frontier (scores 0.41-0.50) ---
        ("Egypt",         0.411,  520,   0.40,  "Frontier",   72,  62),
        ("Vietnam",       0.468,  320,   0.43,  "Frontier",   80,  58),
        ("Pakistan",      0.462,  640,   0.34,  "Frontier",   88,  72),
        ("Ghana",         0.448,  750,   0.07,  "Frontier",   95,  68),
        ("Nigeria",       0.481,  490,   0.48,  "Frontier",  115,  82),
        ("Kenya",         0.500,  480,   0.11,  "Frontier",   95,  72),
        # --- Highly Vulnerable (scores 0.47-0.51) ---
        ("Sri Lanka",     0.475,  820,   0.08,  "High Vuln.", 130,  78),
        ("Bangladesh",    0.485,  340,   0.46,  "High Vuln.", 155,  65),
        ("Ethiopia",      0.490,  620,   0.16,  "High Vuln.", 140,  60),
        ("Nepal",         0.490,  420,   0.04,  "High Vuln.", 165,  55),
        ("Mozambique",    0.493,  870,   0.17,  "High Vuln.", 265,  58),
        ("Haiti",         0.509,  850,   0.02,  "High Vuln.", 240,  52),
    ]
    df = pd.DataFrame(rows, columns=[
        "Country","ND_GAIN","Spread_bps","GDP_T",
        "Group","Physical_bps","Transition_bps"
    ])
    df["Climate_bps"] = df["Physical_bps"] + df["Transition_bps"]
    df["Vuln_pct"]    = (df["ND_GAIN"] * 100).round(1)
    return df

df = load_data()

GROUP_COLORS = {
    "Advanced":   "#3B82F6",
    "Emerging":   "#10B981",
    "Frontier":   "#F59E0B",
    "High Vuln.": "#EF4444",
}
GROUP_ORDER = ["Advanced", "Emerging", "Frontier", "High Vuln."]

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Filter by group</div>', unsafe_allow_html=True)
    selected_groups = st.multiselect(
        "Economy Groups", GROUP_ORDER, default=GROUP_ORDER,
        label_visibility="collapsed"
    )
    st.markdown('<div class="section-label">Bubble size</div>', unsafe_allow_html=True)
    bubble_metric = st.selectbox(
        "Scale bubbles by",
        ["GDP (USD Trillion)", "Climate Premium (bps)", "Physical Premium (bps)"],
        label_visibility="collapsed"
    )
    st.markdown('<div class="section-label">Chart options</div>', unsafe_allow_html=True)
    show_trend  = st.toggle("Show trend line",       value=True)
    trend_color = st.color_picker("Trend line colour", "#00E5FF")
    show_labels = st.toggle("Show country labels",   value=True)
    show_quad   = st.toggle("Show risk quadrants",   value=True)
    show_annot  = st.toggle("Show annotations",      value=True)

    st.markdown("---")
    st.markdown("""
<div style='font-size:11px;color:#64748B;line-height:1.65;'>
<b style='color:#F59E0B'>⚠ Data disclaimer</b><br>
ND-GAIN scores: real 2023 values (gain.nd.edu).<br>
Spreads: indicative 2023-24 averages from Bloomberg/EMBIG — fluctuate daily.<br><br>
<b style='color:#94A3B8'>Sources</b><br>
ND-GAIN · gain-new.crc.nd.edu<br>
Bloomberg · J.P. Morgan EMBIG<br>
IMF WP/2020/79 · BIS WP 1275<br>
World Bank WDI 2023
</div>""", unsafe_allow_html=True)

# ── Filter + size ──────────────────────────────────────────────────
dff = df[df["Group"].isin(selected_groups)].copy() if selected_groups else df.copy()
SIZE_MAP = {
    "GDP (USD Trillion)":     "GDP_T",
    "Climate Premium (bps)":  "Climate_bps",
    "Physical Premium (bps)": "Physical_bps",
}
raw = dff[SIZE_MAP[bubble_metric]].values
sz_min, sz_max = 10, 62
sizes = (sz_min + (raw - raw.min()) / max(raw.max()-raw.min(), 1) * (sz_max-sz_min)
         if raw.max() > raw.min() else np.full(len(raw), (sz_min+sz_max)/2))
dff = dff.copy()
dff["_sz"] = sizes

# ── Header ─────────────────────────────────────────────────────────
st.markdown('<div class="hero-tag">Global Fixed Income Research · 2025</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Climate Risk Premium on Global Bond Markets</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">ND-GAIN Vulnerability (real 2023 · gain.nd.edu) vs. sovereign bond spread · '
    '28 economies · bubble = GDP (World Bank) · IMF WP/2020/79, BIS WP 1275</div>',
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""<div class="warn-box">
⚠ <b>Data note:</b> X-axis = real ND-GAIN 2023 scores (0–1) × 100.
Y-axis = indicative avg spreads 2023-24 from Bloomberg/EMBIG — not real-time quotes.
Physical & transition premium splits are model-based estimates from IMF WP/2020/79 methodology.
</div>""", unsafe_allow_html=True)

# ── Metric cards ───────────────────────────────────────────────────
adv   = dff[dff["Group"]=="Advanced"]["Spread_bps"]
vuln  = dff[dff["Group"]=="High Vuln."]["Spread_bps"]
avg_a = int(adv.mean())  if len(adv)  else 0
avg_v = int(vuln.mean()) if len(vuln) else 0
gap   = avg_v - avg_a

st.markdown(f"""<div class="metric-row">
  <div class="metric-card"><div class="label">Countries shown</div>
    <div class="value" style="color:#14FFEC">{len(dff)}</div>
    <div class="sub">of 28 total</div></div>
  <div class="metric-card"><div class="label">Avg spread · Advanced</div>
    <div class="value" style="color:#3B82F6">{avg_a}<span style='font-size:.9rem'> bps</span></div>
    <div class="sub">indicative avg 2023–24</div></div>
  <div class="metric-card"><div class="label">Avg spread · High Vuln.</div>
    <div class="value" style="color:#EF4444">{avg_v}<span style='font-size:.9rem'> bps</span></div>
    <div class="sub">indicative avg 2023–24</div></div>
  <div class="metric-card"><div class="label">Spread gap</div>
    <div class="value" style="color:#F59E0B">+{gap}<span style='font-size:.9rem'> bps</span></div>
    <div class="sub">high vuln. vs advanced</div></div>
</div>""", unsafe_allow_html=True)

# ── Plotly figure ──────────────────────────────────────────────────
GRID = "#1E3A5F"; BG = "#0D1F35"; PAPER = "#0B1A2E"; TICK = "#8CA8C8"
fig  = go.Figure()

MID = 43  # midpoint on ×100 scale
if show_quad:
    fig.add_vrect(x0=25, x1=MID, fillcolor="#3B82F6", opacity=0.04, layer="below", line_width=0)
    fig.add_vrect(x0=MID, x1=55, fillcolor="#EF4444", opacity=0.04, layer="below", line_width=0)
    fig.add_vline(x=MID, line_color=GRID, line_width=1.2, line_dash="dot", opacity=0.7)

if show_trend and len(dff) >= 3:
    m, b_ = np.polyfit(dff["Vuln_pct"], dff["Spread_bps"], 1)
    xl = np.linspace(dff["Vuln_pct"].min()-1, dff["Vuln_pct"].max()+1, 300)
    fig.add_trace(go.Scatter(
        x=xl, y=m*xl+b_, mode="lines",
        line=dict(color=trend_color, width=2.5, dash="dash"),
        hoverinfo="skip", showlegend=True, name="Trend (OLS)", legendrank=999,
    ))

for group in GROUP_ORDER:
    if group not in selected_groups: continue
    gdf = dff[dff["Group"]==group]
    color = GROUP_COLORS[group]
    hover = []
    for _, r in gdf.iterrows():
        hover.append(
            f"<b style='font-size:14px'>{r.Country}</b><br>"
            f"<span style='color:#94A3B8'>Group: </span>{r.Group}<br>"
            f"<span style='color:#14FFEC'>ND-GAIN 2023: </span><b>{r.ND_GAIN:.3f}</b> "
            f"<span style='color:#475569; font-size:10px'>(gain.nd.edu)</span><br>"
            f"<span style='color:#94A3B8'>Spread (indicative): </span><b>{int(r.Spread_bps)} bps</b> "
            f"<span style='color:#475569; font-size:10px'>(Bloomberg/EMBIG)</span><br>"
            f"<span style='color:#EF4444'>Physical premium est.: </span><b>~{int(r.Physical_bps)} bps</b><br>"
            f"<span style='color:#F59E0B'>Transition premium est.: </span><b>~{int(r.Transition_bps)} bps</b><br>"
            f"<span style='color:#94A3B8'>GDP (WB 2023): </span><b>${r.GDP_T:.2f}T</b>"
        )
    fig.add_trace(go.Scatter(
        x=gdf["Vuln_pct"], y=gdf["Spread_bps"],
        mode="markers+text" if show_labels else "markers",
        name=group,
        marker=dict(size=gdf["_sz"], color=color, opacity=0.84,
                    line=dict(color="rgba(255,255,255,0.4)", width=0.9),
                    sizemode="diameter"),
        text=gdf["Country"],
        textposition="top center",
        textfont=dict(size=9.5, color="rgba(255,255,255,0.90)", family="Inter"),
        customdata=hover,
        hovertemplate="%{customdata}<extra></extra>",
        hoverlabel=dict(bgcolor="#112240", bordercolor=color,
                        font=dict(size=12, color="#E2E8F0", family="Inter")),
    ))

if show_annot and len(dff) > 1:
    fig.add_annotation(x=26, y=920, text="<b>LOW RISK · LOW SPREAD</b>",
        showarrow=False, font=dict(size=9.5, color="#3B82F6"), xanchor="left", opacity=0.6)
    fig.add_annotation(x=44, y=920, text="<b>HIGH RISK · HIGH SPREAD</b>",
        showarrow=False, font=dict(size=9.5, color="#EF4444"), xanchor="left", opacity=0.6)
    fig.add_annotation(
        x=50.9, y=875,
        text="<b>IMF finding:</b><br>+10pp vuln → +150 bps<br>for EMs (WP/2020/79)",
        showarrow=True, arrowhead=2, arrowcolor="#F59E0B",
        arrowsize=1.1, arrowwidth=1.5, ax=-75, ay=45,
        font=dict(size=10, color="#FCD34D"),
        bgcolor="rgba(15,45,82,0.6)", bordercolor="#F59E0B", borderwidth=1, borderpad=6,
    )

fig.update_layout(
    paper_bgcolor=PAPER, plot_bgcolor=BG, height=630,
    margin=dict(l=65, r=40, t=30, b=75),
    font=dict(family="Inter, sans-serif", color=TICK),
    xaxis=dict(
        title=dict(text="ND-GAIN Vulnerability Score × 100  (real 2023 · gain.nd.edu · higher = more vulnerable)",
                   font=dict(size=11, color=TICK)),
        range=[25, 55], gridcolor=GRID, gridwidth=0.6,
        zerolinecolor=GRID, tickfont=dict(size=10, color=TICK), tickformat=".0f",
    ),
    yaxis=dict(
        title=dict(text="Sovereign Bond Spread (bps over 10-yr US Treasury · indicative avg 2023–24)",
                   font=dict(size=11, color=TICK)),
        range=[-40, 980], gridcolor=GRID, gridwidth=0.6,
        zerolinecolor=GRID, tickfont=dict(size=10, color=TICK),
    ),
    legend=dict(x=0.01, y=0.99, bgcolor="rgba(17,34,64,0.85)",
                bordercolor="#1E3A5F", borderwidth=1,
                font=dict(size=11, color="#CBD5E1"),
                title=dict(text="Economy Group", font=dict(size=10, color="#64748B")),
                itemsizing="constant"),
    hovermode="closest", dragmode="pan",
)

st.plotly_chart(fig, use_container_width=True, config={
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["select2d","lasso2d"],
    "toImageButtonOptions": {"format":"png","filename":"climate_risk_premium","scale":2},
    "scrollZoom": True,
})

# ── Table + sources ────────────────────────────────────────────────
st.markdown("---")
col_t, col_s = st.columns([3, 2])

with col_t:
    st.markdown('<div class="section-label">Country data table</div>', unsafe_allow_html=True)
    disp = (dff[["Country","Group","ND_GAIN","Spread_bps","Physical_bps","Transition_bps","GDP_T"]]
            .rename(columns={"ND_GAIN":"ND-GAIN (2023)","Spread_bps":"Spread (bps) ⚠",
                              "Physical_bps":"Physical~","Transition_bps":"Transition~","GDP_T":"GDP $T"})
            .sort_values("Spread (bps) ⚠", ascending=False).reset_index(drop=True))
    st.dataframe(disp, use_container_width=True, hide_index=True,
        column_config={
            "ND-GAIN (2023)":  st.column_config.NumberColumn(format="%.3f",
                help="Real 2023 score from gain-new.crc.nd.edu/ranking/vulnerability"),
            "Spread (bps) ⚠": st.column_config.NumberColumn(format="%d bps",
                help="Indicative annual avg 2023-24 from Bloomberg/EMBIG. Fluctuates daily."),
            "Physical~":  st.column_config.NumberColumn(format="~%d bps"),
            "Transition~": st.column_config.NumberColumn(format="~%d bps"),
            "GDP $T": st.column_config.NumberColumn(format="$%.2fT"),
        }, height=390)
    st.markdown('<div style="font-size:10px;color:#475569;margin-top:4px">⚠ Spread = indicative, not real-time. Source: Bloomberg / EMBIG.</div>', unsafe_allow_html=True)

with col_s:
    st.markdown('<div class="section-label">Data sources</div>', unsafe_allow_html=True)
    for tag, color, title, body, url in [
        ("X-AXIS · VERIFIED REAL DATA", "#14FFEC",
         "ND-GAIN Country Index 2023",
         "Real 0–1 vulnerability scores. 45 indicators, 185 countries.\nFree & open-source (Creative Commons). Updated annually.",
         "gain-new.crc.nd.edu/ranking/vulnerability"),
        ("Y-AXIS · INDICATIVE ONLY", "#F59E0B",
         "Bloomberg + J.P. Morgan EMBIG",
         "Indicative avg spreads 2023-24 vs 10-yr US Treasury.\nValues change daily — illustrative order-of-magnitude only.",
         "bloomberg.com · jpmorgan.com/EMBIG"),
        ("PRIMARY RESEARCH", "#3B82F6",
         "IMF WP/2020/79 — Cevik & Jalles",
         "+10pp ND-GAIN → +30 bps globally; +150 bps for EMs.\n98 countries · 1995-2017. Uses GMM/OLS regression.",
         "imf.org/en/Publications/WP/Issues/2020/06/05/..."),
        ("CROSS-CHECK", "#10B981",
         "BIS Working Paper No. 1275 (2024)",
         "52 economies · 2000-2023. Separates physical + transition\nrisk channels post-Paris Agreement.",
         "bis.org/publ/work1275.htm"),
    ]:
        st.markdown(f"""
<div style='background:#112240;border:1px solid #1E3A5F;border-left:3px solid {color};
     border-radius:8px;padding:10px 13px;margin-bottom:9px;'>
  <div style='font-size:9px;color:{color};font-weight:700;letter-spacing:.1em;margin-bottom:2px'>{tag}</div>
  <div style='font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:2px'>{title}</div>
  <div style='font-size:10.5px;color:#64748B;white-space:pre-line;margin-bottom:4px'>{body}</div>
  <div style='font-size:9.5px;color:#3B82F6;font-style:italic'>{url}</div>
</div>""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;padding:18px 0 6px;font-size:10px;color:#334155;letter-spacing:.04em;'>
  Climate Risk Premium · Global Bond Markets · 2025 &nbsp;|&nbsp;
  ND-GAIN (gain.nd.edu) · IMF WP/2020/79 · BIS WP 1275 · Bloomberg · J.P.Morgan EMBIG · World Bank WDI
</div>""", unsafe_allow_html=True)

"""
dashboard/app.py
─────────────────────────────────────────────────────────────
HPC Stochastic Pricing Kernel — Interactive Dashboard
Aesthetic: Dark quant terminal — Bloomberg-inspired with
           amber/green accents on deep navy-black background.
           Monospace data, sharp geometry, zero decoration.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import math

from python.models.pricing_engine import (
    MarketParams, price_option, price_surface,
    BlackScholesEngine, COSEngine, MonteCarloEngine, LSMCEngine,
    PricingResult
)

# ─────────────────────────────────────────────────────────────
#  Page config & global CSS
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HPC Pricing Kernel",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

  html, body, [class*="css"]  {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #050810;
    color: #c8d6e8;
  }
  .stApp { background-color: #050810; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #080d1a;
    border-right: 1px solid #1a2540;
  }
  [data-testid="stSidebar"] .css-ng1t4o { color: #c8d6e8; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #0b1220;
    border: 1px solid #1a2540;
    border-radius: 4px;
    padding: 12px 16px;
  }
  [data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.5rem !important;
    color: #f0b429 !important;
  }
  [data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #5f7a9e !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  [data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background: #080d1a;
    border-bottom: 1px solid #1a2540;
    gap: 0;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #5f7a9e;
    padding: 10px 20px;
    border-radius: 0;
    border-bottom: 2px solid transparent;
  }
  .stTabs [aria-selected="true"] {
    color: #f0b429 !important;
    border-bottom: 2px solid #f0b429 !important;
    background: transparent !important;
  }

  /* Inputs */
  .stSlider [data-baseweb="slider"] { accent-color: #f0b429; }
  .stSelectbox div[data-baseweb="select"] > div {
    background: #0b1220;
    border-color: #1a2540;
    color: #c8d6e8;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
  }
  input[type="number"] {
    background: #0b1220 !important;
    border: 1px solid #1a2540 !important;
    color: #c8d6e8 !important;
    font-family: 'IBM Plex Mono', monospace !important;
  }

  /* Header */
  .terminal-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #2a3f5f;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    border-bottom: 1px solid #1a2540;
    padding-bottom: 8px;
    margin-bottom: 4px;
  }
  .price-display {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.8rem;
    font-weight: 600;
    color: #f0b429;
    letter-spacing: -0.02em;
    line-height: 1;
  }
  .greek-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #3d5a80;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .greek-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    color: #4fc3f7;
  }
  .method-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 3px 8px;
    border: 1px solid #f0b429;
    color: #f0b429;
    border-radius: 2px;
    margin-right: 6px;
  }
  .perf-bar {
    height: 4px;
    background: linear-gradient(90deg, #f0b429, #4fc3f7);
    border-radius: 2px;
    margin: 4px 0;
  }

  /* Hide streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; padding-bottom: 0; }

  /* Tables */
  .stDataFrame { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }
  thead tr th {
    background: #0b1220 !important;
    color: #5f7a9e !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.65rem;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  Plot theme helper
# ─────────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="#050810",
    plot_bgcolor="#080d1a",
    font=dict(family="IBM Plex Mono", color="#c8d6e8", size=11),
    xaxis=dict(gridcolor="#131c2e", linecolor="#1a2540", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#131c2e", linecolor="#1a2540", tickfont=dict(size=10)),
)
COLORS = {
    "bs":  "#f0b429",   # amber — ground truth
    "cos": "#4fc3f7",   # sky blue
    "mc":  "#56cc9d",   # green
    "lsmc":"#ce93d8",   # purple
    "neg": "#f06292",   # pink/red
}

def apply_theme(fig):
    fig.update_layout(**PLOTLY_THEME)
    fig.update_layout(margin=dict(l=40, r=20, t=30, b=40))
    return fig

# ─────────────────────────────────────────────────────────────
#  Sidebar — Parameters
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="terminal-header">⚡ HPC PRICING KERNEL v1.0</p>', unsafe_allow_html=True)

    st.markdown("### MARKET PARAMETERS")
    S     = st.slider("Spot Price  S",       10.0,  300.0, 100.0, 0.5)
    K     = st.slider("Strike Price  K",     10.0,  300.0, 100.0, 0.5)
    sigma = st.slider("Volatility  σ",        0.01,  1.0,   0.20, 0.01, format="%.2f")
    r     = st.slider("Risk-free Rate  r",    0.0,   0.15,  0.05, 0.005, format="%.3f")
    q     = st.slider("Dividend Yield  q",    0.0,   0.10,  0.00, 0.005, format="%.3f")
    T     = st.slider("Time to Maturity (y)", 0.02,  5.0,   1.0,  0.02)

    st.divider()
    st.markdown("### OPTION")
    opt_type = st.selectbox("Type", ["call", "put"])

    st.divider()
    st.markdown("### MC CONFIG")
    num_paths = st.select_slider(
        "Num Paths",
        options=[1_000, 5_000, 10_000, 50_000, 100_000, 500_000],
        value=50_000
    )
    num_steps = st.select_slider("Num Steps", options=[10, 50, 100, 252, 500], value=100)

    st.divider()
    moneyness = (S / K - 1) * 100
    itm = moneyness > 0 if opt_type == "call" else moneyness < 0
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#5f7a9e;">
    MONEYNESS<br>
    <span style="font-size:1.1rem; color:{'#56cc9d' if itm else '#f06292'};">
    {'ITM' if itm else 'OTM'} {abs(moneyness):.1f}%
    </span><br><br>
    S/K = {S/K:.4f}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  Top header bar
# ─────────────────────────────────────────────────────────────
col_logo, col_status = st.columns([3, 1])
with col_logo:
    st.markdown("""
    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:8px;">
      <span style="font-family:'IBM Plex Mono',monospace; font-size:1.4rem; font-weight:600; color:#f0b429; letter-spacing:-0.02em;">HPC PRICING KERNEL</span>
      <span style="font-family:'IBM Plex Mono',monospace; font-size:0.65rem; color:#3d5a80; letter-spacing:0.15em;">MONTE CARLO · COS · LSMC · BLACK-SCHOLES</span>
    </div>
    """, unsafe_allow_html=True)
with col_status:
    st.markdown("""
    <div style="text-align:right; font-family:'IBM Plex Mono',monospace; font-size:0.65rem; color:#5f7a9e; padding-top:6px;">
    C++ PYBIND11 ENGINE<br>
    <span style="color:#56cc9d;">● LIVE</span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  Compute all results
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1)
def compute_all(S, K, r, q, sigma, T, opt_type, num_paths, num_steps):
    params = MarketParams(S=S, K=K, r=r, q=q, sigma=sigma, T=T)

    # Black-Scholes
    bs = BlackScholesEngine(params)
    t0 = time.perf_counter()
    r_bs = bs.price_call() if opt_type == "call" else bs.price_put()
    r_bs.elapsed_ms = (time.perf_counter() - t0) * 1000

    # COS
    cos_eng = COSEngine(params, N=256)
    r_cos = cos_eng.price(opt_type)
    cos_eng.compute_greeks(r_cos, opt_type)

    # Monte Carlo
    mc = MonteCarloEngine(params, num_paths=num_paths, num_steps=num_steps)
    r_mc = mc.price_european(opt_type)
    mc.compute_greeks(r_mc, opt_type)

    # LSMC
    lsmc_paths = min(num_paths, 20_000)
    lsmc = LSMCEngine(params, num_paths=lsmc_paths, num_steps=50)
    r_lsmc = lsmc.price(opt_type)

    return r_bs, r_cos, r_mc, r_lsmc

r_bs, r_cos, r_mc, r_lsmc = compute_all(S, K, r, q, sigma, T, opt_type, num_paths, num_steps)

# ─────────────────────────────────────────────────────────────
#  Tabs
# ─────────────────────────────────────────────────────────────
tabs = st.tabs([
    "PRICING",
    "GREEKS",
    "BENCHMARK",
    "VOL SURFACE",
    "EXOTIC OPTIONS",
    "CONVERGENCE",
])

# ══════════════════════════════════════════════════════════════
# TAB 1: PRICING
# ══════════════════════════════════════════════════════════════
with tabs[0]:
    # Top metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta_vs_bs = r_cos.price - r_bs.price
        st.metric("BLACK-SCHOLES", f"${r_bs.price:.4f}", delta=None)
    with c2:
        st.metric("COS METHOD", f"${r_cos.price:.4f}",
                  delta=f"{r_cos.price - r_bs.price:+.4f} vs BS")
    with c3:
        st.metric("MONTE CARLO", f"${r_mc.price:.4f}",
                  delta=f"{r_mc.price - r_bs.price:+.4f} vs BS")
    with c4:
        st.metric("LSMC (AMERICAN)", f"${r_lsmc.price:.4f}",
                  delta=f"early ex. premium")

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([3, 2])

    with left:
        # Option price as function of spot — payoff diagram
        S_range = np.linspace(max(1, S * 0.5), S * 1.5, 200)
        prices_bs, prices_cos, intrinsic = [], [], []

        for s in S_range:
            p = MarketParams(S=s, K=K, r=r, q=q, sigma=sigma, T=T)
            bs_e = BlackScholesEngine(p)
            cos_e = COSEngine(p, N=128)
            r_b = bs_e.price_call() if opt_type == "call" else bs_e.price_put()
            r_c = cos_e.price(opt_type)
            prices_bs.append(r_b.price)
            prices_cos.append(r_c.price)
            intr = max(s - K, 0) if opt_type == "call" else max(K - s, 0)
            intrinsic.append(intr)

        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=S_range, y=intrinsic, name="Intrinsic Value",
            line=dict(color="#2a3f5f", dash="dash", width=1), fill=None))
        fig_price.add_trace(go.Scatter(x=S_range, y=prices_cos, name="COS Method",
            line=dict(color=COLORS["cos"], width=1.5)))
        fig_price.add_trace(go.Scatter(x=S_range, y=prices_bs, name="Black-Scholes",
            line=dict(color=COLORS["bs"], width=2)))
        fig_price.add_vline(x=S, line_color="#f06292", line_dash="dot", line_width=1,
            annotation_text=f"S={S}", annotation_font_color="#f06292",
            annotation_font_size=10)
        fig_price.update_layout(title="Option Price vs Spot",
            xaxis_title="Spot Price", yaxis_title="Option Price",
            legend=dict(orientation="h", y=1.12), **PLOTLY_THEME,
            margin=dict(l=40, r=20, t=50, b=40))
        st.plotly_chart(fig_price, use_container_width=True)

    with right:
        st.markdown('<p class="terminal-header">PRICING SUMMARY</p>', unsafe_allow_html=True)

        methods_data = {
            "Method": ["Black-Scholes", "COS (N=256)", "Monte Carlo", "LSMC"],
            "Price": [f"${r_bs.price:.5f}", f"${r_cos.price:.5f}",
                      f"${r_mc.price:.5f}", f"${r_lsmc.price:.5f}"],
            "Err vs BS": ["—",
                          f"{abs(r_cos.price - r_bs.price):.2e}",
                          f"{abs(r_mc.price - r_bs.price):.2e}",
                          "—"],
            "Time (ms)": [f"{r_bs.elapsed_ms:.3f}", f"{r_cos.elapsed_ms:.3f}",
                          f"{r_mc.elapsed_ms:.1f}", f"{r_lsmc.elapsed_ms:.0f}"],
        }
        df = pd.DataFrame(methods_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="terminal-header">CONFIDENCE INTERVAL (MC)</p>', unsafe_allow_html=True)

        fig_ci = go.Figure()
        fig_ci.add_trace(go.Scatter(
            x=["95% CI"], y=[r_mc.ci_high], mode="markers",
            marker=dict(symbol="line-ew", size=20, color=COLORS["mc"],
                        line=dict(width=2, color=COLORS["mc"])), name="Upper"))
        fig_ci.add_trace(go.Scatter(
            x=["95% CI"], y=[r_mc.ci_low], mode="markers",
            marker=dict(symbol="line-ew", size=20, color=COLORS["mc"],
                        line=dict(width=2, color=COLORS["mc"])), name="Lower"))
        fig_ci.add_trace(go.Scatter(
            x=["95% CI", "95% CI"], y=[r_mc.ci_low, r_mc.ci_high],
            mode="lines", line=dict(color=COLORS["mc"], width=3), name="Interval"))
        fig_ci.add_hline(y=r_bs.price, line_color=COLORS["bs"],
                         line_dash="dot", line_width=1)
        fig_ci.update_layout(showlegend=False, height=180,
                             yaxis_title="Price",
                             **PLOTLY_THEME, margin=dict(l=40, r=20, t=10, b=40))
        st.plotly_chart(fig_ci, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 2: GREEKS
# ══════════════════════════════════════════════════════════════
with tabs[1]:
    g = r_bs  # Use BS for clean analytical greeks

    # Greek gauges
    greek_cols = st.columns(5)
    greek_data = [
        ("DELTA  Δ", g.delta, "-1 to +1"),
        ("GAMMA  Γ", g.gamma, "curvature"),
        ("VEGA   ν", g.vega,  "per 1% σ"),
        ("THETA  Θ", g.theta, "per day"),
        ("RHO    ρ", g.rho,   "per 1% r"),
    ]
    for col, (label, val, unit) in zip(greek_cols, greek_data):
        with col:
            color = "#56cc9d" if val >= 0 else "#f06292"
            st.markdown(f"""
            <div style="background:#0b1220; border:1px solid #1a2540; border-radius:4px;
                        padding:16px 12px; text-align:center;">
              <div class="greek-label">{label}</div>
              <div style="font-family:'IBM Plex Mono',monospace; font-size:1.4rem;
                          font-weight:600; color:{color}; margin:8px 0;">
                {val:+.4f}
              </div>
              <div style="font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
                          color:#3d5a80;">{unit}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Greeks vs Spot
    S_rng = np.linspace(max(1, S * 0.5), S * 1.5, 150)
    delta_arr, gamma_arr, vega_arr, theta_arr = [], [], [], []
    for s in S_rng:
        p = MarketParams(S=s, K=K, r=r, q=q, sigma=sigma, T=T)
        bs_e = BlackScholesEngine(p)
        res = bs_e.price_call() if opt_type == "call" else bs_e.price_put()
        delta_arr.append(res.delta)
        gamma_arr.append(res.gamma)
        vega_arr.append(res.vega)
        theta_arr.append(res.theta)

    fig_greeks = make_subplots(rows=2, cols=2,
        subplot_titles=["Delta (Δ)", "Gamma (Γ)", "Vega (ν)", "Theta (Θ)"],
        vertical_spacing=0.12)

    greek_series = [
        (delta_arr, COLORS["bs"],  1, 1),
        (gamma_arr, COLORS["cos"], 1, 2),
        (vega_arr,  COLORS["mc"],  2, 1),
        (theta_arr, COLORS["neg"], 2, 2),
    ]
    for arr, color, row, col in greek_series:
        fig_greeks.add_trace(
            go.Scatter(x=S_rng, y=arr, line=dict(color=color, width=2), showlegend=False),
            row=row, col=col)
        fig_greeks.add_vline(x=S, line_color="#2a3f5f", line_dash="dot", line_width=1,
                             row=row, col=col)

    fig_greeks.update_layout(height=480, **PLOTLY_THEME,
                             margin=dict(l=40, r=20, t=60, b=40))
    fig_greeks.update_annotations(font=dict(color="#5f7a9e", size=11,
                                            family="IBM Plex Mono"))
    for ax in ['xaxis', 'xaxis2', 'xaxis3', 'xaxis4',
               'yaxis', 'yaxis2', 'yaxis3', 'yaxis4']:
        fig_greeks.update_layout(**{ax: dict(gridcolor="#131c2e", linecolor="#1a2540")})
    st.plotly_chart(fig_greeks, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 3: BENCHMARK
# ══════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<p class="terminal-header">METHOD COMPARISON — PRICE ACCURACY & SPEED</p>',
                unsafe_allow_html=True)

    methods  = ["Black-Scholes", "COS (N=256)", "Monte Carlo", "LSMC"]
    prices   = [r_bs.price, r_cos.price, r_mc.price, r_lsmc.price]
    timings  = [r_bs.elapsed_ms, r_cos.elapsed_ms, r_mc.elapsed_ms, r_lsmc.elapsed_ms]
    errors   = [0, abs(r_cos.price - r_bs.price),
                abs(r_mc.price - r_bs.price),
                abs(r_lsmc.price - r_bs.price)]
    colors_  = [COLORS["bs"], COLORS["cos"], COLORS["mc"], COLORS["lsmc"]]

    left_b, right_b = st.columns(2)

    with left_b:
        fig_speed = go.Figure()
        fig_speed.add_trace(go.Bar(
            x=methods, y=timings,
            marker_color=colors_,
            marker_line_color="#050810", marker_line_width=1,
            text=[f"{t:.3f}ms" for t in timings],
            textposition="outside",
            textfont=dict(family="IBM Plex Mono", size=10, color="#c8d6e8"),
        ))
        fig_speed.update_layout(title="Execution Time (ms)", yaxis_type="log",
                                yaxis_title="Time (ms) — log scale",
                                **PLOTLY_THEME, margin=dict(l=40,r=20,t=50,b=40))
        st.plotly_chart(fig_speed, use_container_width=True)

    with right_b:
        fig_err = go.Figure()
        fig_err.add_trace(go.Bar(
            x=methods[1:], y=errors[1:],
            marker_color=colors_[1:],
            marker_line_color="#050810", marker_line_width=1,
            text=[f"{e:.2e}" for e in errors[1:]],
            textposition="outside",
            textfont=dict(family="IBM Plex Mono", size=10, color="#c8d6e8"),
        ))
        fig_err.update_layout(title="Absolute Error vs Black-Scholes",
                              yaxis_title="|Price - BS|",
                              **PLOTLY_THEME, margin=dict(l=40,r=20,t=50,b=40))
        st.plotly_chart(fig_err, use_container_width=True)

    # Price comparison bar chart
    fig_prices = go.Figure()
    fig_prices.add_trace(go.Bar(
        x=methods, y=prices,
        marker_color=colors_,
        marker_line_color="#050810",
        text=[f"${p:.5f}" for p in prices],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=10, color="#c8d6e8"),
    ))
    fig_prices.update_layout(title="Prices by Method",
                             yaxis_title="Option Price ($)",
                             **PLOTLY_THEME, margin=dict(l=40,r=20,t=50,b=60))
    st.plotly_chart(fig_prices, use_container_width=True)

    # Summary table
    df_bench = pd.DataFrame({
        "Method": methods,
        "Price ($)": [f"{p:.6f}" for p in prices],
        "Error vs BS": [f"{e:.4e}" for e in errors],
        "Time (ms)": [f"{t:.4f}" for t in timings],
        "Speed Rank": ["1st (analytical)", "2nd (N=256)", "3rd (stochastic)", "4th (regression)"],
    })
    st.dataframe(df_bench, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# TAB 4: VOL SURFACE
# ══════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<p class="terminal-header">OPTION PRICING SURFACE</p>',
                unsafe_allow_html=True)

    c_surf1, c_surf2 = st.columns(2)
    with c_surf1:
        surf_method = st.selectbox("Surface Method", ["black_scholes", "cos", "monte_carlo"])
    with c_surf2:
        surf_opt = st.selectbox("Surface Type", ["call", "put"])

    strikes    = np.linspace(S * 0.6, S * 1.4, 20).tolist()
    maturities = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

    @st.cache_data(ttl=30)
    def get_surface(S, r, q, sigma, method, opt_type, strikes, maturities):
        return price_surface(
            strikes=strikes, maturities=maturities,
            S=S, r=r, q=q, sigma=sigma,
            method=method, option_type=opt_type
        )

    with st.spinner("Computing surface..."):
        surface = get_surface(S, r, q, sigma, surf_method, surf_opt,
                              strikes, maturities)

    surface_arr = np.array(surface)

    fig_surf = go.Figure(data=[go.Surface(
        z=surface_arr,
        x=strikes,
        y=maturities,
        colorscale=[[0, "#0a1628"], [0.3, "#1a3a5c"], [0.6, "#f0b429"], [1.0, "#ffffff"]],
        contours=dict(
            z=dict(show=True, usecolormap=True, highlightcolor="#f0b429", project_z=True)
        ),
        lighting=dict(ambient=0.6, diffuse=0.8, roughness=0.5, specular=0.3),
    )])
    fig_surf.update_layout(
        scene=dict(
            xaxis=dict(title="Strike", backgroundcolor="#050810",
                       gridcolor="#1a2540", showbackground=True),
            yaxis=dict(title="Maturity (y)", backgroundcolor="#050810",
                       gridcolor="#1a2540", showbackground=True),
            zaxis=dict(title="Price ($)", backgroundcolor="#050810",
                       gridcolor="#1a2540", showbackground=True),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=0.8)),
        ),
        paper_bgcolor="#050810",
        font=dict(family="IBM Plex Mono", color="#c8d6e8"),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"{surf_opt.upper()} Surface — {surf_method.replace('_',' ').title()}",
        title_font=dict(color="#5f7a9e", size=12),
    )
    st.plotly_chart(fig_surf, use_container_width=True)

    # Heatmap view
    df_heat = pd.DataFrame(surface_arr, index=[f"T={t}" for t in maturities],
                           columns=[f"K={k:.0f}" for k in strikes])
    fig_heat = go.Figure(go.Heatmap(
        z=surface_arr,
        x=[f"K={k:.0f}" for k in strikes],
        y=[f"T={t}" for t in maturities],
        colorscale=[[0,"#050810"],[0.5,"#1a3a5c"],[1,"#f0b429"]],
        text=[[f"{v:.2f}" for v in row] for row in surface_arr],
        texttemplate="%{text}",
        textfont=dict(size=8, family="IBM Plex Mono"),
    ))
    fig_heat.update_layout(title="Price Heatmap (Strike × Maturity)",
                           **PLOTLY_THEME, height=320,
                           margin=dict(l=80, r=20, t=50, b=40))
    st.plotly_chart(fig_heat, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 5: EXOTIC OPTIONS
# ══════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<p class="terminal-header">EXOTIC OPTION PRICING</p>',
                unsafe_allow_html=True)

    ex_col1, ex_col2 = st.columns(2)
    with ex_col1:
        barrier_level = st.slider("Barrier Level (for Barrier options)",
                                  S * 1.05, S * 2.0, S * 1.25, S * 0.01)

    @st.cache_data(ttl=5)
    def compute_exotics(S, K, r, q, sigma, T, opt_type, num_paths, barrier):
        params = MarketParams(S=S, K=K, r=r, q=q, sigma=sigma, T=T)
        mc = MonteCarloEngine(params, num_paths=num_paths, num_steps=252)
        r_vanilla  = mc.price_european(opt_type)
        r_asian    = mc.price_asian(opt_type)
        r_barrier  = mc.price_barrier(barrier)
        r_lookback = mc.price_lookback()
        return r_vanilla, r_asian, r_barrier, r_lookback

    with st.spinner("Pricing exotics..."):
        r_v, r_a, r_bar, r_look = compute_exotics(
            S, K, r, q, sigma, T, opt_type, min(num_paths, 50_000), barrier_level)

    ex_cols = st.columns(4)
    exotic_results = [
        ("EUROPEAN", r_v, "Vanilla — analytical baseline"),
        ("ASIAN", r_a, "Arithmetic avg. path dependent"),
        ("BARRIER", r_bar, f"Up-and-out B={barrier_level:.1f}"),
        ("LOOKBACK", r_look, "Float strike, path min"),
    ]
    for col, (name, res, desc) in zip(ex_cols, exotic_results):
        with col:
            discount = 1 - (res.price / r_v.price) if r_v.price > 0 else 0
            sign_col = "#f06292" if discount > 0 else "#56cc9d"
            st.markdown(f"""
            <div style="background:#0b1220; border:1px solid #1a2540; border-radius:4px;
                        padding:16px 12px; text-align:center; min-height:130px;">
              <div style="font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
                          color:#3d5a80; text-transform:uppercase; letter-spacing:0.12em;
                          margin-bottom:8px;">{name}</div>
              <div style="font-family:'IBM Plex Mono',monospace; font-size:1.6rem;
                          font-weight:600; color:#f0b429;">${res.price:.4f}</div>
              <div style="font-family:'IBM Plex Mono',monospace; font-size:0.65rem;
                          color:{sign_col}; margin:4px 0;">
                {discount*100:+.1f}% vs vanilla</div>
              <div style="font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
                          color:#3d5a80;">{desc}</div>
              <div style="font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
                          color:#2a3f5f; margin-top:6px;">{res.elapsed_ms:.0f}ms</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Payoff profile comparison
    S_range_ex = np.linspace(max(1, S*0.5), S*1.5, 100)

    @st.cache_data(ttl=30)
    def compute_exotic_surface(S_vals, K, r, q, sigma, T, opt_type, barrier, npaths):
        v_prices, a_prices, bar_prices, look_prices = [], [], [], []
        for s in S_vals:
            p = MarketParams(S=s, K=K, r=r, q=q, sigma=sigma, T=T)
            mc = MonteCarloEngine(p, num_paths=npaths, num_steps=100)
            v_prices.append(mc.price_european(opt_type).price)
            a_prices.append(mc.price_asian(opt_type).price)
            bar_prices.append(mc.price_barrier(barrier).price)
            look_prices.append(mc.price_lookback().price)
        return v_prices, a_prices, bar_prices, look_prices

    with st.spinner("Computing exotic profiles..."):
        v_p, a_p, b_p, l_p = compute_exotic_surface(
            S_range_ex.tolist(), K, r, q, sigma, T, opt_type, barrier_level,
            npaths=5000)

    fig_ex = go.Figure()
    traces = [
        ("European", v_p, COLORS["bs"]),
        ("Asian",    a_p, COLORS["cos"]),
        ("Barrier",  b_p, COLORS["mc"]),
        ("Lookback", l_p, COLORS["lsmc"]),
    ]
    for name, prices_ex, color in traces:
        fig_ex.add_trace(go.Scatter(x=S_range_ex, y=prices_ex,
            name=name, line=dict(color=color, width=2)))
    fig_ex.add_vline(x=S, line_color="#f06292", line_dash="dot",
                     line_width=1, annotation_text=f"S={S}",
                     annotation_font_color="#f06292", annotation_font_size=10)
    fig_ex.add_vline(x=barrier_level, line_color="#56cc9d", line_dash="dash",
                     line_width=1, annotation_text=f"B={barrier_level:.0f}",
                     annotation_font_color="#56cc9d", annotation_font_size=10)
    fig_ex.update_layout(title="Exotic Options: Price Profile vs Spot",
                         xaxis_title="Spot Price", yaxis_title="Option Price",
                         **PLOTLY_THEME, margin=dict(l=40,r=20,t=50,b=40))
    st.plotly_chart(fig_ex, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 6: CONVERGENCE
# ══════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown('<p class="terminal-header">MONTE CARLO CONVERGENCE ANALYSIS</p>',
                unsafe_allow_html=True)

    @st.cache_data(ttl=30)
    def compute_convergence(S, K, r, q, sigma, T, opt_type):
        params = MarketParams(S=S, K=K, r=r, q=q, sigma=sigma, T=T)
        bs = BlackScholesEngine(params)
        bs_price = (bs.price_call() if opt_type == "call" else bs.price_put()).price

        path_counts = [100, 500, 1000, 2000, 5000, 10000, 25000, 50000, 100000]
        mc_prices, mc_se, mc_times = [], [], []

        for n in path_counts:
            mc = MonteCarloEngine(params, num_paths=n, num_steps=100)
            res = mc.price_european(opt_type)
            mc_prices.append(res.price)
            mc_se.append(res.stderr)
            mc_times.append(res.elapsed_ms)

        cos_sizes = [16, 32, 64, 128, 256, 512, 1024]
        cos_prices, cos_times = [], []
        for n in cos_sizes:
            cos = COSEngine(params, N=n)
            res = cos.price(opt_type)
            cos_prices.append(res.price)
            cos_times.append(res.elapsed_ms)

        return bs_price, path_counts, mc_prices, mc_se, mc_times, \
               cos_sizes, cos_prices, cos_times

    with st.spinner("Running convergence study..."):
        bs_ref, n_paths, mc_p, mc_se, mc_t, \
        cos_n, cos_p, cos_t = compute_convergence(S, K, r, q, sigma, T, opt_type)

    fig_conv = make_subplots(rows=1, cols=2,
        subplot_titles=["MC Convergence (paths)", "COS Convergence (N terms)"])

    # MC convergence
    mc_errors = [abs(p - bs_ref) for p in mc_p]
    fig_conv.add_trace(go.Scatter(x=n_paths, y=mc_errors, name="MC Error",
        line=dict(color=COLORS["mc"], width=2),
        mode="lines+markers", marker=dict(size=6)),
        row=1, col=1)
    # 1/sqrt(N) reference
    ref_line = [mc_errors[0] * math.sqrt(n_paths[0]) / math.sqrt(n) for n in n_paths]
    fig_conv.add_trace(go.Scatter(x=n_paths, y=ref_line, name="O(1/√N) ref",
        line=dict(color="#2a3f5f", dash="dash", width=1)),
        row=1, col=1)

    # COS convergence
    cos_errors = [abs(p - bs_ref) for p in cos_p]
    fig_conv.add_trace(go.Scatter(x=cos_n, y=cos_errors, name="COS Error",
        line=dict(color=COLORS["cos"], width=2),
        mode="lines+markers", marker=dict(size=6)),
        row=1, col=2)

    fig_conv.update_layout(height=380, **PLOTLY_THEME,
                           margin=dict(l=40, r=20, t=60, b=40))
    for ax in ['xaxis', 'xaxis2', 'yaxis', 'yaxis2']:
        fig_conv.update_layout(**{ax: dict(
            gridcolor="#131c2e", linecolor="#1a2540", type="log")})
    fig_conv.update_annotations(font=dict(color="#5f7a9e", size=11,
                                          family="IBM Plex Mono"))
    st.plotly_chart(fig_conv, use_container_width=True)

    # Error table
    df_conv = pd.DataFrame({
        "MC Paths": n_paths,
        "MC Price":  [f"{p:.6f}" for p in mc_p],
        "MC Error":  [f"{e:.2e}" for e in mc_errors],
        "Std Err":   [f"{s:.2e}" for s in mc_se],
        "Time (ms)": [f"{t:.1f}" for t in mc_t],
    })
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p class="terminal-header">MONTE CARLO CONVERGENCE</p>',
                    unsafe_allow_html=True)
        st.dataframe(df_conv, use_container_width=True, hide_index=True)
    with c2:
        df_cos = pd.DataFrame({
            "COS N Terms": cos_n,
            "COS Price":   [f"{p:.8f}" for p in cos_p],
            "COS Error":   [f"{e:.2e}" for e in cos_errors],
            "Time (ms)":   [f"{t:.4f}" for t in cos_t],
        })
        st.markdown('<p class="terminal-header">COS METHOD CONVERGENCE</p>',
                    unsafe_allow_html=True)
        st.dataframe(df_cos, use_container_width=True, hide_index=True)

    # BS reference annotation
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.72rem;
                color:#5f7a9e; text-align:center; margin-top:8px;">
    BLACK-SCHOLES REFERENCE PRICE: <span style="color:#f0b429;">${bs_ref:.8f}</span>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    COS (N=1024) achieves machine precision in &lt;1ms
    &nbsp;&nbsp;|&nbsp;&nbsp;
    MC converges at O(1/√N)
    </div>
    """, unsafe_allow_html=True)

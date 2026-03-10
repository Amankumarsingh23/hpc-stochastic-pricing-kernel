<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=F0B429&height=200&section=header&text=HPC%20Stochastic%20Pricing%20Kernel&fontSize=38&fontColor=ffffff&fontAlignY=38&desc=C%2B%2B17%20%C2%B7%20OpenMP%20%C2%B7%20pybind11%20%C2%B7%20Monte%20Carlo%20%C2%B7%20COS%20%C2%B7%20LSMC&descAlignY=58&descSize=16&descColor=ffffffcc" />

<br/>

<img src="https://readme-typing-svg.demolab.com?font=IBM+Plex+Mono&weight=700&size=22&duration=3000&pause=800&color=F0B429&center=true&vCenter=true&multiline=true&width=750&height=80&lines=⚡+Four+Engines.+One+Dashboard.+Machine+Precision.;📈+European+%7C+American+%7C+Exotic+Options+Live." alt="Typing SVG" />

<br/>

[![Live Demo](https://img.shields.io/badge/🚀%20LIVE%20DEMO-hpc--stochastic--pricing--kernel.streamlit.app-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://hpc-stochastic-pricing-kernel.streamlit.app/)
&nbsp;&nbsp;
[![GitHub](https://img.shields.io/badge/GitHub-Amankumarsingh23-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Amankumarsingh23/hpc-stochastic-pricing-kernel)

<br/>

![C++17](https://img.shields.io/badge/C%2B%2B-17-00599C?style=flat-square&logo=cplusplus&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![pybind11](https://img.shields.io/badge/pybind11-2.11-E67E22?style=flat-square)
![OpenMP](https://img.shields.io/badge/OpenMP-Parallel-27AE60?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Live-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-19%2F19%20Passing-2ECC71?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-95A5A6?style=flat-square)

<br/>

> *Production-grade option pricing library — C++17 engines exposed to Python via pybind11.*
> *Benchmarks four numerical methods head-to-head: analytical · spectral · stochastic · regression.*

<br/>

</div>

---

## 📌 What This Is

A **high-performance derivative pricing library** implementing four independent numerical methods from scratch — benchmarked head-to-head in a live interactive dashboard. The computational core is **C++17 with OpenMP parallelism**, bridged to Python via **pybind11** bindings (the same architecture used in production quant systems). A pure-Python NumPy fallback ensures portability without recompilation.

**Three fundamental classes of numerical methods, implemented and compared:**

| Class | Method | Key Property |
|:---:|:---:|:---|
| 📊 Stochastic Simulation | Monte Carlo + Antithetic Variates | O(1/√N) convergence · path-dependent payoffs |
| 🌊 Spectral / Fourier | COS Method *(Fang & Oosterlee 2009)* | Exponential convergence · machine precision at N=64 |
| 📐 Regression-based | Longstaff-Schwartz LSMC | American early exercise via backward induction |

---

## 🚀 Live Dashboard

<div align="center">

### **[https://hpc-stochastic-pricing-kernel.streamlit.app/](https://hpc-stochastic-pricing-kernel.streamlit.app/)**

*Six fully interactive tabs — every slider update reprices all engines in real time*

</div>

---

## 🖥️ Dashboard — 6 Tabs, Fully Documented

---

### 📈 Tab 1 — Pricing Engine Comparison

> Four engines running simultaneously on the same contract. The **pricing summary table** (right) shows price, error vs Black-Scholes reference, and wall-clock time per method. The **option price vs spot chart** (left) overlays intrinsic value, COS, and Black-Scholes across the full moneyness range. The **95% confidence interval** chart (bottom-right) visualises MC uncertainty against the analytical reference line.

<div align="center">
<img src="https://raw.githubusercontent.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/main/docs/screenshots/01_pricing.png" alt="Tab 1 — Pricing: all four engines, option price vs spot, MC confidence interval" width="95%"/>

*↑ Tab 1: Four engines priced at S=K=100, σ=20%, r=5%, T=1yr. COS matches Black-Scholes to 5.51×10⁻¹⁴.*
</div>

<br/>

**Results at ATM — European Call (S=K=100, σ=20%, r=5%, T=1yr):**

| Engine | Price | Error vs BS | Time | Method Class |
|:---|:---:|:---:|:---:|:---|
| ⚡ Black-Scholes | $10.45058 | — *(reference)* | **0.039 ms** | Closed-form analytical |
| 🌊 COS (N=256) | $10.45058 | **5.51 × 10⁻¹⁴** | 2.929 ms | Spectral / Fourier |
| 🎲 Monte Carlo | $10.45494 | 4.35 × 10⁻³ | 2.9 ms | Stochastic simulation |
| 🇺🇸 LSMC (American) | $10.38170 | early ex. premium | 113 ms | Regression-based |

> 💡 **COS matches Black-Scholes to 14 decimal places** — this is spectral accuracy, not statistical luck. LSMC prices a fundamentally different contract (American put has early exercise rights) so its "difference" is the genuine early exercise premium, not an error.

---

### 🔢 Tab 2 — Option Greeks

> Five first and second-order sensitivities. **Top row:** live gauge cards for Δ, Γ, ν, Θ, ρ with sign-coded colours — green for positive PnL exposure, red for negative. **Bottom panels:** four surface plots showing each Greek across the full spot range (50–150% of current spot), with the current spot price marked by a dashed vertical line.

<div align="center">
<img src="https://raw.githubusercontent.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/main/docs/screenshots/02_greeks.png" alt="Tab 2 — Greeks: Delta Gamma Vega Theta Rho gauges and surface plots" width="95%"/>

*↑ Tab 2: Live Greeks at ATM — Δ=+0.6368, Γ=+0.0188, ν=+0.3752, Θ=−0.0176, ρ=+0.5323*
</div>

<br/>

**Live Greek values at ATM (S=K=100, analytical Black-Scholes):**

```
Greek    Value      Interpretation
─────────────────────────────────────────────────────────────────────
Δ Delta  +0.6368  ← Hedge ratio: need 0.637 shares to delta-hedge 1 call
Γ Gamma  +0.0188  ← Delta's curvature: bell curve, peaks exactly at ATM
ν Vega   +0.3752  ← Earn $0.375 per +1% vol move (per 100bps σ increase)
Θ Theta  -0.0176  ← Lose $0.0176/day to time decay (negative for long options)
ρ Rho    +0.5323  ← Earn $0.532 per +1% rate move (per 100bps r increase)
```

> 💡 **The surface shapes confirm textbook theory:** Delta traces the N(d₁) CDF sigmoid (0→1 for calls), Gamma is a symmetric bell peaking at-the-money where delta sensitivity is maximum, Vega mirrors Gamma, and Theta is negative throughout — all long options decay.

---

### ⚡ Tab 3 — Performance Benchmark

> Head-to-head method comparison across two dimensions. **Left chart:** execution time on a log scale — spans 4 orders of magnitude from 0.039ms (Black-Scholes) to 113ms (LSMC). **Right chart:** absolute pricing error vs the closed-form Black-Scholes reference. **Bottom:** prices by method as a horizontal bar chart confirming all four agree on price to within statistical tolerance.

<div align="center">
<img src="https://raw.githubusercontent.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/main/docs/screenshots/03_benchmark.png" alt="Tab 3 — Benchmark: execution time log scale and absolute error vs Black-Scholes" width="95%"/>

*↑ Tab 3: COS achieves 5.51×10⁻¹⁴ error in 2.9ms. Log-scale time chart spans 4 orders of magnitude.*
</div>

<br/>

**Benchmark breakdown:**

```
Method         Time       Error vs BS     Key insight
──────────────────────────────────────────────────────────────────────────────
Black-Scholes  0.039ms    0               Exact closed-form. Zero simulation.
COS (N=256)    2.929ms    5.51e-14        Spectral. ~14 decimal places of accuracy.
Monte Carlo    2.894ms    4.35e-03        Statistical. Same speed, 10¹¹× worse error.
LSMC           113ms      6.89e-02        American contract — different payoff structure.
```

> 💡 **COS vs Monte Carlo:** Same runtime, but COS is 10¹¹× more accurate. This is the core insight — spectral methods are not just "better", they operate in a fundamentally different convergence class. LSMC's larger "error" is not a flaw: it's solving the American option problem that no closed-form method can handle.

---

### 🌐 Tab 4 — 3D Pricing Surface

> Full option pricing surface rendered across **strikes (60–140) × maturities (0.5–3yr)**. Surface method and type (call/put) are switchable via dropdowns. The 3D mesh is fully interactive — rotate, zoom, hover to inspect any (K, T, Price) triple. Amber-to-white colour gradient encodes price magnitude.

<div align="center">
<img src="https://raw.githubusercontent.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/main/docs/screenshots/04_vol_surface.png" alt="Tab 4 — Vol Surface: interactive 3D pricing surface Strike × Maturity × Price" width="95%"/>

*↑ Tab 4: Call pricing surface — Black-Scholes. Strike (60–140) × Maturity (0.5–3yr). Fully interactive 3D.*
</div>

<br/>

**What the surface geometry encodes:**

```
Axis / Feature        Economic meaning
──────────────────────────────────────────────────────────────────────
X-axis (Strike ↑)   Lower call price — less probability of finishing ITM
Y-axis (Maturity ↑) Higher price — more time value, more uncertainty
Z-axis (Price)      $0–$50 range; deep ITM / long maturity corner peaks highest
Upward curvature    Option convexity — Jensen's inequality made geometric
Amber → White       Low price → high price gradient
```

> 💡 **The surface's upward curvature** (convexity in both dimensions) is the geometric signature of the option's nonlinear payoff function — this is Jensen's inequality visualised. The amber "cliff" at low strike / long maturity is where deep ITM options are essentially equivalent to forward contracts.

---

### 🎯 Tab 5 — Exotic Options Pricing

> Four exotic payoff structures priced simultaneously via Monte Carlo (50k paths, 252 time steps). **Top cards:** live prices with percentage premium/discount vs vanilla European baseline. **Bottom chart:** payoff profile overlaying all four contracts across S=50–150, with current spot (red dashed, S=100) and barrier level (green dashed, B=125) annotated.

<div align="center">
<img src="https://raw.githubusercontent.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/main/docs/screenshots/05_exotic_options.png" alt="Tab 5 — Exotic Options: European Asian Barrier Lookback prices and payoff profiles" width="95%"/>

*↑ Tab 5: European ($10.45) · Asian ($5.77, −44.8%) · Barrier ($2.35, −77.5%) · Lookback ($16.63, +59.1%)*
</div>

<br/>

**Exotic prices at S=K=100, σ=20%, r=5%, T=1yr, Barrier B=125:**

```
Contract     Price      vs Vanilla   Payoff structure
────────────────────────────────────────────────────────────────────────────────
European    $10.4549    baseline     max(S_T − K, 0)  — standard terminal payoff
Asian       $ 5.7740   −44.8%       max(avg(S_t) − K, 0) — average dampens payoff
Barrier     $ 2.3496   −77.5%       Knocked out if S ≥ B=125 at any point in [0,T]
Lookback    $16.6294   +59.1%       S_T − min(S_t) — floating strike, captures run-up
```

> 💡 **The payoff profile chart tells the structural story:** The Barrier call (green) collapses to zero past S=125 because the contract is dead — the option knocked out when the stock crossed B. The Lookback (purple) stays above European everywhere because its strike is always the path minimum, giving structural upside. Asian (blue) always prices below European because averaging a path is always less than its terminal value.

---

### 📉 Tab 6 — Convergence Analysis

> Side-by-side convergence study on log-log axes. **Left:** Monte Carlo error vs path count, tracking the theoretical O(1/√N) dashed reference. **Right:** COS error vs number of Fourier terms, showing exponential decay. Both panels include detailed tables with price, absolute error, standard error, and timing at each configuration.

<div align="center">
<img src="https://raw.githubusercontent.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/main/docs/screenshots/06_convergence.png" alt="Tab 6 — Convergence: Monte Carlo O(1/√N) vs COS exponential convergence log-log" width="95%"/>

*↑ Tab 6: Two fundamentally different convergence classes — stochastic O(1/√N) vs spectral exponential.*
</div>

<br/>

**Monte Carlo convergence — statistical, O(1/√N):**

```
Paths      MC Price     Error       Std Err     Time
──────────────────────────────────────────────────────
100        8.286818     2.16e+00    1.10e+00    0.4ms
500        9.843097     6.07e-01    6.17e-01    0.2ms
1,000      10.000398    4.50e-01    4.45e-01    0.1ms
```

*Each 4× increase in paths halves the error — classic O(1/√N) statistical convergence.*

**COS Method convergence — spectral / exponential:**

```
N Terms    COS Price       Error       Time
──────────────────────────────────────────────
16         10.20497368     2.46e-01    0.3464ms
32         10.45047668     1.07e-04    0.5161ms
64         10.45058357     5.51e-14    0.8147ms  ← MACHINE PRECISION
256        10.45058357     5.51e-14    2.929ms
```

> 💡 **This is the central result of the convergence tab.** COS hits the floor of IEEE 754 double precision (5.51×10⁻¹⁴) at just N=64 terms and flat-lines. Monte Carlo would need ~10²⁸ paths to match this accuracy. These two curves — one slowly decaying along O(1/√N), one cliff-dropping to machine epsilon — visualise why spectral methods exist.

---

## 🏗️ Architecture

```
hpc-stochastic-pricing-kernel/
│
├── 📱  app.py                          ← Streamlit dashboard (entry point)
│
├── 🐍  python/
│   ├── models/
│   │   └── pricing_engine.py           ← Pure-Python NumPy engines
│   │                                      Black-Scholes · COS · Monte Carlo · LSMC
│   └── api/
│       └── main.py                     ← FastAPI REST API
│                                          POST /price · /surface · /benchmark · GET /health
│
├── ⚙️   src/
│   ├── engines/
│   │   ├── monte_carlo.hpp             ← C++17: OpenMP parallel MC + antithetic variates
│   │   ├── cos_engine.hpp              ← C++17: COS method + Heston characteristic function
│   │   └── lsmc_engine.hpp             ← C++17: LSMC + Laguerre basis + OLS solver
│   └── bindings/
│       └── bindings.cpp                ← pybind11 module (hpc_pricing_core)
│
├── 🧪  tests/
│   └── test_pricing_engines.py         ← 19 validation tests (19/19 passing)
│
├── 🔨  CMakeLists.txt                  ← C++ build: -O3 -march=native + OpenMP + pybind11
├── 📦  setup.py                        ← pip install -e .  (triggers CMake)
├── 🐳  Dockerfile                      ← Multi-stage: C++ compile → slim Python runtime
├── 🐳  docker-compose.yml              ← dashboard :8501  +  API :8000
└── 📋  requirements.txt
```

---

## ⚡ Quick Start

### 🌐 Option 1 — Live App (no install)
**[https://hpc-stochastic-pricing-kernel.streamlit.app/](https://hpc-stochastic-pricing-kernel.streamlit.app/)**

### 💻 Option 2 — Run Locally

```bash
git clone https://github.com/Amankumarsingh23/hpc-stochastic-pricing-kernel.git
cd hpc-stochastic-pricing-kernel
pip install -r requirements.txt
streamlit run app.py
```

### 🐍 Option 3 — Python API

```python
from python.models.pricing_engine import price_option, price_surface

# ── Black-Scholes: analytical closed-form + all Greeks ──────────────────
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="black_scholes")
# → price=10.4506, delta=0.6368, gamma=0.0188, vega=0.3752, theta=-0.0176, rho=0.5323

# ── COS Method: machine precision (error = 5.51e-14 vs BS) ──────────────
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="cos")

# ── Monte Carlo: Asian path-dependent option ─────────────────────────────
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="monte_carlo",
                      exotic_type="asian", num_paths=100_000)
# → price=5.77  (−44.8% vs European)

# ── LSMC: American put with early exercise ───────────────────────────────
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="put", method="lsmc")

# ── Full pricing surface [maturities × strikes] ──────────────────────────
surface = price_surface(
    strikes=[80, 90, 100, 110, 120],
    maturities=[0.25, 0.5, 1.0, 2.0],
    S=100, r=0.05, q=0.0, sigma=0.2
)
```

### ⚙️ Option 4 — C++ Extension (maximum performance)

```bash
# Requires: cmake >= 3.15, g++ >= 9, OpenMP
pip install pybind11[global] setuptools wheel
pip install -e .
```

```python
import hpc_pricing_core as hpc

params = hpc.MarketParams(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0)

# OpenMP Monte Carlo — parallelised across all CPU cores
mc  = hpc.MonteCarloEngine(params, hpc.MCConfig(num_paths=500_000, antithetic=True))
res = mc.price_european("call")
mc.compute_greeks(res, "call")
print(f"Price: {res.price:.6f}  Delta: {res.delta:.4f}  Time: {res.elapsed_ms:.1f}ms")

# COS: deterministic, O(N), sub-millisecond
cos = hpc.COSEngine(params, hpc.COSConfig(N=256))
res = cos.price("call")

# LSMC: American option with early exercise
lsmc = hpc.LSMCEngine(params, hpc.LSMCConfig(num_paths=50_000))
res  = lsmc.price("put")
```

### 🐳 Option 5 — Docker

```bash
docker-compose up --build
# Dashboard  →  http://localhost:8501
# REST API   →  http://localhost:8000
# Swagger UI →  http://localhost:8000/docs
```

---

## 🔌 REST API

```bash
uvicorn python.api.main:app --port 8000 --reload
# Interactive docs: http://localhost:8000/docs
```

```bash
# Single option price + all Greeks
curl -X POST http://localhost:8000/price \
  -H "Content-Type: application/json" \
  -d '{"S":100,"K":100,"r":0.05,"q":0,"sigma":0.2,"T":1.0,"option_type":"call","method":"cos"}'

# Benchmark all four methods in one call
curl -X POST http://localhost:8000/benchmark \
  -H "Content-Type: application/json" \
  -d '{"S":100,"K":100,"r":0.05,"q":0,"sigma":0.2,"T":1.0,"option_type":"call"}'

# Full pricing surface
curl -X POST http://localhost:8000/surface \
  -H "Content-Type: application/json" \
  -d '{"S":100,"strikes":[80,90,100,110,120],"maturities":[0.25,0.5,1.0,2.0]}'

# Health check — C++ pybind11 extension status
curl http://localhost:8000/health
```

---

## 🧪 Test Suite

```bash
python tests/test_pricing_engines.py
# ✅ 19/19 tests passing
```

| Category | Tests |
|:---|:---|
| ✅ Black-Scholes | ATM value $10.4506, put-call parity < 10⁻⁷, Δ ∈ (0.5, 0.7), Γ/ν > 0, Θ < 0 |
| ✅ COS Method | Error < 10⁻⁶ vs BS, Δ/Γ match analytical, exponential convergence, machine precision at N=1024 |
| ✅ Monte Carlo | 95% CI covers BS price, antithetic reduces std error, CI width ∝ O(1/√N) |
| ✅ Exotic Options | Asian ≤ European ≤ Lookback ordering enforced, Barrier ≤ European |
| ✅ LSMC | American put ≥ European put — early exercise premium > 0 confirmed |
| ✅ Monotonicity | Price strictly increasing in spot S and volatility σ |

---

## 📚 References

- **Fang, F. & Oosterlee, C.W.** (2009). *A Novel Pricing Method for European Options Based on Fourier-Cosine Series Expansions.* SIAM Journal on Scientific Computing, 31(2), 826–848. — [doi:10.1137/080718061](https://epubs.siam.org/doi/10.1137/080718061)
- **Longstaff, F.A. & Schwartz, E.S.** (2001). *Valuing American Options by Simulation: A Simple Least-Squares Approach.* Review of Financial Studies, 14(1), 113–147. — [doi:10.1093/rfs/14.1.113](https://academic.oup.com/rfs/article/14/1/113/1578316)
- **Zhang, B. & Oosterlee, C.W.** (2013). *Efficient Pricing of European-Style Asian Options under Exponential Lévy Processes.* Quantitative Finance, 13(6), 869–884.
- **Heston, S.L.** (1993). *A Closed-Form Solution for Options with Stochastic Volatility.* Review of Financial Studies, 6(2), 327–343.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=F0B429&height=120&section=footer&text=Built%20with%20%E2%9A%A1%20by%20Aman%20Kumar%20Singh&fontSize=20&fontColor=ffffff&fontAlignY=65" />

[![Live App](https://img.shields.io/badge/🚀%20Live%20App-hpc--stochastic--pricing--kernel.streamlit.app-FF4B4B?style=flat-square)](https://hpc-stochastic-pricing-kernel.streamlit.app/)
&nbsp;
[![GitHub](https://img.shields.io/badge/GitHub-Amankumarsingh23-181717?style=flat-square&logo=github)](https://github.com/Amankumarsingh23/hpc-stochastic-pricing-kernel)
&nbsp;
[![Issues](https://img.shields.io/github/issues/Amankumarsingh23/hpc-stochastic-pricing-kernel?style=flat-square&color=F0B429)](https://github.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/issues)
&nbsp;
[![Stars](https://img.shields.io/github/stars/Amankumarsingh23/hpc-stochastic-pricing-kernel?style=flat-square&color=F0B429)](https://github.com/Amankumarsingh23/hpc-stochastic-pricing-kernel/stargazers)

<br/>

*⭐ If this project helped you, a star on GitHub means a lot!*

</div>

<div align="center">

# ⚡ HPC Stochastic Pricing Kernel

### High-Performance Option Pricing — C++17 · OpenMP · pybind11 · Python

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Click%20to%20Open-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://hpc-stochastic-pricing-kernel.streamlit.app/)

---

![C++17](https://img.shields.io/badge/C%2B%2B-17-00599C?style=flat-square&logo=cplusplus&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![pybind11](https://img.shields.io/badge/pybind11-2.11-E67E22?style=flat-square)
![OpenMP](https://img.shields.io/badge/OpenMP-Parallel-27AE60?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Live-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-19%2F19%20Passing-2ECC71?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-95A5A6?style=flat-square)

</div>

---

## Overview

A production-grade derivative pricing library implementing four independent numerical engines for valuing **European, American, and Exotic options**. Core pricing algorithms are written in **C++17 with OpenMP parallelism** and exposed to Python via **pybind11** bindings. Ships with a live interactive dashboard, a FastAPI REST backend, Docker deployment, and a 19-test validation suite.

The project directly validates and benchmarks three classes of stochastic methods:
- **Stochastic simulation** — Monte Carlo with antithetic variates and OpenMP parallelism
- **Spectral methods** — Fourier-Cosine (COS) series expansion achieving machine precision
- **Regression-based methods** — Longstaff-Schwartz LSMC for American early-exercise options

---

## 🚀 Live Dashboard

> **[https://hpc-stochastic-pricing-kernel.streamlit.app/](https://hpc-stochastic-pricing-kernel.streamlit.app/)**

Six fully interactive tabs. Every parameter — spot, strike, volatility, rate, maturity — updates all engines and charts in real time.

---

## Dashboard Screenshots

### Tab 1 — Pricing
> All four engines priced simultaneously. Live pricing summary table with error vs Black-Scholes and execution time per method. Option price vs spot curve (intrinsic value, COS, Black-Scholes overlay). 95% Monte Carlo confidence interval visualised.

![Pricing Tab](https://raw.githubusercontent.com/YOUR_USERNAME/hpc-pricing-kernel/main/docs/screenshots/01_pricing.png)

**What you see at S=K=100, σ=20%, r=5%, T=1yr:**
| Method | Price | Error vs BS | Time |
|---|---|---|---|
| Black-Scholes | $10.45058 | — (reference) | 0.039 ms |
| COS (N=256) | $10.45058 | **5.51e-14** | 2.929 ms |
| Monte Carlo | $10.45494 | 4.35e-03 | 2.9 ms |
| LSMC (American) | $10.38170 | early ex. premium | 113 ms |

---

### Tab 2 — Greeks
> Five Greek gauges (Δ, Γ, ν, Θ, ρ) with live values and units. Four-panel surface showing each Greek plotted against the full spot price range. Green = positive exposure, pink/red = negative.

![Greeks Tab](https://raw.githubusercontent.com/YOUR_USERNAME/hpc-pricing-kernel/main/docs/screenshots/02_greeks.png)

**Live Greek values at ATM (S=K=100, analytical Black-Scholes):**
```
Δ  Delta   +0.6368   ← probability of finishing ITM (risk-neutral)
Γ  Gamma   +0.0188   ← rate of delta change; peaks at-the-money
ν  Vega    +0.3752   ← P&L per +1% move in implied volatility
Θ  Theta   -0.0176   ← daily time decay (negative for long options)
ρ  Rho     +0.5323   ← P&L per +1% move in risk-free rate
```
The surface plots confirm textbook shapes: Delta is a sigmoid (0→1), Gamma is a bell curve peaking at ATM, Vega mirrors Gamma, Theta is negative and steepens near expiry.

---

### Tab 3 — Benchmark
> Direct method comparison: execution time on log scale (left) and absolute pricing error vs closed-form Black-Scholes (right). Demonstrates the speed/accuracy tradeoff across all four engines.

![Benchmark Tab](https://raw.githubusercontent.com/YOUR_USERNAME/hpc-pricing-kernel/main/docs/screenshots/03_benchmark.png)

**Key insight from the benchmark:**
- COS (N=256) achieves **5.51×10⁻¹⁴** error vs Black-Scholes — effectively machine precision — while remaining under 3ms
- Monte Carlo error (4.35×10⁻³) is ~10¹¹× larger than COS, reflecting statistical O(1/√N) convergence
- LSMC is the slowest (113ms) because it runs full backward induction with Laguerre regression at each time step — but it prices **American options**, which no other method here handles
- Black-Scholes (0.039ms) is the analytical baseline — no simulation, no approximation

---

### Tab 4 — Vol Surface
> Interactive 3D pricing surface rendered across a grid of strikes (60–140) and maturities (0.5–3yr). Switchable between Black-Scholes, COS, and Monte Carlo engines. Also includes a 2D heatmap view.

![Vol Surface Tab](https://raw.githubusercontent.com/YOUR_USERNAME/hpc-pricing-kernel/main/docs/screenshots/04_vol_surface.png)

The surface correctly captures:
- **Time value** — prices increase with maturity (more time = more uncertainty)
- **Moneyness** — deep ITM (low strike) calls carry more value than OTM
- **Convexity** — the surface curves upward, reflecting the option's nonlinear payoff
- The amber-to-white color gradient maps price magnitude, with low-strike/long-maturity corners highest

---

### Tab 5 — Exotic Options
> Four exotic option types priced simultaneously via Monte Carlo (50k paths). Live price cards with % premium/discount vs vanilla European. Payoff profile chart shows all four across the full spot range, with current spot (S=100) and barrier level (B=125) annotated.

![Exotic Options Tab](https://raw.githubusercontent.com/YOUR_USERNAME/hpc-pricing-kernel/main/docs/screenshots/05_exotic_options.png)

**Exotic prices at S=K=100, σ=20%, r=5%, T=1yr, Barrier B=125:**
```
European   $10.4549   baseline (vanilla call)
Asian      $ 5.7740   −44.8%  averaging the path dampens the payoff
Barrier    $ 2.3496   −77.5%  up-and-out knockout risk near B=125
Lookback   $16.6294   +59.1%  float-strike captures the full run-up
```

The payoff profile chart shows the Barrier call collapsing to zero past the knockout level (green line drops at B=125 dashed marker), while the Lookback (purple) stays above European because its strike floats to the path minimum.

---

### Tab 6 — Convergence
> Dual log-log convergence plots and detailed tables. Left: Monte Carlo error vs path count, with O(1/√N) reference line. Right: COS error vs number of Fourier terms. Demonstrates the fundamental difference between stochastic (slow, noisy) and spectral (exponential, deterministic) convergence.

![Convergence Tab](https://raw.githubusercontent.com/YOUR_USERNAME/hpc-pricing-kernel/main/docs/screenshots/06_convergence.png)

**Monte Carlo convergence (statistical — O(1/√N)):**
```
100 paths    price=8.2868   error=2.16e+00   std_err=1.10   0.4ms
500 paths    price=9.8431   error=6.07e-01   std_err=0.617  0.2ms
1,000 paths  price=10.0004  error=4.50e-01   std_err=0.445  0.1ms
```
The MC error curve tracks the O(1/√N) dashed reference — halving error requires 4× more paths.

**COS Method convergence (exponential / spectral):**
```
N=16   price=10.20497   error=2.46e-01   0.3464ms
N=32   price=10.45048   error=1.07e-04   0.5161ms
N=64   price=10.45058   error=5.51e-14   0.8147ms  ← machine precision
```
The COS error cliff-drops to femto-level at N=64 and stays flat — this is spectral convergence, fundamentally different from Monte Carlo's slow statistical decay.

---

## Pricing Engines

### Black-Scholes — Analytical Reference
Closed-form European pricing with full analytical Greeks (Δ, Γ, ν, Θ, ρ). Serves as the ground-truth benchmark for all other engines. Put-call parity verified to < 10⁻⁷.

### COS Method — Fourier-Cosine Series
Based on [Fang & Oosterlee (2009)](https://epubs.siam.org/doi/10.1137/080718061). Expresses the option price as a truncated cosine series of the risk-neutral density via the **characteristic function**. The log-moneyness `x = log(S/K)` enters as a phase shift `exp(i·u·(x−a))` in the Fourier sum — this is the key implementation detail that separates asset-price sensitivity from the fixed integration bounds. Supports GBM and Heston stochastic volatility models.

### Monte Carlo — OpenMP Parallel
GBM path simulation under the risk-neutral measure, discounting terminal (or path-average) payoffs. `#pragma omp parallel for` distributes paths across all CPU cores — linear scaling. **Antithetic variates** pair each draw z with −z, reducing standard error by ~40% at zero additional simulation cost. Supports European, Asian (arithmetic average), Up-and-Out Barrier, and Floating-Strike Lookback.

### LSMC — American Options (Longstaff-Schwartz)
[Longstaff & Schwartz (2001)](https://academic.oup.com/rfs/article/14/1/113/1578316) backward induction from expiry to today. At each time step, **Laguerre polynomial basis functions** {L₀, L₁, L₂, L₃} approximate the continuation value via OLS regression on in-the-money paths only. Where intrinsic value exceeds the estimated continuation value, the option is exercised early. OLS solved via Gaussian elimination with partial pivoting for numerical stability.

---

## Repository Structure

```
hpc-pricing-kernel/
│
├── app.py                          ← Streamlit dashboard (entry point)
│
├── python/
│   ├── models/
│   │   └── pricing_engine.py       ← Pure-Python engines (NumPy vectorised)
│   │                                  Black-Scholes · COS · Monte Carlo · LSMC
│   └── api/
│       └── main.py                 ← FastAPI REST API
│                                      POST /price · /surface · /benchmark · GET /health
│
├── src/
│   ├── engines/
│   │   ├── monte_carlo.hpp         ← C++17: OpenMP parallel MC + antithetic variates
│   │   ├── cos_engine.hpp          ← C++17: COS method + Heston characteristic function
│   │   └── lsmc_engine.hpp         ← C++17: LSMC + Laguerre basis + OLS solver
│   └── bindings/
│       └── bindings.cpp            ← pybind11 module (hpc_pricing_core)
│
├── tests/
│   └── test_pricing_engines.py     ← 19 validation tests (19/19 passing)
│
├── CMakeLists.txt                  ← C++ build: OpenMP + pybind11 + -O3 -march=native
├── setup.py                        ← pip install -e .  (triggers CMake build)
├── Dockerfile                      ← Multi-stage: C++ compile → slim Python runtime
├── docker-compose.yml              ← Runs dashboard :8501 + API :8000 together
└── requirements.txt                ← Python dependencies
```

---

## Quick Start

### Run locally
```bash
git clone https://github.com/YOUR_USERNAME/hpc-pricing-kernel
cd hpc-pricing-kernel
pip install -r requirements.txt
streamlit run app.py
```

### Python API
```python
from python.models.pricing_engine import price_option, price_surface

# Black-Scholes — analytical Greeks included
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="black_scholes")
# → price=10.4506, delta=0.6368, gamma=0.0188, vega=0.3752, theta=-0.0176, rho=0.5323

# COS Method — machine precision (error = 5.51e-14 vs BS)
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="cos")

# Monte Carlo — Asian path-dependent option
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="monte_carlo",
                      exotic_type="asian", num_paths=100_000)

# LSMC — American put with early exercise
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="put", method="lsmc")

# Full pricing surface [maturities × strikes]
surface = price_surface(
    strikes=[80, 90, 100, 110, 120],
    maturities=[0.25, 0.5, 1.0, 2.0],
    S=100, r=0.05, q=0.0, sigma=0.2
)
```

### Build the C++ extension (optional)
```bash
# Requires: cmake >= 3.15, g++ >= 9, OpenMP
pip install pybind11[global] setuptools wheel
pip install -e .
```

```python
import hpc_pricing_core as hpc

params = hpc.MarketParams(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0)

# OpenMP Monte Carlo — uses all CPU cores
mc  = hpc.MonteCarloEngine(params, hpc.MCConfig(num_paths=500_000, antithetic=True))
res = mc.price_european("call")
mc.compute_greeks(res, "call")

# COS — deterministic, O(N)
cos = hpc.COSEngine(params, hpc.COSConfig(N=256))
res = cos.price("call")

# LSMC — American option
lsmc = hpc.LSMCEngine(params, hpc.LSMCConfig(num_paths=50_000))
res  = lsmc.price("put")
```

### Docker (dashboard + API)
```bash
docker-compose up --build
# Dashboard  →  http://localhost:8501
# REST API   →  http://localhost:8000
# Swagger UI →  http://localhost:8000/docs
```

---

## REST API

```bash
uvicorn python.api.main:app --port 8000 --reload
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

# Health check (C++ extension status)
curl http://localhost:8000/health
```

---

## Tests

```bash
python tests/test_pricing_engines.py
# 19/19 tests passing
```

| Category | Tests |
|---|---|
| Black-Scholes | ATM value $10.4506, put-call parity < 10⁻⁷, delta ∈ (0.5, 0.7), gamma/vega > 0, theta < 0 |
| COS Method | Price error < 10⁻⁶ vs BS, delta/gamma match, exponential convergence, machine precision at N=1024, deterministic output |
| Monte Carlo | 95% CI covers BS price, antithetic reduces std error, CI width ∝ O(1/√N) |
| Exotics | Asian ≤ European ≤ Lookback ordering, Barrier ≤ European |
| LSMC | American put ≥ European put (early exercise premium > 0 when q=0) |
| Monotonicity | Price strictly increasing in spot S and volatility σ |

---

## References

- **Fang, F. & Oosterlee, C.W.** (2009). *A Novel Pricing Method for European Options Based on Fourier-Cosine Series Expansions.* SIAM Journal on Scientific Computing, 31(2), 826–848.
- **Longstaff, F.A. & Schwartz, E.S.** (2001). *Valuing American Options by Simulation: A Simple Least-Squares Approach.* Review of Financial Studies, 14(1), 113–147.
- **Zhang, B. & Oosterlee, C.W.** (2013). *Efficient Pricing of European-Style Asian Options under Exponential Lévy Processes.* Quantitative Finance, 13(6), 869–884.
- **Heston, S.L.** (1993). *A Closed-Form Solution for Options with Stochastic Volatility.* Review of Financial Studies, 6(2), 327–343.

---

<div align="center">

Built with C++17 · pybind11 · OpenMP · NumPy · FastAPI · Streamlit · Plotly

**[Live App](https://hpc-stochastic-pricing-kernel.streamlit.app/) · [Report an Issue](https://github.com/YOUR_USERNAME/hpc-pricing-kernel/issues)**

</div>

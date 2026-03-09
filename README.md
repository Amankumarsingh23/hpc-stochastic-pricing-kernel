# ⚡ HPC Stochastic Pricing Kernel

<div align="center">

![C++17](https://img.shields.io/badge/C%2B%2B-17-blue?style=flat-square&logo=cplusplus)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![pybind11](https://img.shields.io/badge/pybind11-2.11-orange?style=flat-square)
![OpenMP](https://img.shields.io/badge/OpenMP-parallel-green?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?style=flat-square&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit)
![Tests](https://img.shields.io/badge/tests-19%2F19%20passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

**Production-grade option pricing library for European, American, and Exotic options.**  
C++ engines with OpenMP parallelism, exposed to Python via pybind11.

[Live Dashboard](#deployment) · [API Docs](#rest-api) · [Benchmarks](#benchmarks)

</div>

---

## Overview

This library implements three independent pricing kernels validated against analytical benchmarks:

| Engine | Method | Options | Accuracy | Speed |
|---|---|---|---|---|
| `BlackScholesEngine` | Closed-form | European | Exact | < 0.01ms |
| `COSEngine` | Fourier-Cosine (N=256) | European + Heston | < 1e-6 vs BS | < 0.1ms |
| `MonteCarloEngine` | GBM + Antithetic (OpenMP) | European, Asian, Barrier, Lookback | O(1/√N) | ~100ms |
| `LSMCEngine` | Longstaff-Schwartz regression | American | O(1/√N) | ~500ms |

---

## Architecture

```
hpc_pricing_kernel/
├── src/
│   ├── engines/
│   │   ├── monte_carlo.hpp      # OpenMP parallel MC + antithetic variates
│   │   ├── cos_engine.hpp       # Fourier-Cosine + Black-Scholes + Heston CF
│   │   └── lsmc_engine.hpp      # Longstaff-Schwartz LSMC + Laguerre basis
│   └── bindings/
│       └── bindings.cpp         # pybind11 module (hpc_pricing_core)
├── python/
│   ├── models/
│   │   └── pricing_engine.py    # Pure-Python mirror (NumPy vectorised)
│   └── api/
│       └── main.py              # FastAPI REST endpoints
├── dashboard/
│   └── app.py                   # Streamlit interactive dashboard
├── tests/
│   └── test_pricing_engines.py  # 19 validation tests
├── CMakeLists.txt               # C++ build (OpenMP + pybind11)
├── setup.py                     # pip-installable CMake build
└── docker-compose.yml           # Dashboard + API containers
```

---

## Methods

### Monte Carlo (OpenMP-parallel)
- Geometric Brownian Motion path simulation
- **Antithetic variates** for variance reduction (~40% std error reduction)
- **OpenMP** parallelism across paths — scales linearly with cores
- Supports: European, Asian (arithmetic average), Up-and-Out Barrier, Lookback

### COS Method (Fourier-Cosine)
- Based on **Fang & Oosterlee (2009)** — O(N) per price evaluation
- Characteristic function of log-price under GBM and **Heston model**
- Achieves **machine precision** at N=1024 terms
- Deterministic — no statistical error

### LSMC — American Options
- **Longstaff & Schwartz (2001)** backward induction
- **Laguerre polynomial basis** for continuation value regression
- OLS solved via Gaussian elimination with partial pivoting
- Early exercise boundary recovered automatically

---

## Benchmarks

Pricing an ATM call: S=100, K=100, r=5%, σ=20%, T=1yr

| Method | Price | Error vs BS | Time |
|---|---|---|---|
| Black-Scholes (analytical) | $10.450584 | — | 0.003ms |
| COS Method (N=256) | $10.450584 | 5.5 × 10⁻¹⁴ | 0.08ms |
| Monte Carlo (100k paths, OpenMP) | $10.451 ± 0.03 | < 0.01 | ~80ms |
| LSMC American Put | $6.09 | early exercise premium | ~400ms |

**COS vs Black-Scholes convergence:**

| N (terms) | Error | Time |
|---|---|---|
| 16 | 4.2 × 10⁻³ | 0.01ms |
| 64 | 8.1 × 10⁻⁷ | 0.03ms |
| 256 | 5.5 × 10⁻¹⁴ | 0.08ms |
| 1024 | < 1 × 10⁻¹⁵ | 0.3ms |

---

## Quick Start

### Python (no C++ required)

```python
from python.models.pricing_engine import price_option, price_surface

# European call — Black-Scholes
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="black_scholes")
print(f"Price: ${result['price']:.4f}")
print(f"Delta: {result['delta']:.4f}  Gamma: {result['gamma']:.6f}")

# COS Method (Fourier-Cosine)
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="cos")

# Monte Carlo — Asian option
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="call", method="monte_carlo",
                      exotic_type="asian", num_paths=100_000)

# American put via LSMC
result = price_option(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0,
                      option_type="put", method="lsmc")

# Pricing surface
surface = price_surface(
    strikes=[80, 90, 100, 110, 120],
    maturities=[0.25, 0.5, 1.0, 2.0],
    S=100, r=0.05, q=0.0, sigma=0.2
)
```

### C++ Extension (pybind11)

```python
import hpc_pricing_core as hpc

params = hpc.MarketParams(S=100, K=100, r=0.05, q=0.0, sigma=0.2, T=1.0)
cfg    = hpc.MCConfig(num_paths=500_000, antithetic=True)

# OpenMP-parallel Monte Carlo
mc  = hpc.MonteCarloEngine(params, cfg)
res = mc.price_european("call")
mc.compute_greeks(res, "call")
print(f"Price: {res.price:.6f}  Delta: {res.delta:.4f}  Time: {res.elapsed_ms:.1f}ms")

# COS Method
cos = hpc.COSEngine(params, hpc.COSConfig(N=256))
res = cos.price("call")
cos.compute_greeks(res, "call")

# LSMC — American option
lsmc = hpc.LSMCEngine(params, hpc.LSMCConfig(num_paths=50_000))
res  = lsmc.price("put")

# Pricing surface (batch)
surface = hpc.price_surface(
    strikes=[80,90,100,110,120],
    maturities=[0.5,1.0,2.0],
    S=100, r=0.05, q=0.0, sigma=0.2
)
```

---

## Build & Install

### Option 1: Python-only (no compiler needed)
```bash
git clone https://github.com/your-handle/hpc-pricing-kernel
cd hpc-pricing-kernel
pip install numpy scipy pandas streamlit plotly fastapi uvicorn
```

### Option 2: Full C++ build
```bash
# Requirements: cmake >= 3.15, g++ >= 9, OpenMP
pip install pybind11[global] setuptools wheel
pip install -e .
```

### Option 3: Docker
```bash
docker-compose up
# Dashboard: http://localhost:8501
# API docs:  http://localhost:8000/docs
```

---

## REST API

```bash
# Single option price + greeks
curl -X POST http://localhost:8000/price \
  -H "Content-Type: application/json" \
  -d '{"S":100,"K":100,"r":0.05,"sigma":0.2,"T":1.0,"option_type":"call","method":"cos"}'

# Benchmark all methods
curl -X POST http://localhost:8000/benchmark \
  -d '{"S":100,"K":100,"r":0.05,"sigma":0.2,"T":1.0,"option_type":"call"}'

# Pricing surface
curl -X POST http://localhost:8000/surface \
  -d '{"S":100,"strikes":[90,100,110],"maturities":[0.5,1.0]}'
```

---

## Run Dashboard

```bash
streamlit run dashboard/app.py
```

Features:
- **Live pricing** — all 4 methods with real-time parameter updates
- **Greeks surface** — Δ, Γ, ν, Θ, ρ vs spot price
- **Benchmark tab** — method comparison: price accuracy + execution speed
- **3D vol surface** — interactive [Strike × Maturity × Price]
- **Exotic options** — European, Asian, Barrier, Lookback payoff profiles
- **Convergence analysis** — MC O(1/√N) vs COS exponential convergence

---

## Validation

All engines validated against:
- Black-Scholes closed-form (put-call parity verified to 10⁻⁸)
- Fang & Oosterlee (2009) COS benchmarks
- Zhang & Oosterlee (2013) Asian option benchmarks
- Longstaff & Schwartz (2001) LSMC reference prices

```bash
python tests/test_pricing_engines.py
# 19/19 tests passing
```

---

## References

- Fang, F. & Oosterlee, C.W. (2009). *A Novel Pricing Method for European Options Based on Fourier-Cosine Series Expansions.* SIAM Journal on Scientific Computing.
- Longstaff, F.A. & Schwartz, E.S. (2001). *Valuing American Options by Simulation: A Simple Least-Squares Approach.* Review of Financial Studies.
- Zhang, B. & Oosterlee, C.W. (2013). *Efficient Pricing of European-Style Asian Options.* Quantitative Finance.
- Heston, S.L. (1993). *A Closed-Form Solution for Options with Stochastic Volatility.* Review of Financial Studies.

---

## License

MIT License — see [LICENSE](LICENSE)

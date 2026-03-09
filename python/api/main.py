"""
python/api/main.py
─────────────────────────────────────────────────────────────
FastAPI REST API for HPC Stochastic Pricing Kernel
Endpoints:
  POST /price          → single option price + greeks
  POST /surface        → full pricing surface
  POST /benchmark      → compare methods + timing
  GET  /health         → service status
"""
from __future__ import annotations
import time
import sys
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# Try C++ extension first, fall back to Python
try:
    sys.path.insert(0, ".")
    import hpc_pricing_core as _cpp
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False

from python.models.pricing_engine import (
    MarketParams, price_option, price_surface,
    BlackScholesEngine, COSEngine, MonteCarloEngine, LSMCEngine
)

# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="HPC Stochastic Pricing Kernel",
    description="High-performance option pricing: Monte Carlo (OpenMP), COS Method, LSMC",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
#  Request / Response schemas
# ─────────────────────────────────────────────────────────────
class PriceRequest(BaseModel):
    S: float = Field(100.0, ge=0.01, description="Spot price")
    K: float = Field(100.0, ge=0.01, description="Strike price")
    r: float = Field(0.05,  ge=0.0,  description="Risk-free rate")
    q: float = Field(0.0,   ge=0.0,  description="Dividend yield")
    sigma: float = Field(0.2, gt=0.0, description="Volatility")
    T: float = Field(1.0,   gt=0.0,  description="Time to maturity (years)")
    option_type: Literal["call", "put"] = "call"
    method: Literal["black_scholes", "cos", "monte_carlo", "lsmc"] = "black_scholes"
    exotic_type: Optional[Literal["european", "asian", "barrier", "lookback"]] = "european"
    barrier: Optional[float] = Field(None, description="Barrier level (for barrier options)")
    compute_greeks: bool = True
    num_paths: int = Field(50_000, ge=1000, le=1_000_000)
    num_steps: int = Field(100,    ge=10,   le=1000)
    cos_N: int = Field(256, ge=16, le=2048)


class SurfaceRequest(BaseModel):
    S:       float = 100.0
    r:       float = 0.05
    q:       float = 0.0
    sigma:   float = 0.2
    strikes:    list[float] = Field(default_factory=lambda: [80,90,95,100,105,110,120])
    maturities: list[float] = Field(default_factory=lambda: [0.25, 0.5, 1.0, 2.0])
    method:     Literal["black_scholes", "cos", "monte_carlo"] = "black_scholes"
    option_type: Literal["call", "put"] = "call"


class BenchmarkRequest(BaseModel):
    S: float = 100.0
    K: float = 100.0
    r: float = 0.05
    q: float = 0.0
    sigma: float = 0.2
    T: float = 1.0
    option_type: Literal["call", "put"] = "call"
    num_paths: int = Field(50_000, ge=1000, le=500_000)


class PriceResponse(BaseModel):
    price:      float
    stderr:     float
    ci_low:     float
    ci_high:    float
    delta:      float
    gamma:      float
    vega:       float
    theta:      float
    rho:        float
    elapsed_ms: float
    method:     str
    cpp_used:   bool


# ─────────────────────────────────────────────────────────────
#  Endpoints
# ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "cpp_extension": CPP_AVAILABLE,
        "version": "1.0.0"
    }


@app.post("/price", response_model=PriceResponse)
def price_endpoint(req: PriceRequest):
    try:
        result = price_option(
            S=req.S, K=req.K, r=req.r, q=req.q, sigma=req.sigma, T=req.T,
            option_type=req.option_type,
            method=req.method,
            exotic_type=req.exotic_type if req.exotic_type != "european" else None,
            barrier=req.barrier,
            compute_greeks=req.compute_greeks,
            num_paths=req.num_paths,
            num_steps=req.num_steps,
            cos_N=req.cos_N,
        )
        result["method"]   = req.method
        result["cpp_used"] = CPP_AVAILABLE
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/surface")
def surface_endpoint(req: SurfaceRequest):
    try:
        surface = price_surface(
            strikes=req.strikes,
            maturities=req.maturities,
            S=req.S, r=req.r, q=req.q, sigma=req.sigma,
            method=req.method,
            option_type=req.option_type,
        )
        return {
            "strikes":    req.strikes,
            "maturities": req.maturities,
            "surface":    surface,
            "method":     req.method,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/benchmark")
def benchmark_endpoint(req: BenchmarkRequest):
    """
    Run all pricing methods on the same option, return comparative timings
    and prices. This is the data powering the benchmarking dashboard.
    """
    params = MarketParams(
        S=req.S, K=req.K, r=req.r, q=req.q, sigma=req.sigma, T=req.T
    )
    results = {}

    # Black-Scholes
    bs = BlackScholesEngine(params)
    t0 = time.perf_counter()
    r_bs = bs.price_call() if req.option_type == "call" else bs.price_put()
    r_bs.elapsed_ms = (time.perf_counter() - t0) * 1000
    results["black_scholes"] = r_bs.to_dict()

    # COS Method
    cos = COSEngine(params, N=256)
    r_cos = cos.price(req.option_type)
    cos.compute_greeks(r_cos, req.option_type)
    results["cos"] = r_cos.to_dict()

    # Monte Carlo
    mc = MonteCarloEngine(params, num_paths=req.num_paths, num_steps=100)
    r_mc = mc.price_european(req.option_type)
    mc.compute_greeks(r_mc, req.option_type)
    results["monte_carlo"] = r_mc.to_dict()

    # LSMC (American)
    lsmc = LSMCEngine(params, num_paths=min(req.num_paths, 20_000))
    r_lsmc = lsmc.price(req.option_type)
    results["lsmc"] = r_lsmc.to_dict()

    # Compute errors relative to BS
    bs_price = results["black_scholes"]["price"]
    for method, res in results.items():
        res["error_vs_bs"] = abs(res["price"] - bs_price)
        res["error_pct"]   = 100.0 * res["error_vs_bs"] / bs_price if bs_price else 0

    return {
        "params":  {"S": req.S, "K": req.K, "r": req.r,
                    "sigma": req.sigma, "T": req.T,
                    "option_type": req.option_type},
        "results": results,
        "cpp_used": CPP_AVAILABLE,
    }

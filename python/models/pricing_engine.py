"""
python/models/pricing_engine.py
─────────────────────────────────────────────────────────────
Pure-Python pricing engine that mirrors the C++ pybind11 API.
Used as fallback when the compiled extension is not available,
and for benchmarking C++ vs Python speed.
"""
from __future__ import annotations
import time
import math
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Literal


# ─────────────────────────────────────────────────────────────
#  Data classes (mirror C++ structs)
# ─────────────────────────────────────────────────────────────
@dataclass
class MarketParams:
    S: float     # Spot price
    K: float     # Strike price
    r: float     # Risk-free rate
    q: float     # Dividend yield
    sigma: float # Volatility
    T: float     # Time to maturity


@dataclass
class PricingResult:
    price:      float = 0.0
    stderr:     float = 0.0
    ci_low:     float = 0.0
    ci_high:    float = 0.0
    delta:      float = 0.0
    gamma:      float = 0.0
    vega:       float = 0.0
    theta:      float = 0.0
    rho:        float = 0.0
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────
#  Black-Scholes Analytical (benchmark reference)
# ─────────────────────────────────────────────────────────────
class BlackScholesEngine:
    def __init__(self, params: MarketParams):
        self.p = params

    @staticmethod
    def _norm_cdf(x: float) -> float:
        return 0.5 * math.erfc(-x / math.sqrt(2))

    @staticmethod
    def _norm_pdf(x: float) -> float:
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    def _d1(self) -> float:
        p = self.p
        return (math.log(p.S / p.K) + (p.r - p.q + 0.5 * p.sigma**2) * p.T) \
               / (p.sigma * math.sqrt(p.T))

    def _d2(self) -> float:
        return self._d1() - self.p.sigma * math.sqrt(self.p.T)

    def price_call(self) -> PricingResult:
        p = self.p
        d1, d2 = self._d1(), self._d2()
        disc = math.exp(-p.r * p.T)
        fwd  = p.S * math.exp(-p.q * p.T)
        px   = fwd * self._norm_cdf(d1) - p.K * disc * self._norm_cdf(d2)
        sqT  = math.sqrt(p.T)
        nd1  = self._norm_pdf(d1)
        res = PricingResult(price=px, ci_low=px, ci_high=px)
        res.delta = math.exp(-p.q * p.T) * self._norm_cdf(d1)
        res.gamma = math.exp(-p.q * p.T) * nd1 / (p.S * p.sigma * sqT)
        res.vega  = p.S * math.exp(-p.q * p.T) * nd1 * sqT / 100.0
        res.theta = (-p.S * math.exp(-p.q * p.T) * nd1 * p.sigma / (2 * sqT)
                     - p.r * p.K * disc * self._norm_cdf(d2)
                     + p.q * p.S * math.exp(-p.q * p.T) * self._norm_cdf(d1)) / 365.0
        res.rho   = p.K * p.T * disc * self._norm_cdf(d2) / 100.0
        return res

    def price_put(self) -> PricingResult:
        p = self.p
        d1, d2 = self._d1(), self._d2()
        disc = math.exp(-p.r * p.T)
        fwd  = p.S * math.exp(-p.q * p.T)
        px   = p.K * disc * self._norm_cdf(-d2) - fwd * self._norm_cdf(-d1)
        sqT  = math.sqrt(p.T)
        nd1  = self._norm_pdf(d1)
        res = PricingResult(price=px, ci_low=px, ci_high=px)
        res.delta = -math.exp(-p.q * p.T) * self._norm_cdf(-d1)
        res.gamma = math.exp(-p.q * p.T) * nd1 / (p.S * p.sigma * sqT)
        res.vega  = p.S * math.exp(-p.q * p.T) * nd1 * sqT / 100.0
        res.theta = (-p.S * math.exp(-p.q * p.T) * nd1 * p.sigma / (2 * sqT)
                     + p.r * p.K * disc * self._norm_cdf(-d2)
                     - p.q * p.S * math.exp(-p.q * p.T) * self._norm_cdf(-d1)) / 365.0
        res.rho   = -p.K * p.T * disc * self._norm_cdf(-d2) / 100.0
        return res


# ─────────────────────────────────────────────────────────────
#  COS (Fourier-Cosine) Method — Python implementation
# ─────────────────────────────────────────────────────────────
class COSEngine:
    def __init__(self, params: MarketParams, N: int = 256, L: float = 12.0):
        self.p = params
        self.N = N
        self.L = L

    def _char_func_gbm(self, u: np.ndarray) -> np.ndarray:
        p = self.p
        mu  = (p.r - p.q - 0.5 * p.sigma**2) * p.T
        var = p.sigma**2 * p.T
        return np.exp(1j * u * mu - 0.5 * var * u**2)

    def _chi(self, k, a, b, c, d):
        kpi = k * np.pi / (b - a)
        return (np.cos(kpi * (d - a)) * np.exp(d)
                - np.cos(kpi * (c - a)) * np.exp(c)
                + kpi * np.sin(kpi * (d - a)) * np.exp(d)
                - kpi * np.sin(kpi * (c - a)) * np.exp(c)) / (1 + kpi**2)

    def _psi(self, k, a, b, c, d):
        if k == 0:
            return d - c
        kpi = k * np.pi / (b - a)
        return (np.sin(kpi * (d - a)) - np.sin(kpi * (c - a))) / kpi

    def price(self, option_type: str = "call") -> PricingResult:
        t0 = time.perf_counter()
        p = self.p
        is_call = option_type == "call"
        # x = log(S/K) enters as shift in char func, NOT in bounds (Fang & Oosterlee 2009)
        x  = math.log(p.S / p.K)
        c1 = (p.r - p.q - 0.5 * p.sigma**2) * p.T
        c2 = p.sigma**2 * p.T
        a  = c1 - self.L * math.sqrt(abs(c2))
        b  = c1 + self.L * math.sqrt(abs(c2))

        k_arr = np.arange(self.N)
        u_arr = k_arr * np.pi / (b - a)
        phi   = self._char_func_gbm(u_arr)
        terms = phi * np.exp(1j * u_arr * (x - a))

        if is_call:
            Vk = np.array([2.0 / (b-a) * (self._chi(k, a, b, 0, b) - self._psi(k, a, b, 0, b))
                           for k in k_arr])
        else:
            Vk = np.array([2.0 / (b-a) * (-self._chi(k, a, b, a, 0) + self._psi(k, a, b, a, 0))
                           for k in k_arr])

        weights = np.ones(self.N); weights[0] = 0.5
        total = float(np.sum(weights * np.real(terms) * Vk))
        px = math.exp(-p.r * p.T) * p.K * total
        intrinsic = max(p.S - p.K * math.exp(-p.r * p.T), 0.0) if is_call \
               else max(p.K * math.exp(-p.r * p.T) - p.S, 0.0)
        px = max(px, intrinsic)

        elapsed = (time.perf_counter() - t0) * 1000
        return PricingResult(price=px, ci_low=px, ci_high=px, elapsed_ms=elapsed)

    def compute_greeks(self, res: PricingResult, option_type: str) -> None:
        p = self.p
        dS = p.S * 0.005
        pu = MarketParams(p.S+dS, p.K, p.r, p.q, p.sigma, p.T)
        pd = MarketParams(p.S-dS, p.K, p.r, p.q, p.sigma, p.T)
        Vu = COSEngine(pu, self.N, self.L).price(option_type).price
        Vd = COSEngine(pd, self.N, self.L).price(option_type).price
        res.delta = (Vu - Vd) / (2 * dS)
        res.gamma = (Vu - 2*res.price + Vd) / (dS**2)

        dsig = 0.001
        pv = MarketParams(p.S, p.K, p.r, p.q, p.sigma+dsig, p.T)
        res.vega = (COSEngine(pv, self.N, self.L).price(option_type).price - res.price) / dsig / 100

        dT = 1/365
        if p.T > dT:
            pt = MarketParams(p.S, p.K, p.r, p.q, p.sigma, p.T-dT)
            res.theta = (COSEngine(pt, self.N, self.L).price(option_type).price - res.price) / dT / 365

        dr = 0.0001
        pr = MarketParams(p.S, p.K, p.r+dr, p.q, p.sigma, p.T)
        res.rho = (COSEngine(pr, self.N, self.L).price(option_type).price - res.price) / dr / 100


# ─────────────────────────────────────────────────────────────
#  Monte Carlo Engine — vectorised NumPy
# ─────────────────────────────────────────────────────────────
class MonteCarloEngine:
    def __init__(self, params: MarketParams, num_paths: int = 100_000,
                 num_steps: int = 252, seed: int = 42, antithetic: bool = True):
        self.p = params
        self.num_paths = num_paths
        self.num_steps = num_steps
        self.seed = seed
        self.antithetic = antithetic

    def _simulate_terminal(self) -> np.ndarray:
        p = self.p
        rng  = np.random.default_rng(self.seed)
        dt   = p.T / self.num_steps
        mu   = (p.r - p.q - 0.5 * p.sigma**2) * p.T
        sig  = p.sigma * math.sqrt(p.T)
        M    = self.num_paths // 2 if self.antithetic else self.num_paths
        z    = rng.standard_normal(M)
        if self.antithetic:
            z = np.concatenate([z, -z])
        return p.S * np.exp(mu + sig * z)

    def _simulate_paths(self) -> np.ndarray:
        """Full path simulation for path-dependent options."""
        p = self.p
        rng  = np.random.default_rng(self.seed)
        dt   = p.T / self.num_steps
        drift = (p.r - p.q - 0.5 * p.sigma**2) * dt
        diff  = p.sigma * math.sqrt(dt)
        Z = rng.standard_normal((self.num_paths, self.num_steps))
        log_ret = drift + diff * Z
        log_paths = np.cumsum(log_ret, axis=1)
        paths = p.S * np.exp(log_paths)
        return np.hstack([np.full((self.num_paths, 1), p.S), paths])

    def _result(self, payoffs: np.ndarray, t0: float) -> PricingResult:
        p = self.p
        disc = math.exp(-p.r * p.T)
        n = len(payoffs)
        mean = np.mean(payoffs)
        se   = np.std(payoffs, ddof=1) / math.sqrt(n)
        elapsed = (time.perf_counter() - t0) * 1000
        return PricingResult(
            price      = disc * mean,
            stderr     = disc * se,
            ci_low     = disc * (mean - 1.96 * se),
            ci_high    = disc * (mean + 1.96 * se),
            elapsed_ms = elapsed
        )

    def price_european(self, option_type: str = "call") -> PricingResult:
        t0 = time.perf_counter()
        ST = self._simulate_terminal()
        if option_type == "call":
            payoffs = np.maximum(ST - self.p.K, 0)
        else:
            payoffs = np.maximum(self.p.K - ST, 0)
        return self._result(payoffs, t0)

    def price_asian(self, option_type: str = "call") -> PricingResult:
        t0 = time.perf_counter()
        paths = self._simulate_paths()
        avg = np.mean(paths[:, 1:], axis=1)
        if option_type == "call":
            payoffs = np.maximum(avg - self.p.K, 0)
        else:
            payoffs = np.maximum(self.p.K - avg, 0)
        return self._result(payoffs, t0)

    def price_barrier(self, barrier: float) -> PricingResult:
        t0 = time.perf_counter()
        paths = self._simulate_paths()
        knocked = np.any(paths >= barrier, axis=1)
        payoffs = np.where(knocked, 0.0, np.maximum(paths[:, -1] - self.p.K, 0))
        return self._result(payoffs, t0)

    def price_lookback(self) -> PricingResult:
        t0 = time.perf_counter()
        paths = self._simulate_paths()
        min_S   = np.min(paths, axis=1)
        payoffs = np.maximum(paths[:, -1] - min_S, 0)
        return self._result(payoffs, t0)

    def compute_greeks(self, res: PricingResult, option_type: str) -> None:
        p = self.p
        dS = p.S * 0.01
        pu = MarketParams(p.S+dS, p.K, p.r, p.q, p.sigma, p.T)
        pd = MarketParams(p.S-dS, p.K, p.r, p.q, p.sigma, p.T)
        Vu = MonteCarloEngine(pu, self.num_paths, self.num_steps, self.seed).price_european(option_type).price
        Vd = MonteCarloEngine(pd, self.num_paths, self.num_steps, self.seed).price_european(option_type).price
        res.delta = (Vu - Vd) / (2*dS)
        res.gamma = (Vu - 2*res.price + Vd) / (dS**2)

        dsig = 0.001
        pv = MarketParams(p.S, p.K, p.r, p.q, p.sigma+dsig, p.T)
        res.vega = (MonteCarloEngine(pv, self.num_paths, self.num_steps, self.seed).price_european(option_type).price - res.price) / dsig / 100

        dT = 1/365
        if p.T > dT:
            pt = MarketParams(p.S, p.K, p.r, p.q, p.sigma, p.T-dT)
            res.theta = (MonteCarloEngine(pt, self.num_paths, self.num_steps, self.seed).price_european(option_type).price - res.price) / dT / 365

        dr = 0.0001
        pr = MarketParams(p.S, p.K, p.r+dr, p.q, p.sigma, p.T)
        res.rho = (MonteCarloEngine(pr, self.num_paths, self.num_steps, self.seed).price_european(option_type).price - res.price) / dr / 100


# ─────────────────────────────────────────────────────────────
#  LSMC — American Options (Python)
# ─────────────────────────────────────────────────────────────
class LSMCEngine:
    def __init__(self, params: MarketParams, num_paths: int = 20_000,
                 num_steps: int = 50, poly_deg: int = 3, seed: int = 42):
        self.p = params
        self.num_paths = num_paths
        self.num_steps = num_steps
        self.poly_deg  = poly_deg
        self.seed      = seed

    def _basis(self, x: np.ndarray) -> np.ndarray:
        ex = np.exp(-x / 2)
        cols = [ex]
        if self.poly_deg >= 1: cols.append(ex * (1 - x))
        if self.poly_deg >= 2: cols.append(ex * (1 - 2*x + 0.5*x**2))
        if self.poly_deg >= 3: cols.append(ex * (1 - 3*x + 1.5*x**2 - x**3/6))
        return np.column_stack(cols)

    def price(self, option_type: str = "put") -> PricingResult:
        t0 = time.perf_counter()
        p = self.p
        rng   = np.random.default_rng(self.seed)
        dt    = p.T / self.num_steps
        disc  = math.exp(-p.r * dt)
        drift = (p.r - p.q - 0.5 * p.sigma**2) * dt
        diff  = p.sigma * math.sqrt(dt)

        # Simulate paths
        Z = rng.standard_normal((self.num_paths, self.num_steps))
        log_inc = drift + diff * Z
        log_paths = np.cumsum(log_inc, axis=1)
        paths = p.S * np.exp(log_paths)
        paths = np.hstack([np.full((self.num_paths, 1), p.S), paths])

        intrinsic = (lambda S: np.maximum(S - p.K, 0)) if option_type == "call" \
               else (lambda S: np.maximum(p.K - S, 0))

        cashflow = intrinsic(paths[:, -1]).copy()

        for t in range(self.num_steps - 1, 0, -1):
            S_t = paths[:, t]
            itm = intrinsic(S_t) > 0
            if not np.any(itm): continue

            X = self._basis(S_t[itm] / p.K)
            Y = disc * cashflow[itm]
            coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
            cont = X @ coef

            exercise = intrinsic(S_t[itm])
            early    = exercise > cont
            idx      = np.where(itm)[0]
            cashflow[idx[early]]  = exercise[early]
            cashflow[idx[~early]] *= disc
            cashflow[~itm] *= disc

        cashflow *= disc
        mean = float(np.mean(cashflow))
        se   = float(np.std(cashflow, ddof=1) / math.sqrt(self.num_paths))
        elapsed = (time.perf_counter() - t0) * 1000
        return PricingResult(
            price=mean, stderr=se,
            ci_low=mean - 1.96*se, ci_high=mean + 1.96*se,
            elapsed_ms=elapsed
        )


# ─────────────────────────────────────────────────────────────
#  Unified Pricer interface
# ─────────────────────────────────────────────────────────────
def price_option(
    S: float, K: float, r: float, q: float, sigma: float, T: float,
    option_type: str = "call",
    method: str = "black_scholes",
    exotic_type: str | None = None,
    barrier: float | None = None,
    compute_greeks: bool = True,
    **kwargs
) -> dict:
    """
    Unified pricing interface. Returns a dict with price + greeks.

    Args:
        method: 'black_scholes' | 'cos' | 'monte_carlo' | 'lsmc'
        exotic_type: None | 'asian' | 'barrier' | 'lookback'
    """
    params = MarketParams(S=S, K=K, r=r, q=q, sigma=sigma, T=T)

    if method == "black_scholes":
        bs = BlackScholesEngine(params)
        res = bs.price_call() if option_type == "call" else bs.price_put()

    elif method == "cos":
        N = kwargs.get("cos_N", 256)
        L = kwargs.get("cos_L", 12.0)
        engine = COSEngine(params, N=N, L=L)
        res = engine.price(option_type)
        if compute_greeks:
            engine.compute_greeks(res, option_type)

    elif method == "monte_carlo":
        num_paths = kwargs.get("num_paths", 100_000)
        num_steps = kwargs.get("num_steps", 252)
        engine = MonteCarloEngine(params, num_paths=num_paths, num_steps=num_steps)
        if exotic_type == "asian":
            res = engine.price_asian(option_type)
        elif exotic_type == "barrier" and barrier is not None:
            res = engine.price_barrier(barrier)
        elif exotic_type == "lookback":
            res = engine.price_lookback()
        else:
            res = engine.price_european(option_type)
            if compute_greeks:
                engine.compute_greeks(res, option_type)

    elif method == "lsmc":
        num_paths = kwargs.get("num_paths", 20_000)
        num_steps = kwargs.get("num_steps", 50)
        engine = LSMCEngine(params, num_paths=num_paths, num_steps=num_steps)
        res = engine.price(option_type)

    else:
        raise ValueError(f"Unknown method: {method}")

    return res.to_dict()


def price_surface(
    strikes: list[float],
    maturities: list[float],
    S: float, r: float, q: float, sigma: float,
    method: str = "black_scholes",
    option_type: str = "call"
) -> list[list[float]]:
    """Compute a full pricing surface [maturity x strike]."""
    surface = []
    for T in maturities:
        row = []
        for K in strikes:
            res = price_option(S=S, K=K, r=r, q=q, sigma=sigma, T=T,
                               option_type=option_type, method=method,
                               compute_greeks=False)
            row.append(res["price"])
        surface.append(row)
    return surface

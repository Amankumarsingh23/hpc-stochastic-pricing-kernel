"""
tests/test_pricing_engines.py
─────────────────────────────────────────────────────────────
Validation suite: prices, greeks, convergence, put-call parity,
and regression against known academic benchmarks.
"""
import math
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.models.pricing_engine import (
    MarketParams, BlackScholesEngine, COSEngine,
    MonteCarloEngine, LSMCEngine, price_option, price_surface
)

# ─────────────────────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def atm_params():
    return MarketParams(S=100, K=100, r=0.05, q=0.0, sigma=0.20, T=1.0)

@pytest.fixture
def itm_call_params():
    return MarketParams(S=110, K=100, r=0.05, q=0.0, sigma=0.20, T=1.0)

@pytest.fixture
def otm_call_params():
    return MarketParams(S=90, K=100, r=0.05, q=0.0, sigma=0.20, T=1.0)

# ─────────────────────────────────────────────────────────────
#  Black-Scholes
# ─────────────────────────────────────────────────────────────
class TestBlackScholes:
    def test_atm_call_known_value(self, atm_params):
        """ATM call with σ=0.2, T=1, r=0.05: BS ≈ 10.4506"""
        bs = BlackScholesEngine(atm_params)
        result = bs.price_call()
        assert abs(result.price - 10.4506) < 0.01, f"Got {result.price}"

    def test_put_call_parity(self, atm_params):
        """C - P = S·e^{-qT} - K·e^{-rT}"""
        bs = BlackScholesEngine(atm_params)
        c = bs.price_call().price
        p = bs.price_put().price
        p_fwd = atm_params.S - atm_params.K * math.exp(-atm_params.r * atm_params.T)
        assert abs((c - p) - p_fwd) < 1e-8, f"PCP violated: {c-p} vs {p_fwd}"

    def test_delta_call_range(self, atm_params):
        bs = BlackScholesEngine(atm_params)
        d = bs.price_call().delta
        assert 0.5 < d < 0.7, f"ATM call delta should be ~0.6, got {d}"

    def test_delta_put_range(self, atm_params):
        bs = BlackScholesEngine(atm_params)
        d = bs.price_put().delta
        assert -0.5 > d > -0.7, f"ATM put delta should be ~-0.4, got {d}"

    def test_gamma_positive(self, atm_params):
        bs = BlackScholesEngine(atm_params)
        assert bs.price_call().gamma > 0
        assert bs.price_put().gamma > 0

    def test_vega_positive(self, atm_params):
        bs = BlackScholesEngine(atm_params)
        assert bs.price_call().vega > 0

    def test_call_theta_negative(self, atm_params):
        bs = BlackScholesEngine(atm_params)
        assert bs.price_call().theta < 0, "Theta should be negative (time decay)"

    def test_deep_itm_call_approaches_forward(self, itm_call_params):
        """Deep ITM call ≈ S - K·e^{-rT}"""
        p = MarketParams(S=200, K=50, r=0.05, q=0.0, sigma=0.20, T=1.0)
        bs = BlackScholesEngine(p)
        c = bs.price_call().price
        fwd = p.S - p.K * math.exp(-p.r * p.T)
        assert abs(c - fwd) < 0.5, f"Deep ITM call {c} vs forward {fwd}"

    def test_zero_time_call(self):
        """At T→0, call = max(S-K, 0)"""
        p = MarketParams(S=105, K=100, r=0.05, q=0.0, sigma=0.20, T=0.001)
        bs = BlackScholesEngine(p)
        c = bs.price_call().price
        assert abs(c - 5.0) < 0.1, f"Near-expiry call should ≈ intrinsic, got {c}"


# ─────────────────────────────────────────────────────────────
#  COS Method
# ─────────────────────────────────────────────────────────────
class TestCOSMethod:
    def test_matches_bs_atm(self, atm_params):
        bs  = BlackScholesEngine(atm_params)
        cos = COSEngine(atm_params, N=512)
        bs_p  = bs.price_call().price
        cos_p = cos.price("call").price
        assert abs(cos_p - bs_p) < 0.001, f"COS {cos_p} vs BS {bs_p}"

    def test_matches_bs_otm(self, otm_call_params):
        bs  = BlackScholesEngine(otm_call_params)
        cos = COSEngine(otm_call_params, N=512)
        assert abs(cos.price("call").price - bs.price_call().price) < 0.001

    def test_put_call_parity(self, atm_params):
        cos = COSEngine(atm_params, N=256)
        c = cos.price("call").price
        p = cos.price("put").price
        p_fwd = atm_params.S - atm_params.K * math.exp(-atm_params.r * atm_params.T)
        assert abs((c - p) - p_fwd) < 0.005

    def test_convergence_with_N(self, atm_params):
        """Higher N → lower error vs BS"""
        bs_price = BlackScholesEngine(atm_params).price_call().price
        errors = []
        for N in [16, 64, 256, 1024]:
            cos_p = COSEngine(atm_params, N=N).price("call").price
            errors.append(abs(cos_p - bs_price))
        # Errors should be decreasing
        assert errors[0] > errors[-1], "COS should converge with more terms"
        assert errors[-1] < 1e-6, f"N=1024 should be near machine precision, got {errors[-1]}"

    def test_greeks_close_to_bs(self, atm_params):
        bs = BlackScholesEngine(atm_params)
        cos_eng = COSEngine(atm_params, N=512)
        r_cos = cos_eng.price("call")
        cos_eng.compute_greeks(r_cos, "call")
        r_bs = bs.price_call()
        assert abs(r_cos.delta - r_bs.delta) < 0.01
        assert abs(r_cos.gamma - r_bs.gamma) < 0.005

    def test_deterministic(self, atm_params):
        """COS should return identical result on repeated calls"""
        cos = COSEngine(atm_params, N=256)
        p1 = cos.price("call").price
        p2 = cos.price("call").price
        assert p1 == p2


# ─────────────────────────────────────────────────────────────
#  Monte Carlo
# ─────────────────────────────────────────────────────────────
class TestMonteCarlo:
    def test_european_call_within_ci(self, atm_params):
        bs_price = BlackScholesEngine(atm_params).price_call().price
        mc = MonteCarloEngine(atm_params, num_paths=100_000, seed=42)
        res = mc.price_european("call")
        assert res.ci_low <= bs_price <= res.ci_high, \
            f"BS price {bs_price} not in MC CI [{res.ci_low}, {res.ci_high}]"

    def test_put_within_ci(self, atm_params):
        bs_price = BlackScholesEngine(atm_params).price_put().price
        mc = MonteCarloEngine(atm_params, num_paths=100_000, seed=42)
        res = mc.price_european("put")
        assert res.ci_low <= bs_price <= res.ci_high

    def test_ci_width_decreases_with_paths(self, atm_params):
        mc1 = MonteCarloEngine(atm_params, num_paths=1_000)
        mc2 = MonteCarloEngine(atm_params, num_paths=100_000)
        w1 = mc1.price_european("call").ci_high - mc1.price_european("call").ci_low
        w2 = mc2.price_european("call").ci_high - mc2.price_european("call").ci_low
        assert w2 < w1, "Wider CI with fewer paths"

    def test_antithetic_reduces_variance(self, atm_params):
        mc_no_anti = MonteCarloEngine(atm_params, num_paths=10_000, antithetic=False)
        mc_anti    = MonteCarloEngine(atm_params, num_paths=10_000, antithetic=True)
        se_no  = mc_no_anti.price_european("call").stderr
        se_yes = mc_anti.price_european("call").stderr
        # On average antithetic should have lower or equal stderr
        assert se_yes <= se_no * 1.1, "Antithetic should reduce std error"

    def test_asian_cheaper_than_european(self, atm_params):
        mc = MonteCarloEngine(atm_params, num_paths=50_000)
        eu = mc.price_european("call").price
        as_ = mc.price_asian("call").price
        # Asian call ≤ European call (averaging reduces payoff)
        assert as_ <= eu * 1.05, f"Asian {as_} should be ≤ European {eu}"

    def test_barrier_cheaper_than_european(self, atm_params):
        mc = MonteCarloEngine(atm_params, num_paths=50_000)
        eu  = mc.price_european("call").price
        bar = mc.price_barrier(barrier=120.0).price
        assert bar <= eu, f"Barrier call {bar} should be ≤ vanilla {eu}"

    def test_lookback_costlier_than_european(self, atm_params):
        mc = MonteCarloEngine(atm_params, num_paths=50_000)
        eu   = mc.price_european("call").price
        look = mc.price_lookback().price
        assert look >= eu * 0.9, f"Lookback {look} should be ≥ European {eu}"


# ─────────────────────────────────────────────────────────────
#  LSMC — American Options
# ─────────────────────────────────────────────────────────────
class TestLSMC:
    def test_american_put_ge_european(self, atm_params):
        """American put ≥ European put (early exercise premium)"""
        lsmc = LSMCEngine(atm_params, num_paths=20_000)
        mc   = MonteCarloEngine(atm_params, num_paths=20_000)
        am_put = lsmc.price("put").price
        eu_put = mc.price_european("put").price
        assert am_put >= eu_put * 0.95, \
            f"American put {am_put} should be ≥ European put {eu_put}"

    def test_american_call_no_premium_no_dividends(self, atm_params):
        """American call ≈ European call when q=0 (no early exercise benefit)"""
        lsmc = LSMCEngine(atm_params, num_paths=20_000)
        mc   = MonteCarloEngine(atm_params, num_paths=20_000)
        am_call = lsmc.price("call").price
        eu_call = mc.price_european("call").price
        # Should be close (within MC noise)
        assert abs(am_call - eu_call) < 1.0, \
            f"Am call {am_call} vs Eu call {eu_call} — no dividend so should be similar"

    def test_price_positive(self, atm_params):
        lsmc = LSMCEngine(atm_params, num_paths=5_000)
        assert lsmc.price("put").price > 0
        assert lsmc.price("call").price > 0

    def test_ci_contains_mean(self, atm_params):
        lsmc = LSMCEngine(atm_params, num_paths=5_000)
        res = lsmc.price("put")
        assert res.ci_low <= res.price <= res.ci_high


# ─────────────────────────────────────────────────────────────
#  Unified interface
# ─────────────────────────────────────────────────────────────
class TestUnifiedInterface:
    def test_price_option_bs(self):
        res = price_option(S=100, K=100, r=0.05, q=0, sigma=0.2, T=1,
                           option_type="call", method="black_scholes")
        assert "price" in res
        assert res["price"] > 0

    def test_price_option_cos(self):
        res = price_option(S=100, K=100, r=0.05, q=0, sigma=0.2, T=1,
                           option_type="call", method="cos")
        assert abs(res["price"] - 10.45) < 0.1

    def test_price_option_mc(self):
        res = price_option(S=100, K=100, r=0.05, q=0, sigma=0.2, T=1,
                           option_type="call", method="monte_carlo", num_paths=50_000)
        assert abs(res["price"] - 10.45) < 0.5

    def test_price_surface_shape(self):
        strikes    = [90, 100, 110]
        maturities = [0.5, 1.0]
        surface = price_surface(strikes, maturities, S=100, r=0.05,
                                q=0, sigma=0.2, method="black_scholes",
                                option_type="call")
        assert len(surface) == 2        # 2 maturities
        assert len(surface[0]) == 3     # 3 strikes
        # All prices positive
        for row in surface:
            for px in row:
                assert px >= 0

    def test_call_price_increases_with_sigma(self):
        prices = []
        for sig in [0.1, 0.2, 0.3, 0.4]:
            res = price_option(S=100, K=100, r=0.05, q=0, sigma=sig, T=1,
                               option_type="call", method="black_scholes")
            prices.append(res["price"])
        assert all(prices[i] < prices[i+1] for i in range(len(prices)-1)), \
            "Call price should increase with volatility"

    def test_call_price_increases_with_spot(self):
        prices = []
        for s in [80, 90, 100, 110, 120]:
            res = price_option(S=s, K=100, r=0.05, q=0, sigma=0.2, T=1,
                               option_type="call", method="black_scholes")
            prices.append(res["price"])
        assert all(prices[i] < prices[i+1] for i in range(len(prices)-1))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

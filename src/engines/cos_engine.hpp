#pragma once
#include <vector>
#include <complex>
#include <cmath>
#include <stdexcept>
#include <chrono>
#include "monte_carlo.hpp"  // for MarketParams, PricingResult

namespace hpc_pricing {

// ─────────────────────────────────────────────────────────────
//  COS Method  (Fang & Oosterlee, 2009)
//  Highly accurate for European options — O(N log N) complexity
//  Numerically stable via log-price transform
// ─────────────────────────────────────────────────────────────
class COSEngine {
public:
    struct COSConfig {
        int    N     = 256;    // Fourier-cosine terms (power of 2 for perf)
        double L     = 12.0;   // Truncation range multiplier
    };

    COSEngine(const MarketParams& p, const COSConfig& cfg = {})
        : p_(p), cfg_(cfg) {}

    // ── Characteristic function of log(S_T/S_0) under GBM ───
    // φ(u) = exp(i·u·μ - ½·σ²·u²·T)
    // where μ = (r - q - ½σ²)T
    std::complex<double> char_func_gbm(double u) const {
        using namespace std::complex_literals;
        double mu = (p_.r - p_.q - 0.5 * p_.sigma * p_.sigma) * p_.T;
        double var = p_.sigma * p_.sigma * p_.T;
        std::complex<double> iu(0.0, u);
        return std::exp(iu * mu - 0.5 * var * u * u);
    }

    // ── Heston Model Characteristic Function ─────────────────
    // v0=initial variance, kappa=mean reversion, theta=long-var
    // xi=vol-of-vol, rho=correlation
    std::complex<double> char_func_heston(
        double u, double v0, double kappa,
        double theta, double xi, double rho) const
    {
        using cd = std::complex<double>;
        cd i(0.0, 1.0);
        cd iu = i * u;
        cd D = std::sqrt((kappa - rho * xi * iu) * (kappa - rho * xi * iu)
                         + xi * xi * (iu + u * u));
        cd G = (kappa - rho * xi * iu - D) / (kappa - rho * xi * iu + D);
        cd eD = std::exp(-D * p_.T);

        cd C = (p_.r - p_.q) * iu * p_.T
             + kappa * theta / (xi * xi)
               * ((kappa - rho * xi * iu - D) * p_.T
                  - 2.0 * std::log((1.0 - G * eD) / (1.0 - G)));
        cd V = (kappa - rho * xi * iu - D) / (xi * xi)
             * (1.0 - eD) / (1.0 - G * eD);

        return std::exp(C + V * v0 + i * u * std::log(p_.S / p_.K));
    }

    // ── COS Coefficients Vm for European Call / Put ──────────
    // Chi and Psi basis integrals (analytical closed-form)
    double chi(int k, double a, double b, double c, double d) const {
        double kpi = k * M_PI / (b - a);
        double num = std::cos(kpi * (d - a)) * std::exp(d)
                   - std::cos(kpi * (c - a)) * std::exp(c)
                   + kpi * std::sin(kpi * (d - a)) * std::exp(d)
                   - kpi * std::sin(kpi * (c - a)) * std::exp(c);
        return num / (1.0 + kpi * kpi);
    }

    double psi(int k, double a, double b, double c, double d) const {
        if (k == 0) return d - c;
        double kpi_ba = k * M_PI / (b - a);
        return (std::sin(kpi_ba * (d - a)) - std::sin(kpi_ba * (c - a))) / kpi_ba;
    }

    // ── Vk coefficients for call and put ────────────────────
    double Vk_call(int k, double a, double b) const {
        return 2.0 / (b - a) * (chi(k, a, b, 0.0, b) - psi(k, a, b, 0.0, b));
    }

    double Vk_put(int k, double a, double b) const {
        return 2.0 / (b - a) * (-chi(k, a, b, a, 0.0) + psi(k, a, b, a, 0.0));
    }

    // ── Main pricing routine ─────────────────────────────────
    PricingResult price(const std::string& option_type,
                        bool use_heston = false,
                        double v0 = 0.04, double kappa = 2.0,
                        double theta = 0.04, double xi = 0.3,
                        double rho_h = -0.7) const
    {
        auto t0 = std::chrono::high_resolution_clock::now();

        bool is_call = (option_type == "call");
        double x = std::log(p_.S / p_.K);  // log-moneyness

        // Integration bounds (Cossine truncation rule)
        double c1 = (p_.r - p_.q - 0.5 * p_.sigma * p_.sigma) * p_.T;
        double c2 = p_.sigma * p_.sigma * p_.T;
        double a = x + c1 - cfg_.L * std::sqrt(std::abs(c2));
        double b = x + c1 + cfg_.L * std::sqrt(std::abs(c2));

        int N = cfg_.N;
        double sum = 0.0;

        for (int k = 0; k < N; ++k) {
            double u = k * M_PI / (b - a);
            std::complex<double> phi;
            if (use_heston)
                phi = char_func_heston(u, v0, kappa, theta, xi, rho_h);
            else
                phi = char_func_gbm(u);

            // Real part of φ(u) * exp(-i·u·a)
            std::complex<double> term = phi
                * std::exp(std::complex<double>(0.0, -u * a));

            double Vk = is_call ? Vk_call(k, a, b) : Vk_put(k, a, b);
            double w  = (k == 0) ? 0.5 : 1.0;  // trapezoidal weight
            sum += w * std::real(term) * Vk;
        }

        double price = std::exp(-p_.r * p_.T) * p_.K * sum;
        // Floor at intrinsic value for numerical stability
        double intrinsic = is_call ? std::max(p_.S - p_.K * std::exp(-p_.r * p_.T), 0.0)
                                   : std::max(p_.K * std::exp(-p_.r * p_.T) - p_.S, 0.0);
        price = std::max(price, intrinsic);

        auto t1 = std::chrono::high_resolution_clock::now();
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

        PricingResult res{};
        res.price      = price;
        res.stderr     = 0.0;  // COS is deterministic
        res.ci_low     = price;
        res.ci_high    = price;
        res.elapsed_ms = ms;
        return res;
    }

    // ── Closed-form Greeks via COS ───────────────────────────
    void compute_greeks(PricingResult& res, const std::string& opt_type) const {
        double dS   = p_.S * 0.005;
        double dsig = 0.001;
        double dT   = 1.0 / 365.0;
        double dr   = 0.0001;

        MarketParams pu = p_; pu.S = p_.S + dS;
        MarketParams pd = p_; pd.S = p_.S - dS;
        COSEngine eu(pu, cfg_), ed(pd, cfg_);
        double Vu = eu.price(opt_type).price;
        double Vd = ed.price(opt_type).price;
        double V0 = res.price;

        res.delta = (Vu - Vd) / (2.0 * dS);
        res.gamma = (Vu - 2.0*V0 + Vd) / (dS * dS);

        MarketParams pv = p_; pv.sigma = p_.sigma + dsig;
        COSEngine ev(pv, cfg_);
        res.vega  = (ev.price(opt_type).price - V0) / dsig / 100.0;

        if (p_.T > dT) {
            MarketParams pt = p_; pt.T = p_.T - dT;
            COSEngine et(pt, cfg_);
            res.theta = (et.price(opt_type).price - V0) / dT / 365.0;
        }

        MarketParams pr = p_; pr.r = p_.r + dr;
        COSEngine er(pr, cfg_);
        res.rho = (er.price(opt_type).price - V0) / dr / 100.0;
    }

private:
    MarketParams p_;
    COSConfig    cfg_;
};

// ─────────────────────────────────────────────────────────────
//  Black-Scholes Analytical (reference / benchmark)
// ─────────────────────────────────────────────────────────────
class BlackScholesEngine {
public:
    BlackScholesEngine(const MarketParams& p) : p_(p) {}

    static double norm_cdf(double x) {
        return 0.5 * std::erfc(-x * M_SQRT1_2);
    }

    double d1() const {
        return (std::log(p_.S / p_.K)
                + (p_.r - p_.q + 0.5 * p_.sigma * p_.sigma) * p_.T)
               / (p_.sigma * std::sqrt(p_.T));
    }

    double d2() const { return d1() - p_.sigma * std::sqrt(p_.T); }

    PricingResult price_call() const {
        double _d1 = d1(), _d2 = d2();
        double disc = std::exp(-p_.r * p_.T);
        double fwd  = p_.S * std::exp(-p_.q * p_.T);
        double px   = fwd * norm_cdf(_d1) - p_.K * disc * norm_cdf(_d2);

        PricingResult res{};
        res.price   = px;
        res.stderr  = 0.0;
        res.ci_low  = px; res.ci_high = px;
        // Analytical Greeks
        double nd1   = std::exp(-0.5*_d1*_d1) / std::sqrt(2.0*M_PI);
        double sqrtT = std::sqrt(p_.T);
        res.delta = std::exp(-p_.q*p_.T) * norm_cdf(_d1);
        res.gamma = std::exp(-p_.q*p_.T) * nd1 / (p_.S * p_.sigma * sqrtT);
        res.vega  = p_.S * std::exp(-p_.q*p_.T) * nd1 * sqrtT / 100.0;
        res.theta = (-p_.S * std::exp(-p_.q*p_.T) * nd1 * p_.sigma
                     / (2.0*sqrtT)
                     - p_.r * p_.K * disc * norm_cdf(_d2)
                     + p_.q * p_.S * std::exp(-p_.q*p_.T) * norm_cdf(_d1)) / 365.0;
        res.rho   = p_.K * p_.T * disc * norm_cdf(_d2) / 100.0;
        return res;
    }

    PricingResult price_put() const {
        double _d1 = d1(), _d2 = d2();
        double disc = std::exp(-p_.r * p_.T);
        double fwd  = p_.S * std::exp(-p_.q * p_.T);
        double px   = p_.K * disc * norm_cdf(-_d2) - fwd * norm_cdf(-_d1);

        PricingResult res{};
        res.price  = px;
        res.ci_low = res.ci_high = px;
        double nd1   = std::exp(-0.5*_d1*_d1) / std::sqrt(2.0*M_PI);
        double sqrtT = std::sqrt(p_.T);
        res.delta = -std::exp(-p_.q*p_.T) * norm_cdf(-_d1);
        res.gamma = std::exp(-p_.q*p_.T) * nd1 / (p_.S * p_.sigma * sqrtT);
        res.vega  = p_.S * std::exp(-p_.q*p_.T) * nd1 * sqrtT / 100.0;
        res.theta = (-p_.S * std::exp(-p_.q*p_.T) * nd1 * p_.sigma
                     / (2.0*sqrtT)
                     + p_.r * p_.K * disc * norm_cdf(-_d2)
                     - p_.q * p_.S * std::exp(-p_.q*p_.T) * norm_cdf(-_d1)) / 365.0;
        res.rho   = -p_.K * p_.T * disc * norm_cdf(-_d2) / 100.0;
        return res;
    }

private:
    MarketParams p_;
};

} // namespace hpc_pricing

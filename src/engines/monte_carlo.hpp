#pragma once
#include <vector>
#include <cmath>
#include <random>
#include <algorithm>
#include <numeric>
#include <stdexcept>
#include <functional>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace hpc_pricing {

// ─────────────────────────────────────────────────────────────
//  Market Parameters
// ─────────────────────────────────────────────────────────────
struct MarketParams {
    double S;      // Spot price
    double K;      // Strike price
    double r;      // Risk-free rate
    double q;      // Dividend yield
    double sigma;  // Volatility
    double T;      // Time to maturity (years)
};

struct MCConfig {
    int    num_paths   = 100000;
    int    num_steps   = 252;
    int    seed        = 42;
    bool   antithetic  = true;
    bool   use_sobol   = false;
};

struct PricingResult {
    double price;
    double stderr;
    double ci_low;
    double ci_high;
    double delta;
    double gamma;
    double vega;
    double theta;
    double rho;
    double elapsed_ms;
};

// ─────────────────────────────────────────────────────────────
//  Numerically Stable Payoff Functions
// ─────────────────────────────────────────────────────────────
namespace payoff {
    inline double european_call(double ST, double K) noexcept {
        return std::max(ST - K, 0.0);
    }
    inline double european_put(double ST, double K) noexcept {
        return std::max(K - ST, 0.0);
    }
    inline double asian_call_arithmetic(const std::vector<double>& path, double K) noexcept {
        double avg = std::accumulate(path.begin(), path.end(), 0.0) / path.size();
        return std::max(avg - K, 0.0);
    }
    inline double asian_put_arithmetic(const std::vector<double>& path, double K) noexcept {
        double avg = std::accumulate(path.begin(), path.end(), 0.0) / path.size();
        return std::max(K - avg, 0.0);
    }
    inline double barrier_up_out_call(const std::vector<double>& path, double K, double B) noexcept {
        bool knocked = false;
        for (double s : path) if (s >= B) { knocked = true; break; }
        if (knocked) return 0.0;
        return std::max(path.back() - K, 0.0);
    }
    inline double lookback_call(const std::vector<double>& path) noexcept {
        double min_S = *std::min_element(path.begin(), path.end());
        return std::max(path.back() - min_S, 0.0);
    }
}

// ─────────────────────────────────────────────────────────────
//  GBM Path Generator  (Mersenne Twister + antithetic)
// ─────────────────────────────────────────────────────────────
class GBMPathGenerator {
public:
    explicit GBMPathGenerator(const MarketParams& p, const MCConfig& cfg)
        : p_(p), cfg_(cfg) {}

    // Returns a single simulated path of log-prices
    std::vector<double> generate_path(std::mt19937_64& rng) const {
        std::normal_distribution<double> N(0.0, 1.0);
        std::vector<double> path(cfg_.num_steps + 1);
        double dt   = p_.T / cfg_.num_steps;
        double drift = (p_.r - p_.q - 0.5 * p_.sigma * p_.sigma) * dt;
        double diff  = p_.sigma * std::sqrt(dt);

        path[0] = p_.S;
        for (int i = 1; i <= cfg_.num_steps; ++i) {
            path[i] = path[i-1] * std::exp(drift + diff * N(rng));
        }
        return path;
    }

    // Antithetic pair
    std::pair<std::vector<double>, std::vector<double>>
    generate_antithetic(std::mt19937_64& rng) const {
        std::normal_distribution<double> N(0.0, 1.0);
        int n = cfg_.num_steps;
        std::vector<double> z(n);
        for (auto& zi : z) zi = N(rng);

        double dt    = p_.T / n;
        double drift = (p_.r - p_.q - 0.5 * p_.sigma * p_.sigma) * dt;
        double diff  = p_.sigma * std::sqrt(dt);

        std::vector<double> path1(n+1), path2(n+1);
        path1[0] = path2[0] = p_.S;
        for (int i = 1; i <= n; ++i) {
            path1[i] = path1[i-1] * std::exp(drift + diff *  z[i-1]);
            path2[i] = path2[i-1] * std::exp(drift + diff * -z[i-1]);
        }
        return {path1, path2};
    }

private:
    MarketParams p_;
    MCConfig     cfg_;
};

// ─────────────────────────────────────────────────────────────
//  Monte Carlo Engine  (OpenMP parallel)
// ─────────────────────────────────────────────────────────────
class MonteCarloEngine {
public:
    MonteCarloEngine(const MarketParams& params, const MCConfig& cfg = {})
        : p_(params), cfg_(cfg) {}

    // ── European Options ─────────────────────────────────────
    PricingResult price_european(const std::string& option_type) const {
        auto t0 = std::chrono::high_resolution_clock::now();

        bool is_call = (option_type == "call");
        int  M = cfg_.num_paths;
        double discount = std::exp(-p_.r * p_.T);

        std::vector<double> payoffs(M);
        GBMPathGenerator gen(p_, cfg_);

        #pragma omp parallel
        {
            int tid = 0;
#ifdef _OPENMP
            tid = omp_get_thread_num();
#endif
            std::mt19937_64 rng(cfg_.seed + tid * 1000007ULL);
            GBMPathGenerator lgen(p_, cfg_);

            #pragma omp for schedule(static)
            for (int i = 0; i < M; i += (cfg_.antithetic ? 2 : 1)) {
                if (cfg_.antithetic && i + 1 < M) {
                    auto [p1, p2] = lgen.generate_antithetic(rng);
                    double S1 = p1.back(), S2 = p2.back();
                    payoffs[i]   = is_call ? payoff::european_call(S1, p_.K)
                                           : payoff::european_put(S1, p_.K);
                    payoffs[i+1] = is_call ? payoff::european_call(S2, p_.K)
                                           : payoff::european_put(S2, p_.K);
                } else {
                    auto path = lgen.generate_path(rng);
                    payoffs[i] = is_call ? payoff::european_call(path.back(), p_.K)
                                        : payoff::european_put(path.back(), p_.K);
                }
            }
        }

        return compute_result(payoffs, discount, t0);
    }

    // ── Asian Options ────────────────────────────────────────
    PricingResult price_asian(const std::string& option_type) const {
        auto t0 = std::chrono::high_resolution_clock::now();
        bool is_call = (option_type == "call");
        int  M = cfg_.num_paths;
        double discount = std::exp(-p_.r * p_.T);
        std::vector<double> payoffs(M);

        #pragma omp parallel
        {
            int tid = 0;
#ifdef _OPENMP
            tid = omp_get_thread_num();
#endif
            std::mt19937_64 rng(cfg_.seed + tid * 999983ULL);
            GBMPathGenerator gen(p_, cfg_);

            #pragma omp for schedule(dynamic, 64)
            for (int i = 0; i < M; ++i) {
                auto path = gen.generate_path(rng);
                payoffs[i] = is_call ? payoff::asian_call_arithmetic(path, p_.K)
                                     : payoff::asian_put_arithmetic(path, p_.K);
            }
        }

        return compute_result(payoffs, discount, t0);
    }

    // ── Barrier Options ──────────────────────────────────────
    PricingResult price_barrier(double barrier) const {
        auto t0 = std::chrono::high_resolution_clock::now();
        int  M = cfg_.num_paths;
        double discount = std::exp(-p_.r * p_.T);
        std::vector<double> payoffs(M);

        #pragma omp parallel
        {
            int tid = 0;
#ifdef _OPENMP
            tid = omp_get_thread_num();
#endif
            std::mt19937_64 rng(cfg_.seed + tid * 998244353ULL);
            GBMPathGenerator gen(p_, cfg_);

            #pragma omp for schedule(dynamic, 64)
            for (int i = 0; i < M; ++i) {
                auto path = gen.generate_path(rng);
                payoffs[i] = payoff::barrier_up_out_call(path, p_.K, barrier);
            }
        }

        return compute_result(payoffs, discount, t0);
    }

    // ── Lookback Options ─────────────────────────────────────
    PricingResult price_lookback() const {
        auto t0 = std::chrono::high_resolution_clock::now();
        int  M = cfg_.num_paths;
        double discount = std::exp(-p_.r * p_.T);
        std::vector<double> payoffs(M);

        #pragma omp parallel
        {
            int tid = 0;
#ifdef _OPENMP
            tid = omp_get_thread_num();
#endif
            std::mt19937_64 rng(cfg_.seed + tid * 1000003ULL);
            GBMPathGenerator gen(p_, cfg_);

            #pragma omp for schedule(dynamic, 64)
            for (int i = 0; i < M; ++i) {
                auto path = gen.generate_path(rng);
                payoffs[i] = payoff::lookback_call(path);
            }
        }

        return compute_result(payoffs, discount, t0);
    }

    // ── Finite-difference Greeks via bump-and-reprice ────────
    void compute_greeks(PricingResult& res, const std::string& option_type) const {
        double dS    = p_.S * 0.01;
        double dsig  = p_.sigma * 0.01;
        double dT    = 1.0 / 365.0;
        double dr    = 0.0001;

        // Delta & Gamma (central differences)
        MarketParams pu = p_; pu.S = p_.S + dS;
        MarketParams pd = p_; pd.S = p_.S - dS;
        MonteCarloEngine eu(pu, cfg_), ed(pd, cfg_);
        double Vu = eu.price_european(option_type).price;
        double Vd = ed.price_european(option_type).price;
        double V0 = res.price;
        res.delta = (Vu - Vd) / (2.0 * dS);
        res.gamma = (Vu - 2.0*V0 + Vd) / (dS * dS);

        // Vega
        MarketParams pv = p_; pv.sigma = p_.sigma + dsig;
        MonteCarloEngine ev(pv, cfg_);
        res.vega = (ev.price_european(option_type).price - V0) / dsig / 100.0;

        // Theta (forward difference)
        MarketParams pt = p_; pt.T = p_.T - dT;
        if (pt.T > 0) {
            MonteCarloEngine et(pt, cfg_);
            res.theta = (et.price_european(option_type).price - V0) / dT / 365.0;
        }

        // Rho
        MarketParams pr = p_; pr.r = p_.r + dr;
        MonteCarloEngine er(pr, cfg_);
        res.rho = (er.price_european(option_type).price - V0) / dr / 100.0;
    }

private:
    MarketParams p_;
    MCConfig     cfg_;

    PricingResult compute_result(
        const std::vector<double>& payoffs,
        double discount,
        std::chrono::high_resolution_clock::time_point t0) const
    {
        int n = (int)payoffs.size();
        double mean = 0.0, m2 = 0.0;
        for (double v : payoffs) {
            double delta = v - mean;
            mean += delta / n;
            m2 += delta * (v - mean);
        }
        double var    = m2 / (n - 1);
        double se     = std::sqrt(var / n);
        double z95    = 1.96;

        auto t1 = std::chrono::high_resolution_clock::now();
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

        return {
            discount * mean,
            discount * se,
            discount * (mean - z95 * se),
            discount * (mean + z95 * se),
            0.0, 0.0, 0.0, 0.0, 0.0,
            ms
        };
    }
};

} // namespace hpc_pricing

#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <chrono>
#include <random>
#include "monte_carlo.hpp"

namespace hpc_pricing {

// ─────────────────────────────────────────────────────────────
//  Least-Squares Monte Carlo  (Longstaff & Schwartz, 2001)
//  For American option pricing via backward induction
//  Uses Laguerre polynomial basis for regression
// ─────────────────────────────────────────────────────────────
class LSMCEngine {
public:
    struct LSMCConfig {
        int    num_paths  = 50000;
        int    num_steps  = 50;
        int    poly_deg   = 3;   // polynomial basis degree
        int    seed       = 42;
    };

    LSMCEngine(const MarketParams& p, const LSMCConfig& cfg = {})
        : p_(p), cfg_(cfg) {}

    // ── Laguerre polynomial basis functions ──────────────────
    // L0=1, L1=(1-x), L2=(1-2x+0.5x²), L3=(1-3x+1.5x²-x³/6)
    std::vector<double> basis(double x) const {
        double ex = std::exp(-x / 2.0);
        std::vector<double> b;
        b.push_back(ex);
        if (cfg_.poly_deg >= 1) b.push_back(ex * (1.0 - x));
        if (cfg_.poly_deg >= 2) b.push_back(ex * (1.0 - 2.0*x + 0.5*x*x));
        if (cfg_.poly_deg >= 3) b.push_back(ex * (1.0 - 3.0*x + 1.5*x*x - x*x*x/6.0));
        return b;
    }

    // ── Least-squares regression (OLS via normal equations) ──
    // Solves A'Ax = A'b — small system, numerically stable
    std::vector<double> ols(
        const std::vector<std::vector<double>>& X,
        const std::vector<double>& y) const
    {
        int n = (int)X.size();
        int d = (int)X[0].size();
        // A = X'X  (d x d)
        std::vector<double> A(d*d, 0.0), b(d, 0.0);
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < d; ++j) {
                b[j] += X[i][j] * y[i];
                for (int k = 0; k < d; ++k)
                    A[j*d+k] += X[i][j] * X[i][k];
            }
        }
        // Gaussian elimination with partial pivoting
        for (int col = 0; col < d; ++col) {
            int pivot = col;
            for (int row = col+1; row < d; ++row)
                if (std::abs(A[row*d+col]) > std::abs(A[pivot*d+col]))
                    pivot = row;
            std::swap(b[col], b[pivot]);
            for (int k = 0; k < d; ++k) std::swap(A[col*d+k], A[pivot*d+k]);
            if (std::abs(A[col*d+col]) < 1e-14) continue;
            double inv = 1.0 / A[col*d+col];
            for (int row = col+1; row < d; ++row) {
                double fac = A[row*d+col] * inv;
                b[row] -= fac * b[col];
                for (int k = col; k < d; ++k) A[row*d+k] -= fac * A[col*d+k];
            }
        }
        std::vector<double> coef(d);
        for (int i = d-1; i >= 0; --i) {
            coef[i] = b[i];
            for (int j = i+1; j < d; ++j) coef[i] -= A[i*d+j] * coef[j];
            if (std::abs(A[i*d+i]) > 1e-14) coef[i] /= A[i*d+i];
        }
        return coef;
    }

    double dot(const std::vector<double>& a, const std::vector<double>& b) const {
        double s = 0.0;
        for (int i = 0; i < (int)a.size(); ++i) s += a[i]*b[i];
        return s;
    }

    // ── LSMC pricing ─────────────────────────────────────────
    PricingResult price(const std::string& option_type) const {
        auto t0 = std::chrono::high_resolution_clock::now();
        bool is_call = (option_type == "call");
        int  M = cfg_.num_paths;
        int  N = cfg_.num_steps;
        double dt  = p_.T / N;
        double disc = std::exp(-p_.r * dt);
        double drift = (p_.r - p_.q - 0.5*p_.sigma*p_.sigma) * dt;
        double diff  = p_.sigma * std::sqrt(dt);

        // ── Forward simulation: generate all paths ───────────
        // paths[i][t] = stock price at path i, time step t
        std::vector<std::vector<double>> paths(M, std::vector<double>(N+1));
        std::mt19937_64 rng(cfg_.seed);
        std::normal_distribution<double> N01(0.0, 1.0);

        for (int i = 0; i < M; ++i) {
            paths[i][0] = p_.S;
            for (int t = 1; t <= N; ++t)
                paths[i][t] = paths[i][t-1] * std::exp(drift + diff * N01(rng));
        }

        // ── Backward induction ───────────────────────────────
        auto intrinsic = [&](double S) -> double {
            return is_call ? std::max(S - p_.K, 0.0)
                           : std::max(p_.K - S, 0.0);
        };

        // cashflow[i] = discounted exercise value for path i
        std::vector<double> cashflow(M);
        for (int i = 0; i < M; ++i)
            cashflow[i] = intrinsic(paths[i][N]);  // terminal payoff

        // Step backwards from N-1 to 1
        for (int t = N-1; t >= 1; --t) {
            // Select in-the-money paths for regression
            std::vector<int> itm_idx;
            for (int i = 0; i < M; ++i)
                if (intrinsic(paths[i][t]) > 0.0) itm_idx.push_back(i);

            if (itm_idx.empty()) continue;

            // Build basis matrix X and discounted continuation values y
            std::vector<std::vector<double>> X;
            std::vector<double> y;
            for (int i : itm_idx) {
                X.push_back(basis(paths[i][t] / p_.K));
                y.push_back(disc * cashflow[i]);
            }

            // Regress: continuation value ≈ X * coef
            std::vector<double> coef = ols(X, y);

            // Exercise decision
            for (int idx = 0; idx < (int)itm_idx.size(); ++idx) {
                int  i   = itm_idx[idx];
                double cont = dot(coef, X[idx]);
                double exer = intrinsic(paths[i][t]);
                if (exer > cont) cashflow[i] = exer;  // exercise early
                else             cashflow[i] = disc * cashflow[i];
            }
            // Non-ITM paths: just discount
            for (int i = 0; i < M; ++i) {
                bool was_itm = false;
                for (int j : itm_idx) if (j == i) { was_itm = true; break; }
                if (!was_itm) cashflow[i] *= disc;
            }
        }

        // Discount all cashflows back to t=0
        double mean = 0.0, m2 = 0.0;
        for (int i = 0; i < M; ++i) {
            cashflow[i] *= disc;
            double d = cashflow[i] - mean;
            mean += d / (i+1);
            m2   += d * (cashflow[i] - mean);
        }
        double var = m2 / (M-1);
        double se  = std::sqrt(var / M);
        double z95 = 1.96;

        auto t1 = std::chrono::high_resolution_clock::now();
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

        PricingResult res{};
        res.price      = mean;
        res.stderr     = se;
        res.ci_low     = mean - z95 * se;
        res.ci_high    = mean + z95 * se;
        res.elapsed_ms = ms;
        return res;
    }

private:
    MarketParams p_;
    LSMCConfig   cfg_;
};

} // namespace hpc_pricing

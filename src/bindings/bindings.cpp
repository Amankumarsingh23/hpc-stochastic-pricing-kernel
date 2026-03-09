#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <string>
#include <vector>
#include <chrono>

#include "engines/monte_carlo.hpp"
#include "engines/cos_engine.hpp"
#include "engines/lsmc_engine.hpp"

namespace py = pybind11;
using namespace hpc_pricing;

// ─────────────────────────────────────────────────────────────
//  Pybind11 module definition
// ─────────────────────────────────────────────────────────────
PYBIND11_MODULE(hpc_pricing_core, m) {
    m.doc() = R"pbdoc(
        HPC Stochastic Pricing Kernel
        ─────────────────────────────
        High-performance option pricing library.
        Engines: Monte Carlo (OpenMP), COS Method, LSMC (American).
        Supports: European, American, Asian, Barrier, Lookback options.
        Greeks: Delta, Gamma, Vega, Theta, Rho via finite-differences.
    )pbdoc";

    // ── MarketParams ─────────────────────────────────────────
    py::class_<MarketParams>(m, "MarketParams", R"pbdoc(
        Container for market and option parameters.

        Args:
            S (float): Spot price
            K (float): Strike price
            r (float): Risk-free rate (annualised)
            q (float): Continuous dividend yield
            sigma (float): Implied volatility (annualised)
            T (float): Time to maturity in years
    )pbdoc")
        .def(py::init<>())
        .def(py::init([](double S, double K, double r, double q, double sigma, double T) {
            MarketParams p; p.S=S; p.K=K; p.r=r; p.q=q; p.sigma=sigma; p.T=T;
            return p;
        }), py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"),
            py::arg("sigma"), py::arg("T"))
        .def_readwrite("S",     &MarketParams::S)
        .def_readwrite("K",     &MarketParams::K)
        .def_readwrite("r",     &MarketParams::r)
        .def_readwrite("q",     &MarketParams::q)
        .def_readwrite("sigma", &MarketParams::sigma)
        .def_readwrite("T",     &MarketParams::T)
        .def("__repr__", [](const MarketParams& p) {
            return "<MarketParams S=" + std::to_string(p.S)
                 + " K=" + std::to_string(p.K)
                 + " r=" + std::to_string(p.r)
                 + " sigma=" + std::to_string(p.sigma)
                 + " T=" + std::to_string(p.T) + ">";
        });

    // ── MCConfig ─────────────────────────────────────────────
    py::class_<MCConfig>(m, "MCConfig")
        .def(py::init<>())
        .def(py::init([](int paths, int steps, int seed, bool anti) {
            MCConfig c; c.num_paths=paths; c.num_steps=steps;
            c.seed=seed; c.antithetic=anti; return c;
        }), py::arg("num_paths")=100000, py::arg("num_steps")=252,
            py::arg("seed")=42, py::arg("antithetic")=true)
        .def_readwrite("num_paths",  &MCConfig::num_paths)
        .def_readwrite("num_steps",  &MCConfig::num_steps)
        .def_readwrite("seed",       &MCConfig::seed)
        .def_readwrite("antithetic", &MCConfig::antithetic);

    // ── LSMCConfig ───────────────────────────────────────────
    py::class_<LSMCEngine::LSMCConfig>(m, "LSMCConfig")
        .def(py::init<>())
        .def(py::init([](int paths, int steps, int deg, int seed) {
            LSMCEngine::LSMCConfig c;
            c.num_paths=paths; c.num_steps=steps;
            c.poly_deg=deg;    c.seed=seed; return c;
        }), py::arg("num_paths")=50000, py::arg("num_steps")=50,
            py::arg("poly_deg")=3, py::arg("seed")=42)
        .def_readwrite("num_paths", &LSMCEngine::LSMCConfig::num_paths)
        .def_readwrite("num_steps", &LSMCEngine::LSMCConfig::num_steps)
        .def_readwrite("poly_deg",  &LSMCEngine::LSMCConfig::poly_deg)
        .def_readwrite("seed",      &LSMCEngine::LSMCConfig::seed);

    // ── COSConfig ────────────────────────────────────────────
    py::class_<COSEngine::COSConfig>(m, "COSConfig")
        .def(py::init<>())
        .def(py::init([](int N, double L) {
            COSEngine::COSConfig c; c.N=N; c.L=L; return c;
        }), py::arg("N")=256, py::arg("L")=12.0)
        .def_readwrite("N", &COSEngine::COSConfig::N)
        .def_readwrite("L", &COSEngine::COSConfig::L);

    // ── PricingResult ─────────────────────────────────────────
    py::class_<PricingResult>(m, "PricingResult")
        .def(py::init<>())
        .def_readwrite("price",      &PricingResult::price)
        .def_readwrite("stderr",     &PricingResult::stderr)
        .def_readwrite("ci_low",     &PricingResult::ci_low)
        .def_readwrite("ci_high",    &PricingResult::ci_high)
        .def_readwrite("delta",      &PricingResult::delta)
        .def_readwrite("gamma",      &PricingResult::gamma)
        .def_readwrite("vega",       &PricingResult::vega)
        .def_readwrite("theta",      &PricingResult::theta)
        .def_readwrite("rho",        &PricingResult::rho)
        .def_readwrite("elapsed_ms", &PricingResult::elapsed_ms)
        .def("to_dict", [](const PricingResult& r) {
            return py::dict(
                py::arg("price")      = r.price,
                py::arg("stderr")     = r.stderr,
                py::arg("ci_low")     = r.ci_low,
                py::arg("ci_high")    = r.ci_high,
                py::arg("delta")      = r.delta,
                py::arg("gamma")      = r.gamma,
                py::arg("vega")       = r.vega,
                py::arg("theta")      = r.theta,
                py::arg("rho")        = r.rho,
                py::arg("elapsed_ms") = r.elapsed_ms
            );
        })
        .def("__repr__", [](const PricingResult& r) {
            return "<PricingResult price=" + std::to_string(r.price)
                 + " delta=" + std::to_string(r.delta)
                 + " elapsed_ms=" + std::to_string(r.elapsed_ms) + ">";
        });

    // ── MonteCarloEngine ─────────────────────────────────────
    py::class_<MonteCarloEngine>(m, "MonteCarloEngine", R"pbdoc(
        Parallel Monte Carlo pricing engine (OpenMP-accelerated).

        Supports European, Asian, Barrier, and Lookback options.
        Uses antithetic variates for variance reduction.
    )pbdoc")
        .def(py::init<const MarketParams&, const MCConfig&>(),
             py::arg("params"), py::arg("config") = MCConfig{})
        .def("price_european", &MonteCarloEngine::price_european,
             py::arg("option_type"),
             R"pbdoc(Price a European call or put via Monte Carlo.)pbdoc")
        .def("price_asian", &MonteCarloEngine::price_asian,
             py::arg("option_type"),
             R"pbdoc(Price an arithmetic-average Asian option.)pbdoc")
        .def("price_barrier", &MonteCarloEngine::price_barrier,
             py::arg("barrier"),
             R"pbdoc(Price an up-and-out barrier call option.)pbdoc")
        .def("price_lookback", &MonteCarloEngine::price_lookback,
             R"pbdoc(Price a floating-strike lookback call option.)pbdoc")
        .def("compute_greeks", &MonteCarloEngine::compute_greeks,
             py::arg("result"), py::arg("option_type"),
             R"pbdoc(Compute Delta/Gamma/Vega/Theta/Rho via finite differences.)pbdoc");

    // ── COSEngine ────────────────────────────────────────────
    py::class_<COSEngine>(m, "COSEngine", R"pbdoc(
        COS (Fourier-Cosine) Method pricing engine.

        Highly accurate for European options under GBM or Heston model.
        Deterministic — no statistical error. O(N) per pricing call.
    )pbdoc")
        .def(py::init<const MarketParams&, const COSEngine::COSConfig&>(),
             py::arg("params"), py::arg("config") = COSEngine::COSConfig{})
        .def("price", &COSEngine::price,
             py::arg("option_type"),
             py::arg("use_heston") = false,
             py::arg("v0")    = 0.04,
             py::arg("kappa") = 2.0,
             py::arg("theta") = 0.04,
             py::arg("xi")    = 0.3,
             py::arg("rho_h") = -0.7,
             R"pbdoc(Price a European option via COS method. Optionally uses Heston model.)pbdoc")
        .def("compute_greeks", &COSEngine::compute_greeks,
             py::arg("result"), py::arg("option_type"));

    // ── BlackScholesEngine ───────────────────────────────────
    py::class_<BlackScholesEngine>(m, "BlackScholesEngine", R"pbdoc(
        Analytical Black-Scholes engine. Used as ground-truth benchmark.
    )pbdoc")
        .def(py::init<const MarketParams&>(), py::arg("params"))
        .def("price_call", &BlackScholesEngine::price_call)
        .def("price_put",  &BlackScholesEngine::price_put);

    // ── LSMCEngine ───────────────────────────────────────────
    py::class_<LSMCEngine>(m, "LSMCEngine", R"pbdoc(
        Longstaff-Schwartz Monte Carlo for American options.

        Uses Laguerre polynomial regression basis for continuation value
        estimation in the backward induction step.
    )pbdoc")
        .def(py::init<const MarketParams&, const LSMCEngine::LSMCConfig&>(),
             py::arg("params"), py::arg("config") = LSMCEngine::LSMCConfig{})
        .def("price", &LSMCEngine::price,
             py::arg("option_type"),
             R"pbdoc(Price an American call or put via LSMC.)pbdoc");

    // ── Convenience batch pricing function ───────────────────
    m.def("price_surface", [](
        const std::vector<double>& strikes,
        const std::vector<double>& maturities,
        double S, double r, double q, double sigma,
        const std::string& method,
        const std::string& option_type)
    {
        std::vector<std::vector<double>> surface;
        for (double T : maturities) {
            std::vector<double> row;
            for (double K : strikes) {
                MarketParams p; p.S=S; p.K=K; p.r=r; p.q=q; p.sigma=sigma; p.T=T;
                double px = 0.0;
                if (method == "black_scholes") {
                    BlackScholesEngine bs(p);
                    px = (option_type=="call") ? bs.price_call().price : bs.price_put().price;
                } else if (method == "cos") {
                    COSEngine cos(p);
                    px = cos.price(option_type).price;
                } else {
                    MCConfig cfg; cfg.num_paths=10000;
                    MonteCarloEngine mc(p, cfg);
                    px = mc.price_european(option_type).price;
                }
                row.push_back(px);
            }
            surface.push_back(row);
        }
        return surface;
    }, py::arg("strikes"), py::arg("maturities"),
       py::arg("S"), py::arg("r"), py::arg("q"), py::arg("sigma"),
       py::arg("method")="black_scholes", py::arg("option_type")="call",
       R"pbdoc(Batch price an entire vol surface. Returns 2D list [maturity x strike].)pbdoc");

    m.attr("__version__") = "1.0.0";
    m.attr("__author__")  = "HPC Stochastic Pricing Kernel";
}

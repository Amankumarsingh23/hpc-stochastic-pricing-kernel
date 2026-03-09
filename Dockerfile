# ─────────────────────────────────────────────────────────────
# HPC Stochastic Pricing Kernel — Docker Image
# Multi-stage: C++ build → lean Python runtime
# ─────────────────────────────────────────────────────────────

# Stage 1: C++ build environment
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake libgomp1 git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY . .

# Install Python build dependencies
RUN pip install --no-cache-dir pybind11[global] numpy setuptools wheel

# Build C++ extension
RUN pip install --no-cache-dir -e . --no-build-isolation || \
    echo "C++ build failed — Python fallback will be used"

# ─────────────────────────────────────────────────────────────
# Stage 2: Runtime image
FROM python:3.11-slim AS runtime

LABEL maintainer="HPC Stochastic Pricing Kernel"
LABEL description="Option pricing: MC, COS, LSMC via C++/pybind11 + Streamlit"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built artifacts
COPY --from=builder /build /app

# Install runtime Python dependencies
RUN pip install --no-cache-dir \
    numpy>=1.24 \
    scipy>=1.10 \
    pandas>=2.0 \
    streamlit>=1.28 \
    fastapi>=0.104 \
    uvicorn>=0.24 \
    plotly>=5.17 \
    httpx>=0.25 \
    pydantic>=2.0

# Streamlit config
RUN mkdir -p /app/.streamlit
COPY docker/streamlit_config.toml /app/.streamlit/config.toml

# Expose ports: 8501 (Streamlit) + 8000 (FastAPI)
EXPOSE 8501 8000

# Default: run Streamlit dashboard
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]

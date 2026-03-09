cmake_minimum_required(VERSION 3.15)
project(hpc_pricing_kernel VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Release build with full optimisation ────────────────────
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -ffast-math -DNDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG   "-O0 -g -fsanitize=address,undefined")

# ── OpenMP ───────────────────────────────────────────────────
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    message(STATUS "OpenMP found — parallel Monte Carlo enabled")
else()
    message(WARNING "OpenMP not found — single-threaded MC only")
endif()

# ── pybind11 (via pip install pybind11 or cmake) ─────────────
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v2.11.1
    )
    FetchContent_MakeAvailable(pybind11)
endif()

# ── Python extension module ──────────────────────────────────
pybind11_add_module(hpc_pricing_core
    src/bindings/bindings.cpp
)

target_include_directories(hpc_pricing_core PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_features(hpc_pricing_core PRIVATE cxx_std_17)

if(OpenMP_CXX_FOUND)
    target_link_libraries(hpc_pricing_core PRIVATE OpenMP::OpenMP_CXX)
    target_compile_definitions(hpc_pricing_core PRIVATE USE_OPENMP)
endif()

# Aggressive optimisation flags per-target
target_compile_options(hpc_pricing_core PRIVATE
    $<$<CONFIG:Release>:-O3 -march=native -ffast-math -funroll-loops>
    $<$<CXX_COMPILER_ID:MSVC>:/O2 /arch:AVX2 /fp:fast>
)

# ── Install target ───────────────────────────────────────────
install(TARGETS hpc_pricing_core
    COMPONENT python
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_PREFIX}
    RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}
)

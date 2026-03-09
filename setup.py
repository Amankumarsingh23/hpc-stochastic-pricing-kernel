"""
setup.py — HPC Stochastic Pricing Kernel
Builds the C++ pybind11 extension and installs the Python package.
"""
import os
import sys
import subprocess
from pathlib import Path
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext


class CMakeBuild(build_ext):
    """Build the C++ extension via CMake."""

    def build_extension(self, ext):
        ext_fullpath = Path(self.get_ext_fullpath(ext.name))
        extdir = ext_fullpath.parent.resolve()

        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            "-DCMAKE_BUILD_TYPE=Release",
        ]

        build_args = ["--config", "Release", "--parallel", "4"]

        build_temp = Path(self.build_temp) / ext.name
        build_temp.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["cmake", str(Path(__file__).parent)] + cmake_args,
            cwd=build_temp, check=True
        )
        subprocess.run(
            ["cmake", "--build", ".", "--target", "hpc_pricing_core"] + build_args,
            cwd=build_temp, check=True
        )


class CMakeExtension(Extension):
    def __init__(self, name):
        super().__init__(name, sources=[])


setup(
    name="hpc-pricing-kernel",
    version="1.0.0",
    author="HPC Stochastic Pricing Kernel",
    description="High-performance option pricing: Monte Carlo, COS, LSMC via C++/pybind11",
    long_description=open("README.md").read() if Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    ext_modules=[CMakeExtension("hpc_pricing_core")],
    cmdclass={"build_ext": CMakeBuild},
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24",
        "scipy>=1.10",
        "pandas>=2.0",
    ],
    extras_require={
        "dashboard": [
            "streamlit>=1.28",
            "fastapi>=0.104",
            "uvicorn>=0.24",
            "plotly>=5.17",
            "httpx>=0.25",
        ],
        "dev": ["pytest", "black", "mypy"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Office/Business :: Financial",
    ],
)

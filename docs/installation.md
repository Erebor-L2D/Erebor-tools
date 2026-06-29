# Installation

There are two ways to install the L2D Erebor stack:

- **[Quick install (pip / uv)](#quick-install-pip-uv)** — recommended. One command,
  versions pinned for you.
- **[From source (legacy)](#from-source-legacy)** — the manual, repo-by-repo build;
  useful for development (editable installs) or when you need a specific tag.

Either way the native packages (`gpubackendtools`, `lisaanalysistools`, …) compile
C++/CUDA, so install the build prerequisites **first**.

## Prerequisites

- **CMake** and compatible **C++ (C++17 or newer) and Fortran compilers**. If
  `cmake` isn't already on your machine, the platform block below installs it for you.
- **LAPACK / LAPACKE** — see [Making LAPACK findable](#making-lapack-findable-required) below.
- **GPU only:** the matching **CUDA toolkit** on your `PATH`, plus the matching
  `cupy` (`cupy-cuda12x` / `cupy-cuda13x`).

### Making LAPACK findable (required)

The CPU backend links **LAPACKE**, and the build won't find it automatically on
most machines — so point CMake / `pkg-config` at it by exporting two variables
**before** you install. Pick the block matching your setup:

**conda (macOS or Linux):**
```bash
# Create and activate an environment first, if you don't have one yet:
conda create -n erebor python=3.12
conda activate erebor

# CMake, a Fortran compiler, and the full BLAS/LAPACK stack from conda-forge:
conda install -c conda-forge --yes \
  cmake fortran-compiler pkg-config \
  lapack blas blas-devel libblas libcblas liblapack liblapacke libtmglib
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:$CMAKE_PREFIX_PATH"

# Reactivate so conda's compiler vars ($CPPFLAGS, …) are populated, then force
# C++17 — conda's compiler otherwise defaults to an older standard the build rejects:
conda activate erebor
export CXXFLAGS="-std=c++17 $CPPFLAGS"
```

**macOS (Homebrew):**
```bash
brew install cmake lapack   # drop cmake if you already have it
export PKG_CONFIG_PATH="$(brew --prefix lapack)/lib/pkgconfig:$PKG_CONFIG_PATH"
export CMAKE_PREFIX_PATH="$(brew --prefix lapack):$CMAKE_PREFIX_PATH"
```

**Linux (apt / system):**
```bash
sudo apt-get install -y cmake g++ pkg-config liblapack-dev liblapacke-dev
# Usually found on the default path. If the build still can't locate it, point at
# the install prefix, e.g.:
export PKG_CONFIG_PATH="/usr/lib/$(uname -m)-linux-gnu/pkgconfig:$PKG_CONFIG_PATH"
```

!!! note
    If LAPACK still isn't found, `gpubackendtools` falls back to downloading and
    compiling LAPACK from source — the build still succeeds, just more slowly.

!!! tip "C++17 build errors"
    If a native package fails to compile with errors about C++ features needing a
    newer standard, force C++17 **before** installing (the conda block above already
    does this):
    ```bash
    export CXXFLAGS="-std=c++17 $CPPFLAGS"
    ```
    You can also prefix a single command instead: `CXXFLAGS="-std=c++17 $CPPFLAGS" pip install …`

## Quick install (pip / uv)

With the LAPACK variables above exported in your shell:

**pip (works in a conda or plain venv) — straight from git:**
```bash
pip install --extra-index-url https://test.pypi.org/simple/ \
  "erebortools[globalfit] @ git+https://github.com/Erebor-L2D/Erebor-tools.git"
pip install --no-build-isolation   "fastlisaresponse @ git+https://github.com/asantini29/lisa-on-gpu.git@v1.2.1.post1"
```

**pip — from a local clone:**
```bash
git clone https://github.com/Erebor-L2D/Erebor-tools.git
cd Erebor-tools
pip install --extra-index-url https://test.pypi.org/simple/ ".[globalfit]"
pip install --no-build-isolation   "fastlisaresponse @ git+https://github.com/asantini29/lisa-on-gpu.git@v1.2.1.post1"
```

**uv (from a clone):**
```bash
uv pip install ".[globalfit]"
uv pip install --no-build-isolation   "fastlisaresponse @ git+https://github.com/asantini29/lisa-on-gpu.git@v1.2.1.post1"
```
uv reads the TestPyPI index from `pyproject.toml`, so it pulls `phentax`
automatically — no `--extra-index-url` needed. (Plain pip *does* need that flag:
it can't read the index from `pyproject.toml`.)

**Pin a specific Erebor-tools release.** To install a particular tag (or branch)
instead of the default branch, append `@TAG_NAME` to the git URL:
```bash
pip install --extra-index-url https://test.pypi.org/simple/ \
  "erebortools[globalfit] @ git+https://github.com/Erebor-L2D/Erebor-tools.git@TAG_NAME"
```
From a local clone, `git checkout TAG_NAME` before running the `pip`/`uv` install.
Available tags are listed in the [runs catalog](index.md).

The `globalfit` extra pins the whole stack (Eryn, GPUBackendTools,
LISAanalysistools, GBGPU, phentax) at known-good tags. `fastlisaresponse` needs an explicit install for the time being, but the long-term plan is to deprecate it and include the response directly in `lisatools`.

**Check it worked:**
```bash
python -c "import lisatools; print(lisatools.get_backend('cpu'))"
```
On a GPU machine with the matching CUDA toolkit + cupy:
```bash
python -c "import lisatools; print(lisatools.get_backend('cuda_12x'))"  # adjust CUDA version
```

## From source (legacy)

The manual, repo-by-repo build. Prefer this for development (editable `-e`
installs) or to check out a specific `TAG_NAME`. Per-run tags are listed in the
[runs catalog](index.md). Make sure the [LAPACK variables](#making-lapack-findable-required)
are exported first.

### Create and activate a virtual environment
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install scikit_build_core setuptools_scm mojito cython
```
On a GPU machine also install the matching cupy, e.g. `uv pip install cupy-cuda12x`.

### Eryn (the sampler core)
```bash
git clone https://github.com/Erebor-L2D/Eryn
cd Eryn && git checkout gf-dev && cd ..
uv pip install -e Eryn/
```

### GPUBackendTools
All the LISAanalysistools suite relies on it.
```bash
git clone https://github.com/Erebor-L2D/GPUBackendTools.git
cd GPUBackendTools && git checkout TAG_NAME && cd ..   # replace TAG_NAME
```
If `TAG_NAME` is not of the form `vX.Y.Z`, set a pretend version so
`setuptools_scm` is happy:
```bash
SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0 uv pip install -e GPUBackendTools/
```

### LISAanalysistools
```bash
git clone https://github.com/Erebor-L2D/LISAanalysistools.git
cd LISAanalysistools && git checkout TAG_NAME && cd ..
SETUPTOOLS_SCM_PRETEND_VERSION=2.0.0 uv pip install --no-build-isolation LISAanalysistools/
```
(The high pretend version satisfies downstream minimum-version requirements.)
Check:
```bash
uv run python -c "import lisatools; print(lisatools.get_backend('cpu'))"
```

### lisa-on-gpu (the response)
```bash
git clone https://github.com/asantini29/lisa-on-gpu.git   # TODO: Erebor-L2D fork
cd lisa-on-gpu && git checkout TAG_NAME && cd ..
SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0 uv pip install --no-build-isolation lisa-on-gpu/
uv run python -c "import fastlisaresponse; print(fastlisaresponse.get_backend('cpu'))"
```

### GBGPU (galactic-binary waveforms)
```bash
git clone https://github.com/Erebor-L2D/GBGPU.git
cd GBGPU && git checkout TAG_NAME && cd ..
SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0 uv pip install --no-build-isolation GBGPU/
```

### bbhx and phentax
```bash
uv pip install bbhx
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ 'phentax[cpu] == PHENTAX_VERSION'
```
Replace `[cpu]` with `[cuda12]` / `[cuda13]` on a GPU machine.

That's it — you now have the full stack.

## Note on the installation process

These codes are under active development, so the process may change. If you hit
any issue, please open an issue here or email
[the Erebor group](mailto:ereborl2d@googlegroups.com).

*~~ The Erebor group ~~*

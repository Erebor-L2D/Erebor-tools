# Installation instructions
The installation process for this project may not be straightforward, given the necessity of linking the CUDA / C++ code.

We assume you are installing a specific ``TAG_NAME`` version of the codes, provided by the Erebor group to identify a specific global fit run. 
In the same way, we assume you want to install the ``PHENTAX_VERSION`` version of the `phentax` package. We provide a mapping between the global fit runs and the code versions below.

## TAG_NAME and PHENTAX_VERSION
**run 0**: General development and testing of the infrastructure: `TAG_NAME = cdl1-run0`, `PHENTAX_VERSION = 0.1.1b4`

**run 1**: 

**run 2**: 

**run 3**: 

**run 4**: 

**run 5**: 


## Prerequisites
- CMake 
- A compatible C++ compiler
- if you are installing on a GPU machine, you will also need to have the CUDA toolkit installed and visible on your PATH.

## Installation steps
### Creating a virtual environment
We strongly recommend using `uv` for the installation. You can install `uv` using:
```bash 
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then, create a virtual environment in the root of the project and activate the virtual environment:
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install scikit_build_core setuptools_scm mojito cython
```
if you are installing on a GPU machine, you will also need to install the appropriate version of `cupy` for your CUDA toolkit. For example, if you have CUDA 12 installed, you can install `cupy` with:
```bash
uv pip install cupy-cuda12x
```
Replace `cuda12x` with the appropriate version if necessary.
### Cloning the repositories
Before cloning the actual global fit code, install the development branch of the `eryn` sampler:
```bash
git clone https://github.com/Erebor-L2D/Eryn 
cd Eryn
git checkout gf-dev
cd ..
uv pip install -e Eryn/
```
This is the core of `Erebor`.

Then, we need to clone the repository `GPUBackendTools`. All the libraries in the `LISAAnalysistools` suit rely on it.
```bash
git clone git@github.com:Erebor-L2D/GPUBackendTools.git
cd GPUBackendTools
git checkout TAG_NAME # replace with the tag name you want to checkout
cd ..
```
If `TAG_NAME` is not of the form `vX.Y.Z`, we need to work around `setuptools` with the following command:
```bash
SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0 uv pip install -e GPUBackendTools/
```

Then, we can clone the `LISAAnalysistools` repository:
```bash
git clone git@github.com:Erebor-L2D/LISAanalysistools.git
cd LISAanalysistools
git checkout TAG_NAME # replace with the tag name you want to checkout
cd ..
```
Install the `LISAAnalysistools` package with:
```bash
SETUPTOOLS_SCM_PRETEND_VERSION=2.0.0 uv pip install --no-build-isolation LISAanalysistools/ # we need a high version here to comply with the minimum version required by downstream packages
```
You can check the installation worked by running the following command:
```bash
uv run python -c "import lisatools; print(lisatools.get_backend('cpu'))"
```
This should print the CPU backend. If you have a compatible GPU and CUDA toolkit installed with CUDA 11, 12, or 13, you can also check the GPU backend with:
```bash
uv run python -c "import lisatools; print(lisatools.get_backend('cuda_12x')) # replace with the appropriate CUDA version if necessary"
```
We are skipping this here.

We can now install the response code:
```bash
git clone git@github.com:asantini29/lisa-on-gpu.git #NOTE: this will be replaced with a fork on the Erebor-L2D organization
cd lisa-on-gpu
git checkout TAG_NAME # replace with the tag name you want to checkout
cd ..
SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0 uv pip install --no-build-isolation lisa-on-gpu/
```
Again, you can check the installation worked by running the following command:
```bash
uv run python -c "import fastlisaresponse; print(fastlisaresponse.get_backend('cpu'))"
```
Finally, clone and the install the `gbgpu` package, used for galactic binary waveform generation:
```bash
git clone git@github.com:Erebor-L2D/GBGPU.git
cd GBGPU
git checkout TAG_NAME # replace with the tag name you want to checkout
cd ..
SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0 uv pip install --no-build-isolation GBGPU/
``` 

Now install the `bbhx` package, used for useful transformations and proposals:
```bash
uv pip install bbhx
```
and the `phentax` package, currently used for massive black hole binary waveform generation:
```bash
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ 'phentax[cpu] == PHENTAX_VERSION'
```
Replace `[cpu]` with `[cuda12]` or `[cuda13]` if you have a compatible GPU and CUDA toolkit installed.

That should be it! If you have made it this far, you should now have all the necessary packages to interact with our global fit code and results.

## Note on the installation process
As it should expected, all of the codes we have installed are in active development, and not in their final form. This means that the installation process may change in the future. If you encounter any issues during the installation, please reach out one of us or send an email to [our group email](mailto:ereborl2d@googlegroups.com).

*~~ The Erebor group ~~*
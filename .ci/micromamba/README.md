Micromamba
==========

Micromamba is a fast, lightweight package manager compatible with conda packages.  
Read more: https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html  
You can use micromamba to quickly set up a development environment with all required tools.


Files
-----

File                       | Description
-------------------------- | -----------
.ci/micromamba/dev.yaml    | Conda environment specification with all dependencies
.ci/micromamba/init.sh     | Source this script to install micromamba and create environment
.ci/micromamba/uninstall.sh| Script to remove micromamba installation


How to use
----------

### Install & init

To install micromamba and create the development environment:
```bash
source .ci/micromamba/init.sh
```

This script automatically:
- Downloads and installs micromamba to `.ci/micromamba/bin/`
- Creates a conda environment from `dev.yaml`
- Activates the environment

> [!IMPORTANT]
> You must source the `init.sh` script (not just execute it) to properly activate
> the micromamba environment in your current shell session.

For verbose output, use the `-v` or `-vv` flags:
```bash
source .ci/micromamba/init.sh -v
```

### After installation

Once the environment is activated, all tools (Python, Bazel, CodeChecker, clang, etc.) 
are available in your PATH.

To deactivate the environment:
```bash
micromamba deactivate
```

To reactivate later without reinstalling:
```bash
source .ci/micromamba/init.sh
```

### Custom environments

You can create additional environment files (e.g., `prod.yaml`) and activate them:
```bash
source .ci/micromamba/init.sh prod
```

### Uninstall

To completely remove micromamba and all environments:
```bash
bash .ci/micromamba/uninstall.sh
```

Then exit your shell session to complete the cleanup.

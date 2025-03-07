# Flytekit NVIDIA Cloud Functions Plugin

[![CI/CD](https://github.com/ansjindal/flytekitplugins-nvcf/.github/workflows/ci.yml/badge.svg)](https://github.com/ansjindal/flytekitplugins-nvcf/.github/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/flytekitplugins-nvcf.svg)](https://badge.fury.io/py/flytekitplugins-nvcf)
[![codecov](https://codecov.io/gh/ansjindal/flytekitplugins-nvcf/branch/main/graph/badge.svg)](https://codecov.io/gh/ansjindal/flytekitplugins-nvcf)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Flytekit plugin that enables running tasks on NVIDIA Cloud Functions (NVCF).

## Installation

```bash
pip install flytekitplugins-nvcf
```

## Usage

```python
from flytekit import workflow
from flytekitplugins.nvcf import nvcf_task
import os

# Get API key and org name from environment variables
api_key = os.environ.get("NVCF_API_KEY")
org_name = os.environ.get("NGC_ORG")

# Define an NVCF task
my_task = nvcf_task(
    name="my-nvcf-task",
    container_image="nvcr.io/nvidia/pytorch:23.10-py3",
    gpu_specification={
        "gpu": "L40S",
        "instanceType": "gl40s_1.br25_2xlarge",
        "backend": "GFN"
    },
    container_args="python -c 'import torch; print(torch.__version__); print(torch.cuda.is_available())'",
    max_runtime_duration="PT1H",
    result_handling_strategy="UPLOAD",
    results_location="your-org/task-results",
    api_key=api_key,
    org_name=org_name
)

# Define a workflow that uses the NVCF task
@workflow
def my_workflow():
    result = my_task()
    return result
```

## Configuration

The plugin requires the following configuration:

- `NVCF_API_KEY`: Your NVIDIA Cloud Functions API key
- `NGC_ORG`: Your NGC organization name

These can be provided as environment variables or passed directly to the `nvcf_task` function.

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/flytekitplugins-nvcf.git
cd flytekitplugins-nvcf

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
pytest
```

## License

Apache License 2.0

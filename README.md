# Flytekit NVIDIA Cloud Functions Plugin

[![CI/CD](https://github.com/ansjindal/flytekitplugins-nvcf/actions/workflows/ci.yml/badge.svg)](https://github.com/ansjindal/flytekitplugins-nvcf/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/flytekitplugins-nvcf.svg)](https://badge.fury.io/py/flytekitplugins-nvcf)
[![codecov](https://codecov.io/gh/ansjindal/flytekitplugins-nvcf/branch/main/graph/badge.svg)](https://codecov.io/gh/ansjindal/flytekitplugins-nvcf)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Flytekit plugin that enables running tasks on NVIDIA Cloud Functions (NVCF).

## Installation

```bash
pip install flytekitplugins-nvcf
```

## Usage

To use agent locallly, check example `examples/test_agent_directly.py`. Adjust the `NVCF_API_KEY` and `NGC_ORG`. Plus other functions related parameters accordingly. It creates the task, check the status and immediately delete it. We can further extend to monitor the status of task and then delete it.

We have more examples added under example folder as shown below which shows examples of using tasks.
```
examples/
├── basic_task_usage.py
├── basic_task_usage_inference.py
├── t5_text_processor
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   └── requirements.txt
├── tasks_sample
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   └── requirements.txt
└── test_agent_directly.py
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

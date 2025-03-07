# Contributing to flytekitplugins-nvcf

Thank you for considering contributing to the NVIDIA Cloud Functions plugin for Flytekit!

## Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flytekitplugins-nvcf.git
   cd flytekitplugins-nvcf
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Running Tests

Run the tests with pytest:
```bash
pytest
```

To check test coverage:
```bash
pytest --cov
```

## Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting

The pre-commit hooks will automatically check these when you commit.

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Release Process

1. Update version in `setup.py`
2. Create a new tag: `git tag v0.1.0`
3. Push the tag: `git push origin v0.1.0`
4. The CI/CD pipeline will automatically build and publish to PyPI

## License

By contributing, you agree that your contributions will be licensed under the project's Apache 2.0 License.

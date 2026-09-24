# Contributing

Thank you for your interest in contributing to HomePortal!

## How to contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run `ruff check .`, `ruff format --check .` and `pytest`
   (install with `pip install --require-hashes -r requirements.lock` and `pip install pytest pytest-cov`)
5. If you changed `requirements.txt`, regenerate the lock file; CI refuses a lock that does not match:
   `uv pip compile requirements.txt --universal --python-version 3.12 --generate-hashes -o requirements.lock`
6. Commit with a clear message
7. Open a Pull Request

## Code style

- Python: follow PEP 8, use `ruff` for linting
- Keep Docker images minimal

## Reporting bugs

Use the GitHub issue tracker and fill in the bug report template.

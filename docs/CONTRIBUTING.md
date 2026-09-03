# Contributing Guidelines

1. **Fork and Branch**: Create feature branches named `feature/your-feature`.
2. **Adhere to Code Standards**: Follow PEP 8 and include type annotations.
3. **Write Unit Tests**: Add tests to `tests/test_<domain>.py` maintaining >=80% coverage.
4. **Pass Regression**: Ensure `python -m unittest discover -s tests -t .` passes with 0 failures.
5. **Open Pull Request**: Detail the architectural justification and attach test results.

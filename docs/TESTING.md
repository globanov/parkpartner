# ParkPartner Testing Guide

**See also:** [README.md](../README.md) | [Architecture](architecture.md) | [E2E Tests](E2E.md)

## Quick Start

```bash
pytest --cov=app          # Run tests with coverage
pytest tests/system/ -m system  # System tests (needs Ollama, see README.md)
```

## Test Types

| Type | Location | Services |
|------|----------|----------|
| **Unit** | `tests/`, `tests/core/`, `tests/domain/` | Mocked |
| **Integration** | `tests/integration/` | Partial |
| **System** | `tests/system/` | Real |

## System Tests

See [README.md](../README.md#system-tests) for Ollama setup.

For manual testing, start server first:
```bash
python parkpartner.py
```

## Test Markers

Project-specific markers:
- `@pytest.mark.system` - E2E tests
- `@pytest.mark.requires_services` - Needs Ollama/Whisper
- `@pytest.mark.slow` - Slow tests (>1s)

## Troubleshooting

**Tests hang** - Add timeout: `pytest --timeout=60`

**Import errors** - Run from project root: `python -m pytest tests/`

**Cleanup caches:**
```bash
rm -rf .pytest_cache .ruff_cache .coverage_cache/ htmlcov/ logs/*.log
```

---

For pytest options: `pytest --help` | [pytest docs](https://docs.pytest.org/)

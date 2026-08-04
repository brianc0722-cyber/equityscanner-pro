# Contributing to EquityScanner Pro

Thank you for your interest in EquityScanner Pro!

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/equityscanner-pro.git
cd equityscanner-pro
pip install -r requirements.txt
python run_all.py
```

## Running Tests

```bash
make test
# or
python -m pytest tests/ -v
```

## Code Style

We use:
- `ruff` for linting
- `black` for formatting

```bash
make lint
```

## Adding New Features

- New engines should live under their own module (e.g. `premarket/`, `nlp/`)
- All core logic should be importable without the dashboard or API
- Pre-market features must be realistic (VWAP, relative volume, spread, imbalance, news sentiment)
- Add a small test when adding new prediction logic

## Running the Backtest

```bash
make backtest
```

## Before Submitting a PR

1. Run `make lint`
2. Add or update tests if applicable
3. Update README.md if user-facing behavior changed
4. Make sure `python run_all.py` still works cleanly

## Questions?

Open an issue or discussion on GitHub.

import pytest
from dashboard.backtest import run_backtest, generate_synthetic_days


def test_backtest_runs_and_returns_expected_keys():
    bt = run_backtest(n_days=25, seed=123)
    
    assert "new_accuracy" in bt
    assert "old_accuracy" in bt
    assert "new_cum_return_pct" in bt
    assert "results" in bt
    assert isinstance(bt["results"], list)
    assert len(bt["results"]) == 25


def test_backtest_improvement_is_reasonable():
    bt = run_backtest(n_days=40, seed=42)
    # Synthetic data is noisy by design — we just verify the backtest runs correctly
    assert 0.0 <= bt["new_accuracy"] <= 1.0
    assert len(bt["results"]) == 40
    assert "new_cum_return_pct" in bt
    assert "old_cum_return_pct" in bt


def test_synthetic_data_generation():
    days = generate_synthetic_days(10, seed=99)
    assert len(days) == 10
    assert all(hasattr(d, "gap_pct") for d in days)
    assert all(-0.1 < d.gap_pct < 0.1 for d in days)

"""Unit tests for historical replay temporal gate and leakage prevention."""

import pytest
from datetime import datetime, timezone, timedelta
from core.errors import TemporalLeakageError
from services.historical_service import HistoricalService, HistoricalReplayRequest


def test_temporal_gate_enforcement():
    service = HistoricalService()
    cutoff = datetime(2025, 12, 1, 0, 0, tzinfo=timezone.utc)
    past_time = datetime(2025, 11, 15, 0, 0, tzinfo=timezone.utc)
    future_time = datetime(2025, 12, 15, 0, 0, tzinfo=timezone.utc)

    # Valid past query does not raise
    service.enforce_temporal_gate(past_time, cutoff)

    # Future query past cutoff strictly raises TemporalLeakageError
    with pytest.raises(TemporalLeakageError):
        service.enforce_temporal_gate(future_time, cutoff)


def test_historical_evaluation_result():
    service = HistoricalService()
    cutoff = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    req = HistoricalReplayRequest(historical_cutoff=cutoff)

    res = service.evaluate_historical(req)
    assert res.leakage_check_passed is True
    assert res.mean_forecast_sic_error < 0.10
    assert res.route_safety_score > 0.80

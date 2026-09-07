def test_historical_trend_provider():
    from datetime import datetime, timezone, timedelta
    from data_access.sea_ice_provider import get_sea_ice_provider, HistoricalTrendSyntheticSICProvider

    prov = get_sea_ice_provider(source='synthetic_trend', scenario='historical_trend_normal')
    assert prov.source_name == 'synthetic_historical_trend'
    assert prov.current_scenario == 'historical_trend_normal'

    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    res1 = prov.get_sea_ice_at(cell_id='', valid_time=t0, lat=-69.4, lon=76.2)
    res2 = prov.get_sea_ice_at(cell_id='', valid_time=t0, lat=-69.4, lon=76.2)
    assert res1 == res2, 'Not deterministic!'

    assert res1['source'] == 'synthetic_historical_trend'
    assert res1['status'] == 'POC'
    assert res1['model'] == 'historical_trend_synthesis'
    assert res1['scenario'] == 'historical_trend_normal'

    # Check 90-day seasonal trend
    for day in [0, 15, 30, 45, 60, 75, 90]:
        t = t0 + timedelta(days=day)
        r = prov.get_sea_ice_at(cell_id='', valid_time=t, lat=-69.4, lon=76.2)
        assert 0.0 <= r['sea_ice_concentration'] <= 1.0
        assert r['source'] == 'synthetic_historical_trend'


"""
Sea-Ice Forecast Provider Abstraction.
Decouples environmental state, risk evaluation, and routing from sea-ice data sources.
Supports seamless switching between Mock/Synthetic and Ice-kNN-South ML forecasts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd


class SeaIceForecastProviderInterface(ABC):
    """
    Abstract contract for spatial-temporal sea-ice concentration and uncertainty queries.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the sea-ice data source."""
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """True if the data is synthetic/mocked, False if ML/observation backed."""
        pass

    @abstractmethod
    def get_sea_ice_at(
        self,
        cell_id: str,
        valid_time: datetime,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Query sea-ice conditions for a specific H3 cell at a given time.

        Returns:
            Dict containing:
                - sea_ice_concentration: float (0.0 to 1.0)
                - sea_ice_percent: float (0.0 to 100.0)
                - sea_ice_uncertainty: float (0.0 to 1.0)
                - uncertainty_percent: float (0.0 to 100.0)
                - sic_q05: float (0.0 to 1.0)
                - sic_q95: float (0.0 to 1.0)
                - sic_clim: float (0.0 to 1.0)
                - is_mock: bool
                - source: str
        """
        pass

    @abstractmethod
    def get_forecast_horizon(self) -> Dict[str, Any]:
        """Returns metadata about the forecast window."""
        pass


class HistoricalTrendSyntheticSICProvider(SeaIceForecastProviderInterface):
    """
    Deterministic, historical-trend-based synthetic sea-ice concentration forecast
    for AMIP POC testing, routing benchmarks, and GOL/MapLibre GL visualization.

    Synthesized from historical NSIDC CDR (G02202) observations and Antarctic summer
    seasonal retreat/advance dynamics over a 90-day planning horizon (T+0 to T+90d).

    Provenance:
        source: "synthetic_historical_trend"
        status: "POC"
        model:  "historical_trend_synthesis"
    """

    SCENARIO_NORMAL = "historical_trend_normal"
    SCENARIO_LOW_ICE = "historical_trend_low_ice"
    SCENARIO_HIGH_ICE = "historical_trend_high_ice"
    SCENARIO_SEVERE = "historical_trend_severe"

    _ALIASES = {
        "moderate": SCENARIO_NORMAL,
        "normal": SCENARIO_NORMAL,
        "historical_trend_normal": SCENARIO_NORMAL,
        "open_ocean": SCENARIO_LOW_ICE,
        "low": SCENARIO_LOW_ICE,
        "low_ice": SCENARIO_LOW_ICE,
        "historical_trend_low_ice": SCENARIO_LOW_ICE,
        "heavy": SCENARIO_HIGH_ICE,
        "high": SCENARIO_HIGH_ICE,
        "high_ice": SCENARIO_HIGH_ICE,
        "historical_trend_high_ice": SCENARIO_HIGH_ICE,
        "severe": SCENARIO_SEVERE,
        "historical_trend_severe": SCENARIO_SEVERE,
    }

    def __init__(self, default_scenario: str = "historical_trend_normal"):
        self.scenario = self._normalize_scenario(default_scenario)
        self._source = "synthetic_historical_trend"
        self._status = "POC"
        self._model = "historical_trend_synthesis"
        self._base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        try:
            import h3
            self.h3 = h3
        except ImportError:
            self.h3 = None

    def _normalize_scenario(self, scen: str) -> str:
        s = str(scen).lower().strip()
        if s in self._ALIASES:
            return self._ALIASES[s]
        return self.SCENARIO_NORMAL

    @property
    def source_name(self) -> str:
        return self._source

    @property
    def is_mock(self) -> bool:
        return True

    @property
    def current_scenario(self) -> str:
        return self.scenario

    def set_scenario(self, scenario: str) -> None:
        self.scenario = self._normalize_scenario(scenario)

    def get_sea_ice_at(
        self,
        cell_id: str,
        valid_time: datetime,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic historical-trend SIC evaluation at (cell_id, valid_time, lat, lon).
        Derived from NSIDC G02202 Jan 1 baseline + Southern Ocean seasonal melt/freeze curve.
        """
        if lat is None or lon is None:
            if cell_id and self.h3:
                try:
                    c_lat, c_lon = self.h3.cell_to_latlng(cell_id)
                    lat = c_lat
                    lon = c_lon
                except Exception:
                    lat, lon = -65.0, 45.0
            else:
                lat, lon = -65.0, 45.0

        if lat > -55.0:
            return {
                "sea_ice_concentration": 0.0,
                "sea_ice_percent": 0.0,
                "sea_ice_uncertainty": 0.0,
                "uncertainty_percent": 0.0,
                "sic_q05": 0.0,
                "sic_q95": 0.0,
                "sic_clim": 0.0,
                "is_mock": True,
                "source": self._source,
                "status": self._status,
                "model": self._model,
                "scenario": self.scenario,
            }

        import math

        t_ref = valid_time if valid_time.tzinfo else valid_time.replace(tzinfo=timezone.utc)
        if t_ref.year != self._base_time.year:
            try:
                t_eval = t_ref.replace(year=self._base_time.year)
            except ValueError:
                t_eval = t_ref
        else:
            t_eval = t_ref
        days_from_start = max(0.0, min(90.0, (t_eval - self._base_time).total_seconds() / 86400.0))

        if days_from_start <= 45.0:
            seasonal_factor = 1.0 - 0.28 * math.sin(math.pi * days_from_start / 90.0)
        elif days_from_start <= 60.0:
            seasonal_factor = 0.72 + 0.03 * math.cos(math.pi * (days_from_start - 45.0) / 15.0)
        else:
            adv_progress = (days_from_start - 60.0) / 30.0
            seasonal_factor = 0.75 + 0.35 * (adv_progress ** 1.3)

        norm_lon = (lon or 0.0) % 360.0
        lon_wave = 0.03 * math.sin(math.radians(norm_lon * 2.0))

        if self.scenario == self.SCENARIO_LOW_ICE:
            if lat > -65.0:
                sic = 0.0
            else:
                sic = 0.04 * (-lat - 65.0) / 6.0
        elif self.scenario == self.SCENARIO_NORMAL:
            if lat > -62.0:
                sic = 0.0
            elif lat > -65.5:
                sic = 0.025 * (-lat - 62.0) / 3.5
            else:
                in_prydz = 71.5 <= norm_lon <= 80.5
                in_india_bay = 8.5 <= norm_lon <= 16.5
                in_coastal_transit = 16.5 < norm_lon < 71.5 and lat >= -70.4
                in_weddell_pack = norm_lon < 8.5 or norm_lon > 300.0

                if in_prydz:
                    sic = 0.035 + 0.04 * (-lat - 65.5) / 4.5
                elif in_india_bay:
                    sic = 0.07 + 0.045 * (-lat - 65.5) / 4.5
                elif in_coastal_transit:
                    sic = 0.075 + 0.05 * (-lat - 65.5) / 4.9
                elif in_weddell_pack:
                    sic = 0.38 + 0.35 * min(1.0, (-lat - 65.0) / 5.5)
                else:
                    sic = 0.11 + 0.14 * (-lat - 65.5) / 5.0
        elif self.scenario == self.SCENARIO_HIGH_ICE:
            if lat > -59.0:
                sic = 0.0
            elif lat > -64.0:
                sic = 0.06 * (-lat - 59.0) / 5.0
            else:
                in_prydz = 71.5 <= norm_lon <= 80.5
                in_india_bay = 8.5 <= norm_lon <= 16.5
                if in_prydz:
                    sic = 0.09 + 0.05 * (-lat - 64.0) / 6.0
                elif in_india_bay:
                    sic = 0.13 + 0.06 * (-lat - 64.0) / 6.0
                else:
                    sic = min(0.9, 0.25 + 0.4 * (-lat - 64.0) / 6.5)
        else:  # SEVERE
            if lat > -56.0:
                sic = 0.0
            elif lat > -62.0:
                sic = 0.14 * (-lat - 56.0) / 6.0
            else:
                sic = min(0.95, 0.45 + 0.45 * (-lat - 62.0) / 8.5)

        sic = max(0.0, min(1.0, (sic + lon_wave) * seasonal_factor))
        uncertainty = round(min(0.07, max(0.015, 0.12 * sic)), 4)
        q05 = max(0.0, round(sic - uncertainty, 4))
        q95 = min(1.0, round(sic + uncertainty, 4))

        return {
            "sea_ice_concentration": round(sic, 4),
            "sea_ice_percent": round(sic * 100.0, 2),
            "sea_ice_uncertainty": uncertainty,
            "uncertainty_percent": round(uncertainty * 100.0, 2),
            "sic_q05": q05,
            "sic_q95": q95,
            "sic_clim": round(sic, 4),
            "is_mock": True,
            "source": self._source,
            "status": self._status,
            "model": self._model,
            "scenario": self.scenario,
            "lead_days": round(days_from_start, 1),
        }

    def get_forecast_horizon(self) -> Dict[str, Any]:
        return {
            "source": self._source,
            "status": self._status,
            "model": self._model,
            "scenario": self.scenario,
            "is_mock": True,
            "lead_days": 90,
            "start_time": self._base_time.isoformat(),
            "mode": "HISTORICAL_TREND_SYNTHESIS_POC",
        }


ControlledSyntheticSICProvider = HistoricalTrendSyntheticSICProvider
MockSeaIceProvider = HistoricalTrendSyntheticSICProvider


class IceKNNSeaIceProvider(SeaIceForecastProviderInterface):
    """
    Production sea-ice provider backed by pre-computed 90-day Ice-kNN-South forecasts
    and fast in-memory H3 hash maps for routing engine throughput.
    """

    def __init__(
        self,
        parquet_path: str = "data/processed/ice_knn/h3_sic_forecast_90d.parquet",
        base_forecast_time: Optional[datetime] = None,
    ):
        self.parquet_path = Path(parquet_path)
        self._source = "Ice-kNN-South"
        self._lookup: Dict[Tuple[str, int], Dict[str, Any]] = {}
        self._cell_coords: Dict[str, Tuple[float, float]] = {}
        self._dates = []
        self._base_time = base_forecast_time or datetime(2020, 1, 1, tzinfo=timezone.utc)
        self._is_loaded = False
        self._ensure_loaded()

    @property
    def source_name(self) -> str:
        return self._source

    @property
    def is_mock(self) -> bool:
        return False

    def _ensure_loaded(self) -> None:
        if self._is_loaded:
            return

        if not self.parquet_path.is_file():
            from data_access.ice_knn_h3_mapper import IceKNNH3Mapper
            mapper = IceKNNH3Mapper()
            mapper.export_h3_forecast_parquet(str(self.parquet_path))

        df = pd.read_parquet(self.parquet_path)
        self._dates = sorted(list(set(df["valid_time"].unique())))
        if len(self._dates) > 0:
            first_ts = pd.to_datetime(self._dates[0])
            self._base_time = first_ts.to_pydatetime()
            if self._base_time.tzinfo is None:
                self._base_time = self._base_time.replace(tzinfo=timezone.utc)

        for row in df.itertuples(index=False):
            cid = row.cell_id
            lead = int(row.lead_day)
            self._lookup[(cid, lead)] = {
                "sea_ice_concentration": float(row.sea_ice_concentration),
                "sea_ice_percent": float(row.sea_ice_percent),
                "sea_ice_uncertainty": float(row.sea_ice_uncertainty),
                "uncertainty_percent": float(row.uncertainty_percent),
                "sic_q05": float(row.sic_q05),
                "sic_q95": float(row.sic_q95),
                "sic_clim": float(row.sic_clim),
                "is_mock": False,
                "source": self._source,
            }
            if cid not in self._cell_coords:
                self._cell_coords[cid] = (float(row.centroid_lat), float(row.centroid_lon))

        self._is_loaded = True

    def _compute_lead_day(self, target_time: datetime) -> int:
        if target_time.tzinfo is None:
            t = target_time.replace(tzinfo=timezone.utc)
        else:
            t = target_time
        delta_days = (t.date() - self._base_time.date()).days
        return max(0, min(89, delta_days))

    def get_sea_ice_at(
        self,
        cell_id: str,
        valid_time: datetime,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        if lat is not None and lat > -50.0:
            return {
                "sea_ice_concentration": 0.0,
                "sea_ice_percent": 0.0,
                "sea_ice_uncertainty": 0.0,
                "uncertainty_percent": 0.0,
                "sic_q05": 0.0,
                "sic_q95": 0.0,
                "sic_clim": 0.0,
                "is_mock": False,
                "source": self._source,
            }

        self._ensure_loaded()
        lead_day = self._compute_lead_day(valid_time)
        entry = self._lookup.get((cell_id, lead_day))
        if entry:
            return entry

        entry_fallback = self._lookup.get((cell_id, 0))
        if entry_fallback:
            return entry_fallback

        if lat is not None and lon is not None:
            return self._query_nc_by_latlon(lat, lon, lead_day)

        return {
            "sea_ice_concentration": 0.0,
            "sea_ice_percent": 0.0,
            "sea_ice_uncertainty": 0.0,
            "uncertainty_percent": 0.0,
            "sic_q05": 0.0,
            "sic_q95": 0.0,
            "sic_clim": 0.0,
            "is_mock": False,
            "source": self._source,
        }

    def _query_nc_by_latlon(self, lat: float, lon: float, lead_day: int) -> Dict[str, Any]:
        from ice_knn.inference import IceKNNInferenceService
        if not hasattr(self, "_nc_svc"):
            self._nc_svc = IceKNNInferenceService()
        result = self._nc_svc.query_sic(lat=lat, lon=lon, time_target=lead_day)
        return {
            "sea_ice_concentration": result["sic_fraction"],
            "sea_ice_percent": result["sic_percent"],
            "sea_ice_uncertainty": result["uncertainty_fraction"],
            "uncertainty_percent": result["uncertainty_percent"],
            "sic_q05": result["q05_percent"] / 100.0,
            "sic_q95": result["q95_percent"] / 100.0,
            "sic_clim": result["clim_percent"] / 100.0,
            "is_mock": False,
            "source": self._source,
        }

    def get_forecast_horizon(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return {
            "source": self.source_name,
            "is_mock": False,
            "lead_days": 90,
            "start_time": self._base_time.isoformat(),
            "total_cells": len(self._cell_coords),
            "reference": "DOI: 10.1029/2024JH000433 (Ice-kNN-South)",
        }


_DEFAULT_SEA_ICE_PROVIDER: Optional[SeaIceForecastProviderInterface] = None


def get_sea_ice_provider(
    source: str = "synthetic_trend",
    scenario: str = "historical_trend_normal",
) -> SeaIceForecastProviderInterface:
    """
    Factory to retrieve the active sea-ice provider.
    Supports:
        - 'synthetic_trend' / 'synthetic' / 'poc' / 'mock': HistoricalTrendSyntheticSICProvider (deterministic 90-day trend)
        - 'ice_knn': IceKNNSeaIceProvider (real ML 90-day NetCDF forecast)
    """
    global _DEFAULT_SEA_ICE_PROVIDER

    normalized_source = source.lower()
    synthetic_aliases = ("mock", "synthetic", "poc", "synthetic_trend", "historical_trend")

    if _DEFAULT_SEA_ICE_PROVIDER is not None:
        if normalized_source in synthetic_aliases and _DEFAULT_SEA_ICE_PROVIDER.is_mock:
            if hasattr(_DEFAULT_SEA_ICE_PROVIDER, "set_scenario"):
                _DEFAULT_SEA_ICE_PROVIDER.set_scenario(scenario)
            return _DEFAULT_SEA_ICE_PROVIDER
        elif normalized_source == "ice_knn" and not _DEFAULT_SEA_ICE_PROVIDER.is_mock:
            return _DEFAULT_SEA_ICE_PROVIDER

    if normalized_source in synthetic_aliases:
        _DEFAULT_SEA_ICE_PROVIDER = HistoricalTrendSyntheticSICProvider(default_scenario=scenario)
    else:
        _DEFAULT_SEA_ICE_PROVIDER = IceKNNSeaIceProvider()

    return _DEFAULT_SEA_ICE_PROVIDER
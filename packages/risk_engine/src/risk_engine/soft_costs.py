"""Soft environmental cost formulation and factor weighting."""

from typing import Tuple, Optional
import numpy as np
from domain.risk import RiskWeightsConfig


def compute_soft_risk_factors(
    sic_grid: np.ndarray,
    sic_unc_grid: np.ndarray,
    iceberg_hazard_grid: np.ndarray,
    wind_u: np.ndarray,
    wind_v: np.ndarray,
    current_u: np.ndarray,
    current_v: np.ndarray,
    wave_hs: np.ndarray,
    max_navigable_sic: float = 0.85,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Normalizes individual hazard dimensions to [0.0, 1.0].
    Returns:
        r_ice, r_berg, r_wind, r_wave, c_current
    """
    # 1. Sea Ice Soft Risk: Quadratic penalty approaching limit
    r_ice = np.clip((sic_grid / max(0.1, max_navigable_sic)) ** 2.0, 0.0, 1.0)

    # 2. Iceberg Hazard: direct probability density
    r_berg = np.clip(iceberg_hazard_grid, 0.0, 1.0)

    # 3. Wind Risk: Penalizes wind speeds above 25 knots (~12.8 m/s)
    wind_speed = np.sqrt(wind_u ** 2.0 + wind_v ** 2.0)
    r_wind = np.clip((wind_speed - 12.8) / 15.0, 0.0, 1.0)

    # 4. Wave Risk: Smooth logistic penalty above 3.5m wave height
    r_wave = 1.0 / (1.0 + np.exp(-1.5 * (wave_hs - 4.0)))
    r_wave = np.clip(r_wave, 0.0, 1.0)

    # 5. Current Penalty: Normalized adverse current
    current_speed = np.sqrt(current_u ** 2.0 + current_v ** 2.0)
    c_current = np.clip(current_speed / 1.0, 0.0, 1.0) * 0.5

    return r_ice, r_berg, r_wind, r_wave, c_current


def combine_risk_field(
    r_ice: np.ndarray,
    r_berg: np.ndarray,
    r_wind: np.ndarray,
    r_wave: np.ndarray,
    c_current: np.ndarray,
    r_unc: np.ndarray,
    weights: RiskWeightsConfig,
) -> np.ndarray:
    """Combines individual normalized hazard components with configurable weights."""
    composite = (
        weights.weight_sea_ice * r_ice
        + weights.weight_iceberg_hazard * r_berg
        + weights.weight_wind * r_wind
        + weights.weight_waves * r_wave
        + weights.weight_current_cost * c_current
        + weights.weight_uncertainty * r_unc
    )
    total_weight = (
        weights.weight_sea_ice
        + weights.weight_iceberg_hazard
        + weights.weight_wind
        + weights.weight_waves
        + weights.weight_current_cost
        + weights.weight_uncertainty
    )
    if total_weight > 0:
        composite /= total_weight

    return np.clip(composite, 0.0, 1.0)


class SoftCostCalculator:
    """Calculates normalized soft environmental risk factors."""

    def __init__(self, max_navigable_sic: float = 0.85) -> None:
        self.max_navigable_sic = max_navigable_sic

    def compute_factors(
        self,
        sic_grid: np.ndarray,
        sic_unc_grid: np.ndarray,
        iceberg_hazard_grid: np.ndarray,
        wind_u: np.ndarray,
        wind_v: np.ndarray,
        current_u: np.ndarray,
        current_v: np.ndarray,
        wave_hs: np.ndarray,
        max_navigable_sic: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        limit = max_navigable_sic or self.max_navigable_sic
        return compute_soft_risk_factors(
            sic_grid=sic_grid,
            sic_unc_grid=sic_unc_grid,
            iceberg_hazard_grid=iceberg_hazard_grid,
            wind_u=wind_u,
            wind_v=wind_v,
            current_u=current_u,
            current_v=current_v,
            wave_hs=wave_hs,
            max_navigable_sic=limit,
        )

"""Vessel Fuel Consumption Estimator using Naval Architecture Formulations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from domain.vessel import VesselProfile


class FuelModelInterface(ABC):
    """Abstract interface for vessel fuel consumption models."""

    @abstractmethod
    def estimate_fuel_burn(
        self,
        vessel: VesselProfile,
        speed_knots: float,
        duration_hours: float,
        mean_sic: float = 0.0,
        wave_height_m: float = 2.5,
        adverse_current_knots: float = 0.0,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates estimated fuel burn in metric tons (MT).
        Returns:
            fuel_mt (float), explanation_metadata (dict)
        """
        pass


class NavalArchitectureFuelModel(FuelModelInterface):
    """
    Empirical naval architecture fuel consumption model for ORV Sagar Kanya.
    Uses speed-cubed propulsion power laws modulated by ice resistance, wave drag, and currents.
    """

    def estimate_fuel_burn(
        self,
        vessel: VesselProfile,
        speed_knots: float,
        duration_hours: float,
        mean_sic: float = 0.0,
        wave_height_m: float = 2.5,
        adverse_current_knots: float = 0.0,
    ) -> Tuple[float, Dict[str, Any]]:
        if duration_hours <= 0 or speed_knots <= 0:
            return 0.0, {"note": "Zero speed or duration"}

        days = duration_hours / 24.0
        v_cruise = max(4.0, getattr(vessel, "cruising_speed_knots", 10.0))
        base_burn_rate = getattr(
            getattr(vessel, "fuel_params", None),
            "base_burn_rate_mt_per_day",
            16.5,
        )
        aux_burn_rate = getattr(
            getattr(vessel, "fuel_params", None),
            "auxiliary_burn_rate_mt_per_day",
            2.5,
        )

        # Effective speed through water including adverse head current
        v_effective = max(2.0, speed_knots + adverse_current_knots)

        # Speed-cubed propulsion power relationship
        power_ratio = (v_effective / v_cruise) ** 3.0

        # Environmental resistance multiplier:
        # Ice resistance penalty increases non-linearly with concentration
        ice_penalty = 1.0 + (3.2 * (mean_sic ** 2.0))

        # Wave resistance penalty (above 3.0m significant wave height)
        wave_penalty = 1.0 + 0.06 * max(0.0, wave_height_m - 3.0)

        daily_rate_mt = (base_burn_rate * power_ratio * ice_penalty * wave_penalty) + aux_burn_rate
        total_fuel_mt = daily_rate_mt * days

        metadata = {
            "vessel_name": vessel.name,
            "speed_knots": speed_knots,
            "duration_days": round(days, 2),
            "daily_fuel_rate_mt": round(daily_rate_mt, 2),
            "ice_resistance_factor": round(ice_penalty, 3),
            "wave_resistance_factor": round(wave_penalty, 3),
            "power_ratio": round(power_ratio, 3),
            "is_verified_operational": vessel.is_verified_operational,
            "note": "Provisional naval architecture estimate based on speed-cubed power curve. Subject to telemetry calibration.",
        }

        return round(total_fuel_mt, 2), metadata

    def estimate_leg_fuel(
        self,
        vessel: VesselProfile,
        distance_nm: float,
        speed_knots: float,
        sic: float = 0.0,
        wave_height_m: float = 2.5,
        adverse_current_knots: float = 0.0,
    ) -> float:
        """Estimate fuel in metric tons for a single route leg."""
        duration_hours = distance_nm / max(1.0, speed_knots)
        fuel_tonnes, _ = self.estimate_fuel_burn(
            vessel=vessel,
            speed_knots=speed_knots,
            duration_hours=duration_hours,
            mean_sic=sic,
            wave_height_m=wave_height_m,
            adverse_current_knots=adverse_current_knots,
        )
        return fuel_tonnes


default_fuel_model = NavalArchitectureFuelModel()

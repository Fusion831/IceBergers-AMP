"""
Reduced-Order Fuel Consumption Model for Polar Research Vessels.
Calibrated for ORV Sagar Kanya: 433 m3 bunker capacity, 45 days endurance.
Explicitly labeled: 'POC estimate (reduced-order cubic propulsion model + auxiliary hotel load)'.
"""

import math
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from vessel.models import VesselProfile


class FuelRateResult(BaseModel):
    """Instantaneous and transition fuel evaluation result."""
    fuel_rate_mt_per_hour: float = Field(..., description="Hourly fuel consumption in metric tonnes")
    propulsion_rate_mt_per_hour: float = Field(..., description="Hourly propulsion component (speed-dependent)")
    auxiliary_rate_mt_per_hour: float = Field(..., description="Hourly hotel and scientific auxiliary load")
    environmental_multiplier: float = Field(..., description="Multiplier applied due to wave/wind/ice added resistance")
    model_label: str = "POC estimate (reduced-order cubic propulsion model + auxiliary hotel load)"
    fuel_density_t_per_m3: float = 0.850


class FuelConsumptionModel:
    """
    Transparent reduced-order fuel consumption engine.
    Uses Admiralty cubic speed-power scaling for propulsion, plus fixed hotel load.
    """

    def __init__(self, vessel: Optional[VesselProfile] = None):
        self.vessel = vessel

    def evaluate_rate(
        self,
        achievable_speed_knots: float,
        vessel: Optional[VesselProfile] = None,
        wave_resistance_factor: float = 0.0,
        wind_resistance_factor: float = 0.0,
        ice_resistance_factor: float = 0.0,
        requested_speed_knots: Optional[float] = None,
    ) -> FuelRateResult:
        """
        Computes hourly fuel consumption (MT/h) for a given commanded speed and resistance.
        Propulsion power scales cubically with commanded speed, augmented by added resistance
        from waves, wind, and sea ice.
        """
        v = vessel or self.vessel
        if v is None:
            raise ValueError("VesselProfile must be supplied to evaluate fuel consumption.")

        ref_speed = v.cruising_speed_knots  # Default 9.0 knots
        if ref_speed <= 0:
            ref_speed = 9.0

        # Base hourly propulsion rate at nominal cruise speed (~0.28 MT/h for Sagar Kanya)
        base_prop_rate = float(v.endurance_and_fuel.nominal_propulsion_rate_mt_per_hour.value)
        # Constant auxiliary hotel load (~0.06 MT/h)
        hotel_rate = float(v.endurance_and_fuel.hotel_auxiliary_rate_mt_per_hour.value)

        # Commanded speed for engine power calculation (fallback to achievable if not specified)
        cmd_speed = max(0.0, float(requested_speed_knots if requested_speed_knots is not None else achievable_speed_knots))

        if cmd_speed < 0.1:
            # Vessel idling or drifting: propulsion load zero, hotel load active
            prop_rate = 0.0
            env_mult = 1.0
        else:
            # Cubic power scaling law: P ~ V^3 at commanded operating point
            speed_ratio = cmd_speed / ref_speed
            power_ratio = math.pow(speed_ratio, 3.0)
            
            # Environmental resistance addition (waves, winds, sea ice added drag)
            env_mult = 1.0 + max(0.0, wave_resistance_factor) + max(0.0, wind_resistance_factor) + max(0.0, ice_resistance_factor)
            # Cap environmental penalty multiplier at 2.5 to avoid unrealistic unbounded fuel burns
            env_mult = min(2.5, env_mult)

            prop_rate = base_prop_rate * power_ratio * env_mult

        total_rate = prop_rate + hotel_rate

        return FuelRateResult(
            fuel_rate_mt_per_hour=round(total_rate, 4),
            propulsion_rate_mt_per_hour=round(prop_rate, 4),
            auxiliary_rate_mt_per_hour=round(hotel_rate, 4),
            environmental_multiplier=round(env_mult, 3),
        )

    def evaluate_transit_fuel(
        self,
        achievable_speed_knots: float,
        transit_duration_hours: float,
        vessel: Optional[VesselProfile] = None,
        wave_resistance_factor: float = 0.0,
        wind_resistance_factor: float = 0.0,
        ice_resistance_factor: float = 0.0,
        requested_speed_knots: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes total fuel used over a specific leg duration.
        """
        rate_res = self.evaluate_rate(
            achievable_speed_knots=achievable_speed_knots,
            vessel=vessel,
            wave_resistance_factor=wave_resistance_factor,
            wind_resistance_factor=wind_resistance_factor,
            ice_resistance_factor=ice_resistance_factor,
            requested_speed_knots=requested_speed_knots,
        )

        hours = max(0.0, transit_duration_hours)
        fuel_mt = rate_res.fuel_rate_mt_per_hour * hours
        fuel_m3 = fuel_mt / rate_res.fuel_density_t_per_m3

        return {
            "fuel_rate_mt_per_hour": rate_res.fuel_rate_mt_per_hour,
            "propulsion_rate_mt_per_hour": rate_res.propulsion_rate_mt_per_hour,
            "auxiliary_rate_mt_per_hour": rate_res.auxiliary_rate_mt_per_hour,
            "environmental_multiplier": rate_res.environmental_multiplier,
            "fuel_used_mt": round(fuel_mt, 4),
            "fuel_used_m3": round(fuel_m3, 4),
            "transit_duration_hours": round(hours, 3),
            "model_label": rate_res.model_label,
        }


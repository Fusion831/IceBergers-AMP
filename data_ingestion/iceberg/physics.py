"""
Lagrangian iceberg drift force and momentum formulation.
Implements relative ocean drag, relative atmospheric drag, Southern Hemisphere Coriolis,
and non-linear sea-ice pack interaction for tabular and non-tabular icebergs.
"""

from typing import Tuple, Optional, Dict, Any
import math
import numpy as np

# Physical constants
OMEGA_EARTH = 7.292115e-5  # Earth angular velocity (rad/s)
RHO_WATER = 1027.0          # Seawater density (kg/m^3)
RHO_AIR = 1.25              # Surface air density (kg/m^3)
RHO_ICE = 900.0             # Glacial ice density (kg/m^3)
G_ACCEL = 9.81              # Gravitational acceleration (m/s^2)


class IcebergPhysicalProfile:
    """Dimensions and mass estimation for an individual iceberg."""

    def __init__(
        self,
        length_m: float = 1000.0,
        width_m: float = 500.0,
        thickness_m: float = 230.0,
        water_drag_coeff: float = 1.0,
        air_drag_coeff: float = 1.3,
    ):
        self.length_m = max(50.0, float(length_m))
        self.width_m = max(50.0, float(width_m))
        self.thickness_m = max(20.0, float(thickness_m))
        self.water_drag_coeff = water_drag_coeff
        self.air_drag_coeff = air_drag_coeff

        # Hydrostatic equilibrium (Archimedes)
        self.draft_m = self.thickness_m * (RHO_ICE / RHO_WATER)
        self.freeboard_m = self.thickness_m - self.draft_m

        # Mass calculation (tabular slab approximation)
        self.volume_m3 = self.length_m * self.width_m * self.thickness_m
        self.mass_kg = self.volume_m3 * RHO_ICE

        # Effective cross-sectional areas
        char_dim = math.sqrt(self.length_m * self.width_m)
        self.area_underwater_m2 = char_dim * self.draft_m
        self.area_abovewater_m2 = char_dim * self.freeboard_m


class IcebergPhysicsEngine:
    """Calculates instantaneous forces and accelerations acting on an iceberg."""

    def __init__(self, profile: Optional[IcebergPhysicalProfile] = None):
        self.profile = profile or IcebergPhysicalProfile()

    def coriolis_parameter(self, lat_deg: float) -> float:
        """
        Calculates Coriolis parameter f = 2 * Omega * sin(latitude).
        Units: rad/s.
        In the Southern Hemisphere (lat < 0), f is strictly negative.
        """
        phi_rad = math.radians(lat_deg)
        return 2.0 * OMEGA_EARTH * math.sin(phi_rad)

    def coriolis_acceleration(
        self,
        u_mps: float,
        v_mps: float,
        lat_deg: float,
    ) -> Tuple[float, float]:
        """
        Calculates Coriolis acceleration vector (a_x, a_y) in m/s^2.
        Equations:
          a_x = + f * v
          a_y = - f * u
        Verification: In Southern Hemisphere (f < 0), motion northward (v > 0, u = 0)
        yields a_x = f * v < 0 (deflection to the left / West).
        """
        f = self.coriolis_parameter(lat_deg)
        a_x = f * v_mps
        a_y = -f * u_mps
        return a_x, a_y

    def ocean_drag_acceleration(
        self,
        u_ice: float,
        v_ice: float,
        u_ocean: float,
        v_ocean: float,
    ) -> Tuple[float, float]:
        """
        Calculates ocean form drag acceleration based on relative water velocity:
          V_rel = V_ocean - V_ice
          F_ocean = 0.5 * rho_w * C_w * A_w * |V_rel| * V_rel
          a_ocean = F_ocean / M
        """
        rel_u = u_ocean - u_ice
        rel_v = v_ocean - v_ice
        rel_speed = math.hypot(rel_u, rel_v)

        if rel_speed < 1e-6:
            return 0.0, 0.0

        force_factor = 0.5 * RHO_WATER * self.profile.water_drag_coeff * self.profile.area_underwater_m2
        accel_factor = (force_factor * rel_speed) / self.profile.mass_kg

        a_x = accel_factor * rel_u
        a_y = accel_factor * rel_v
        return a_x, a_y

    def atmospheric_drag_acceleration(
        self,
        u_ice: float,
        v_ice: float,
        u_wind: float,
        v_wind: float,
    ) -> Tuple[float, float]:
        """
        Calculates atmospheric form drag acceleration based on relative wind velocity:
          V_rel = V_wind - V_ice
          F_air = 0.5 * rho_a * C_a * A_a * |V_rel| * V_rel
          a_air = F_air / M
        """
        rel_u = u_wind - u_ice
        rel_v = v_wind - v_ice
        rel_speed = math.hypot(rel_u, rel_v)

        if rel_speed < 1e-6:
            return 0.0, 0.0

        force_factor = 0.5 * RHO_AIR * self.profile.air_drag_coeff * self.profile.area_abovewater_m2
        accel_factor = (force_factor * rel_speed) / self.profile.mass_kg

        a_x = accel_factor * rel_u
        a_y = accel_factor * rel_v
        return a_x, a_y

    def sea_ice_interaction_acceleration(
        self,
        u_ice: float,
        v_ice: float,
        u_ocean: float,
        v_ocean: float,
        u_wind: float,
        v_wind: float,
        sic: float,
    ) -> Tuple[float, float]:
        """
        Calculates sea-ice interaction force:
        - SIC < 0.15: Free drift (a = 0)
        - 0.15 <= SIC <= 0.85: Viscous pack resistance dampening relative velocity towards sea-ice drift
        - SIC > 0.85: Compact pack ice heavily constraining iceberg motion to sea ice drift
        """
        if sic < 0.15:
            return 0.0, 0.0

        # Estimated sea ice drift velocity (empirical free drift rule: 2% wind + 100% surface current)
        u_si = u_ocean + 0.02 * u_wind
        v_si = v_ocean + 0.02 * v_wind

        rel_u = u_si - u_ice
        rel_v = v_si - v_ice

        # Resistance damping coefficient scales non-linearly with ice concentration
        damping_rate = 1.0e-4 * (sic ** 2)
        a_x = damping_rate * rel_u
        a_y = damping_rate * rel_v
        return a_x, a_y

    def total_acceleration(
        self,
        u_ice: float,
        v_ice: float,
        lat_deg: float,
        u_ocean: float,
        v_ocean: float,
        u_wind: float,
        v_wind: float,
        sic: float = 0.0,
    ) -> Tuple[float, float]:
        """
        Computes net horizontal acceleration (a_x, a_y) in m/s^2 from all active physical forces:
          a_net = a_ocean + a_air + a_coriolis + a_sea_ice
        """
        a_oc_x, a_oc_y = self.ocean_drag_acceleration(u_ice, v_ice, u_ocean, v_ocean)
        a_at_x, a_at_y = self.atmospheric_drag_acceleration(u_ice, v_ice, u_wind, v_wind)
        a_cor_x, a_cor_y = self.coriolis_acceleration(u_ice, v_ice, lat_deg)
        a_si_x, a_si_y = self.sea_ice_interaction_acceleration(u_ice, v_ice, u_ocean, v_ocean, u_wind, v_wind, sic)

        total_ax = a_oc_x + a_at_x + a_cor_x + a_si_x
        total_ay = a_oc_y + a_at_y + a_cor_y + a_si_y
        return total_ax, total_ay

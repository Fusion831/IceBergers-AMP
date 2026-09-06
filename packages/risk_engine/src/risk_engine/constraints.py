"""Hard navigational constraints evaluation."""

from typing import Optional, Tuple, Any
import numpy as np
from domain.vessel import VesselProfile


def evaluate_hard_constraints(
    depth_grid: np.ndarray,
    sic_grid: np.ndarray,
    iceberg_hazard_grid: np.ndarray,
    vessel: VesselProfile,
    min_depth_margin_m: float = 3.0,
    max_navigable_sic: float = 0.85,
    critical_iceberg_threshold: float = 0.85,
) -> np.ndarray:
    """
    Evaluates binary hard constraints for all spatial cells.
    Returns:
        impassable_mask (boolean 2D array, True where cell is strictly forbidden/inaccessible).
    """
    # 1. Land and grounded ice shelf mask (bathymetry <= 0m means land/ice above sea level)
    land_mask = depth_grid <= 0.0

    # 2. Bathymetric clearance violation: depth < vessel draft + under-keel safety margin
    draft = getattr(vessel, "draft_meters", getattr(vessel, "draft_m", 5.6))
    min_safe_depth = draft + min_depth_margin_m
    shallow_mask = (depth_grid > 0.0) & (depth_grid < min_safe_depth)

    # 3. Impenetrable sea-ice concentration: SIC exceeds vessel structural capability
    heavy_ice_mask = sic_grid > max_navigable_sic

    # 4. Critical iceberg density: areas with near-certain collision hazard
    extreme_berg_mask = iceberg_hazard_grid > critical_iceberg_threshold

    # Composite impassable boolean mask
    impassable_mask = land_mask | shallow_mask | heavy_ice_mask | extreme_berg_mask
    return impassable_mask


class HardConstraintChecker:
    """Point-wise and grid-wise hard constraint validator."""

    def __init__(self, min_depth_margin_m: float = 3.0, max_navigable_sic: float = 0.85) -> None:
        self.min_depth_margin_m = min_depth_margin_m
        self.max_navigable_sic = max_navigable_sic

    def check_point(
        self,
        point: Any,
        depth_m: float,
        sic: float,
        iceberg_dist_nm: float = 10.0,
        vessel: Optional[VesselProfile] = None,
        is_land: bool = False,
    ) -> Tuple[bool, str]:
        """Check if a specific coordinate violates hard navigational constraints."""
        if is_land or depth_m <= 0.0:
            return True, "Land/ice shelf barrier"

        draft = 5.6
        if vessel:
            draft = getattr(vessel, "draft_meters", getattr(vessel, "draft_m", 5.6))
            margin = getattr(vessel, "ice_clearance_depth_margin_m", self.min_depth_margin_m)
        else:
            margin = self.min_depth_margin_m

        if depth_m < (draft + margin):
            return True, f"Shallow bathymetry: depth {depth_m}m is less than draft+margin ({draft + margin}m)"

        if sic > self.max_navigable_sic:
            return True, f"Sea ice concentration {sic:.2f} exceeds limit {self.max_navigable_sic:.2f}"

        if iceberg_dist_nm < 0.5:
            return True, f"Within critical iceberg exclusion zone ({iceberg_dist_nm:.2f} NM < 0.5 NM)"

        return False, ""

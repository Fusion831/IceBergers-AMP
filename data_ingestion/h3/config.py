"""
Configuration for AMIP Canonical H3 Spatial Grid and Temporal Integration.
Supports runtime configurability of H3 resolution, domain bounds, and time steps.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Any


@dataclass
class H3Config:
    """Configuration parameters for H3 spatial and temporal integration."""

    # POC Starting Resolution (configurable via AMIP_H3_RESOLUTION)
    resolution: int = field(
        default_factory=lambda: int(os.environ.get("AMIP_H3_RESOLUTION", "5"))
    )

    # Canonical temporal step in hours (configurable via AMIP_TEMPORAL_STEP_HOURS)
    temporal_step_hours: int = field(
        default_factory=lambda: int(os.environ.get("AMIP_TEMPORAL_STEP_HOURS", "6"))
    )

    # Primary Antarctic Domain (covers Southern Ocean and all Antarctic margins)
    # -80.0°S to -40.0°S, all longitudes
    primary_domain_lat_min: float = -80.0
    primary_domain_lat_max: float = -40.0
    primary_domain_lon_min: float = -180.0
    primary_domain_lon_max: float = 180.0

    # Cape Town to Antarctica Navigation Corridor
    # -40.0°S to -33.5°S, 15.0°E to 25.0°E
    corridor_lat_min: float = -40.0
    corridor_lat_max: float = -33.5
    corridor_lon_min: float = 15.0
    corridor_lon_max: float = 25.0

    # Geographic blocking threshold for cell navigability (fraction >= 0.5 is blocked)
    default_blocking_threshold: float = 0.5

    # Storage paths
    data_root: Path = field(default_factory=lambda: Path("data"))
    antarctica_root: Path = field(default_factory=lambda: Path("data/antarctica"))
    grid_dir: Path = field(default_factory=lambda: Path("data/antarctica/grid"))
    env_dir: Path = field(default_factory=lambda: Path("data/antarctica/environment"))
    iceberg_dir: Path = field(default_factory=lambda: Path("data/antarctica/icebergs"))
    hazard_dir: Path = field(default_factory=lambda: Path("data/antarctica/hazard"))
    validation_dir: Path = field(default_factory=lambda: Path("data/validation/h3"))

    def ensure_directories(self) -> None:
        """Ensures all output directories exist."""
        for d in [
            self.grid_dir,
            self.env_dir,
            self.iceberg_dir,
            self.hazard_dir,
            self.validation_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


default_h3_config = H3Config()

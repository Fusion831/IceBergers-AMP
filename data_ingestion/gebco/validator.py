"""
Quality and Validation Subsystem for GEBCO Bathymetry Data.
Enforces AMIP data contracts:
- Water depth must be strictly positive (> 0.0 m) for all ocean cells.
- Land/ice cells must be NaN, not collapsed to 0.0 m.
- Coordinates must be monotonic, within valid spatial bounds, and free of missing values.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
import numpy as np
import xarray as xr
from core.logging import get_logger

logger = get_logger("data_ingestion.gebco.validator")


class GEBCOValidationError(Exception):
    """Raised when a GEBCO bathymetry dataset fails data contract validation."""
    pass


class GEBCOValidator:
    """
    Validates processed GEBCO NetCDF datasets against strict AMIP navigation requirements.
    """

    def __init__(self, report_dir: Optional[Union[str, Path]] = None):
        self.report_dir = Path(report_dir or "data/validation/gebco")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, processed_nc_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Executes comprehensive validation of the processed bathymetry dataset.

        Returns:
            Dict containing detailed validation metrics, boolean 'passed', and 'errors'.
        """
        nc_path = Path(processed_nc_path)
        if not nc_path.exists():
            raise FileNotFoundError(f"File not found: {nc_path}")

        errors = []
        warnings = []
        metrics = {}

        with xr.open_dataset(nc_path) as ds:
            # 1. Variable and Dimension checks
            required_vars = ["depth_m", "is_land", "is_ocean"]
            for v in required_vars:
                if v not in ds.data_vars:
                    errors.append(f"Missing required data variable: '{v}'")

            for coord in ["lat", "lon"]:
                if coord not in ds.coords:
                    errors.append(f"Missing required coordinate: '{coord}'")

            if errors:
                return self._finalize_report(nc_path, False, errors, warnings, metrics)

            lats = ds["lat"].values
            lons = ds["lon"].values
            depth = ds["depth_m"].values
            is_land = ds["is_land"].values.astype(bool)
            is_ocean = ds["is_ocean"].values.astype(bool)

            # 2. Coordinate validations
            if np.isnan(lats).any() or np.isnan(lons).any():
                errors.append("Coordinate arrays contain NaN values")

            if not np.all(np.diff(lats) > 0):
                errors.append("Latitude coordinates are not strictly monotonically increasing")

            if not np.all(np.diff(lons) > 0):
                errors.append("Longitude coordinates are not strictly monotonically increasing")

            if lats.min() < -90.0 or lats.max() > 90.0:
                errors.append(f"Latitude out of bounds [-90, 90]: [{lats.min()}, {lats.max()}]")

            if lons.min() < -180.0 or lons.max() > 180.0:
                errors.append(f"Longitude out of bounds [-180, 180]: [{lons.min()}, {lons.max()}]")

            metrics["spatial_extent"] = {
                "lat_min": float(lats.min()),
                "lat_max": float(lats.max()),
                "lon_min": float(lons.min()),
                "lon_max": float(lons.max()),
                "grid_shape": [int(len(lats)), int(len(lons))],
            }

            # 3. Bathymetry Depth Validations
            ocean_depths = depth[is_ocean]
            nan_ocean_count = int(np.isnan(ocean_depths).sum())
            if nan_ocean_count > 0:
                errors.append(f"Found {nan_ocean_count} NaN values in cells marked as is_ocean")

            valid_depths = ocean_depths[~np.isnan(ocean_depths)]
            if len(valid_depths) == 0:
                errors.append("No valid ocean depth values found in dataset")
            else:
                min_depth = float(np.min(valid_depths))
                max_depth = float(np.max(valid_depths))

                # Water depth must be strictly positive (> 0.0 m)
                if min_depth <= 0.0:
                    errors.append(f"Ocean depth contains non-positive values (min={min_depth} m). Expected depth > 0.0 m.")

                # Physical depth limits (deepest ocean is Mariana Trench ~11,000m)
                if max_depth > 11000.0:
                    errors.append(f"Ocean depth exceeds physical maximum of 11,000 m (max={max_depth} m)")

                metrics["depth_stats"] = {
                    "min_m": round(min_depth, 2),
                    "max_m": round(max_depth, 2),
                    "mean_m": round(float(np.mean(valid_depths)), 2),
                    "median_m": round(float(np.median(valid_depths)), 2),
                    "p10_m": round(float(np.percentile(valid_depths, 10)), 2),
                    "p90_m": round(float(np.percentile(valid_depths, 90)), 2),
                }

            # 4. Land Mask Validations
            land_depths = depth[is_land]
            non_nan_land_count = int((~np.isnan(land_depths)).sum())
            if non_nan_land_count > 0:
                errors.append(
                    f"Found {non_nan_land_count} non-NaN depth values on land cells. "
                    "Land cells must be strictly masked as NaN."
                )

            # Check for false zero depths
            zero_count = int((depth == 0.0).sum())
            if zero_count > 0:
                warnings.append(
                    f"Found {zero_count} exact 0.0m depth cells. Verify whether these represent true sea level shoreline."
                )

            metrics["cell_counts"] = {
                "total": int(depth.size),
                "ocean": int(is_ocean.sum()),
                "land": int(is_land.sum()),
                "exact_zero": zero_count,
            }

        passed = len(errors) == 0
        return self._finalize_report(nc_path, passed, errors, warnings, metrics)

    def _finalize_report(
        self,
        file_path: Path,
        passed: bool,
        errors: list,
        warnings: list,
        metrics: dict,
    ) -> Dict[str, Any]:
        report = {
            "file": str(file_path),
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "metrics": metrics,
        }

        report_file = self.report_dir / f"{file_path.stem}_validation.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        if not passed:
            logger.error("GEBCO validation failed", errors=errors)
        else:
            logger.info("GEBCO validation passed successfully", metrics=metrics)

        return report

"""
Validation suite and visualization generator for processed NSIDC Antarctic SIC datasets.
Confirms physical validity, geographic orientation, coordinate accuracy, and provenance.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from core.logging import get_logger

logger = get_logger("data_ingestion.nsidc.validator")


class NSIDCValidator:
    """
    Validates processed NSIDC SIC datasets and produces visual validation maps.
    """

    @staticmethod
    def validate_dataset(processed_file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Runs comprehensive scientific validation checks on a processed NetCDF file.
        Returns a dictionary of check results, raising AssertionError if critical checks fail.
        """
        p = Path(processed_file_path)
        if not p.exists():
            raise FileNotFoundError(f"Processed file not found: {p}")

        report = {"file": str(p), "checks_passed": True, "details": {}}

        with xr.open_dataset(p) as ds:
            # 1. Variables check
            required_vars = ["sea_ice_concentration", "surface_type", "latitude", "longitude", "crs"]
            for v in required_vars:
                assert v in ds, f"Missing required variable '{v}' in processed dataset"
            report["details"]["variables_present"] = True

            # 2. Dimensions check
            assert "y" in ds.dims and "x" in ds.dims, "Missing spatial dimensions 'y' and 'x'"
            assert ds.sizes["y"] == 332, f"Expected 332 y-cells, got {ds.sizes['y']}"
            assert ds.sizes["x"] == 316, f"Expected 316 x-cells, got {ds.sizes['x']}"
            report["details"]["dimensions_valid"] = True

            # 3. Coordinate bounds check
            lats = ds["latitude"].values
            lons = ds["longitude"].values

            lat_min, lat_max = float(np.nanmin(lats)), float(np.nanmax(lats))
            lon_min, lon_max = float(np.nanmin(lons)), float(np.nanmax(lons))

            assert -90.0 <= lat_min <= -89.0, f"South Pole latitude bounds invalid: {lat_min}"
            assert -40.0 <= lat_max <= -38.0, f"Northern edge latitude bounds invalid: {lat_max}"
            assert -180.0 <= lon_min <= -170.0, f"Longitude min invalid: {lon_min}"
            assert 170.0 <= lon_max <= 180.0, f"Longitude max invalid: {lon_max}"
            report["details"]["spatial_bounds"] = {
                "lat_min": lat_min,
                "lat_max": lat_max,
                "lon_min": lon_min,
                "lon_max": lon_max,
            }

            # 4. Physical SIC range check
            sic = ds["sea_ice_concentration"].values[0]
            st = ds["surface_type"].values

            ocean_mask = st == 50
            land_mask = (st == 250) | (st == 200)

            # Ocean pixels must have valid values in [0.0, 100.0]
            ocean_sic = sic[ocean_mask]
            assert not np.isnan(ocean_sic).any(), "Ocean contains unexpected NaN values"
            assert np.min(ocean_sic) >= 0.0, f"SIC below 0% detected: {np.min(ocean_sic)}"
            assert np.max(ocean_sic) <= 100.0, f"SIC above 100% detected: {np.max(ocean_sic)}"

            # Land pixels must be NaN
            land_sic = sic[land_mask]
            assert np.isnan(land_sic).all(), "Land contains non-NaN SIC values"
            report["details"]["physical_ranges_valid"] = True

            # 5. Provenance attributes check
            required_attrs = ["title", "source_dataset", "spatial_crs", "processing_timestamp"]
            for attr in required_attrs:
                assert attr in ds.attrs, f"Missing provenance attribute '{attr}'"
            report["details"]["provenance_valid"] = True

        logger.info("Validation passed successfully", file=str(p))
        return report

    @staticmethod
    def generate_validation_plot(
        processed_file_path: Union[str, Path],
        output_image_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Generates and saves a two-panel visual validation map:
        1. Native polar stereographic view with land contours and sea ice concentration.
        2. Geographic lat/lon scatter verification.
        """
        p = Path(processed_file_path)
        out_img = Path(output_image_path or "data/validation/nsidc/antarctica_sic_validation.png")
        out_img.parent.mkdir(parents=True, exist_ok=True)

        with xr.open_dataset(p) as ds:
            sic = ds["sea_ice_concentration"].values[0]
            st = ds["surface_type"].values
            lats = ds["latitude"].values
            lons = ds["longitude"].values
            time_str = str(ds["time"].values[0])[:10] if "time" in ds else "Unknown Date"

        fig, axs = plt.subplots(1, 2, figsize=(15, 6.5))

        # Panel 1: Native Polar Stereographic view
        im0 = axs[0].imshow(sic, origin="upper", cmap="Blues_r", vmin=0, vmax=100)
        axs[0].set_title(f"Antarctic Sea Ice Concentration (%)\nDate: {time_str} (Native EPSG:3412 Grid)")
        cbar0 = plt.colorbar(im0, ax=axs[0], label="Sea Ice Concentration (%)")

        # Overlay land boundary
        land_mask = (st == 250) | (st == 200)
        axs[0].contour(land_mask, levels=[0.5], colors="red", linewidths=0.7)
        axs[0].text(
            157,
            173,
            "South Pole",
            color="yellow",
            fontweight="bold",
            ha="center",
            va="center",
            fontsize=8,
        )

        # Panel 2: Geographic Projection Check (Scatter sample)
        step = 3
        im1 = axs[1].scatter(
            lons[::step, ::step],
            lats[::step, ::step],
            c=sic[::step, ::step],
            cmap="Blues_r",
            s=4,
            vmin=0,
            vmax=100,
        )
        axs[1].set_title(f"Geographic Coordinate Verification\nLatitude vs Longitude ({time_str})")
        axs[1].set_xlabel("Longitude (°E)")
        axs[1].set_ylabel("Latitude (°N)")
        axs[1].set_ylim(-90, -38)
        axs[1].set_xlim(-180, 180)
        cbar1 = plt.colorbar(im1, ax=axs[1], label="Sea Ice Concentration (%)")

        plt.tight_layout()
        plt.savefig(out_img, dpi=150)
        plt.close(fig)

        logger.info("Validation map saved successfully", path=str(out_img))
        return out_img

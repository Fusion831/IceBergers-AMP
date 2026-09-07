"""
Validation visualizer for Antarctic Geographic Mask.
Produces diagnostic maps for land, ice shelves, combined classifications,
H3 grid overlays, and the 60°S source coverage boundary.
"""

from pathlib import Path
from typing import Optional, Union, Sequence
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
import numpy as np
import geopandas as gpd
import pyproj
from shapely.geometry import Polygon
import h3
from core.logging import get_logger
from data_ingestion.geographic_mask.h3_mask import H3GeographicMaskAggregator
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask

logger = get_logger("data_ingestion.geographic_mask.visualizer")


class GeographicMaskVisualizer:
    """Generates diagnostic validation maps for SCAR ADD geographic mask."""

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
    ):
        self.output_dir = Path(output_dir or "data/validation/geographic_mask")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.to_epsg3031 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3031", always_xy=True)

    def plot_land_polygons(self, gdf: gpd.GeoDataFrame) -> Path:
        """Visualizes continental land polygons in native EPSG:3031."""
        out_path = self.output_dir / "antarctic_land_polygons.png"
        land_gdf = gdf[gdf["surface"] == "land"]
        
        fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
        ax.set_facecolor("#0b192c")
        land_gdf.plot(ax=ax, color="#4a5568", edgecolor="#718096", linewidth=0.2)
        
        ax.set_title("SCAR ADD v7.12 - Antarctic Land Polygons (EPSG:3031)", color="white", fontsize=14, pad=15)
        ax.set_xlabel("Polar Stereographic X (metres)", color="white", fontsize=10)
        ax.set_ylabel("Polar Stereographic Y (metres)", color="white", fontsize=10)
        ax.tick_params(colors="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved land validation map", path=str(out_path))
        return out_path

    def plot_ice_shelves(self, gdf: gpd.GeoDataFrame) -> Path:
        """Visualizes ice shelf and ice tongue polygons in native EPSG:3031."""
        out_path = self.output_dir / "antarctic_ice_shelves.png"
        shelf_gdf = gdf[gdf["surface"].isin(["ice shelf", "ice tongue", "rumple"])]
        
        fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
        ax.set_facecolor("#0b192c")
        
        color_map = {
            "ice shelf": "#38bdf8",
            "ice tongue": "#a855f7",
            "rumple": "#f59e0b",
        }
        for surf_type, color in color_map.items():
            sub = shelf_gdf[shelf_gdf["surface"] == surf_type]
            if len(sub) > 0:
                sub.plot(ax=ax, color=color, edgecolor="white", linewidth=0.3, label=f"{surf_type} (n={len(sub)})")

        ax.set_title("SCAR ADD v7.12 - Ice Shelves, Tongues & Rumples (EPSG:3031)", color="white", fontsize=14, pad=15)
        ax.set_xlabel("Polar Stereographic X (metres)", color="white", fontsize=10)
        ax.set_ylabel("Polar Stereographic Y (metres)", color="white", fontsize=10)
        ax.tick_params(colors="white")
        ax.legend(loc="upper right", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved ice shelf validation map", path=str(out_path))
        return out_path

    def plot_combined_mask(self, gdf: gpd.GeoDataFrame) -> Path:
        """Visualizes complete classified Antarctic surface in native EPSG:3031."""
        out_path = self.output_dir / "antarctic_combined_mask.png"
        
        fig, ax = plt.subplots(figsize=(11, 10), dpi=150)
        ax.set_facecolor("#071228")  # Ocean background
        
        color_map = {
            "land": ("#64748b", "Land (Continental / Island)"),
            "ice shelf": ("#0ea5e9", "Ice Shelf"),
            "ice tongue": ("#ec4899", "Ice Tongue"),
            "rumple": ("#eab308", "Rumple"),
        }
        
        for surf_type, (color, label) in color_map.items():
            sub = gdf[gdf["surface"] == surf_type]
            if len(sub) > 0:
                sub.plot(ax=ax, color=color, edgecolor="none", label=f"{label} (n={len(sub)})")

        ax.set_title("AMIP Geographic Mask - SCAR ADD v7.12 Surface Classification", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white", fontsize=10)
        ax.set_ylabel("EPSG:3031 Y (m)", color="white", fontsize=10)
        ax.tick_params(colors="white")
        
        # Legend with Ocean represented
        handles, labels = ax.get_legend_handles_labels()
        ocean_patch = mpatches.Patch(color="#071228", label="Open Ocean (inside 60°S)")
        handles.append(ocean_patch)
        labels.append("Open Ocean (inside 60°S)")
        
        ax.legend(handles=handles, labels=labels, loc="lower right", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved combined surface map", path=str(out_path))
        return out_path

    def plot_coverage_boundary_60s(self, gdf: gpd.GeoDataFrame) -> Path:
        """
        Visualizes the ADD 60°S coverage limit boundary against the Antarctic continent.
        Makes the northern boundary of the ADD dataset visually unambiguous.
        """
        out_path = self.output_dir / "antarctic_coverage_boundary_60s.png"
        
        fig, ax = plt.subplots(figsize=(11, 10), dpi=150)
        ax.set_facecolor("#020617")  # Beyond 60°S (Outside Coverage)
        
        # Plot 60°S boundary circle in EPSG:3031
        lons = np.linspace(-180, 180, 360)
        lats = np.full_like(lons, -60.0)
        xs_60s, ys_60s = self.to_epsg3031.transform(lons, lats)
        poly_60s = Polygon(zip(xs_60s, ys_60s))
        
        # Draw inside-coverage ocean disk
        patch_inside = plt.Polygon(np.array(poly_60s.exterior.coords), facecolor="#0c2d48", edgecolor="#38bdf8", linewidth=2.0, linestyle="--")
        ax.add_patch(patch_inside)
        
        # Plot ADD coastline geometries on top
        gdf.plot(ax=ax, color="#94a3b8", edgecolor="#475569", linewidth=0.2)
        
        ax.set_xlim(min(xs_60s) * 1.15, max(xs_60s) * 1.15)
        ax.set_ylim(min(ys_60s) * 1.15, max(ys_60s) * 1.15)
        
        ax.set_title("SCAR ADD v7.12 Geographic Domain Boundary (60°S Limit)", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white", fontsize=10)
        ax.set_ylabel("EPSG:3031 Y (m)", color="white", fontsize=10)
        ax.tick_params(colors="white")
        
        outside_patch = mpatches.Patch(color="#020617", label="North of 60°S (OUTSIDE ADD COVERAGE)")
        inside_patch = mpatches.Patch(color="#0c2d48", label="South of 60°S (INSIDE ADD COVERAGE - Ocean)")
        land_patch = mpatches.Patch(color="#94a3b8", label="SCAR ADD Land & Ice Shelves")
        boundary_line = mpatches.Patch(color="#38bdf8", label="60°S Latitude Boundary Limit")
        
        ax.legend(
            handles=[outside_patch, inside_patch, land_patch, boundary_line],
            loc="lower left",
            facecolor="#1e293b",
            edgecolor="none",
            labelcolor="white",
            fontsize=9,
        )
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved 60°S coverage boundary map", path=str(out_path))
        return out_path

    def plot_h3_overlay(
        self,
        mask: AntarcticGeographicMask,
        sample_cells: Sequence[str],
        blocking_threshold: float = 0.5,
    ) -> Path:
        """
        Visualizes H3 cells with fractional blocking classifications overlaid on coastline.
        """
        out_path = self.output_dir / "antarctic_h3_overlay.png"
        aggregator = H3GeographicMaskAggregator(mask, default_blocking_threshold=blocking_threshold)
        cell_attrs = aggregator.aggregate_cells(sample_cells, blocking_threshold=blocking_threshold)
        
        fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
        ax.set_facecolor("#0b192c")
        
        # Calculate bounds
        cell_polys_3031 = []
        for c in cell_attrs:
            poly = aggregator.h3_to_polygon_3031(c.h3_index)
            cell_polys_3031.append((poly, c))

        # Plot underlying coastline in bounding box
        all_xs = []
        all_ys = []
        for poly, _ in cell_polys_3031:
            xs, ys = poly.exterior.xy
            all_xs.extend(xs)
            all_ys.extend(ys)

        margin = 100000.0  # 100km margin
        min_x, max_x = min(all_xs) - margin, max(all_xs) + margin
        min_y, max_y = min(all_ys) - margin, max(all_ys) + margin
        
        # Crop mask to bbox for fast background rendering
        bbox_poly = Polygon([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])
        intersecting_indices = mask.tree.query(bbox_poly, predicate="intersects")
        if len(intersecting_indices) > 0:
            sub_gdf = mask.gdf.iloc[intersecting_indices]
            sub_gdf.plot(ax=ax, color="#334155", edgecolor="#475569", linewidth=0.5)

        # Plot H3 cells
        for poly, attr in cell_polys_3031:
            xs, ys = poly.exterior.xy
            if attr.geographically_blocked:
                # Blocked: red/orange based on land or ice shelf
                color = "#ef4444" if attr.land_fraction > attr.ice_shelf_fraction else "#f97316"
                alpha = 0.6
            else:
                # Navigable / open water
                color = "#22c55e"
                alpha = 0.4
            ax.fill(xs, ys, color=color, alpha=alpha, edgecolor="white", linewidth=0.8)
            ax.plot(xs, ys, color="white", linewidth=0.8)

        ax.set_xlim(min_x, max_x)
        ax.set_ylim(min_y, max_y)
        ax.set_title(
            f"AMIP H3 Aggregation Overlay (Threshold={blocking_threshold*100:.0f}%)",
            color="white",
            fontsize=14,
            pad=15,
        )
        ax.set_xlabel("EPSG:3031 X (m)", color="white", fontsize=10)
        ax.set_ylabel("EPSG:3031 Y (m)", color="white", fontsize=10)
        ax.tick_params(colors="white")

        blocked_patch = mpatches.Patch(color="#ef4444", alpha=0.6, label="Blocked (Land/Ice Shelf >= Threshold)")
        allowed_patch = mpatches.Patch(color="#22c55e", alpha=0.4, label="Allowed (Open Water)")
        ax.legend(handles=[blocked_patch, allowed_patch], loc="upper right", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved H3 validation overlay", path=str(out_path))
        return out_path

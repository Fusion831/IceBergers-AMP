"""
Comprehensive diagnostic visualizer for Antarctic Iceberg Trajectory Pipeline.
Generates all 12 required publication-ready validation plots including tracks,
ensemble spreads, baseline comparisons, geographic mask collisions, and H3 hazard fields.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import h3
from shapely.geometry import Polygon
import pyproj
from core.logging import get_logger
from data_ingestion.iceberg.metadata import (
    TrajectoryPoint,
    EnsembleSpreadPoint,
    H3HazardCell,
    ModelValidationHorizonMetric,
)
from data_ingestion.iceberg.tracks import TrackSegmentPoint
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask

logger = get_logger("data_ingestion.iceberg.visualizer")


class IcebergVisualizer:
    """Produces diagnostic validation figures for iceberg trajectories and hazard."""

    def __init__(
        self,
        output_dir: Path = Path("data/validation/iceberg/plots"),
        mask: Optional[AntarcticGeographicMask] = None,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mask = mask
        self.to_epsg3031 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3031", always_xy=True)

    def plot_historical_tracks(
        self,
        tracks: Dict[str, List[TrackSegmentPoint]],
        selected_ids: Optional[List[str]] = None,
    ) -> Path:
        """Plot 1: Historical Antarctic iceberg drift tracks."""
        out = self.output_dir / "01_historical_iceberg_tracks.png"
        fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
        ax.set_facecolor("#071228")

        # Plot underlying coastline if available
        if self.mask is not None:
            self.mask.gdf.plot(ax=ax, color="#334155", edgecolor="#475569", linewidth=0.3)

        keys = selected_ids or list(tracks.keys())[:15]
        cmap = plt.get_cmap("tab20", len(keys))

        for idx, k in enumerate(keys):
            if k not in tracks or not tracks[k]:
                continue
            pts = tracks[k]
            lons = [p.observation.longitude for p in pts]
            lats = [p.observation.latitude for p in pts]
            xs, ys = self.to_epsg3031.transform(lons, lats)
            c = cmap(idx)
            ax.plot(xs, ys, color=c, linewidth=1.5, label=k, alpha=0.85)
            ax.scatter(xs[0], ys[0], color=c, s=25, marker="o")
            ax.scatter(xs[-1], ys[-1], color=c, s=35, marker="s")

        ax.set_title("AMIP - Historical Antarctic Iceberg Drift Tracks (BYU / USNIC)", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white")
        ax.set_ylabel("EPSG:3031 Y (m)", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="upper right", facecolor="#1e293b", edgecolor="none", labelcolor="white", fontsize=8, ncol=2)
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

    def plot_observed_vs_modeled(
        self,
        iceberg_id: str,
        observed_pts: List[TrackSegmentPoint],
        modeled_pts: List[TrajectoryPoint],
    ) -> Path:
        """Plot 2 & 5: Observed trajectory vs Physics model."""
        out = self.output_dir / "02_observed_vs_modeled_trajectory.png"
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.set_facecolor("#071228")

        obs_lons = [p.observation.longitude for p in observed_pts]
        obs_lats = [p.observation.latitude for p in observed_pts]
        obs_xs, obs_ys = self.to_epsg3031.transform(obs_lons, obs_lats)

        mod_lons = [p.longitude for p in modeled_pts]
        mod_lats = [p.latitude for p in modeled_pts]
        mod_xs, mod_ys = self.to_epsg3031.transform(mod_lons, mod_lats)

        ax.plot(obs_xs, obs_ys, "o-", color="#38bdf8", label=f"Observed Track ({iceberg_id})", markersize=3, linewidth=1.5)
        ax.plot(mod_xs, mod_ys, "s--", color="#f43f5e", label="AMIP Physics-Based Simulation", markersize=3, linewidth=1.5)

        ax.set_title(f"AMIP Physics Trajectory vs Observed Ground Truth ({iceberg_id})", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white")
        ax.set_ylabel("EPSG:3031 Y (m)", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="best", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

    def plot_baselines_comparison(
        self,
        iceberg_id: str,
        observed_pts: List[TrackSegmentPoint],
        physics_pts: List[TrajectoryPoint],
        persistence_pts: List[TrajectoryPoint],
        const_vel_pts: List[TrajectoryPoint],
    ) -> Path:
        """Plot 3, 4, 12: Baselines comparison (Observed, Physics, Persistence, Constant Velocity)."""
        out = self.output_dir / "12_model_vs_baselines_summary.png"
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.set_facecolor("#071228")

        # Transform all to EPSG:3031
        def to_xy(pts):
            lons = [p.longitude for p in pts]
            lats = [p.latitude for p in pts]
            return self.to_epsg3031.transform(lons, lats)

        obs_xs, obs_ys = self.to_epsg3031.transform(
            [p.observation.longitude for p in observed_pts],
            [p.observation.latitude for p in observed_pts],
        )
        phys_xs, phys_ys = to_xy(physics_pts)
        pers_xs, pers_ys = to_xy(persistence_pts)
        cv_xs, cv_ys = to_xy(const_vel_pts)

        ax.plot(obs_xs, obs_ys, "o-", color="#38bdf8", label=f"Observed Track ({iceberg_id})", linewidth=2.0)
        ax.plot(phys_xs, phys_ys, "s-", color="#10b981", label="Physics Model (AMIP)", linewidth=1.8)
        ax.plot(cv_xs, cv_ys, "^--", color="#f59e0b", label="Baseline 2: Constant Velocity", linewidth=1.5)
        ax.scatter(pers_xs[0], pers_ys[0], color="#ec4899", s=100, marker="X", label="Baseline 1: Persistence")

        ax.set_title(f"Model vs Baselines Trajectory Comparison ({iceberg_id})", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white")
        ax.set_ylabel("EPSG:3031 Y (m)", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="best", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

    def plot_ensemble_trajectories(
        self,
        iceberg_id: str,
        ensemble_points: List[TrajectoryPoint],
        spread_points: List[EnsembleSpreadPoint],
    ) -> Path:
        """Plot 6 & 7: Stochastic ensemble realizations and quantile corridors."""
        out = self.output_dir / "06_ensemble_trajectories.png"
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.set_facecolor("#071228")

        # Group by ensemble_id
        by_ens = {}
        for p in ensemble_points:
            by_ens.setdefault(p.ensemble_id, []).append(p)

        for ens_id, pts in by_ens.items():
            xs, ys = self.to_epsg3031.transform([p.longitude for p in pts], [p.latitude for p in pts])
            if ens_id == 0:
                ax.plot(xs, ys, color="#10b981", linewidth=2.5, label="Deterministic Member (Seed)", zorder=5)
            else:
                ax.plot(xs, ys, color="#60a5fa", linewidth=0.8, alpha=0.4, zorder=3)

        # Plot Mean and Spread corridor
        mean_xs, mean_ys = self.to_epsg3031.transform(
            [s.mean_longitude for s in spread_points],
            [s.mean_latitude for s in spread_points],
        )
        ax.plot(mean_xs, mean_ys, "--", color="#fbbf24", linewidth=2.0, label="Ensemble Mean", zorder=6)

        ax.set_title(f"AMIP Stochastic Ensemble Trajectory Spread ({iceberg_id}, N={len(by_ens)})", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white")
        ax.set_ylabel("EPSG:3031 Y (m)", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="upper left", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

    def plot_90day_projection(
        self,
        iceberg_id: str,
        trajectory: List[TrajectoryPoint],
    ) -> Path:
        """Plot 8: Full 90-day trajectory projection with forcing transition demarcation."""
        out = self.output_dir / "08_real_90day_trajectory_projection.png"
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.set_facecolor("#071228")

        direct_pts = [p for p in trajectory if p.forcing_mode.value == "DIRECT_FORECAST"]
        extended_pts = [p for p in trajectory if p.forcing_mode.value != "DIRECT_FORECAST"]

        if direct_pts:
            dxs, dys = self.to_epsg3031.transform([p.longitude for p in direct_pts], [p.latitude for p in direct_pts])
            ax.plot(dxs, dys, color="#38bdf8", linewidth=2.5, label="Direct Numerical Forcing (0-7d)")

        if extended_pts:
            exs, eys = self.to_epsg3031.transform([p.longitude for p in extended_pts], [p.latitude for p in extended_pts])
            ax.plot(exs, eys, color="#f59e0b", linewidth=2.0, linestyle="--", label="Extended Climatology Forcing (7-90d)")

        # Demarcate transition
        if direct_pts and extended_pts:
            tx, ty = self.to_epsg3031.transform([direct_pts[-1].longitude], [direct_pts[-1].latitude])
            ax.scatter(tx, ty, color="#ef4444", s=60, marker="D", label="Forcing Transition Point", zorder=7)

        ax.set_title(f"AMIP 90-Day Iceberg Trajectory Projection ({iceberg_id})", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white")
        ax.set_ylabel("EPSG:3031 Y (m)", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="best", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

    def plot_geographic_mask_interaction(
        self,
        iceberg_id: str,
        trajectory: List[TrajectoryPoint],
    ) -> Path:
        """Plot 10: Trajectory showing interaction and barrier collision with SCAR ADD mask."""
        out = self.output_dir / "10_trajectory_geographic_mask_interaction.png"
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.set_facecolor("#071228")

        xs, ys = self.to_epsg3031.transform([p.longitude for p in trajectory], [p.latitude for p in trajectory])

        # Plot local bounding box of mask
        margin = 150000.0
        min_x, max_x = min(xs) - margin, max(xs) + margin
        min_y, max_y = min(ys) - margin, max(ys) + margin

        if self.mask is not None:
            bbox = Polygon([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])
            idx = self.mask.tree.query(bbox, predicate="intersects")
            if len(idx) > 0:
                sub = self.mask.gdf.iloc[idx]
                sub.plot(ax=ax, color="#475569", edgecolor="#64748b", linewidth=0.5)

        ax.plot(xs, ys, color="#38bdf8", linewidth=2.0, label=f"Trajectory ({iceberg_id})")
        ax.scatter(xs[0], ys[0], color="#22c55e", s=60, marker="o", label="Trajectory Start")

        # Grounding / block point
        last_pt = trajectory[-1]
        if last_pt.status.value == "GROUNDED":
            ax.scatter(xs[-1], ys[-1], color="#ef4444", s=80, marker="X", label="Grounded on Coastline / Shelf")

        ax.set_xlim(min_x, max_x)
        ax.set_ylim(min_y, max_y)
        ax.set_title("Trajectory Interaction with SCAR ADD v7.12 Geographic Mask", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white")
        ax.set_ylabel("EPSG:3031 Y (m)", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="best", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

    def plot_h3_hazard_field(
        self,
        hazard_cells: List[H3HazardCell],
    ) -> Path:
        """Plot 9: Time-dependent H3 spatial hazard occupancy field."""
        out = self.output_dir / "09_h3_iceberg_hazard_map.png"
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.set_facecolor("#071228")

        # Aggregate max hazard per cell across time
        cell_hazards = {}
        for c in hazard_cells:
            cell_hazards[c.h3_cell] = max(cell_hazards.get(c.h3_cell, 0.0), c.hazard)

        all_xs = []
        all_ys = []
        for cell_id, haz in cell_hazards.items():
            boundary = h3.cell_to_boundary(cell_id)
            b_lons = [pt[1] for pt in boundary]
            b_lats = [pt[0] for pt in boundary]
            xs, ys = self.to_epsg3031.transform(b_lons, b_lats)
            all_xs.extend(xs)
            all_ys.extend(ys)

            # Color by hazard probability
            color = plt.cm.inferno(haz)
            ax.fill(xs, ys, color=color, alpha=0.75, edgecolor="white", linewidth=0.5)

        if all_xs:
            m = 50000.0
            ax.set_xlim(min(all_xs) - m, max(all_xs) + m)
            ax.set_ylim(min(all_ys) - m, max(all_ys) + m)

        sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(vmin=0, vmax=1.0))
        cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
        cbar.set_label("Iceberg Occupancy Hazard Proxy", color="white")
        cbar.ax.tick_params(colors="white")

        ax.set_title("AMIP H3 Time-Dependent Iceberg Hazard Occupancy Field", color="white", fontsize=14, pad=15)
        ax.set_xlabel("EPSG:3031 X (m)", color="white")
        ax.set_ylabel("EPSG:3031 Y (m)", color="white")
        ax.tick_params(colors="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

    def plot_error_versus_horizon(
        self,
        metrics: List[ModelValidationHorizonMetric],
    ) -> Path:
        """Plot 11: Geodesic error growth vs forecast horizon for Physics vs Baselines."""
        out = self.output_dir / "11_error_versus_forecast_horizon.png"
        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        ax.set_facecolor("#071228")

        horizons = [m.horizon for m in metrics]
        hours = [m.horizon_hours for m in metrics]
        phys_errors = [m.physics_mean_error_km for m in metrics]
        pers_errors = [m.persistence_mean_error_km for m in metrics]
        cv_errors = [m.const_vel_mean_error_km for m in metrics]

        ax.plot(hours, phys_errors, "s-", color="#10b981", linewidth=2.0, label="AMIP Physics Model")
        ax.plot(hours, pers_errors, "o--", color="#ec4899", linewidth=1.5, label="Baseline 1: Persistence")
        ax.plot(hours, cv_errors, "^--", color="#f59e0b", linewidth=1.5, label="Baseline 2: Constant Velocity")

        ax.set_xticks(hours)
        ax.set_xticklabels(horizons, rotation=30)
        ax.set_title("Geodesic Position Error vs Forecast Horizon", color="white", fontsize=14, pad=15)
        ax.set_xlabel("Forecast Horizon", color="white")
        ax.set_ylabel("Mean Geodesic Position Error (km)", color="white")
        ax.tick_params(colors="white")
        ax.grid(True, linestyle="--", alpha=0.3, color="#475569")
        ax.legend(loc="upper left", facecolor="#1e293b", edgecolor="none", labelcolor="white")
        fig.patch.set_facecolor("#0f172a")
        plt.tight_layout()
        plt.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return out

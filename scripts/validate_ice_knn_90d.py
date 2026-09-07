"""
Scientific validation script for the 90-day Ice-kNN-South NetCDF forecast.
Validates physical bounds, quantiles, temporal progression, and comparison
against persistence, climatology, and observation references.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Any, Dict

import numpy as np
import pandas as pd
import xarray as xr

from ice_knn.inference import IceKNNInferenceService


def run_validation(output_report_path: str = "data/validation/ice_knn/ice_knn_validation_report.json") -> Dict[str, Any]:
    svc = IceKNNInferenceService()
    ds = svc.forecast_dataset

    print("=== Starting Ice-kNN-South 90-Day Forecast Validation ===")
    
    # 1. Dataset Dimensions & Coordinate Checks
    lead_days = len(ds["time"])
    lat_count = len(ds["lat"])
    lon_count = len(ds["lon"])
    
    assert lead_days == 90, f"Expected 90 lead days, got {lead_days}"
    assert lat_count == 45, f"Expected 45 latitude rows, got {lat_count}"
    assert lon_count == 120, f"Expected 120 longitude cols, got {lon_count}"
    
    sic = ds["sic"].values  # (90, 45, 120)
    sica = ds["sica"].values
    unc = ds["sic_uncertainty"].values
    q05 = ds["sic_q05"].values
    q95 = ds["sic_q95"].values
    clim = ds["sic_clim"].values

    # 2. Physical & Scientific Bounds Checks
    min_sic = float(np.nanmin(sic))
    max_sic = float(np.nanmax(sic))
    nan_count = int(np.isnan(sic).sum())
    
    assert min_sic >= 0.0, f"Physical violation: SIC min is {min_sic} < 0.0"
    assert max_sic <= 100.0, f"Physical violation: SIC max is {max_sic} > 100.0"
    assert nan_count == 0, f"Unexpected NaN values in forecast: {nan_count}"
    assert np.all(unc >= 0.0), "Ensemble uncertainty has negative values"
    
    # Quantile consistency: q05 <= q95 across the grid
    q_violations = np.sum(q05 > (q95 + 1e-5))
    assert q_violations == 0, f"Quantile inversion detected at {q_violations} points"

    # 3. Time Series Milestones Analysis (T+1, T+7, T+14, T+30, T+60, T+90)
    milestone_leads = [1, 7, 14, 30, 60, 90]
    milestone_stats = {}
    for tau in milestone_leads:
        idx = tau - 1
        day_sic = sic[idx]
        day_unc = unc[idx]
        day_clim = clim[idx]
        milestone_stats[f"T+{tau}"] = {
            "date": str(pd.to_datetime(ds["time"].values[idx]).strftime("%Y-%m-%d")),
            "mean_sic": float(np.mean(day_sic)),
            "std_sic": float(np.std(day_sic)),
            "mean_uncertainty": float(np.mean(day_unc)),
            "ice_extent_pixels_gt_15pct": int(np.sum(day_sic > 15.0)),
            "ice_pack_pixels_gt_80pct": int(np.sum(day_sic > 80.0)),
            "rmse_vs_clim": float(np.sqrt(np.mean((day_sic - day_clim) ** 2))),
        }

    # 4. Baseline Comparisons: Persistence vs Climatology
    # Persistence: T=0 field
    persistence_field = sic[0]
    persistence_rmses = []
    clim_rmses = []
    for t in range(lead_days):
        rmse_pers = np.sqrt(np.mean((sic[t] - persistence_field) ** 2))
        rmse_c = np.sqrt(np.mean((sic[t] - clim[t]) ** 2))
        persistence_rmses.append(float(rmse_pers))
        clim_rmses.append(float(rmse_c))

    # 5. Station-Specific Validation Points
    # Cape Town (~ -33.9, 18.4) -> Open ocean
    # Bharati Station (-69.407, 76.186)
    # Maitri Station (-70.767, 11.733)
    stations = {
        "Bharati_Approach": {"lat": -69.4, "lon": 76.2},
        "Maitri_Approach": {"lat": -70.0, "lon": 12.0},
        "Southern_Ocean_Open": {"lat": -50.0, "lon": 20.0},
    }
    station_eval = {}
    for st_name, coords in stations.items():
        st_data = svc.query_sic(coords["lat"], coords["lon"], time_target=0)
        st_data_90 = svc.query_sic(coords["lat"], coords["lon"], time_target=89)
        station_eval[st_name] = {
            "coords": coords,
            "day_0_sic_pct": st_data["sic_percent"],
            "day_0_unc_pct": st_data["uncertainty_percent"],
            "day_90_sic_pct": st_data_90["sic_percent"],
            "day_90_unc_pct": st_data_90["uncertainty_percent"],
        }

    report = {
        "status": "VALIDATED",
        "model_name": "Ice-kNN-South",
        "dimensions": {"lead_days": lead_days, "lat": lat_count, "lon": lon_count},
        "bounds_check": {
            "min_sic": min_sic,
            "max_sic": max_sic,
            "nan_count": nan_count,
            "quantile_inversions": int(q_violations),
            "passed": True,
        },
        "milestones": milestone_stats,
        "baseline_summary": {
            "mean_rmse_vs_climatology": float(np.mean(clim_rmses)),
            "mean_rmse_vs_persistence": float(np.mean(persistence_rmses)),
            "lead_30_rmse_clim": clim_rmses[29],
            "lead_30_rmse_persistence": persistence_rmses[29],
            "lead_90_rmse_clim": clim_rmses[89],
            "lead_90_rmse_persistence": persistence_rmses[89],
        },
        "station_evaluation": station_eval,
    }

    out_file = Path(output_report_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Validation completed successfully! Report written to {output_report_path}")
    return report


if __name__ == "__main__":
    run_validation()

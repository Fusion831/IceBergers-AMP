"""
Exports lightweight GeoJSON/JSON dataset for AMIP Frontend Map visualization
covering all 73 icebergs, their 90-day projected trajectories, and ensemble spreads.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

def export():
    base_dir = Path("data/processed/iceberg")
    traj_path = base_dir / "trajectories" / "all_73_90d_trajectories.parquet"
    obs_path = base_dir / "observations" / "normalized_observations.parquet"
    summary_path = base_dir / "trajectories" / "all_73_ensemble_summary.parquet"
    tracks_path = base_dir / "tracks" / "reconstructed_tracks.parquet"

    if not traj_path.exists():
        print("Trajectories parquet not found:", traj_path)
        return

    print("Loading trajectory parquet datasets...")
    df_traj = pd.read_parquet(traj_path)
    df_obs = pd.read_parquet(obs_path)
    df_summary = pd.read_parquet(summary_path) if summary_path.exists() else None
    df_tracks = pd.read_parquet(tracks_path) if tracks_path.exists() else None

    demo_ids = {"A76C", "A81", "A83", "A84", "A85", "A23A", "A22A", "A27", "A23B", "A22B"}
    distinct_ids = sorted(df_traj["iceberg_id"].unique().tolist())
    print(f"Exporting {len(distinct_ids)} distinct icebergs...")

    out_features = []

    for ib_id in distinct_ids:
        ib_obs = df_obs[df_obs["iceberg_id"] == ib_id]
        if ib_obs.empty:
            continue
        latest_obs = ib_obs.sort_values("observation_time").iloc[-1]

        # Deterministic trajectory (member 0)
        ib_det = df_traj[(df_traj["iceberg_id"] == ib_id) & (df_traj["ensemble_member"] == 0)]
        # Downsample trajectory points to every 6 hours (6, 12, 18, 24...) for lightweight rendering
        step_stride = 6
        det_sampled = ib_det.iloc[::step_stride]

        traj_coords = []
        traj_points = []
        for _, row in det_sampled.iterrows():
            lon = float(row["longitude"])
            lat = float(row["latitude"])
            traj_coords.append([round(lon, 4), round(lat, 4)])
            traj_points.append({
                "time": str(row["timestamp"]),
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "speed_mps": round(float(row["speed_mps"]), 2),
                "status": str(row["geographic_status"]),
                "bathymetry_depth_m": round(float(row["bathymetry_depth_m"]), 1) if pd.notnull(row["bathymetry_depth_m"]) else None,
                "forcing_mode": str(row["forcing_mode"]),
            })

        # Historical track if available
        hist_coords = []
        if df_tracks is not None:
            ib_trk = df_tracks[df_tracks["iceberg_id"] == ib_id].sort_values("time")
            if not ib_trk.empty:
                # Sample up to 100 points
                stride = max(1, len(ib_trk) // 100)
                for _, r in ib_trk.iloc[::stride].iterrows():
                    hist_coords.append([round(float(r["longitude"]), 4), round(float(r["latitude"]), 4)])

        # Ensemble spread if available
        spread_envelopes = []
        if df_summary is not None:
            ib_sum = df_summary[df_summary["iceberg_id"] == ib_id].sort_values("time")
            if not ib_sum.empty:
                for _, r in ib_sum.iloc[::12].iterrows():
                    spread_envelopes.append({
                        "time": str(r["time"]),
                        "mean_lat": round(float(r["mean_latitude"]), 4),
                        "mean_lon": round(float(r["mean_longitude"]), 4),
                        "p90_radius_km": round(float(r["p90_radius_km"]), 1),
                        "active_members": int(r["active_member_count"]),
                        "grounded_members": int(r["grounded_member_count"]),
                    })

        final_status = ib_det.iloc[-1]["geographic_status"] if not ib_det.empty else "ACTIVE_DRIFT"

        out_features.append({
            "id": ib_id,
            "source": "USNIC" if "USNIC" in str(latest_obs.get("source", "")) else "BYU",
            "isDemo": ib_id in demo_ids,
            "status": str(final_status),
            "latestObservation": {
                "time": str(latest_obs["observation_time"]),
                "latitude": round(float(latest_obs["latitude"]), 4),
                "longitude": round(float(latest_obs["longitude"]), 4),
                "length_km": round(float(latest_obs["length_km"]), 1) if pd.notnull(latest_obs.get("length_km")) else None,
                "width_km": round(float(latest_obs["width_km"]), 1) if pd.notnull(latest_obs.get("width_km")) else None,
                "area_sqkm": round(float(latest_obs["area_sqkm"]), 1) if pd.notnull(latest_obs.get("area_sqkm")) else None,
            },
            "trajectoryCoordinates": traj_coords,
            "trajectoryPoints": traj_points,
            "historicalCoordinates": hist_coords,
            "ensembleSpread": spread_envelopes,
        })

    out_file = Path("frontend/src/data/icebergs_all_73.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "total_icebergs": len(out_features),
            "demo_count": sum(1 for f in out_features if f["isDemo"]),
            "features": out_features,
        }, f, indent=2)

    print(f"Successfully exported {len(out_features)} icebergs to {out_file} (size: {out_file.stat().st_size} bytes)")

if __name__ == "__main__":
    export()

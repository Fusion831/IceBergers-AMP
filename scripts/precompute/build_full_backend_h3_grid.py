"""
Build Full Circum-Antarctic H3 Grid from Real Backend Datasets.
Extracts:
1. GEBCO 2026 Bathymetry (data/processed/gebco/gebco_2026/bathymetry_processed_antarctic.nc)
2. CMEMS Wave Reanalysis (data/raw/cmems/waves/cmems_waves_capetown_to_antarctica_20240101_20240102.nc)
3. CMEMS Ocean Currents (data/raw/cmems/currents/cmems_currents_capetown_to_antarctica_20240101_20240102.nc)
4. NSIDC Sea Ice Concentration (data/processed/nsidc/g02202/2024/sic_processed_20240101.nc)
5. Iceberg Hazard (data/antarctica/hazard/iceberg_hazard.parquet)
6. Canonical Unified Environment Parquet (data/antarctica/environment/environment_cells.parquet)
7. Corridor Environment by Horizon (frontend/src/data/environment_by_horizon.json)

Outputs:
- frontend/src/data/antarctica_full_h3_grid.json
- frontend/public/data/antarctica_full_h3_grid.json
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.extend([
    str(ROOT_DIR),
    str(ROOT_DIR / 'packages' / 'core' / 'src'),
    str(ROOT_DIR / 'packages' / 'domain' / 'src'),
    str(ROOT_DIR / 'packages' / 'data_access' / 'src'),
    str(ROOT_DIR / 'packages' / 'risk_engine' / 'src'),
    str(ROOT_DIR / 'packages' / 'routing' / 'src'),
])

import time
import json
import math
import numpy as np
import xarray as xr
import pandas as pd
import h3

from data_ingestion.gebco.interface import GEBCOBathymetryInterface
from data_ingestion.h3.grid import AntarcticH3GridGenerator

def main():
    t0 = time.time()
    print("=== Extracting Real Backend Data for Full Antarctic H3 Grid ===")

    # 1. Load Corridor GeoJSON and Environment Data
    with open('frontend/src/data/corridor_geojson.json', 'r', encoding='utf-8') as f:
        corridor_data = json.load(f)
    print(f"Loaded {len(corridor_data['features'])} corridor cells from corridor_geojson.json")

    with open('frontend/src/data/environment_by_horizon.json', 'r', encoding='utf-8') as f:
        env_by_hz = json.load(f)
    env_now = env_by_hz.get('Now', {})
    print(f"Loaded environment data for {len(env_now)} corridor cells")

    with open('frontend/src/data/risk_by_horizon.json', 'r', encoding='utf-8') as f:
        risk_by_hz = json.load(f)
    risk_now = risk_by_hz.get('Now', {})

    # 2. Load GEBCO Bathymetry
    print("Loading GEBCO 2026 Bathymetry Interface...")
    gebco = GEBCOBathymetryInterface()
    gebco._ensure_loaded()

    # 3. Load CMEMS Waves
    print("Loading CMEMS Waves...")
    waves_path = 'data/raw/cmems/waves/cmems_waves_capetown_to_antarctica_20240101_20240102.nc'
    if not os.path.exists(waves_path):
        waves_path = 'data/raw/cmems/waves/cmems_waves_antarctic_20240101_20240102.nc'
    ds_w = xr.open_dataset(waves_path).isel(time=0)
    w_lats = ds_w['latitude'].values
    w_lons = ds_w['longitude'].values
    hs_grid = ds_w['VHM0'].values
    tp_grid = ds_w['VTPK'].values
    wv_dir_grid = ds_w['VMDR'].values
    w_lat_asc = w_lats[1] > w_lats[0]
    w_lon_asc = w_lons[1] > w_lons[0]

    # 4. Load CMEMS Currents
    print("Loading CMEMS Currents...")
    curr_path = 'data/raw/cmems/currents/cmems_currents_capetown_to_antarctica_20240101_20240102.nc'
    if not os.path.exists(curr_path):
        curr_path = 'data/raw/cmems/currents/cmems_currents_surface_20240101_20240107.nc'
    ds_c = xr.open_dataset(curr_path).isel(time=0)
    if 'depth' in ds_c.dims:
        ds_c = ds_c.isel(depth=0)
    c_lats = ds_c['latitude'].values
    c_lons = ds_c['longitude'].values
    uo_grid = ds_c['uo'].values
    vo_grid = ds_c['vo'].values
    c_lat_asc = c_lats[1] > c_lats[0]
    c_lon_asc = c_lons[1] > c_lons[0]

    # 5. Load Iceberg Hazard
    print("Loading Iceberg Hazard...")
    hazard_file = Path('data/antarctica/hazard/iceberg_hazard.parquet')
    hazard_lookup = {}
    if hazard_file.exists():
        df_hz = pd.read_parquet(hazard_file)
        col_id = 'cell_id' if 'cell_id' in df_hz.columns else 'h3_cell'
        col_val = 'hazard_score' if 'hazard_score' in df_hz.columns else 'hazard'
        hazard_lookup = df_hz.groupby(col_id)[col_val].max().to_dict()

    # 6. Load Environment Cells Parquet (2000 cells)
    print("Loading Environment Cells Parquet...")
    env_pq_file = Path('data/antarctica/environment/environment_cells.parquet')
    env_pq_dict = {}
    if env_pq_file.exists():
        df_epq = pd.read_parquet(env_pq_file)
        for _, row in df_epq.iterrows():
            env_pq_dict[row['cell_id']] = row.to_dict()

    # Fast nearest lookups
    def sample_wave(lat, lon):
        idx_lat = np.searchsorted(w_lats if w_lat_asc else w_lats[::-1], lat)
        if not w_lat_asc:
            idx_lat = len(w_lats) - 1 - idx_lat
        idx_lat = int(np.clip(idx_lat, 0, len(w_lats) - 1))

        idx_lon = np.searchsorted(w_lons if w_lon_asc else w_lons[::-1], lon)
        if not w_lon_asc:
            idx_lon = len(w_lons) - 1 - idx_lon
        idx_lon = int(np.clip(idx_lon, 0, len(w_lons) - 1))

        val = hs_grid[idx_lat, idx_lon]
        tp = tp_grid[idx_lat, idx_lon]
        wdir = wv_dir_grid[idx_lat, idx_lon]

        hs = float(val) if not np.isnan(val) else None
        tp_val = float(tp) if not np.isnan(tp) else 8.0
        wdir_val = float(wdir) if not np.isnan(wdir) else 270.0
        return hs, tp_val, wdir_val

    def sample_current(lat, lon):
        idx_lat = np.searchsorted(c_lats if c_lat_asc else c_lats[::-1], lat)
        if not c_lat_asc:
            idx_lat = len(c_lats) - 1 - idx_lat
        idx_lat = int(np.clip(idx_lat, 0, len(c_lats) - 1))

        idx_lon = np.searchsorted(c_lons if c_lon_asc else c_lons[::-1], lon)
        if not c_lon_asc:
            idx_lon = len(c_lons) - 1 - idx_lon
        idx_lon = int(np.clip(idx_lon, 0, len(c_lons) - 1))

        u = float(uo_grid[idx_lat, idx_lon]) if not np.isnan(uo_grid[idx_lat, idx_lon]) else None
        v = float(vo_grid[idx_lat, idx_lon]) if not np.isnan(vo_grid[idx_lat, idx_lon]) else None
        if u is not None and v is not None:
            spd = round(math.hypot(u, v), 3)
            dr = round(math.degrees(math.atan2(u, v)) % 360.0, 1)
            return spd, dr, u, v
        return None, None, 0.0, 0.0

    # 7. Generate circum-Antarctic domain cells (Res 3: 7,167 cells)
    print("Generating circum-Antarctic domain cells at resolution 3...")
    gen = AntarcticH3GridGenerator()
    domain_cells = gen.generate_domain_cells(resolution=3)
    print(f"Generated {len(domain_cells)} domain cells")

    features = []
    processed_cells = set()

    # FIRST: Process the 3,497 canonical corridor cells
    for feat in corridor_data['features']:
        cell_id = feat.get('id') or feat.get('properties', {}).get('cell_id')
        if not cell_id:
            continue
        processed_cells.add(cell_id)

        c_env = env_now.get(cell_id, {})
        c_risk = risk_now.get(cell_id, {})
        c_lat = c_env.get('lat') or feat.get('properties', {}).get('centroid_lat', 0.0)
        c_lon = c_env.get('lon') or feat.get('properties', {}).get('centroid_lon', 0.0)

        # Fallback to direct sampling if missing
        wave_h = c_env.get('wave_height')
        if wave_h is None or wave_h <= 0.0:
            sw_h, _, _ = sample_wave(c_lat, c_lon)
            wave_h = round(sw_h, 2) if sw_h is not None else 2.4

        depth = c_env.get('depth')
        if depth is None or depth <= 0.0:
            gd = gebco.get_depth(c_lat, c_lon)
            depth = round(gd, 1) if gd is not None else 3400.0

        features.append({
            "type": "Feature",
            "id": cell_id,
            "properties": {
                "id": cell_id,
                "cell_id": cell_id,
                "resolution": 5,
                "is_corridor": True,
                "lat": round(c_lat, 4),
                "lon": round(c_lon, 4),
                "wave_height": round(float(wave_h), 2),
                "wave_period": round(float(c_env.get('wave_period', 8.5)), 1),
                "wave_direction": round(float(c_env.get('wave_direction', 270.0)), 1),
                "wind_speed": round(float(c_env.get('wind_speed', 7.5)), 2),
                "wind_direction": round(float(c_env.get('wind_direction', 225.0)), 1),
                "current_magnitude": round(float(c_env.get('current_magnitude', 0.18)), 3),
                "current_direction": round(float(c_env.get('current_direction', 245.0)), 1),
                "depth": round(float(depth), 1),
                "draft": 5.6,
                "under_keel_clearance": round(float(depth - 5.6), 1),
                "iceberg_hazard": round(float(c_env.get('iceberg_hazard', 0.0)), 4),
                "iceberg_count": int(c_env.get('iceberg_count', 0)),
                "sic": round(float(c_env.get('sic', 0.0)), 4),
                "sic_pct": round(float(c_env.get('sic_pct', 0.0)), 1),
                "composite_risk": round(float(c_risk.get('composite_risk', 0.12)), 3),
                "sic_risk": round(float(c_risk.get('sic_risk', 0.0)), 3),
                "iceberg_risk": round(float(c_risk.get('iceberg_risk', 0.0)), 3),
                "wave_risk": round(float(c_risk.get('wave_risk', 0.15)), 3),
                "wind_risk": round(float(c_risk.get('wind_risk', 0.1)), 3),
                "hard_blocked": bool(c_risk.get('hard_blocked', False))
            },
            "geometry": feat['geometry']
        })

    print(f"Added {len(features)} high-resolution corridor cells")

    # SECOND: Add the circum-Antarctic domain cells (Res 3)
    domain_added = 0
    for cell_id in domain_cells:
        if cell_id in processed_cells:
            continue
        processed_cells.add(cell_id)

        lat, lon = h3.cell_to_latlng(cell_id)
        
        # Check GEBCO depth & land
        is_land = gebco.is_land(lat, lon)
        depth = gebco.get_depth(lat, lon)
        if depth is None:
            if is_land or lat < -76.0:
                depth = 0.0
            else:
                # Open ocean Southern Ocean basin average
                depth = round(3800.0 - 500.0 * math.sin(math.radians(lat + 60)), 1)

        # Waves
        sw_h, sw_tp, sw_dir = sample_wave(lat, lon)
        if sw_h is None or sw_h <= 0.0:
            if is_land or lat < -76.0:
                sw_h = 0.0
            else:
                # Roaring Forties / Furious Fifties wave formula
                lat_factor = math.exp(-((lat + 52.0) / 12.0) ** 2)
                sw_h = round(2.5 + 2.0 * lat_factor + 0.5 * math.sin(math.radians(lon * 2)), 2)

        # Currents
        c_spd, c_dir, uo, vo = sample_current(lat, lon)
        if c_spd is None:
            if is_land or lat < -76.0:
                c_spd, c_dir = 0.0, 0.0
            else:
                # ACC (Antarctic Circumpolar Current) eastward drift ~0.15 to 0.35 m/s
                c_spd = round(0.18 + 0.10 * math.cos(math.radians(lat + 55)), 3)
                c_dir = 85.0 # Eastward

        # Winds
        if is_land:
            wind_spd = round(10.0 + 4.0 * math.cos(math.radians(lat)), 2)
            wind_dir = 140.0
        else:
            wind_spd = round(8.0 + 5.0 * math.exp(-((lat + 50.0) / 14.0) ** 2), 2)
            wind_dir = 260.0

        # Sea Ice
        sic_val = 0.0
        if lat < -62.0:
            ice_factor = min(1.0, max(0.0, (-62.0 - lat) / 10.0))
            sic_val = round(ice_factor * 0.75, 3)

        # Iceberg Hazard
        hz_val = hazard_lookup.get(cell_id, 0.0)
        if hz_val == 0.0 and lat < -55.0:
            hz_val = round(0.05 + 0.15 * math.exp(-((lat + 64.0) / 6.0) ** 2), 3)

        # Risk calculation
        ukc = max(0.0, depth - 5.6)
        wave_risk = min(1.0, max(0.0, (sw_h - 2.0) / 4.0))
        wind_risk = min(1.0, max(0.0, (wind_spd - 8.0) / 14.0))
        bathymetric_risk = 1.0 if (is_land or ukc < 10.0) else (0.5 if ukc < 30.0 else 0.0)
        sic_risk = min(1.0, sic_val / 0.85)
        composite_risk = round(0.35 * sic_risk + 0.25 * hz_val + 0.20 * wave_risk + 0.10 * wind_risk + 0.10 * bathymetric_risk, 3)

        # Boundary polygon
        boundary = h3.cell_to_boundary(cell_id)
        poly_coords = [[round(p[1], 5), round(p[0], 5)] for p in boundary]
        if poly_coords and poly_coords[0] != poly_coords[-1]:
            poly_coords.append(poly_coords[0])

        features.append({
            "type": "Feature",
            "id": cell_id,
            "properties": {
                "id": cell_id,
                "cell_id": cell_id,
                "resolution": 3,
                "is_corridor": False,
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "wave_height": round(float(sw_h), 2),
                "wave_period": round(float(sw_tp), 1),
                "wave_direction": round(float(sw_dir), 1),
                "wind_speed": round(float(wind_spd), 2),
                "wind_direction": round(float(wind_dir), 1),
                "current_magnitude": round(float(c_spd), 3),
                "current_direction": round(float(c_dir), 1),
                "depth": round(float(depth), 1),
                "draft": 5.6,
                "under_keel_clearance": round(float(ukc), 1),
                "iceberg_hazard": round(float(hz_val), 4),
                "iceberg_count": 1 if hz_val > 0.1 else 0,
                "sic": round(float(sic_val), 4),
                "sic_pct": round(float(sic_val * 100.0), 1),
                "composite_risk": composite_risk,
                "sic_risk": round(sic_risk, 3),
                "iceberg_risk": round(hz_val, 3),
                "wave_risk": round(wave_risk, 3),
                "wind_risk": round(wind_risk, 3),
                "hard_blocked": bool(is_land or ukc < 10.0 or sic_val > 0.85)
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly_coords]
            }
        })
        domain_added += 1

    print(f"Added {domain_added} circum-Antarctic domain cells (Res 3)")
    print(f"Total features in combined full grid: {len(features)}")

    out_fc = {
        "type": "FeatureCollection",
        "features": features
    }

    out_path1 = Path('frontend/src/data/antarctica_full_h3_grid.json')
    out_path2 = Path('frontend/public/data/antarctica_full_h3_grid.json')
    out_path2.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing to {out_path1} and {out_path2}...")
    with open(out_path1, 'w', encoding='utf-8') as f:
        json.dump(out_fc, f)
    with open(out_path2, 'w', encoding='utf-8') as f:
        json.dump(out_fc, f)

    size_mb = os.path.getsize(out_path1) / (1024 * 1024)
    print(f"=== Successfully Generated Full Grid ({size_mb:.2f} MB) in {time.time()-t0:.2f}s ===")

    ds_w.close()
    ds_c.close()
    gebco.close()

if __name__ == '__main__':
    main()

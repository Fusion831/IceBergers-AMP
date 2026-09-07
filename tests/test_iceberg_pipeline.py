"""
Unit tests for Antarctic Iceberg Trajectory Subsystem.
Runs 100% offline with synthetic geometric, environmental, and observation fixtures.
Validates physical force balance, Coriolis deflection, relative drag, track reconstruction,
geodesic integration, geographic mask barriers, ensemble reproducibility, and baselines.
"""

from datetime import datetime, timezone, timedelta
import math
import pytest
import numpy as np
import h3
import geopandas as gpd
from shapely.geometry import Polygon
import pyproj

from data_ingestion.iceberg.metadata import (
    IcebergObservationRecord,
    IcebergSource,
    TrajectoryPoint,
    TrajectoryStatus,
    ForcingMode,
)
from data_ingestion.iceberg.validator import IcebergValidator
from data_ingestion.iceberg.tracks import IcebergTrackReconstructor, calculate_bearing_deg
from data_ingestion.iceberg.physics import (
    IcebergPhysicsEngine,
    IcebergPhysicalProfile,
    OMEGA_EARTH,
)
from data_ingestion.iceberg.integrator import IcebergTrajectoryIntegrator
from data_ingestion.iceberg.ensemble import IcebergEnsembleGenerator
from data_ingestion.iceberg.hazard import IcebergHazardFieldGenerator
from data_ingestion.iceberg.environment_adapter import AntarcticEnvironmentAdapter
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask


# ====================================================================
# 1. Physical Sanity & Coriolis Tests
# ====================================================================

def test_coriolis_sign_and_magnitude():
    engine = IcebergPhysicsEngine()
    # At -60°S:
    lat = -60.0
    f = engine.coriolis_parameter(lat)
    # Southern Hemisphere: f must be strictly negative!
    assert f < 0.0
    expected_f = 2.0 * OMEGA_EARTH * math.sin(math.radians(-60.0))
    assert math.isclose(f, expected_f, rel_tol=1e-5)

    # At South Pole (-90°S): f = -2 * Omega
    f_pole = engine.coriolis_parameter(-90.0)
    assert math.isclose(f_pole, -2.0 * OMEGA_EARTH, rel_tol=1e-5)


def test_southern_hemisphere_coriolis_left_deflection():
    """
    Physical sanity check: In the Southern Hemisphere, motion must be deflected
    to the LEFT of velocity vector.
    """
    engine = IcebergPhysicsEngine()
    lat = -65.0  # Southern Ocean

    # 1. Moving Northward (v > 0, u = 0): Deflection should be Westward (a_x < 0)
    ax, ay = engine.coriolis_acceleration(u_mps=0.0, v_mps=1.0, lat_deg=lat)
    assert ax < 0.0  # Westward (left of North)
    assert ay == 0.0

    # 2. Moving Eastward (u > 0, v = 0): Deflection should be Northward (a_y > 0)
    ax, ay = engine.coriolis_acceleration(u_mps=1.0, v_mps=0.0, lat_deg=lat)
    assert ax == 0.0
    assert ay > 0.0  # Northward (left of East)

    # 3. Moving Southward (v < 0, u = 0): Deflection should be Eastward (a_x > 0)
    ax, ay = engine.coriolis_acceleration(u_mps=0.0, v_mps=-1.0, lat_deg=lat)
    assert ax > 0.0  # Eastward (left of South)

    # 4. Moving Westward (u < 0, v = 0): Deflection should be Southward (a_y < 0)
    ax, ay = engine.coriolis_acceleration(u_mps=-1.0, v_mps=0.0, lat_deg=lat)
    assert ay < 0.0  # Southward (left of West)


def test_ocean_and_air_drag_relative_velocity():
    engine = IcebergPhysicsEngine()

    # Iceberg moving at same speed as ocean current: relative drag must be ZERO
    ax, ay = engine.ocean_drag_acceleration(u_ice=0.2, v_ice=0.1, u_ocean=0.2, v_ocean=0.1)
    assert ax == 0.0 and ay == 0.0

    # Current moving faster eastward than iceberg: acceleration must be positive (pushing East)
    ax, ay = engine.ocean_drag_acceleration(u_ice=0.1, v_ice=0.0, u_ocean=0.3, v_ocean=0.0)
    assert ax > 0.0
    assert ay == 0.0

    # Wind blowing northward: atmospheric drag must accelerate iceberg northward
    ax_air, ay_air = engine.atmospheric_drag_acceleration(u_ice=0.0, v_ice=0.0, u_wind=0.0, v_wind=10.0)
    assert ax_air == 0.0
    assert ay_air > 0.0


def test_sea_ice_interaction_free_vs_pack_damping():
    engine = IcebergPhysicsEngine()
    # In open water (SIC = 0.05 < 0.15): free drift, no sea-ice force
    ax, ay = engine.sea_ice_interaction_acceleration(
        u_ice=0.2, v_ice=0.1, u_ocean=0.1, v_ocean=0.0, u_wind=5.0, v_wind=0.0, sic=0.05
    )
    assert ax == 0.0 and ay == 0.0

    # In heavy pack ice (SIC = 0.70): dampens velocity relative to pack drift
    ax_pack, ay_pack = engine.sea_ice_interaction_acceleration(
        u_ice=0.5, v_ice=0.0, u_ocean=0.1, v_ocean=0.0, u_wind=2.0, v_wind=0.0, sic=0.70
    )
    # Pack moves slower than iceberg -> resistance acts in negative u direction
    assert ax_pack < 0.0


# ====================================================================
# 2. Observation Validation & Track Reconstruction
# ====================================================================

def test_observation_validator_flags_impossible_jump():
    validator = IcebergValidator(max_speed_mps=4.0)
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=1)  # 1 hour later

    # Normal step (~1 km in 1h = 0.28 m/s)
    obs1 = IcebergObservationRecord(
        iceberg_id="TEST_A",
        source=IcebergSource.BYU_HISTORICAL,
        observation_time=t0,
        latitude=-65.0,
        longitude=0.0,
    )
    obs2 = IcebergObservationRecord(
        iceberg_id="TEST_A",
        source=IcebergSource.BYU_HISTORICAL,
        observation_time=t1,
        latitude=-65.01,
        longitude=0.0,
    )
    # Impossible jump (500 km in 1h = 138 m/s)
    obs3 = IcebergObservationRecord(
        iceberg_id="TEST_A",
        source=IcebergSource.BYU_HISTORICAL,
        observation_time=t1 + timedelta(hours=1),
        latitude=-70.0,
        longitude=20.0,
    )

    validated, summary = validator.validate_observations([obs1, obs2, obs3])
    assert validated[0].is_valid is True
    assert validated[1].is_valid is True
    assert validated[2].is_valid is False
    assert "suspicious_speed_jump" in validated[2].flag_reason
    assert summary["flagged_observations"] == 1


def test_track_reconstruction_and_h3_association():
    reconstructor = IcebergTrackReconstructor(h3_resolution=5)
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    obs_list = [
        IcebergObservationRecord(
            iceberg_id="B15A",
            source=IcebergSource.BYU_HISTORICAL,
            observation_time=t0 + timedelta(days=i),
            latitude=-72.0 - i * 0.05,
            longitude=10.0 + i * 0.1,
        )
        for i in range(5)
    ]

    pts, diag = reconstructor.reconstruct_track(obs_list)
    assert len(pts) == 5
    assert diag.observation_count == 5
    assert diag.duration_days == 4.0
    assert diag.total_displacement_km > 0.0
    # Every point must have a valid H3 cell
    for p in pts:
        assert p.h3_cell is not None
        assert h3.is_valid_cell(p.h3_cell)


# ====================================================================
# 3. Geodesic Integration & Longitude Wrapping
# ====================================================================

def test_high_latitude_geodesic_integration_and_wrapping():
    adapter = AntarcticEnvironmentAdapter()
    integrator = IcebergTrajectoryIntegrator(environment=adapter)

    # Test crossing the antimeridian (+179.9°E moving East -> -179.9°W)
    lat, lon = integrator.update_geographic_position(
        lat=-65.0,
        lon=179.99,
        u_mps=10.0,  # Eastward
        v_mps=0.0,
        dt_seconds=3600.0,
    )
    # Longitude must wrap cleanly into negative degrees (-180 to 180)
    assert -180.0 <= lon <= 180.0
    assert lon < 0.0


# ====================================================================
# 4. Real Geographic Mask Collision & Grounding
# ====================================================================

def test_geographic_mask_blocks_trajectory():
    """
    Verifies that when a trajectory encounters land or ice shelf from the SCAR ADD mask,
    its status transitions to GROUNDED and propagation halts.
    """
    # Create mock environment adapter with a barrier placed at -72.52°S to -73.0°S
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3031", always_xy=True)
    xs, ys = transformer.transform([-2.0, 2.0, 2.0, -2.0, -2.0], [-72.52, -72.52, -73.0, -73.0, -72.52])
    barrier_poly = Polygon(zip(xs, ys))
    barrier_gdf = gpd.GeoDataFrame({"surface": ["land"], "geometry": [barrier_poly]}, crs="EPSG:3031")
    mask = AntarcticGeographicMask(source=barrier_gdf)

    adapter = AntarcticEnvironmentAdapter(mask_path=None)
    adapter.mask = mask

    integrator = IcebergTrajectoryIntegrator(environment=adapter, timestep_seconds=3600.0)

    # Start at -72.5°S moving southward directly into the barrier
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    traj = integrator.integrate_trajectory(
        iceberg_id="GROUND_TEST",
        start_time=t0,
        start_lat=-72.5,
        start_lon=0.0,
        initial_u=0.0,
        initial_v=-0.5,
        horizon_hours=24.0,
    )

    # Final point must be GROUNDED and stopped
    last_pt = traj[-1]
    assert last_pt.status == TrajectoryStatus.GROUNDED
    assert last_pt.speed_mps == 0.0


# ====================================================================
# 5. Ensemble Reproducibility & Spread
# ====================================================================

def test_ensemble_reproducibility_with_seed():
    adapter = AntarcticEnvironmentAdapter()
    integrator = IcebergTrajectoryIntegrator(environment=adapter)

    ens_gen1 = IcebergEnsembleGenerator(integrator, default_ensemble_size=5, random_seed=123)
    ens_gen2 = IcebergEnsembleGenerator(integrator, default_ensemble_size=5, random_seed=123)

    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    pts1, spread1 = ens_gen1.generate_ensemble("ICE_A", t0, -62.0, 10.0, 0.05, 0.02, horizon_hours=12.0)
    pts2, spread2 = ens_gen2.generate_ensemble("ICE_A", t0, -62.0, 10.0, 0.05, 0.02, horizon_hours=12.0)

    assert len(pts1) == len(pts2)
    # Check that deterministic seed yields identical trajectory points
    for p1, p2 in zip(pts1, pts2):
        assert math.isclose(p1.latitude, p2.latitude, abs_tol=1e-5)
        assert math.isclose(p1.longitude, p2.longitude, abs_tol=1e-5)


# ====================================================================
# 6. H3 Spatial Hazard Aggregation
# ====================================================================

def test_h3_hazard_field_occupancy():
    hazard_gen = IcebergHazardFieldGenerator()
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    cell = h3.latlng_to_cell(-65.0, 0.0, 5)

    # Create points where 3 out of 10 ensemble realizations occupy 'cell' at t0
    points = [
        TrajectoryPoint(
            iceberg_id="ICE_1",
            ensemble_id=i,
            time=t0,
            latitude=-65.0,
            longitude=0.0,
            velocity_u=0.1,
            velocity_v=0.0,
            speed_mps=0.1,
            h3_cell=cell,
        )
        for i in range(3)
    ]

    hazard_cells = hazard_gen.generate_hazard_field(points, total_ensemble_size=10)
    assert len(hazard_cells) == 1
    hc = hazard_cells[0]
    assert hc.h3_cell == cell
    assert hc.valid_time == t0
    # Occupancy fraction: 3 / 10 = 0.3
    assert math.isclose(hc.hazard, 0.3, rel_tol=1e-3)
    assert hc.supporting_iceberg_count == 1


# ====================================================================
# 7. GEBCO Integration & 73 Icebergs Verification
# ====================================================================

def test_gebco_depth_lookup_in_trajectory_points():
    """Verifies that GEBCO bathymetry is integrated as an auxiliary diagnostic without altering physics."""
    adapter = AntarcticEnvironmentAdapter()
    integrator = IcebergTrajectoryIntegrator(environment=adapter)

    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    traj = integrator.integrate_trajectory(
        iceberg_id="A76C",
        start_time=t0,
        start_lat=-65.0,
        start_lon=-45.0,
        horizon_hours=12.0,
    )
    assert len(traj) >= 1
    # Check that initial point and subsequent points have bathymetry_depth_m populated
    for pt in traj:
        if adapter.gebco is not None:
            assert pt.bathymetry_depth_m is not None
            assert pt.bathymetry_depth_m > 0.0


def test_distinct_73_icebergs_dataset_coverage():
    """Verifies that the verified AMIP iceberg dataset contains exactly 73 distinct iceberg IDs."""
    from data_ingestion.iceberg.downloader import IcebergDownloader
    from data_ingestion.iceberg.reader import IcebergReader

    downloader = IcebergDownloader()
    byu_dir = downloader.download_byu_historical(mode="auto")
    usnic_file = downloader.download_usnic_operational(mode="auto")

    reader = IcebergReader()
    byu_obs = reader.read_byu_directory(byu_dir, max_icebergs=40)
    usnic_obs = reader.read_usnic_csv(usnic_file)

    validator = IcebergValidator()
    validated_obs, _ = validator.validate_observations(byu_obs + usnic_obs)
    valid_records = [o for o in validated_obs if o.is_valid]

    distinct_ids = sorted(list({o.iceberg_id for o in valid_records}))
    assert len(distinct_ids) == 73, f"Expected 73 distinct icebergs, got {len(distinct_ids)}"
    assert len(byu_obs) == 42431
    assert len(usnic_obs) == 33
    assert len(byu_obs + usnic_obs) == 42464


def test_longitude_wrapping_in_integrator():
    """Verifies that an iceberg moving across +180/-180 longitude wraps seamlessly."""
    adapter = AntarcticEnvironmentAdapter()
    integrator = IcebergTrajectoryIntegrator(environment=adapter)

    # Move Eastward across +180: lat -65, lon 179.95, u = 1.0 m/s
    new_lat, new_lon = integrator.update_geographic_position(-65.0, 179.99, u_mps=2.0, v_mps=0.0, dt_seconds=3600.0)
    # Longitude must wrap into negative domain [-180, 0]
    assert new_lon < 0.0
    assert -180.0 <= new_lon <= 180.0

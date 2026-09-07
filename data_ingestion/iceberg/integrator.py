"""
High-latitude geodesic numerical integrator for iceberg trajectories.
Integrates equations of motion on a spherical Earth, enforces SCAR ADD geographic mask constraints,
and attaches environmental forcing and H3 cell indexes at each discrete timestep.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone
import math
import h3
from core.logging import get_logger
from data_ingestion.iceberg.metadata import (
    TrajectoryPoint,
    TrajectoryStatus,
    ForcingMode,
)
from data_ingestion.iceberg.physics import (
    IcebergPhysicsEngine,
    IcebergPhysicalProfile,
)
from data_ingestion.iceberg.environment_adapter import AntarcticEnvironmentAdapter

logger = get_logger("data_ingestion.iceberg.integrator")

R_EARTH_METERS = 6371000.0


class IcebergTrajectoryIntegrator:
    """Simulates deterministic iceberg trajectories coupled with environmental forcing."""

    def __init__(
        self,
        environment: AntarcticEnvironmentAdapter,
        timestep_seconds: float = 3600.0,  # 1 hour default
        h3_resolution: int = 5,
    ):
        self.env = environment
        self.dt = timestep_seconds
        self.h3_resolution = h3_resolution

    def update_geographic_position(
        self,
        lat: float,
        lon: float,
        u_mps: float,
        v_mps: float,
        dt_seconds: float,
    ) -> Tuple[float, float]:
        """
        Geodesic spherical position integration:
          dlat = (v * dt) / R
          dlon = (u * dt) / (R * cos(lat))
        Handles polar proximity and longitude wrapping [-180, 180].
        """
        dlat_rad = (v_mps * dt_seconds) / R_EARTH_METERS
        new_lat = lat + math.degrees(dlat_rad)
        new_lat = max(-89.9, min(89.9, new_lat))

        # Clamp cos(lat) to prevent division by zero at pole
        cos_lat = max(0.01, math.cos(math.radians(new_lat)))
        dlon_rad = (u_mps * dt_seconds) / (R_EARTH_METERS * cos_lat)
        new_lon = lon + math.degrees(dlon_rad)

        # Normalize longitude into [-180.0, 180.0]
        norm_lon = ((new_lon + 180.0) % 360.0) - 180.0
        return round(new_lat, 5), round(norm_lon, 5)

    def integrate_trajectory(
        self,
        iceberg_id: str,
        start_time: datetime,
        start_lat: float,
        start_lon: float,
        initial_u: float = 0.0,
        initial_v: float = 0.0,
        horizon_hours: float = 2160.0,  # 90 days default = 90 * 24 = 2160 hours
        profile: Optional[IcebergPhysicalProfile] = None,
        ensemble_id: int = 0,
    ) -> List[TrajectoryPoint]:
        """
        Executes forward trajectory integration from initial state up to specified horizon.
        """
        physics = IcebergPhysicsEngine(profile=profile or IcebergPhysicalProfile())
        steps_count = int(math.ceil((horizon_hours * 3600.0) / self.dt))

        current_lat = start_lat
        current_lon = start_lon
        current_u = initial_u
        current_v = initial_v
        current_time = start_time

        trajectory: List[TrajectoryPoint] = []

        # 0. Initial step check
        is_blocked, cov_status = self.env.get_geographic_status(current_lat, current_lon)
        initial_cell = h3.latlng_to_cell(current_lat, current_lon, self.h3_resolution)
        init_depth = self.env.get_bathymetry_depth(current_lat, current_lon)
        
        trajectory.append(
            TrajectoryPoint(
                iceberg_id=iceberg_id,
                ensemble_id=ensemble_id,
                time=current_time,
                latitude=current_lat,
                longitude=current_lon,
                velocity_u=0.0 if is_blocked else round(current_u, 3),
                velocity_v=0.0 if is_blocked else round(current_v, 3),
                speed_mps=0.0 if is_blocked else round(math.hypot(current_u, current_v), 3),
                h3_cell=initial_cell,
                status=TrajectoryStatus.GROUNDED if is_blocked else TrajectoryStatus.ACTIVE_DRIFT,
                forcing_mode=ForcingMode.DIRECT_FORECAST,
                forcing_source="INITIAL_OBSERVATION",
                bathymetry_depth_m=round(init_depth, 1) if init_depth is not None else None,
            )
        )

        if is_blocked:
            logger.info("Iceberg initial state is grounded", iceberg_id=iceberg_id, lat=start_lat, lon=start_lon)
            return trajectory

        for step in range(1, steps_count + 1):
            sim_time = current_time + timedelta(seconds=self.dt)

            # 1. Retrieve environmental forcing
            u_oc, v_oc, oc_mode, oc_src = self.env.get_current(current_lat, current_lon, sim_time)
            u_wd, v_wd, wd_mode, wd_src = self.env.get_wind(current_lat, current_lon, sim_time)
            sic, sic_mode, sic_src = self.env.get_sic(current_lat, current_lon, sim_time)

            step_mode = (
                ForcingMode.DIRECT_FORECAST
                if (oc_mode == ForcingMode.DIRECT_FORECAST and wd_mode == ForcingMode.DIRECT_FORECAST)
                else ForcingMode.EXTENDED_FORCING
            )
            step_src = f"{oc_src}+{wd_src}"

            # 2. Sub-step integration within the timestep for numerical stability
            n_substeps = 12
            sub_dt = self.dt / n_substeps
            curr_u_sub = current_u
            curr_v_sub = current_v

            for _ in range(n_substeps):
                ax, ay = physics.total_acceleration(
                    u_ice=curr_u_sub,
                    v_ice=curr_v_sub,
                    lat_deg=current_lat,
                    u_ocean=u_oc,
                    v_ocean=v_oc,
                    u_wind=u_wd,
                    v_wind=v_wd,
                    sic=sic,
                )
                # Physical acceleration sanity bound
                ax = max(-0.05, min(0.05, ax))
                ay = max(-0.05, min(0.05, ay))
                curr_u_sub += ax * sub_dt
                curr_v_sub += ay * sub_dt

                # Realistic speed capping (~3.5 m/s maximum sustained drift)
                spd = math.hypot(curr_u_sub, curr_v_sub)
                if spd > 3.5:
                    curr_u_sub = (curr_u_sub / spd) * 3.5
                    curr_v_sub = (curr_v_sub / spd) * 3.5

            new_u = curr_u_sub
            new_v = curr_v_sub

            # 3. Update geographic position
            new_lat, new_lon = self.update_geographic_position(
                current_lat, current_lon, (current_u + new_u) * 0.5, (current_v + new_v) * 0.5, self.dt
            )

            # 5. Check real SCAR ADD geographic mask and GEBCO bathymetry
            is_grounded, cov = self.env.get_geographic_status(new_lat, new_lon)
            depth_m = self.env.get_bathymetry_depth(new_lat, new_lon)

            # 6. Assign H3 cell
            cell = h3.latlng_to_cell(new_lat, new_lon, self.h3_resolution)

            if is_grounded:
                # Iceberg has grounded on land or ice shelf: freeze motion
                pt = TrajectoryPoint(
                    iceberg_id=iceberg_id,
                    ensemble_id=ensemble_id,
                    time=sim_time,
                    latitude=new_lat,
                    longitude=new_lon,
                    velocity_u=0.0,
                    velocity_v=0.0,
                    speed_mps=0.0,
                    h3_cell=cell,
                    status=TrajectoryStatus.GROUNDED,
                    forcing_mode=step_mode,
                    forcing_source=step_src,
                    current_u=u_oc,
                    current_v=v_oc,
                    wind_u=u_wd,
                    wind_v=v_wd,
                    sic=sic,
                    bathymetry_depth_m=round(depth_m, 1) if depth_m is not None else None,
                )
                trajectory.append(pt)
                break

            pt = TrajectoryPoint(
                iceberg_id=iceberg_id,
                ensemble_id=ensemble_id,
                time=sim_time,
                latitude=new_lat,
                longitude=new_lon,
                velocity_u=round(new_u, 3),
                velocity_v=round(new_v, 3),
                speed_mps=round(math.hypot(new_u, new_v), 3),
                h3_cell=cell,
                status=TrajectoryStatus.ACTIVE_DRIFT,
                forcing_mode=step_mode,
                forcing_source=step_src,
                current_u=round(u_oc, 3),
                current_v=round(v_oc, 3),
                wind_u=round(u_wd, 3),
                wind_v=round(v_wd, 3),
                sic=round(sic, 2),
                bathymetry_depth_m=round(depth_m, 1) if depth_m is not None else None,
            )
            trajectory.append(pt)

            current_lat = new_lat
            current_lon = new_lon
            current_u = new_u
            current_v = new_v
            current_time = sim_time

        return trajectory

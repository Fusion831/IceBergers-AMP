"""SQLAlchemy 2.0 ORM Models for AMIP."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from core.database import Base


class MissionModel(Base):
    """Mission persistence model."""
    __tablename__ = "missions"

    mission_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    planning_start = Column(DateTime, nullable=False)
    planning_end = Column(DateTime, nullable=False)
    origin_name = Column(String(100), nullable=False)
    origin_latitude = Column(Float, nullable=False)
    origin_longitude = Column(Float, nullable=False)
    vessel_id = Column(String(100), nullable=False)
    priority_safety = Column(Float, default=0.5, nullable=False)
    priority_fuel = Column(Float, default=0.3, nullable=False)
    priority_time = Column(Float, default=0.2, nullable=False)
    status = Column(String(50), default="CONFIGURED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    destinations = relationship("DestinationModel", back_populates="mission", cascade="all, delete-orphan")
    routes = relationship("RouteModel", back_populates="mission", cascade="all, delete-orphan")


class DestinationModel(Base):
    """Destination stations and waypoints for a mission."""
    __tablename__ = "mission_destinations"

    destination_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    station_code = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    sequence_order = Column(Integer, default=1, nullable=False)

    mission = relationship("MissionModel", back_populates="destinations")


class VesselModel(Base):
    """Vessel profile persistence model."""
    __tablename__ = "vessels"

    vessel_id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    length_m = Column(Float, nullable=False)
    beam_m = Column(Float, nullable=False)
    draft_m = Column(Float, nullable=False)
    displacement_mt = Column(Float, nullable=False)
    ice_class = Column(String(20), nullable=False)
    cruising_speed_knots = Column(Float, nullable=False)
    max_speed_knots = Column(Float, nullable=False)
    endurance_days = Column(Integer, nullable=False)
    max_navigable_sic = Column(Float, nullable=False)
    under_keel_margin_m = Column(Float, nullable=False)
    base_fuel_burn_mt_per_day = Column(Float, nullable=False)
    is_verified_operational = Column(Boolean, default=False, nullable=False)
    config_json = Column(JSON, default=dict)


class RouteModel(Base):
    """Optimized route persistence model."""
    __tablename__ = "routes"

    route_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False, index=True)
    objective = Column(String(50), nullable=False)  # SAFEST, FASTEST, FUEL_EFFICIENT, BALANCED
    departure_time = Column(DateTime, nullable=False)
    distance_nm = Column(Float, nullable=False)
    duration_hours = Column(Float, nullable=False)
    duration_days = Column(Float, nullable=False)
    estimated_fuel_mt = Column(Float, nullable=False)
    mean_risk = Column(Float, nullable=False)
    max_risk = Column(Float, nullable=False)
    p95_risk = Column(Float, nullable=False)
    ice_exposure_nm = Column(Float, default=0.0)
    iceberg_hazard_exposure = Column(Float, default=0.0)
    weather_rough_seas_hours = Column(Float, default=0.0)
    geojson_linestring = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=True)
    is_mock = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    mission = relationship("MissionModel", back_populates="routes")
    waypoints = relationship("WaypointModel", back_populates="route", cascade="all, delete-orphan")


class WaypointModel(Base):
    """Discrete waypoint along an optimized route."""
    __tablename__ = "route_waypoints"

    waypoint_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_id = Column(String(36), ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    estimated_arrival = Column(DateTime, nullable=False)
    speed_knots = Column(Float, nullable=False)
    local_risk = Column(Float, nullable=False)
    local_sic = Column(Float, nullable=False)
    risk_attribution_json = Column(JSON, nullable=True)

    route = relationship("RouteModel", back_populates="waypoints")


class IcebergObservationModel(Base):
    """Satellite or radar reported iceberg observation."""
    __tablename__ = "iceberg_observations"

    iceberg_id = Column(String(100), primary_key=True)
    observation_time = Column(DateTime, primary_key=True)
    source = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    length_m = Column(Float, nullable=True)
    width_m = Column(Float, nullable=True)
    drift_speed_knots = Column(Float, nullable=True)
    drift_direction_deg = Column(Float, nullable=True)
    is_grounded = Column(Boolean, default=False)


class ModelRunModel(Base):
    """Provenance and audit log for model runs."""
    __tablename__ = "model_runs"

    run_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    execution_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    parameters = Column(JSON, default=dict)
    input_dataset_refs = Column(JSON, default=dict)
    artifact_checksum = Column(String(64), nullable=True)
    is_mock = Column(Boolean, default=True)


class DatasetCatalogModel(Base):
    """Catalog of scientific raster arrays and Zarr slices."""
    __tablename__ = "dataset_catalog"

    layer_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    variable_name = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    initialization_time = Column(DateTime, nullable=False)
    valid_time = Column(DateTime, nullable=False, index=True)
    lead_time_days = Column(Integer, default=0, nullable=False)
    uri = Column(String(512), nullable=False)
    checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

"""Route optimization, 4D validation, and alternative comparison endpoints."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query, status, HTTPException
from domain.route import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteAlternative,
    RouteComparison,
)
from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from routing.amip_custom_router import AMIPCustomRouter
from services.routing_service import RoutingService
from api.dependencies import get_routing_service

router = APIRouter(prefix="/routes", tags=["Routes"])


class RouteCompareRequest(BaseModel):
    route_ids: List[str]


STATIONS_CATALOG = [
    {"id": "cape-town", "name": "Cape Town Gateway Port", "latitude": -33.9249, "longitude": 18.4241, "country": "South Africa", "type": "Gateway Port", "category": "Gateway Port", "description": "Primary departure and logistics hub"},
    {"id": "bharati", "name": "Bharati Station (Larsemann Hills)", "latitude": -69.4072, "longitude": 76.1911, "country": "India", "type": "Antarctic Station", "category": "Antarctic Station", "description": "Indian Antarctic research base in Prydz Bay"},
    {"id": "maitri", "name": "Maitri Station (India Bay Access)", "latitude": -69.9500, "longitude": 11.7300, "country": "India", "type": "Antarctic Station", "category": "Antarctic Station", "description": "Indian Antarctic maritime access node at India Bay / Queen Maud Land"},
    {"id": "hobart", "name": "Hobart Gateway Port", "latitude": -42.8821, "longitude": 147.3272, "country": "Australia", "type": "Gateway Port", "category": "Gateway Port", "description": "Tasmanian gateway port to East Antarctica"},
    {"id": "fremantle", "name": "Fremantle / Perth Gateway", "latitude": -32.0569, "longitude": 115.7439, "country": "Australia", "type": "Gateway Port", "category": "Gateway Port", "description": "Western Australian Indian Ocean port"},
    {"id": "punta-arenas", "name": "Punta Arenas Gateway", "latitude": -53.1638, "longitude": -70.9171, "country": "Chile", "type": "Gateway Port", "category": "Gateway Port", "description": "Strait of Magellan southern gateway"},
    {"id": "ushuaia", "name": "Ushuaia Gateway", "latitude": -54.8019, "longitude": -68.3030, "country": "Argentina", "type": "Gateway Port", "category": "Gateway Port", "description": "Tierra del Fuego gateway to Antarctic Peninsula"},
    {"id": "christchurch", "name": "Christchurch / Lyttelton Gateway", "latitude": -43.6038, "longitude": 172.7194, "country": "New Zealand", "type": "Gateway Port", "category": "Gateway Port", "description": "Pacific gateway to Ross Sea"},
    {"id": "mcmurdo", "name": "McMurdo Station (Ross Island)", "latitude": -77.8419, "longitude": 166.6863, "country": "USA", "type": "Antarctic Station", "category": "Antarctic Station", "description": "Largest research station in Antarctica"},
    {"id": "casey", "name": "Casey Station (Vincennes Bay)", "latitude": -66.2822, "longitude": 110.5276, "country": "Australia", "type": "Antarctic Station", "category": "Antarctic Station", "description": "Australian Antarctic base"},
    {"id": "davis", "name": "Davis Station (Vestfold Hills)", "latitude": -68.5764, "longitude": 77.9672, "country": "Australia", "type": "Antarctic Station", "category": "Antarctic Station", "description": "Australian Antarctic base"},
    {"id": "mawson", "name": "Mawson Station (Holme Bay)", "latitude": -67.6044, "longitude": 62.8739, "country": "Australia", "type": "Antarctic Station", "category": "Antarctic Station", "description": "Oldest continuously operating Antarctic base"},
    {"id": "troll", "name": "Troll Station (Crown Bay Access)", "latitude": -69.8500, "longitude": 2.5350, "country": "Norway", "type": "Antarctic Station", "category": "Antarctic Station", "description": "Norwegian Antarctic base maritime access"},
    {"id": "neumayer", "name": "Neumayer Station III (Ekström Ice Shelf)", "latitude": -70.6744, "longitude": -8.2742, "country": "Germany", "type": "Antarctic Station", "category": "Antarctic Station", "description": "German Antarctic research station"}
]

STATION_MAP = {s["id"]: s for s in STATIONS_CATALOG}


class DynamicVoyagePlanRequest(BaseModel):
    origin_station_id: Optional[str] = None
    destination_station_id: Optional[str] = None
    origin_coords: Optional[Tuple[float, float]] = None  # (lon, lat)
    destination_coords: Optional[Tuple[float, float]] = None  # (lon, lat)
    origin_name: Optional[str] = None
    destination_name: Optional[str] = None
    vessel_id: Optional[str] = "sagar-kanya"
    departure_time: Optional[datetime] = None
    objectives: Optional[List[str]] = Field(default_factory=lambda: ["FASTEST", "SAFEST", "SHORTEST", "FUEL_EFFICIENT", "BALANCED"])


@router.get("/stations", status_code=status.HTTP_200_OK)
async def get_available_stations() -> Dict[str, Any]:
    """Retrieve catalog of 14 supported Antarctic stations and gateway ports."""
    return {"stations": STATIONS_CATALOG}


@router.post("/plan-voyage", status_code=status.HTTP_200_OK)
async def plan_dynamic_voyage(request: DynamicVoyagePlanRequest) -> Dict[str, Any]:
    """Dynamically evaluate multi-objective Pareto-optimal voyage alternatives between custom stations or coordinates."""
    # 1. Resolve Origin
    if request.origin_coords:
        orig_lon, orig_lat = request.origin_coords
        orig_name = request.origin_name or f"Custom ({orig_lat:.2f}°, {orig_lon:.2f}°)"
    elif request.origin_station_id and request.origin_station_id in STATION_MAP:
        st = STATION_MAP[request.origin_station_id]
        orig_lat, orig_lon = st["latitude"], st["longitude"]
        orig_name = st["name"]
    else:
        st = STATIONS_CATALOG[0]
        orig_lat, orig_lon = st["latitude"], st["longitude"]
        orig_name = st["name"]

    # 2. Resolve Destination
    if request.destination_coords:
        dest_lon, dest_lat = request.destination_coords
        dest_name = request.destination_name or f"Custom ({dest_lat:.2f}°, {dest_lon:.2f}°)"
    elif request.destination_station_id and request.destination_station_id in STATION_MAP:
        st = STATION_MAP[request.destination_station_id]
        dest_lat, dest_lon = st["latitude"], st["longitude"]
        dest_name = st["name"]
    else:
        st = STATIONS_CATALOG[1]
        dest_lat, dest_lon = st["latitude"], st["longitude"]
        dest_name = st["name"]

    origin_point = GeoPoint(latitude=orig_lat, longitude=orig_lon)
    dest_point = GeoPoint(latitude=dest_lat, longitude=dest_lon)
    dep_time = request.departure_time or datetime(2024, 1, 1, tzinfo=timezone.utc)
    if dep_time.tzinfo is None:
        dep_time = dep_time.replace(tzinfo=timezone.utc)

    # 3. Instantiate Router & Vessel
    router_engine = AMIPCustomRouter(mode="corridor")
    vessel = VesselProfile()

    # 4. Generate Alternative for Each Requested Objective
    objectives_to_run = request.objectives or ["FASTEST", "SAFEST", "SHORTEST", "FUEL_EFFICIENT", "BALANCED"]
    calculated_routes = []

    for obj_name in objectives_to_run:
        try:
            obj_enum = RouteObjective(obj_name)
        except Exception:
            obj_enum = RouteObjective.FASTEST

        alt: RouteAlternative = router_engine.optimize_leg(
            origin=origin_point,
            destination=dest_point,
            departure_time=dep_time,
            objective=obj_enum,
            vessel=vessel,
        )

        calculated_routes.append(alt.model_dump(mode="json"))

    return {
        "origin": {"name": orig_name, "latitude": orig_lat, "longitude": orig_lon},
        "destination": {"name": dest_name, "latitude": dest_lat, "longitude": dest_lon},
        "departure_time": dep_time.isoformat(),
        "vessel_id": request.vessel_id or "sagar-kanya",
        "routes": calculated_routes,
    }


@router.get("/canonical", response_model=RouteOptimizationResponse, status_code=status.HTTP_200_OK)
async def get_canonical_ncpor_routes(
    scenario: str = Query("historical_trend_normal", description="SIC scenario (historical_trend_normal, historical_trend_low_ice, historical_trend_high_ice, ice_knn)"),
    service: RoutingService = Depends(get_routing_service),
) -> RouteOptimizationResponse:
    """Retrieve the canonical NCPOR mission route alternatives (Cape Town -> Bharati -> Maitri -> Cape Town)."""
    return service.get_canonical_ncpor_routes(scenario=scenario)


@router.post("/optimize", response_model=RouteOptimizationResponse, status_code=status.HTTP_200_OK)
async def optimize_routes(
    request: RouteOptimizationRequest,
    service: RoutingService = Depends(get_routing_service),
) -> RouteOptimizationResponse:
    """Generate 4 geometrically distinct route alternatives (Safest, Fastest, Fuel-Efficient, Balanced)."""
    return service.optimize_routes(request)


@router.get("/{id}", response_model=RouteAlternative)
async def get_route(
    id: str,
    service: RoutingService = Depends(get_routing_service),
) -> RouteAlternative:
    """Retrieve detailed geometry, 4D waypoints, and validated risk metrics for a route."""
    return service.get_route(id)


@router.post("/compare", response_model=RouteComparison)
async def compare_routes(
    body: RouteCompareRequest,
    service: RoutingService = Depends(get_routing_service),
) -> RouteComparison:
    """Compare multiple route alternatives side-by-side on duration, fuel, and risk exposure."""
    return service.compare_routes(body.route_ids)

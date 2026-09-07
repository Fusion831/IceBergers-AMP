"""
Mission-Ready Navigation Nodes and Maritime Access Points.
Defines canonical waypoints for the Indian Antarctic Expedition transect:
    Cape Town -> Bharati Maritime Access -> Maitri Maritime Access -> Cape Town

CRITICAL GEOGRAPHIC DISTINCTION:
Maitri research station (-70.7644°S, 11.7340°E) is located inland on ice/rock
in the Schirmacher Oasis and is classified as LAND/ICE_SHELF in SCAR ADD.
Vessels CANNOT navigate directly to inland coordinates.
The operational maritime access point is India Bay / Princess Astrid Coast (~69.95°S, 11.73°E),
from where overland tracked vehicle traverses or helicopter operations resupply the station.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MaritimeAccessNode(BaseModel):
    """Represents a validated maritime departure, destination, or access node."""
    node_id: str
    name: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    is_inland: bool = False
    station_code: Optional[str] = None
    description: str = ""
    operational_sector: str = ""


# Canonical Navigation Nodes
CAPE_TOWN = MaritimeAccessNode(
    node_id="cape_town_port",
    name="Port of Cape Town",
    latitude=-33.9188,
    longitude=18.4233,
    is_inland=False,
    station_code="CPT",
    description="Expedition staging base and primary departure/demobilization port in South Africa.",
    operational_sector="South Atlantic / Southern Ocean Gate",
)

BHARATI_MARITIME_ACCESS = MaritimeAccessNode(
    node_id="bharati_maritime_access",
    name="Bharati Maritime Access Node (Larsemann Hills / Prydz Bay)",
    latitude=-69.3800,
    longitude=76.1900,
    is_inland=False,
    station_code="BHARATI",
    description="Coastal ocean access point in Prydz Bay adjacent to Larsemann Hills.",
    operational_sector="Prydz Bay / East Antarctica",
)

MAITRI_MARITIME_ACCESS = MaritimeAccessNode(
    node_id="maitri_maritime_access",
    name="Maitri Maritime Access Node (India Bay / Lazarev Sea)",
    latitude=-69.9500,
    longitude=11.7300,
    is_inland=False,
    station_code="MAITRI_MARITIME",
    description="Navigable coastal shelf edge / fast ice margin at India Bay (Princess Astrid Coast). Overland staging point for Maitri.",
    operational_sector="Princess Astrid Coast / Lazarev Sea",
)

MAITRI_INLAND_STATION = MaritimeAccessNode(
    node_id="maitri_inland_station",
    name="Maitri Inland Research Station (Schirmacher Oasis)",
    latitude=-70.7644,
    longitude=11.7340,
    is_inland=True,
    station_code="MAITRI_INLAND",
    description="Inland Antarctic research station situated on rock/continental ice sheet. Hard blocked for maritime transit by SCAR ADD.",
    operational_sector="Schirmacher Oasis (Inland)",
)

# Canonical 4-Leg Expedition Transect
MISSION_TRANSECT_NODES: List[MaritimeAccessNode] = [
    CAPE_TOWN,
    BHARATI_MARITIME_ACCESS,
    MAITRI_MARITIME_ACCESS,
    CAPE_TOWN,
]


def get_canonical_mission_transect() -> List[MaritimeAccessNode]:
    """Returns the ordered 4-stage maritime voyage nodes for AMIP routing."""
    return list(MISSION_TRANSECT_NODES)


def explain_maitri_node_selection() -> Dict[str, Any]:
    """Provides architectural explanation of the Maitri maritime access node."""
    return {
        "maritime_access_point": {
            "name": MAITRI_MARITIME_ACCESS.name,
            "coordinates": [MAITRI_MARITIME_ACCESS.latitude, MAITRI_MARITIME_ACCESS.longitude],
            "navigable": True,
            "rationale": "Located at the coastal fast-ice / shelf boundary in India Bay (~69.95°S).",
        },
        "inland_station": {
            "name": MAITRI_INLAND_STATION.name,
            "coordinates": [MAITRI_INLAND_STATION.latitude, MAITRI_INLAND_STATION.longitude],
            "navigable": False,
            "scar_add_mask": "LAND / ICE_SHELF",
            "rationale": "Maitri is situated ~100 km inland in the Schirmacher Oasis (-70.76°S). Vessels attempting to route directly to this point violate SCAR ADD constraints.",
        },
    }

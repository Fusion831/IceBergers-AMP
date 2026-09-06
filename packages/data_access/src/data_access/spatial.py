"""Geospatial utilities, distance calculations, and coordinate transforms."""
import math
from typing import Tuple, List
from domain.coordinates import GeoPoint, BoundingBox

EARTH_RADIUS_KM = 6371.0
KM_TO_NM = 0.539957


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in Nautical Miles."""
    return haversine_distance_km(lat1, lon1, lat2, lon2) * KM_TO_NM


def interpolate_great_circle_path(
    origin: GeoPoint,
    destination: GeoPoint,
    n_points: int = 50,
) -> List[Tuple[float, float]]:
    """Generates intermediate (lat, lon) coordinates along a great-circle path."""
    lat1 = math.radians(origin.latitude)
    lon1 = math.radians(origin.longitude)
    lat2 = math.radians(destination.latitude)
    lon2 = math.radians(destination.longitude)

    d = 2.0 * math.asin(
        math.sqrt(
            math.sin((lat2 - lat1) / 2.0) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2.0) ** 2
        )
    )

    if d == 0:
        return [(origin.latitude, origin.longitude)]

    points = []
    for i in range(n_points):
        f = i / (n_points - 1)
        a = math.sin((1.0 - f) * d) / math.sin(d)
        b = math.sin(f * d) / math.sin(d)

        x = a * math.cos(lat1) * math.cos(lon1) + b * math.cos(lat2) * math.cos(lon2)
        y = a * math.cos(lat1) * math.sin(lon1) + b * math.cos(lat2) * math.sin(lon2)
        z = a * math.sin(lat1) + b * math.sin(lat2)

        lat = math.atan2(z, math.sqrt(x**2 + y**2))
        lon = math.atan2(y, x)

        points.append((math.degrees(lat), math.degrees(lon)))

    return points


def is_point_in_bbox(point: GeoPoint, bbox: BoundingBox) -> bool:
    """Checks whether a point falls within a geographic bounding box."""
    return (
        bbox.min_latitude <= point.latitude <= bbox.max_latitude
        and bbox.min_longitude <= point.longitude <= bbox.max_longitude
    )

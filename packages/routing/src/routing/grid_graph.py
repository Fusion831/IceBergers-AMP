"""
AMIP Environmental Grid Graph.
Constructs a discrete 2D spatial mesh of environmental cells with structured cell IDs,
geographic/bathymetric constraint pruning, and geodesic 8-connectivity.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from domain.coordinates import GeoPoint, BoundingBox
from domain.vessel import VesselProfile
from domain.mission import AvoidanceZone, MissionTarget
from domain.environment import EnvironmentCell
from data_access.spatial import haversine_distance_nm
from data_access.environment_provider import default_environment_provider, EnvironmentalDataProviderInterface


class EnvironmentalGridNode:
    """A discrete node in the computational environmental graph."""

    def __init__(
        self,
        cell_id: str,
        row: int,
        col: int,
        point: GeoPoint,
        resolution_deg: float,
        is_land: bool = False,
        is_ice_shelf: bool = False,
        depth_m: float = 3500.0,
        alias: Optional[str] = None,
    ):
        self.cell_id = cell_id
        self.h3_index = cell_id
        self.row = row
        self.col = col
        self.point = point
        self.resolution_deg = resolution_deg
        self.is_land = is_land
        self.is_ice_shelf = is_ice_shelf
        self.depth_m = depth_m
        self.alias = alias
        self.is_navigable: bool = True
        self.exclusion_reason: Optional[str] = None


class EnvironmentalGridGraph:
    """
    Discrete spatial mesh graph for Antarctic / Southern Ocean routing.
    Discretizes the relevant bounding domain into structured cells with
    8-directional geodesic connectivity and explicit physical constraint pruning.
    """

    def __init__(
        self,
        bounds: BoundingBox,
        resolution_deg: float = 1.0,
        env_provider: Optional[EnvironmentalDataProviderInterface] = None,
        aliases: Optional[Dict[str, Tuple[float, float]]] = None,
        query_time: Optional[datetime] = None,
    ):
        self.bounds = bounds
        self.resolution_deg = resolution_deg
        self.env = env_provider or default_environment_provider
        self.res_code = int(round(resolution_deg * 100))
        # query_time is used only for static properties (bathymetry, land mask)
        # that do not change over the operational window in mock mode.
        self.query_time = query_time or datetime(2026, 1, 15, 0, 0)

        # Calculate rows and columns
        self.lat_min = bounds.min_latitude
        self.lat_max = bounds.max_latitude
        self.lon_min = bounds.min_longitude
        self.lon_max = bounds.max_longitude

        self.num_rows = int(math.ceil((self.lat_max - self.lat_min) / self.resolution_deg)) + 1
        self.num_cols = int(math.ceil((self.lon_max - self.lon_min) / self.resolution_deg)) + 1

        self.nodes: Dict[str, EnvironmentalGridNode] = {}
        self.coord_to_id: Dict[Tuple[int, int], str] = {}
        self.aliases: Dict[str, str] = {}  # alias_name -> cell_id

        self._build_nodes(aliases)

    def _make_cell_id(self, row: int, col: int) -> str:
        """Structured cell identifier: grid_{res}_r{row}_c{col}."""
        return f"grid_{self.res_code:03d}_r{row}_c{col}"

    def _build_nodes(self, aliases: Optional[Dict[str, Tuple[float, float]]] = None) -> None:
        """Instantiate grid nodes. Bathymetry/land-mask are queried at self.query_time
        (static in mock mode — these fields do not vary with forecast time)."""

        for r in range(self.num_rows):
            lat = round(self.lat_min + r * self.resolution_deg, 4)
            for c in range(self.num_cols):
                lon = round(self.lon_min + c * self.resolution_deg, 4)
                cell_id = self._make_cell_id(r, c)
                pt = GeoPoint(latitude=lat, longitude=lon)

                # Query static bathymetry & land mask
                env_pt = self.env.get_point_environment(pt, self.query_time)
                depth = env_pt["bathymetry_depth_m"]
                is_land = env_pt["is_land"] == 1.0 or depth <= 0.0 or lat < -78.0
                is_ice_shelf = lat < -72.0 and depth < 200.0

                node = EnvironmentalGridNode(
                    cell_id=cell_id,
                    row=r,
                    col=c,
                    point=pt,
                    resolution_deg=self.resolution_deg,
                    is_land=is_land,
                    is_ice_shelf=is_ice_shelf,
                    depth_m=depth,
                )
                self.nodes[cell_id] = node
                self.coord_to_id[(r, c)] = cell_id

        # Bind aliases if provided (e.g. S17, Bharati)
        if aliases:
            for alias_name, (a_lat, a_lon) in aliases.items():
                target_pt = GeoPoint(latitude=a_lat, longitude=a_lon)
                closest_id = self.find_closest_node_id(target_pt)
                if closest_id in self.nodes:
                    self.nodes[closest_id].alias = alias_name
                    self.aliases[alias_name] = closest_id

    def apply_hard_constraints(
        self,
        vessel: VesselProfile,
        avoidance_zones: Optional[List[AvoidanceZone]] = None,
    ) -> None:
        """
        Evaluate and prune unnavigable nodes based strictly on hard barriers:
        1. Continental land and permanent ice shelves.
        2. Bathymetric grounding: depth < vessel.draft_m + 5.0m under-keel clearance.
        3. Active user avoidance zones.
        """
        draft_limit = vessel.draft_m + 5.0  # 5m under-keel safety margin

        for node in self.nodes.values():
            # 1. Land / Ice Shelf Mask
            if node.is_land:
                node.is_navigable = False
                node.exclusion_reason = "LAND_MASK"
                continue
            if node.is_ice_shelf:
                node.is_navigable = False
                node.exclusion_reason = "ICE_SHELF"
                continue

            # 2. Bathymetric Under-Keel Clearance
            if node.depth_m < draft_limit:
                node.is_navigable = False
                node.exclusion_reason = f"SHALLOW_DEPTH_{node.depth_m:.0f}m"
                continue

            # 3. User Avoidance Zones
            if avoidance_zones:
                in_zone = False
                for az in avoidance_zones:
                    if az.center:
                        dist_nm = haversine_distance_nm(
                            node.point.latitude, node.point.longitude,
                            az.center.latitude, az.center.longitude
                        )
                        radius_nm = (az.radius_km or 25.0) / 1.852
                        if dist_nm <= radius_nm:
                            in_zone = True
                            break
                    elif az.polygon and len(az.polygon) >= 3:
                        min_lat = min(p.latitude for p in az.polygon)
                        max_lat = max(p.latitude for p in az.polygon)
                        min_lon = min(p.longitude for p in az.polygon)
                        max_lon = max(p.longitude for p in az.polygon)
                        if min_lat <= node.point.latitude <= max_lat and min_lon <= node.point.longitude <= max_lon:
                            in_zone = True
                            break
                if in_zone:
                    node.is_navigable = False
                    node.exclusion_reason = "AVOIDANCE_ZONE"
                    continue

            # Passed all hard constraints
            node.is_navigable = True
            node.exclusion_reason = None

    def get_neighbors(self, cell_id: str) -> List[Tuple[str, float, float]]:
        """
        Return navigable 8-directional neighbor transitions.
        Returns list of (neighbor_cell_id, geodesic_distance_nm, heading_deg).
        Properly handles meridian convergence via Haversine distance and spherical heading.
        """
        node = self.nodes.get(cell_id)
        if not node or not node.is_navigable:
            return []

        neighbors: List[Tuple[str, float, float]] = []
        r, c = node.row, node.col

        # 8-directional offsets: N, NE, E, SE, S, SW, W, NW
        offsets = [
            (1, 0), (1, 1), (0, 1), (-1, 1),
            (-1, 0), (-1, -1), (0, -1), (1, -1)
        ]

        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            neighbor_id = self.coord_to_id.get((nr, nc))
            if not neighbor_id:
                continue

            neighbor_node = self.nodes[neighbor_id]
            if not neighbor_node.is_navigable:
                continue

            # Calculate exact geodesic Haversine distance
            dist_nm = haversine_distance_nm(
                node.point.latitude, node.point.longitude,
                neighbor_node.point.latitude, neighbor_node.point.longitude
            )
            if dist_nm <= 0.0:
                continue

            # Calculate geographic heading taking into account cosine latitude convergence
            d_lat = neighbor_node.point.latitude - node.point.latitude
            d_lon = neighbor_node.point.longitude - node.point.longitude
            mean_lat_rad = math.radians((node.point.latitude + neighbor_node.point.latitude) / 2.0)
            heading_deg = math.degrees(math.atan2(d_lon * math.cos(mean_lat_rad), d_lat)) % 360.0

            neighbors.append((neighbor_id, dist_nm, heading_deg))

        return neighbors

    def find_closest_node_id(self, point: GeoPoint, navigable_only: bool = False) -> str:
        """Find the closest grid node to a geographic point."""
        best_id = ""
        min_dist = float("inf")

        for cell_id, node in self.nodes.items():
            if navigable_only and not node.is_navigable:
                continue
            dist = haversine_distance_nm(
                point.latitude, point.longitude,
                node.point.latitude, node.point.longitude
            )
            if dist < min_dist:
                min_dist = dist
                best_id = cell_id

        return best_id

    def to_environment_cell(self, cell_id: str, valid_time: datetime) -> EnvironmentCell:
        """Convert node to full EnvironmentCell schema at a specific valid_time."""
        node = self.nodes[cell_id]
        env_pt = self.env.get_point_environment(node.point, valid_time)

        sic = env_pt["sea_ice_concentration"]
        wave = env_pt["wave_height_m"]
        curr_u = env_pt["current_u_ms"]
        curr_v = env_pt["current_v_ms"]
        wind_u = env_pt["wind_u10"] if "wind_u10" in env_pt else 0.0
        wind_v = env_pt["wind_v10"] if "wind_v10" in env_pt else 0.0
        wind_spd = env_pt["wind_speed_ms"]

        # Local composite risk
        in_berg_belt = (-65.0 < node.point.latitude < -50.0) and (node.point.longitude < 54.0)
        berg_hazard = 0.30 if in_berg_belt else 0.04
        risk = min(0.95, 0.40 * sic + 0.20 * (wave / 6.0) + berg_hazard)

        sic_unc = float(env_pt.get("sea_ice_uncertainty", 0.08))

        return EnvironmentCell(
            cell_id=node.cell_id,
            alias=node.alias,
            point=node.point,
            row=node.row,
            col=node.col,
            resolution_deg=node.resolution_deg,
            timestamp=valid_time,
            sea_ice_concentration=sic,
            sea_ice_uncertainty=sic_unc,
            current_u_ms=curr_u,
            current_v_ms=curr_v,
            wind_u_ms=wind_u,
            wind_v_ms=wind_v,
            wind_speed_ms=wind_spd,
            wave_height_m=wave,
            wave_period_s=8.0,
            bathymetry_depth_m=node.depth_m,
            iceberg_hazard=berg_hazard,
            composite_risk=round(risk, 3),
            is_land=node.is_land,
            is_ice_shelf=node.is_ice_shelf,
            is_navigable=node.is_navigable,
            provenance="MOCK / SYNTHETIC",
        )


class H3EnvironmentalGridGraph:
    """
    Canonical H3 Environmental Grid Graph for Antarctic & Southern Ocean navigation.
    Operates over discrete hexagonal H3 cells with topological neighborhood expansion,
    authoritative SCAR ADD geographic boundaries, and GEBCO bathymetric pruning.
    """

    def __init__(
        self,
        bounds: Optional[BoundingBox] = None,
        h3_resolution: int = 5,
        env_provider: Optional[EnvironmentalDataProviderInterface] = None,
        lookup_service: Optional[Any] = None,
        aliases: Optional[Dict[str, Tuple[float, float]]] = None,
        query_time: Optional[datetime] = None,
    ):
        import h3
        self.h3 = h3
        self.bounds = bounds
        self.h3_resolution = h3_resolution
        self.env = env_provider or default_environment_provider
        self.query_time = query_time or datetime(2026, 1, 15, 0, 0)

        if lookup_service is None:
            from data_ingestion.h3.lookup import H3CellLookupService
            self.lookup = H3CellLookupService()
        else:
            self.lookup = lookup_service

        from data_ingestion.h3.geometry import H3GeometryEngine
        self.geom = H3GeometryEngine()

        self.approx_edge_km = self.geom.get_approx_cell_edge_km(h3_resolution)
        self.approx_deg = self.approx_edge_km / 111.0

        self.nodes: Dict[str, EnvironmentalGridNode] = {}
        self.aliases: Dict[str, str] = {}
        self.vessel: Optional[VesselProfile] = None
        self.avoidance_zones: Optional[List[AvoidanceZone]] = None

        if aliases:
            for alias_name, (a_lat, a_lon) in aliases.items():
                pt = GeoPoint(latitude=a_lat, longitude=a_lon)
                c_id = self.find_closest_node_id(pt)
                self.aliases[alias_name] = c_id
                if c_id in self.nodes:
                    self.nodes[c_id].alias = alias_name

    def _get_or_create_node(self, cell_id: str) -> EnvironmentalGridNode:
        """Retrieves or creates an H3 grid node on the fly."""
        if cell_id in self.nodes:
            return self.nodes[cell_id]

        lat, lon = self.geom.cell_to_latlng(cell_id)
        pt = GeoPoint(latitude=round(lat, 4), longitude=round(lon, 4))

        # 1. Query static lookup
        static_cell = self.lookup.get_cell(cell_id)
        if static_cell:
            depth = float(static_cell.bathymetry_mean_m) if static_cell.bathymetry_mean_m is not None else 3500.0
            is_land = bool(static_cell.is_blocked) or (static_cell.land_fraction > 0.5)
            is_ice_shelf = float(static_cell.ice_shelf_fraction) > 0.5
        else:
            # Fallback to environmental provider for coordinates outside static partition
            env_pt = self.env.get_point_environment(pt, self.query_time)
            depth = float(env_pt.get("bathymetry_depth_m", 3500.0))
            is_land = env_pt.get("is_land", 0.0) == 1.0 or depth <= 0.0 or lat < -78.0
            is_ice_shelf = lat < -72.0 and depth < 200.0

        node = EnvironmentalGridNode(
            cell_id=cell_id,
            row=0,
            col=0,
            point=pt,
            resolution_deg=self.approx_deg,
            is_land=is_land,
            is_ice_shelf=is_ice_shelf,
            depth_m=depth,
        )

        # Apply constraint check if active
        if self.vessel:
            draft_limit = self.vessel.draft_m + 3.0  # minimum UKC safety margin
            if node.is_land:
                node.is_navigable = False
                node.exclusion_reason = "LAND_MASK"
            elif node.is_ice_shelf:
                node.is_navigable = False
                node.exclusion_reason = "ICE_SHELF"
            elif node.depth_m < draft_limit:
                node.is_navigable = False
                node.exclusion_reason = f"SHALLOW_DEPTH_{node.depth_m:.0f}m"
            elif self.avoidance_zones:
                in_zone = False
                for az in self.avoidance_zones:
                    if az.center:
                        d_nm = haversine_distance_nm(pt.latitude, pt.longitude, az.center.latitude, az.center.longitude)
                        if d_nm <= ((az.radius_km or 25.0) / 1.852):
                            in_zone = True
                            break
                    elif az.polygon and len(az.polygon) >= 3:
                        min_lat = min(p.latitude for p in az.polygon)
                        max_lat = max(p.latitude for p in az.polygon)
                        min_lon = min(p.longitude for p in az.polygon)
                        max_lon = max(p.longitude for p in az.polygon)
                        if min_lat <= pt.latitude <= max_lat and min_lon <= pt.longitude <= max_lon:
                            in_zone = True
                            break
                if in_zone:
                    node.is_navigable = False
                    node.exclusion_reason = "AVOIDANCE_ZONE"

        self.nodes[cell_id] = node
        return node

    def apply_hard_constraints(
        self,
        vessel: VesselProfile,
        avoidance_zones: Optional[List[AvoidanceZone]] = None,
    ) -> None:
        """Stores vessel and avoidance zones to prune unnavigable H3 nodes."""
        self.vessel = vessel
        self.avoidance_zones = avoidance_zones
        draft_limit = vessel.draft_m + 3.0

        for node in list(self.nodes.values()):
            if node.is_land:
                node.is_navigable = False
                node.exclusion_reason = "LAND_MASK"
            elif node.is_ice_shelf:
                node.is_navigable = False
                node.exclusion_reason = "ICE_SHELF"
            elif node.depth_m < draft_limit:
                node.is_navigable = False
                node.exclusion_reason = f"SHALLOW_DEPTH_{node.depth_m:.0f}m"
            elif avoidance_zones:
                in_zone = False
                for az in avoidance_zones:
                    if az.center:
                        d_nm = haversine_distance_nm(node.point.latitude, node.point.longitude, az.center.latitude, az.center.longitude)
                        if d_nm <= ((az.radius_km or 25.0) / 1.852):
                            in_zone = True
                            break
                if in_zone:
                    node.is_navigable = False
                    node.exclusion_reason = "AVOIDANCE_ZONE"
            else:
                node.is_navigable = True
                node.exclusion_reason = None

    def find_closest_node_id(self, point: GeoPoint, navigable_only: bool = False) -> str:
        """Finds the closest canonical H3 cell index to a geographic coordinate."""
        start_id = self.geom.latlng_to_cell(point.latitude, point.longitude, self.h3_resolution)
        node = self._get_or_create_node(start_id)

        if not navigable_only or node.is_navigable:
            return start_id

        # Search outward through concentric H3 disks to find nearest navigable water cell
        for k in range(1, 15):
            disk = self.geom.neighboring_cells(start_id, k=k)
            for c_id in disk:
                cand = self._get_or_create_node(c_id)
                if cand.is_navigable:
                    return c_id

        return start_id

    def get_neighbors(self, cell_id: str) -> List[Tuple[str, float, float]]:
        """
        Returns topological H3 hexagonal neighbor transitions.
        Returns list of (neighbor_cell_id, geodesic_distance_nm, heading_deg).
        """
        node = self._get_or_create_node(cell_id)
        if not node.is_navigable:
            return []

        neighbors: List[Tuple[str, float, float]] = []
        disk = self.h3.grid_disk(cell_id, 1)

        for nbr_id in disk:
            if nbr_id == cell_id:
                continue

            nbr_node = self._get_or_create_node(nbr_id)
            if not nbr_node.is_navigable:
                continue

            # Great-circle distance
            dist_nm = haversine_distance_nm(
                node.point.latitude, node.point.longitude,
                nbr_node.point.latitude, nbr_node.point.longitude,
            )
            if dist_nm <= 0.0:
                continue

            # Forward azimuth heading
            d_lat = nbr_node.point.latitude - node.point.latitude
            d_lon = nbr_node.point.longitude - node.point.longitude
            mean_lat_rad = math.radians((node.point.latitude + nbr_node.point.latitude) / 2.0)
            heading_deg = (math.degrees(math.atan2(d_lon * math.cos(mean_lat_rad), d_lat)) + 360.0) % 360.0

            neighbors.append((nbr_id, dist_nm, heading_deg))

        return neighbors

    def to_environment_cell(self, cell_id: str, valid_time: datetime) -> EnvironmentCell:
        """Converts an H3 node into an EnvironmentCell."""
        node = self._get_or_create_node(cell_id)
        env_pt = self.env.get_point_environment(node.point, valid_time)

        sic = env_pt.get("sea_ice_concentration", 0.0)
        wave = env_pt.get("wave_height_m", 2.0)
        curr_u = env_pt.get("current_u_ms", 0.0)
        curr_v = env_pt.get("current_v_ms", 0.0)
        wind_spd = env_pt.get("wind_speed_ms", 10.0)

        in_berg_belt = (-65.0 < node.point.latitude < -50.0) and (node.point.longitude < 54.0)
        berg_hazard = 0.30 if in_berg_belt else 0.04
        risk = min(0.95, 0.40 * sic + 0.20 * (wave / 6.0) + berg_hazard)

        sic_unc = float(env_pt.get("sea_ice_uncertainty", 0.08))

        return EnvironmentCell(
            cell_id=node.cell_id,
            alias=node.alias,
            point=node.point,
            row=node.row,
            col=node.col,
            resolution_deg=node.resolution_deg,
            timestamp=valid_time,
            sea_ice_concentration=sic,
            sea_ice_uncertainty=sic_unc,
            current_u_ms=curr_u,
            current_v_ms=curr_v,
            wind_u_ms=0.0,
            wind_v_ms=0.0,
            wind_speed_ms=wind_spd,
            wave_height_m=wave,
            wave_period_s=8.0,
            bathymetry_depth_m=node.depth_m,
            iceberg_hazard=berg_hazard,
            composite_risk=round(risk, 3),
            is_land=node.is_land,
            is_ice_shelf=node.is_ice_shelf,
            is_navigable=node.is_navigable,
            provenance="H3_CANONICAL / UNIFIED",
        )


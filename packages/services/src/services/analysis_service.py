"""Analysis Service evaluating Antarctic station accessibility windows and mission feasibility."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from domain.coordinates import GeoPoint
from domain.analysis import (
    StationAccessibilityPoint,
    StationAccessibilityWindow,
    MissionAnalysisResult,
)
from domain.mission import Mission
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from services.risk_service import RiskService
from services.sea_ice_service import SeaIceService

logger = logging.getLogger(__name__)

# Key Antarctic research stations
ANTARCTIC_STATIONS = {
    "Bharati": GeoPoint(latitude=-69.4072, longitude=76.1911),
    "Maitri": GeoPoint(latitude=-70.7670, longitude=11.7330),
    "Syowa": GeoPoint(latitude=-69.0042, longitude=39.5817),
    "McMurdo": GeoPoint(latitude=-77.8463, longitude=166.6682),
    "Palmer": GeoPoint(latitude=-64.7742, longitude=-64.0531),
    "Rothera": GeoPoint(latitude=-67.5700, longitude=-68.1250),
    "Concordia": GeoPoint(latitude=-75.1000, longitude=123.3333),
    "Casey": GeoPoint(latitude=-66.2822, longitude=110.5286),
    "Davis": GeoPoint(latitude=-68.5764, longitude=77.9672),
    "Mawson": GeoPoint(latitude=-67.6047, longitude=62.8739),
}


class AnalysisService:
    """Evaluates station accessibility, ice barrier penetration, and mission feasibility windows."""

    def __init__(
        self,
        risk_service: Optional[RiskService] = None,
        sea_ice_service: Optional[SeaIceService] = None,
    ) -> None:
        self.risk_service = risk_service or RiskService()
        self.sea_ice_service = sea_ice_service or SeaIceService()

    def get_station_accessibility(
        self,
        station_name: str,
        reference_time: datetime,
        vessel: Optional[VesselProfile] = None,
        horizons: Optional[List[int]] = None,
    ) -> StationAccessibilityWindow:
        """Compute accessibility scores and ice barriers for a station across forecast horizons."""
        target_horizons = horizons or [0, 7, 14, 30, 60, 90]
        station_loc = ANTARCTIC_STATIONS.get(station_name)
        if not station_loc:
            # Fallback default near Larsemann Hills (Bharati)
            station_loc = ANTARCTIC_STATIONS["Bharati"]

        points: List[StationAccessibilityPoint] = []

        for h in target_horizons:
            target_time = reference_time + timedelta(days=h)
            # Evaluate point risk at the station approach corridor (0.5 deg north of station)
            approach_pt = GeoPoint(latitude=station_loc.latitude + 0.5, longitude=station_loc.longitude)
            risk_info = self.risk_service.evaluate_point_risk(
                point=approach_pt,
                valid_time=target_time,
                vessel=vessel,
            )

            sic = risk_info["sea_ice_concentration"]
            risk = risk_info["composite_risk"]
            is_accessible = not risk_info["hard_constraint_violated"] and sic < 0.85

            # Accessibility score (1.0 = completely open ocean, 0.0 = impenetrable fast ice)
            accessibility_score = max(0.0, min(1.0, 1.0 - (sic * 0.7 + risk * 0.3)))

            # Distance through ice pack to reach station
            ice_dist_nm = max(0.0, sic * 45.0)

            # Recommended operational speed
            rec_speed = max(3.0, 12.0 * (1.0 - sic * 0.6)) if is_accessible else 0.0

            points.append(
                StationAccessibilityPoint(
                    horizon_days=h,
                    valid_time=target_time,
                    is_accessible=is_accessible,
                    accessibility_score=round(accessibility_score, 3),
                    expected_sic=round(sic, 3),
                    ice_barrier_thickness_nm=round(ice_dist_nm, 1),
                    recommended_entry_speed_knots=round(rec_speed, 1),
                )
            )

        # Identify optimal arrival window
        accessible_points = [p for p in points if p.is_accessible]
        if accessible_points:
            best_point = max(accessible_points, key=lambda p: p.accessibility_score)
            optimal_window = f"Day T+{best_point.horizon_days} ({best_point.valid_time.strftime('%Y-%m-%d')})"
        else:
            optimal_window = "No fully accessible window in current 90-day forecast horizon. Icebreaker escort required."

        return StationAccessibilityWindow(
            station_name=station_name,
            location=station_loc,
            reference_time=reference_time,
            accessibility_points=points,
            optimal_arrival_window=optimal_window,
        )

    def analyze_mission(
        self,
        mission: Mission,
        vessel: Optional[VesselProfile] = None,
    ) -> MissionAnalysisResult:
        """Run comprehensive feasibility and risk analysis for a mission."""
        v = vessel or VesselProfile()
        start_time = mission.planning_window.earliest_departure

        # Analyze accessibility for all mission destinations
        station_windows: List[StationAccessibilityWindow] = []
        for dest in mission.destinations:
            win = self.get_station_accessibility(
                station_name=dest.station_name,
                reference_time=start_time,
                vessel=v,
            )
            station_windows.append(win)

        # Overall accessibility score
        all_scores = [p.accessibility_score for w in station_windows for p in w.accessibility_points]
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0.8

        is_feasible = overall_score >= 0.35

        recommendations = [
            f"Mission {mission.name} evaluated across planning window {mission.planning_window.earliest_departure.date()} to {mission.planning_window.latest_departure.date()}.",
            "Maintain continuous radar watch in sub-Antarctic waters between 55°S and 65°S for iceberg fragmentation.",
            "Recommended departure timing aligns with opening polynyas near Larsemann Hills / Prydz Bay.",
        ]
        if not is_feasible:
            recommendations.append("CAUTION: Heavy multi-year ice projected near coastal approach. Ensure ice escort standby.")

        return MissionAnalysisResult(
            mission_id=mission.id,
            analyzed_at=datetime.now(timezone.utc),
            is_feasible=is_feasible,
            overall_accessibility_score=round(overall_score, 3),
            station_windows=station_windows,
            operational_recommendations=recommendations,
        )

"""Main Risk Engine Implementation for AMIP POC."""
from datetime import datetime
from typing import Optional, Tuple, Any
import numpy as np
from domain.coordinates import BoundingBox, GridSpec, GeoPoint
from domain.risk import RiskField, RiskWeightsConfig, RiskFactorAttribution
from domain.vessel import VesselProfile
from risk_engine.interface import RiskEngineInterface
from risk_engine.constraints import evaluate_hard_constraints
from risk_engine.soft_costs import compute_soft_risk_factors, combine_risk_field
from data_access.zarr_reader import default_zarr_reader


class RiskEngine(RiskEngineInterface):
    """
    Deterministic Environmental Risk Engine.
    Fuses sea ice, iceberg hazard, wind, waves, currents, and bathymetry into R(x, y, t).
    """

    def compute_risk_field(
        self,
        valid_time: datetime,
        lead_time_days: int,
        vessel: VesselProfile,
        weights: Optional[RiskWeightsConfig] = None,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[RiskField, np.ndarray, np.ndarray]:
        weights = weights or RiskWeightsConfig()

        if bbox is None:
            bbox = BoundingBox(
                min_latitude=-80.0,
                min_longitude=-20.0,
                max_latitude=-30.0,
                max_longitude=100.0,
            )

        # 1. Fetch physical layers from Zarr reader
        _, _, sic_grid = default_zarr_reader.get_grid_slice("sea_ice_concentration", valid_time, bbox, grid_spec)
        _, _, unc_grid = default_zarr_reader.get_grid_slice("sic_uncertainty", valid_time, bbox, grid_spec)
        _, _, depth_grid = default_zarr_reader.get_grid_slice("bathymetry", valid_time, bbox, grid_spec)
        _, _, wind_u = default_zarr_reader.get_grid_slice("wind_u", valid_time, bbox, grid_spec)
        _, _, wind_v = default_zarr_reader.get_grid_slice("wind_v", valid_time, bbox, grid_spec)
        _, _, current_u = default_zarr_reader.get_grid_slice("ocean_u", valid_time, bbox, grid_spec)
        _, _, current_v = default_zarr_reader.get_grid_slice("ocean_v", valid_time, bbox, grid_spec)
        _, _, wave_hs = default_zarr_reader.get_grid_slice("significant_wave_height", valid_time, bbox, grid_spec)

        # 2. Mock iceberg hazard surface (derived from active positions)
        iceberg_hazard_grid = np.zeros_like(sic_grid)
        # Synthetic iceberg corridor near 62S to 65S, 20E to 80E
        lat_grid, lon_grid = np.meshgrid(
            np.linspace(bbox.min_latitude, bbox.max_latitude, sic_grid.shape[0]),
            np.linspace(bbox.min_longitude, bbox.max_longitude, sic_grid.shape[1]),
            indexing="ij",
        )
        berg_center_lat = -63.5 + (0.02 * lead_time_days)
        berg_center_lon = 45.0 + (0.25 * lead_time_days)
        d_berg = ((lat_grid - berg_center_lat) ** 2) + (((lon_grid - berg_center_lon) * 0.5) ** 2)
        iceberg_hazard_grid = np.clip(0.85 * np.exp(-d_berg / 8.0), 0.0, 1.0)

        # 3. Evaluate Hard Constraints (Inaccessible Cells)
        impassable_mask = evaluate_hard_constraints(
            depth_grid=depth_grid,
            sic_grid=sic_grid,
            iceberg_hazard_grid=iceberg_hazard_grid,
            vessel=vessel,
            min_depth_margin_m=vessel.under_keel_margin_m,
            max_navigable_sic=vessel.max_navigable_sic,
        )

        # 4. Evaluate Soft Costs
        r_ice, r_berg, r_wind, r_wave, c_current = compute_soft_risk_factors(
            sic_grid=sic_grid,
            sic_unc_grid=unc_grid,
            iceberg_hazard_grid=iceberg_hazard_grid,
            wind_u=wind_u,
            wind_v=wind_v,
            current_u=current_u,
            current_v=current_v,
            wave_hs=wave_hs,
            max_navigable_sic=vessel.max_navigable_sic,
        )

        composite_risk = combine_risk_field(
            r_ice=r_ice,
            r_berg=r_berg,
            r_wind=r_wind,
            r_wave=r_wave,
            c_current=c_current,
            r_unc=unc_grid,
            weights=weights,
        )

        # Impassable cells take maximum risk penalty
        composite_risk[impassable_mask] = 1.0

        mean_r = float(np.mean(composite_risk))
        max_r = float(np.max(composite_risk))
        p90_r = float(np.percentile(composite_risk, 90))
        p95_r = float(np.percentile(composite_risk, 95))
        impassable_count = int(np.sum(impassable_mask))
        impassable_area = float(impassable_count * 100.0)

        risk_field = RiskField(
            valid_time=valid_time,
            lead_time_days=lead_time_days,
            bounds=bbox,
            bbox=bbox,
            grid_shape=list(composite_risk.shape),
            mean_risk=round(mean_r, 4),
            max_risk=round(max_r, 4),
            p90_risk=round(p90_r, 4),
            p95_risk=round(p95_r, 4),
            impassable_cells_count=impassable_count,
            impassable_area_sqkm=round(impassable_area, 1),
            data_ref=f"data/processed/risk/{valid_time.strftime('%Y%m%d')}",
            values=composite_risk.tolist(),
            hard_constraint_mask=impassable_mask.tolist(),
        )

        return risk_field, composite_risk, impassable_mask

    def evaluate_grid(
        self,
        valid_time: datetime,
        env_slice: Any = None,
        sea_ice_forecast: Any = None,
        iceberg_hazard: Any = None,
        vessel: Optional[VesselProfile] = None,
        weights: Optional[RiskWeightsConfig] = None,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
        horizon_days: int = 14,
    ) -> RiskField:
        v = vessel or VesselProfile()
        target_bbox = bbox or (getattr(env_slice, "bounds", None) if env_slice else None)
        target_grid = grid_spec
        if target_grid is None and env_slice and hasattr(env_slice, "grid_shape") and env_slice.grid_shape:
            target_grid = GridSpec(
                bounds=target_bbox,
                n_lat=env_slice.grid_shape[0],
                n_lon=env_slice.grid_shape[1],
            )
        field, _, _ = self.compute_risk_field(
            valid_time=valid_time,
            lead_time_days=horizon_days,
            vessel=v,
            weights=weights,
            bbox=target_bbox,
            grid_spec=target_grid,
        )
        return field

    def evaluate_point(
        self,
        point: GeoPoint,
        valid_time: datetime,
        point_env: Any = None,
        sea_ice_forecast: Any = None,
        iceberg_hazard: Any = None,
        vessel: Optional[VesselProfile] = None,
        weights: Optional[RiskWeightsConfig] = None,
    ) -> RiskFactorAttribution:
        v = vessel or VesselProfile()
        attrib = self.evaluate_point_risk(point=point, timestamp=valid_time, vessel=v, weights=weights)
        if point_env:
            attrib.sea_ice_concentration = getattr(point_env, "sea_ice_concentration", attrib.sea_ice_risk)
        attrib.composite_risk = max(attrib.sea_ice_risk, attrib.iceberg_risk, attrib.wave_risk)
        return attrib

    def evaluate_point_risk(
        self,
        point: GeoPoint,
        timestamp: datetime,
        vessel: VesselProfile,
        weights: Optional[RiskWeightsConfig] = None,
    ) -> RiskFactorAttribution:
        weights = weights or RiskWeightsConfig()

        lat = point.latitude
        lon = point.longitude

        is_hard = False
        dominant = "FAVORABLE_OPEN_WATER"

        if lat < -71.0:
            is_hard = True
            dominant = "GROUNDED_ICE_SHELF"
            explanation = "Point intersects grounded Antarctic ice shelf."
            return RiskFactorAttribution(
                sea_ice_risk=1.0,
                iceberg_risk=0.1,
                weather_risk=0.2,
                wave_risk=0.0,
                current_penalty=0.0,
                is_hard_constrained=True,
                dominant_hazard=dominant,
                explanation=explanation,
            )

        # Sea-ice component
        ice_risk = max(0.0, min(1.0, (-62.0 - lat) / 8.0))
        if ice_risk > vessel.max_navigable_sic:
            is_hard = True
            dominant = "MAXIMUM_SEA_ICE_EXCEEDED"

        # Iceberg component
        d_berg = ((lat + 63.5) ** 2) + (((lon - 45.0) * 0.5) ** 2)
        berg_risk = float(np.clip(0.85 * np.exp(-d_berg / 8.0), 0.0, 1.0))

        # Weather / waves
        storm_risk = 0.45 if -55.0 <= lat <= -45.0 else 0.15
        wave_risk = 0.40 if -55.0 <= lat <= -48.0 else 0.10

        if is_hard:
            explanation = f"Hard constraint violation: {dominant}."
        elif ice_risk > 0.40:
            dominant = "SEA_ICE_CONCENTRATION"
            explanation = f"Elevated hazard from {round(ice_risk * 100)}% sea-ice concentration near approach."
        elif berg_risk > 0.30:
            dominant = "ICEBERG_COLLISION_HAZARD"
            explanation = "Elevated risk due to proximity to active iceberg drift corridor."
        elif storm_risk > 0.35:
            dominant = "ROUGH_SEAS_AND_WIND"
            explanation = "Significant wave height and gale-force westerly winds in the Southern Ocean belt."
        else:
            explanation = "Conditions within normal operating envelope."

        return RiskFactorAttribution(
            sea_ice_risk=round(ice_risk, 3),
            iceberg_risk=round(berg_risk, 3),
            weather_risk=round(storm_risk, 3),
            wave_risk=round(wave_risk, 3),
            current_penalty=0.05,
            is_hard_constrained=is_hard,
            dominant_hazard=dominant,
            explanation=explanation,
        )


default_risk_engine = RiskEngine()

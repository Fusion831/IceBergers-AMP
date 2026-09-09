import React, { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import {
  Compass,
  Play,
  Pause,
  Calendar,
  Eye,
  EyeOff,
  X,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { useMission } from '../context/MissionContext';
import antarcticaFullH3GridData from '../data/antarctica_full_h3_grid.json';
import displayAggregateGeojsonData from '../data/display_aggregate_h3.json';

interface AntarcticMapProps {
  selectedHorizon: string;
  activeLayer?: 'sic' | 'icebergs' | 'risk' | 'weather';
  selectedRoute: string;
  onHorizonChange?: (hz: string) => void;
  onInspectPoint?: (coords: [number, number]) => void;
  onSelectRoute?: (routeId: string) => void;
  showH3Grid?: boolean;
  showIcebergs?: boolean;
  showTrajectories?: boolean;
  basemapStyle?: 'google-earth' | 'google-terrain' | 'osm';
  onHoverCell?: (data: any | null) => void;
}

// Stable route colors
const STABLE_ROUTE_COLORS: Record<string, string> = {
  fastest: '#3b82f6',
  shortest: '#f59e0b',
  safest: '#22c55e',
  fuel_efficient: '#a855f7',
  balanced: '#14b8a6'
};

const HORIZON_DAYS_MAP: Record<string, number> = {
  'Now': 0,
  '+1d': 1,
  '+3d': 3,
  '+7d': 7,
  '+14d': 14,
  '+30d': 30,
  '+60d': 60,
  '+90d': 90
};

const DAY_TO_NEAREST_HORIZON = (day: number): string => {
  if (day < 0.5) return 'Now';
  if (day < 2) return '+1d';
  if (day < 5) return '+3d';
  if (day < 10.5) return '+7d';
  if (day < 22) return '+14d';
  if (day < 45) return '+30d';
  if (day < 75) return '+60d';
  return '+90d';
};

const roundVal = (v: any, d: number) => (typeof v === 'number' && !isNaN(v) ? +(v.toFixed(d)) : v);

export const AntarcticMap: React.FC<AntarcticMapProps> = ({
  selectedHorizon,
  selectedRoute: propSelectedRoute,
  onHorizonChange,
  onInspectPoint,
  onSelectRoute,
  showH3Grid: propShowH3Grid,
  showIcebergs: propShowIcebergs = true,
  showTrajectories: propShowTrajectories,
  basemapStyle: propBasemapStyle,
  onHoverCell
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const hoveredPopupRef = useRef<maplibregl.Popup | null>(null);

  const {
    routes,
    selectedRouteId,
    setSelectedRouteId,
    selectedRoute,
    setTimeHorizon,
    corridorGeojson,
    getCellEnvironment,
    getCellRisk,
    icebergsList,
    showTrajectories: contextShowTrajectories,
    showH3Grid: contextShowH3Grid,
    selectedH3Cell,
    setSelectedH3Cell,
    selectedSegment,
    setSelectedSegment,
    selectedIceberg,
    setSelectedIceberg,
    enabledRoutes,
    toggleRouteEnabled
  } = useMission();

  // Controlled or context fallback states
  const showH3Grid = propShowH3Grid !== undefined ? propShowH3Grid : contextShowH3Grid;
  const showIcebergs = propShowIcebergs !== undefined ? propShowIcebergs : true;
  const showTrajectories = propShowTrajectories !== undefined ? propShowTrajectories : contextShowTrajectories;
  const basemapStyle = propBasemapStyle || 'google-earth';

  // Timeline slider state: T+0 to T+90 days
  const [sliderDay, setSliderDay] = useState<number>(0);
  const [isTimelinePlaying, setIsTimelinePlaying] = useState<boolean>(false);
  const [hoveredCellData, setHoveredCellData] = useState<any | null>(null);

  // Collapsible inspector accordion state
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    ocean: true,
    risk: true,
    geo: true
  });

  const toggleSection = (s: string) => {
    setExpandedSections((prev) => ({ ...prev, [s]: !prev[s] }));
  };

  const activeRouteId = propSelectedRoute || selectedRouteId || 'fastest';
  const currentHz = DAY_TO_NEAREST_HORIZON(sliderDay);

  const toggleRouteVisibility = (routeId: string, ev?: React.MouseEvent) => {
    if (ev) ev.stopPropagation();
    toggleRouteEnabled(routeId);
  };

  const prevPropHorizonRef = useRef<string>(selectedHorizon);

  // Sync external selectedHorizon changes into slider ONLY when selectedHorizon genuinely changes from outside
  useEffect(() => {
    if (selectedHorizon && selectedHorizon !== prevPropHorizonRef.current) {
      prevPropHorizonRef.current = selectedHorizon;
      if (HORIZON_DAYS_MAP[selectedHorizon] !== undefined && !isTimelinePlaying) {
        setSliderDay(HORIZON_DAYS_MAP[selectedHorizon]);
      }
    }
  }, [selectedHorizon, isTimelinePlaying]);

  // Handle Play/Pause timer (250ms per day step: 90 days in 22.5s)
  useEffect(() => {
    if (!isTimelinePlaying) return;
    const interval = setInterval(() => {
      setSliderDay((prev) => {
        const next = prev >= 90 ? 0 : prev + 1;
        const newHz = DAY_TO_NEAREST_HORIZON(next);
        prevPropHorizonRef.current = newHz;
        setTimeHorizon(newHz as any);
        if (onHorizonChange) onHorizonChange(newHz);
        return next;
      });
    }, 250);
    return () => clearInterval(interval);
  }, [isTimelinePlaying, setTimeHorizon, onHorizonChange]);

  const handleSliderChange = (day: number) => {
    setSliderDay(day);
    const newHz = DAY_TO_NEAREST_HORIZON(day);
    prevPropHorizonRef.current = newHz;
    setTimeHorizon(newHz as any);
    if (onHorizonChange) onHorizonChange(newHz);
  };

  const getTileUrl = (style: 'google-earth' | 'google-terrain' | 'osm') => {
    switch (style) {
      case 'osm':
        return 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
      case 'google-terrain':
        return 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}';
      case 'google-earth':
      default:
        return 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}';
    }
  };

  // Helper to unwrap polygon coordinates that cross the antimeridian (+180/-180)
  const sanitizeGeometry = (geom: any) => {
    if (!geom || geom.type !== 'Polygon' || !geom.coordinates) return geom;
    const newRings = geom.coordinates.map((ring: number[][]) => {
      if (!ring || ring.length === 0) return ring;
      let prevLon = ring[0][0];
      return ring.map(([lon, lat]: number[]) => {
        let adjLon = lon;
        if (adjLon - prevLon > 180) adjLon -= 360;
        else if (prevLon - adjLon > 180) adjLon += 360;
        prevLon = adjLon;
        return [adjLon, lat];
      });
    });
    return { ...geom, coordinates: newRings };
  };

  // 1. Authentic H3 Grid (RES-5 cells across circum-Antarctic and corridor)
  const authenticH3GeoJSON: GeoJSON.FeatureCollection = useMemo(() => {
    const rawGrid = (antarcticaFullH3GridData as any) || corridorGeojson;
    if (!rawGrid || !rawGrid.features) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = rawGrid.features.map((feat: any) => {
      const cellId = feat.id || feat.properties?.cell_id;
      const env = getCellEnvironment(cellId, currentHz) || {};
      const risk = getCellRisk(cellId, currentHz) || {};
      const base = feat.properties || {};

      const lat = env.lat ?? base.lat ?? (feat.geometry?.type === 'Polygon' ? feat.geometry.coordinates[0][0][1] : 0);
      const lon = env.lon ?? base.lon ?? (feat.geometry?.type === 'Polygon' ? feat.geometry.coordinates[0][0][0] : 0);
      const depth = env.depth ?? base.depth ?? 3400.0;
      const wave_height = env.wave_height ?? base.wave_height ?? 2.8;
      const wind_speed = env.wind_speed ?? base.wind_speed ?? 8.5;
      const current_magnitude = env.current_magnitude ?? base.current_magnitude ?? 0.18;
      const composite_risk = risk.composite_risk ?? base.composite_risk ?? 0.12;

      // Seasonal retreat factor for cell SIC
      const retreatFactor = sliderDay <= 60
        ? 1.0 - (sliderDay / 60) * 0.25
        : 0.75 + ((sliderDay - 60) / 30) * 0.10;
      const baseSic = env.sic ?? base.sic ?? 0.0;
      const dynamicSic = lat > -50.0 ? 0.0 : Math.max(0.0, Math.min(1.0, +(baseSic * retreatFactor).toFixed(4)));

      return {
        type: 'Feature',
        id: cellId,
        properties: {
          ...base,
          id: cellId,
          cell_id: cellId,
          lat: roundVal(lat, 4),
          lon: roundVal(lon, 4),
          wave_height: roundVal(wave_height, 2),
          wave_period: roundVal(env.wave_period ?? base.wave_period ?? 8.5, 1),
          wave_direction: roundVal(env.wave_direction ?? base.wave_direction ?? 270.0, 1),
          wind_speed: roundVal(wind_speed, 2),
          wind_direction: roundVal(env.wind_direction ?? base.wind_direction ?? 225.0, 1),
          current_magnitude: roundVal(current_magnitude, 3),
          current_direction: roundVal(env.current_direction ?? base.current_direction ?? 240.0, 1),
          depth: roundVal(depth, 1),
          draft: 5.6,
          under_keel_clearance: roundVal(env.under_keel_clearance ?? (depth - 5.6), 1),
          iceberg_hazard: roundVal(env.iceberg_hazard ?? base.iceberg_hazard ?? 0.0, 4),
          iceberg_count: env.iceberg_count ?? base.iceberg_count ?? 0,
          sic: dynamicSic,
          sic_pct: +(dynamicSic * 100).toFixed(1),
          composite_risk: roundVal(composite_risk, 3),
          sic_risk: roundVal(risk.sic_risk ?? base.sic_risk ?? 0.0, 3),
          iceberg_risk: roundVal(risk.iceberg_risk ?? base.iceberg_risk ?? 0.0, 3),
          wave_risk: roundVal(risk.wave_risk ?? base.wave_risk ?? 0.15, 3),
          wind_risk: roundVal(risk.wind_risk ?? base.wind_risk ?? 0.1, 3),
          hard_blocked: Boolean(risk.hard_blocked ?? base.hard_blocked ?? false)
        },
        geometry: sanitizeGeometry(feat.geometry)
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [corridorGeojson, currentHz, getCellEnvironment, getCellRisk, sliderDay]);

  // 2. Display-Aggregated SIC Layer (RES-4 parent polygons with exact 9-color gradient)
  const displayAggregateSICGeoJSON: GeoJSON.FeatureCollection = useMemo(() => {
    const rawData = (displayAggregateGeojsonData as any) || { type: 'FeatureCollection', features: [] };
    if (!rawData || !rawData.features) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const retreatFactor = sliderDay <= 60
      ? 1.0 - (sliderDay / 60) * 0.25
      : 0.75 + ((sliderDay - 60) / 30) * 0.10;

    const features = rawData.features.map((feat: any) => {
      const props = feat.properties || {};
      if (props.is_land) {
        return {
          ...feat,
          properties: {
            ...props,
            sic: null,
            sic_percent: null,
            is_land: true
          }
        };
      }

      const lat = props.centroid_lat ?? 0;
      let dynamicSic = 0.0;
      if (lat <= -50.0) {
        const baseSic = props.sic ?? 0.0;
        dynamicSic = Math.max(0.0, Math.min(1.0, +(baseSic * retreatFactor).toFixed(4)));
      }

      return {
        ...feat,
        properties: {
          ...props,
          sic: dynamicSic,
          sic_percent: +(dynamicSic * 100).toFixed(1),
          is_land: false
        }
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [sliderDay]);

  // 3. Iceberg Current Positions at Current Slider Day (linear waypoint interpolation)
  const currentIcebergsGeoJSON = useMemo(() => {
    if (!icebergsList || icebergsList.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = icebergsList.map((berg: any) => {
      let coords: [number, number] = [0, 0];
      let speed = 0;
      let depth = 0;
      let status = berg.status || 'ACTIVE_DRIFT';

      if (berg.trajectoryPoints && berg.trajectoryPoints.length > 0) {
        const floatIdx = (sliderDay / 90) * (berg.trajectoryPoints.length - 1);
        const idx0 = Math.floor(floatIdx);
        const idx1 = Math.min(idx0 + 1, berg.trajectoryPoints.length - 1);
        const frac = floatIdx - idx0;
        const p0 = berg.trajectoryPoints[idx0];
        const p1 = berg.trajectoryPoints[idx1];

        coords = [
          +(p0.lon + (p1.lon - p0.lon) * frac).toFixed(4),
          +(p0.lat + (p1.lat - p0.lat) * frac).toFixed(4)
        ];
        speed = p0.speed_mps ? +(p0.speed_mps * 1.94384).toFixed(2) : 0.24;
        depth = p0.bathymetry_depth_m ?? 3200;
        status = p0.status || status;
      } else if (berg.latestObservation) {
        coords = [berg.latestObservation.longitude, berg.latestObservation.latitude];
      }

      return {
        type: 'Feature',
        id: berg.id,
        properties: {
          id: berg.id,
          source: berg.source || 'USNIC / NIC Antarctic Dataset',
          speed_knots: speed,
          depth_m: depth,
          status,
          length_km: berg.latestObservation?.length_km ?? 15,
          width_km: berg.latestObservation?.width_km ?? 8,
          area_sqkm: berg.latestObservation?.area_sqkm ?? 120,
          isSelected: selectedIceberg?.id === berg.id
        },
        geometry: {
          type: 'Point',
          coordinates: coords
        }
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [icebergsList, sliderDay, selectedIceberg]);

  // 3b. Real-time live kinematic telemetry for the selected iceberg at current sliderDay
  const activeIcebergLive = useMemo(() => {
    if (!selectedIceberg) return null;
    const berg = icebergsList.find((b: any) => b.id === selectedIceberg.id) || selectedIceberg;
    let coords: [number, number] = [0, 0];
    let speed = 0.24;
    let depth = 3200;
    let status = berg.status || 'ACTIVE_DRIFT';
    let driftedNM = 0.0;

    if (berg.trajectoryPoints && berg.trajectoryPoints.length > 0) {
      const floatIdx = (sliderDay / 90) * (berg.trajectoryPoints.length - 1);
      const idx0 = Math.floor(floatIdx);
      const idx1 = Math.min(idx0 + 1, berg.trajectoryPoints.length - 1);
      const frac = floatIdx - idx0;
      const p0 = berg.trajectoryPoints[idx0];
      const p1 = berg.trajectoryPoints[idx1];

      coords = [
        +(p0.lon + (p1.lon - p0.lon) * frac).toFixed(4),
        +(p0.lat + (p1.lat - p0.lat) * frac).toFixed(4)
      ];
      speed = p0.speed_mps ? +(p0.speed_mps * 1.94384).toFixed(2) : 0.24;
      depth = p0.bathymetry_depth_m ?? 3200;
      status = p0.status || status;

      // Cumulative drift distance from Day 0 to current sliderDay
      const pStart = berg.trajectoryPoints[0];
      const dLat = (coords[1] - pStart.lat) * 60; // 1 deg lat = 60 NM
      const midLatRad = ((coords[1] + pStart.lat) / 2) * (Math.PI / 180);
      const dLon = (coords[0] - pStart.lon) * 60 * Math.cos(midLatRad);
      driftedNM = +Math.sqrt(dLat * dLat + dLon * dLon).toFixed(1);
    } else if (berg.latestObservation) {
      coords = [berg.latestObservation.longitude, berg.latestObservation.latitude];
    }

    return {
      ...berg,
      coords,
      speed,
      depth,
      status,
      driftedNM,
      day: sliderDay
    };
  }, [selectedIceberg, icebergsList, sliderDay]);

  // 4. Iceberg Trajectories (Precomputed 90-day drift lines)
  const icebergTrajectoriesGeoJSON = useMemo(() => {
    if (!icebergsList || icebergsList.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = icebergsList.map((berg: any) => {
      let coords = berg.trajectoryCoordinates || [];
      if (!coords || coords.length === 0) {
        if (berg.trajectoryPoints) {
          coords = berg.trajectoryPoints.map((p: any) => [p.lon, p.lat]);
        }
      }
      return {
        type: 'Feature',
        id: berg.id,
        properties: {
          id: berg.id,
          isSelected: selectedIceberg?.id === berg.id
        },
        geometry: {
          type: 'LineString',
          coordinates: coords
        }
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [icebergsList, selectedIceberg]);

  // 5. Canonical Routes GeoJSON - Filtered to visible/enabled routes
  const canonicalRoutesGeoJSON = useMemo(() => {
    const visibleRoutes = routes.filter((r) => enabledRoutes[r.id] !== false);
    return {
      type: 'FeatureCollection',
      features: visibleRoutes.map((r) => {
        const routeColor = STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6';
        const isSelected = r.id === activeRouteId;
        return {
          type: 'Feature',
          id: r.id,
          properties: {
            id: r.id,
            name: r.name,
            objective: (r.objective || r.id).toUpperCase(),
            color: routeColor,
            distance: r.distanceNM,
            transitDays: r.transitDays,
            dwellDays: r.dwellDays || 5.0,
            durationDays: r.durationDays || r.transitDays,
            fuel: r.estimatedFuelMT,
            meanRisk: r.meanRisk,
            maxRisk: r.maxRisk,
            isSelected: isSelected ? 1 : 0,
            shortLabel: {
              fastest: 'FASTEST',
              shortest: 'SHORTEST',
              safest: 'SAFEST',
              fuel_efficient: 'FUEL-EFF',
              balanced: 'BALANCED'
            }[r.id] || r.id.toUpperCase().slice(0, 5)
          },
          geometry: {
            type: 'LineString',
            coordinates: r.waypoints
          }
        };
      })
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId, enabledRoutes]);


  // 6. Route Segment Click Geometry
  const selectedRouteSegmentsGeoJSON = useMemo(() => {
    const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
    if (!activeRoute || !activeRoute.segments || activeRoute.segments.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = activeRoute.segments.map((seg: any, idx: number) => {
      const fromLon = seg.from_lon ?? seg.from_coords?.[0] ?? activeRoute.waypoints[idx]?.[0] ?? 0;
      const fromLat = seg.from_lat ?? seg.from_coords?.[1] ?? activeRoute.waypoints[idx]?.[1] ?? 0;
      const toLon = seg.to_lon ?? seg.to_coords?.[0] ?? activeRoute.waypoints[idx + 1]?.[0] ?? fromLon;
      const toLat = seg.to_lat ?? seg.to_coords?.[1] ?? activeRoute.waypoints[idx + 1]?.[1] ?? fromLat;

      return {
        type: 'Feature',
        id: `SEG-${idx}`,
        properties: {
          segmentIndex: idx,
          from_cell: seg.from_h3 || seg.from_cell || `CELL-${idx}`,
          to_cell: seg.to_h3 || seg.to_cell || `CELL-${idx + 1}`,
          distance_nm: seg.distance_nm,
          heading_deg: seg.heading_deg,
          stw_kt: seg.vessel_stw_kt || seg.stw_kt || 9.0,
          sog_kt: seg.sog_kt || 9.0,
          current_along_track_kt: seg.current_along_track_kt || 0.0,
          current_u_ms: seg.current_u_ms || 0.0,
          current_v_ms: seg.current_v_ms || 0.0,
          sic_pct: seg.sic_percent ?? seg.sic_pct ?? 0.0,
          wave_height_m: seg.wave_height_m || 2.0,
          wind_speed_kt: seg.wind_speed_ms ? +(seg.wind_speed_ms * 1.94384).toFixed(1) : (seg.wind_speed_kt || 12.0),
          depth_m: seg.depth_m || 3500,
          under_keel_clearance_m: seg.under_keel_clearance_m || ((seg.depth_m || 3500) - 5.6),
          fuel_burn_mt: seg.fuel_mt || seg.fuel_burn_mt || 1.5,
          segment_cost: seg.objective_cost || seg.segment_cost || 10.0,
          risk_composite: seg.risk_composite || seg.risk || 0.1,
          departure_eta: seg.departure_time || seg.departure_eta,
          arrival_eta: seg.arrival_time || seg.arrival_eta,
          departure_hours: seg.departure_hours,
          arrival_hours: seg.arrival_hours,
          duration_hours: seg.segment_duration_hours || seg.duration_hours,
          isSelected: (selectedSegment?.from_cell === (seg.from_h3 || seg.from_cell)) ||
                      (selectedSegment?.segmentIndex === idx)
        },
        geometry: {
          type: 'LineString',
          coordinates: [
            [fromLon, fromLat],
            [toLon, toLat]
          ]
        }
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId, selectedSegment]);

  // 7. Vessel Real-Time Position Interpolator along Selected Route
  const vesselGeoJSON = useMemo(() => {
    const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
    if (!activeRoute || !activeRoute.waypoints || activeRoute.waypoints.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const totalDays = activeRoute.durationDays || activeRoute.transitDays || 35.0;
    const progressTotal = Math.min(1.0, Math.max(0.0, sliderDay / Math.max(1.0, totalDays)));

    const numPoints = activeRoute.waypoints.length;
    const floatIdx = progressTotal * (numPoints - 1);
    const idx0 = Math.floor(floatIdx);
    const idx1 = Math.min(idx0 + 1, numPoints - 1);
    const frac = floatIdx - idx0;

    const p0 = activeRoute.waypoints[idx0];
    const p1 = activeRoute.waypoints[idx1];

    const targetCoords: [number, number] = [
      +(p0[0] + (p1[0] - p0[0]) * frac).toFixed(4),
      +(p0[1] + (p1[1] - p0[1]) * frac).toFixed(4)
    ];

    let currentStage = 'En Route';
    if (sliderDay === 0) currentStage = 'Departing Cape Town Gateway';
    else if (sliderDay >= totalDays) currentStage = 'Mission Completed - Returned to Cape Town';
    else if (sliderDay >= 12 && sliderDay <= 16) currentStage = 'At Bharati Maritime Access (Prydz Bay)';
    else if (sliderDay >= 22 && sliderDay <= 27) currentStage = 'At Maitri Maritime Access (India Bay)';

    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            vesselName: 'ORV Sagar Kanya',
            sog_kt: (activeRoute as any).meanSOG || 9.0,
            stage: currentStage,
            day: sliderDay
          },
          geometry: {
            type: 'Point',
            coordinates: targetCoords
          }
        }
      ]
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId, sliderDay]);


  // -------------------------------------------------------------
  // Map Initialization: Muted Basemap, Display-Aggregated SIC & H3 Grid
  // -------------------------------------------------------------
  useEffect(() => {
    if (!mapContainer.current) return;

    if (map.current) {
      map.current.remove();
      map.current = null;
    }

    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'satellite-basemap-tiles': {
            type: 'raster',
            tiles: [getTileUrl(basemapStyle)],
            tileSize: 256,
            attribution: '© Google Earth / ESRI Ocean, NCPOR AMIP'
          }
        },
        layers: [
          {
            id: 'ocean-natural-base',
            type: 'background',
            paint: {
              'background-color': '#080e1e'
            }
          },
          // 1. Basemap (Muted to ensure data prominence: raster-saturation -0.6, brightness 0.4)
          {
            id: 'satellite-basemap-layer',
            type: 'raster',
            source: 'satellite-basemap-tiles',
            paint: {
              'raster-opacity': 1.0,
              'raster-saturation': -0.6,
              'raster-brightness-max': 0.4
            },
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [45.0, -53.0],
      zoom: 2.9,
      attributionControl: false
    });

    map.current = mapInstance;
    mapInstance.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    mapInstance.on('load', () => {
      // Coherent Framing of Mission Geometry (Cape Town, Southern Ocean, Antarctica, nodes & routes)
      try {
        mapInstance.fitBounds(
          [
            [6.0, -72.0],
            [82.0, -32.0]
          ],
          {
            padding: { top: 100, bottom: 100, left: 100, right: 400 },
            maxZoom: 3.5,
            duration: 0
          }
        );
      } catch {
        // bounds fallback
      }

      // =========================================================
      // MANDATORY LAYER ORDER (bottom -> top):
      // 1. Basemap (muted)
      // 2. Land mask (#1a1a1a)
      // 3. Canonical H3 outlines (RES-5, subtle)
      // 4. Display-aggregated SIC fill (RES-3/4)
      // 5. Iceberg hazard (if enabled, off by default)
      // 6. Iceberg trajectories (if enabled)
      // 7. Unselected routes (thin, low opacity)
      // 8. Selected route (thick, bright, white under-glow)
      // 9. Mission nodes
      // 10. Vessel position (on selected route at current time)
      // 11. Iceberg observation points
      // 12. Selected cell highlight
      // 13. Selected iceberg highlight
      // 14. Selected route segment highlight
      // =========================================================

      // Sources
      mapInstance.addSource('display-aggregated-sic-source', {
        type: 'geojson',
        data: displayAggregateSICGeoJSON
      });

      mapInstance.addSource('canonical-h3-source', {
        type: 'geojson',
        data: authenticH3GeoJSON
      });

      mapInstance.addSource('iceberg-trajectories-source', {
        type: 'geojson',
        data: icebergTrajectoriesGeoJSON
      });

      mapInstance.addSource('canonical-routes-source', {
        type: 'geojson',
        data: canonicalRoutesGeoJSON
      });

      mapInstance.addSource('route-segments-source', {
        type: 'geojson',
        data: selectedRouteSegmentsGeoJSON
      });

      mapInstance.addSource('vessel-source', {
        type: 'geojson',
        data: vesselGeoJSON
      });

      mapInstance.addSource('icebergs-source', {
        type: 'geojson',
        data: currentIcebergsGeoJSON
      });

      // 2. Land Mask Fill (#1a1a1a)
      mapInstance.addLayer({
        id: 'land-mask-fill',
        type: 'fill',
        source: 'display-aggregated-sic-source',
        filter: ['==', ['get', 'is_land'], true],
        paint: {
          'fill-color': '#1a1a1a',
          'fill-opacity': 1.0
        }
      });

      mapInstance.addLayer({
        id: 'land-mask-outline',
        type: 'line',
        source: 'display-aggregated-sic-source',
        filter: ['==', ['get', 'is_land'], true],
        paint: {
          'line-color': 'rgba(80, 80, 80, 0.3)',
          'line-width': 1.0
        }
      });

      // 3. Canonical H3 Outlines (RES-5, subtle)
      mapInstance.addLayer({
        id: 'canonical-h3-lines',
        type: 'line',
        source: 'canonical-h3-source',
        layout: {
          visibility: showH3Grid ? 'visible' : 'none'
        },
        paint: {
          'line-color': [
            'interpolate',
            ['linear'],
            ['zoom'],
            4, 'rgba(255, 255, 255, 0.15)',
            5, 'rgba(255, 255, 255, 0.45)',
            7, 'rgba(255, 255, 255, 0.70)'
          ],
          'line-width': [
            'interpolate',
            ['linear'],
            ['zoom'],
            4, 0.5,
            5, 1.0,
            7, 1.5
          ]
        }
      });

      // 4. Display-Aggregated SIC Fill (RES-3/4, fill-opacity 0.9, exact 9-color gradient)
      mapInstance.addLayer({
        id: 'display-aggregated-sic-fill',
        type: 'fill',
        source: 'display-aggregated-sic-source',
        filter: ['!=', ['get', 'is_land'], true],
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'sic'],
            0.00, '#0b1d3a',
            0.05, '#1e4d7b',
            0.15, '#2e7d9e',
            0.30, '#4a9bc7',
            0.50, '#6baed6',
            0.70, '#9ecae1',
            0.85, '#c6dbef',
            0.95, '#e6f2ff',
            1.00, '#ffffff'
          ],
          'fill-opacity': 0.90
        }
      });

      // Canonical H3 Click / Hover Transparent Interaction Layer
      mapInstance.addLayer({
        id: 'canonical-h3-hit',
        type: 'fill',
        source: 'canonical-h3-source',
        paint: {
          'fill-color': 'rgba(0, 0, 0, 0.0)'
        }
      });

      // 6a. Iceberg Trajectories for All Tracked Icebergs (vibrant dashed coral/orange lines)
      mapInstance.addLayer({
        id: 'iceberg-trajectories-all',
        type: 'line',
        source: 'iceberg-trajectories-source',
        layout: {
          visibility: showTrajectories ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#f97316',
          'line-width': 1.8,
          'line-opacity': 0.65,
          'line-dasharray': [4, 2]
        }
      });

      // 6b. Selected Iceberg Trajectory Glow (Luminous 10px halo under the active iceberg's 90d drift line)
      mapInstance.addLayer({
        id: 'iceberg-trajectory-selected-glow',
        type: 'line',
        source: 'iceberg-trajectories-source',
        layout: {
          visibility: selectedIceberg ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#ea580c',
          'line-width': 10.0,
          'line-opacity': 0.75,
          'line-blur': 4.0
        },
        filter: ['==', ['get', 'id'], selectedIceberg?.id || '']
      });

      // 6c. Selected Iceberg Trajectory Line (Thick, solid, vibrant line)
      mapInstance.addLayer({
        id: 'iceberg-trajectory-selected-line',
        type: 'line',
        source: 'iceberg-trajectories-source',
        layout: {
          visibility: selectedIceberg ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#fed7aa',
          'line-width': 3.5,
          'line-opacity': 1.0
        },
        filter: ['==', ['get', 'id'], selectedIceberg?.id || '']
      });

      // 7. Unselected Routes — uniform solid lines, clear 0.80 opacity, no dashes
      mapInstance.addLayer({
        id: 'routes-unselected-line',
        type: 'line',
        source: 'canonical-routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': [
            'match', ['get', 'id'],
            'fastest',        '#38bdf8',
            'shortest',       '#f59e0b',
            'safest',         '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced',       '#14b8a6',
            '#94a3b8'
          ],
          'line-width': 3.0,
          'line-opacity': 0.80
        },
        filter: ['!=', ['get', 'id'], activeRouteId]
      });

      // 8. Selected Route Glow — subtle soft aura to accent selection without heavy bulk
      mapInstance.addLayer({
        id: 'routes-selected-glow',
        type: 'line',
        source: 'canonical-routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': [
            'match', ['get', 'id'],
            'fastest',        '#38bdf8',
            'shortest',       '#f59e0b',
            'safest',         '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced',       '#14b8a6',
            '#38bdf8'
          ],
          'line-width': 7.0,
          'line-opacity': 0.40,
          'line-blur': 2.0
        },
        filter: ['==', ['get', 'id'], activeRouteId]
      });

      // 8a. Selected Route Line — uniform solid line matching other routes in thickness
      mapInstance.addLayer({
        id: 'routes-selected-line',
        type: 'line',
        source: 'canonical-routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': [
            'match', ['get', 'id'],
            'fastest',        '#38bdf8',
            'shortest',       '#f59e0b',
            'safest',         '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced',       '#14b8a6',
            '#ffffff'
          ],
          'line-width': 3.0,
          'line-opacity': 1.0
        },
        filter: ['==', ['get', 'id'], activeRouteId]
      });

      // 8b. Route Labels (short readable name along each visible route)
      mapInstance.addLayer({
        id: 'routes-labels',
        type: 'symbol',
        source: 'canonical-routes-source',
        layout: {
          'symbol-placement': 'line-center',
          'text-field': [
            'match', ['get', 'id'],
            'fastest',        'FASTEST',
            'shortest',       'SHORTEST',
            'safest',         'SAFEST',
            'fuel_efficient', 'FUEL-EFF',
            'balanced',       'BALANCED',
            'ROUTE'
          ],
          'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
          'text-size': 11,
          'text-offset': [0, -0.9],
          'text-max-angle': 30,
          'text-keep-upright': true,
          'text-allow-overlap': false,
          'text-ignore-placement': false
        },
        paint: {
          'text-color': [
            'match', ['get', 'id'],
            'fastest',        '#60a5fa',
            'shortest',       '#fbbf24',
            'safest',         '#4ade80',
            'fuel_efficient', '#c084fc',
            'balanced',       '#2dd4bf',
            '#ffffff'
          ],
          'text-halo-color': '#080d1a',
          'text-halo-width': 2.5,
          'text-opacity': 1.0
        }
      });


      // 14. Selected Route Segment Highlight (thick cyan)
      mapInstance.addLayer({
        id: 'route-segments-line',
        type: 'line',
        source: 'route-segments-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#00ffff',
          'line-width': 6.0,
          'line-opacity': [
            'case',
            ['==', ['get', 'isSelected'], true],
            0.90,
            0.0
          ]
        }
      });

      // 10. Vessel Position (ORV Sagar Kanya along selected route)
      mapInstance.addLayer({
        id: 'vessel-halo',
        type: 'circle',
        source: 'vessel-source',
        paint: {
          'circle-radius': 14,
          'circle-color': '#38bdf8',
          'circle-opacity': 0.45,
          'circle-blur': 0.6
        }
      });

      mapInstance.addLayer({
        id: 'vessel-point',
        type: 'circle',
        source: 'vessel-source',
        paint: {
          'circle-radius': 7.0,
          'circle-color': '#ffffff',
          'circle-stroke-width': 3.0,
          'circle-stroke-color': '#1d4ed8'
        }
      });

      // 11a. Iceberg Clickable Hit Target (14px transparent circle for easy clicks)
      mapInstance.addLayer({
        id: 'icebergs-hit',
        type: 'circle',
        source: 'icebergs-source',
        layout: {
          visibility: showIcebergs ? 'visible' : 'none'
        },
        paint: {
          'circle-radius': 14.0,
          'circle-color': 'rgba(0, 0, 0, 0.0)'
        }
      });

      // 11b. Iceberg Observation Points (~73 tracked bergs, 5.5px radius, #f97316, opacity 0.90)
      mapInstance.addLayer({
        id: 'icebergs-point',
        type: 'circle',
        source: 'icebergs-source',
        layout: {
          visibility: showIcebergs ? 'visible' : 'none'
        },
        paint: {
          'circle-radius': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            9.0,
            5.5
          ],
          'circle-color': '#f97316',
          'circle-opacity': 0.90,
          'circle-stroke-width': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            2.5,
            1.5
          ],
          'circle-stroke-color': '#ffffff'
        }
      });

      // 13. Selected Iceberg Highlight (Luminous 20px Orange Halo)
      mapInstance.addLayer({
        id: 'icebergs-selected-halo',
        type: 'circle',
        source: 'icebergs-source',
        layout: {
          visibility: selectedIceberg ? (showIcebergs ? 'visible' : 'none') : 'none'
        },
        paint: {
          'circle-radius': 20.0,
          'circle-color': '#f97316',
          'circle-opacity': 0.60,
          'circle-blur': 0.5
        },
        filter: ['==', ['get', 'id'], selectedIceberg?.id || '']
      });

      // 12. Selected Cell Highlight (Cyan/white outline #00ffff, 2px)
      mapInstance.addLayer({
        id: 'canonical-h3-selected-line',
        type: 'line',
        source: 'canonical-h3-source',
        paint: {
          'line-color': '#00ffff',
          'line-width': 2.5
        },
        filter: ['==', ['get', 'id'], selectedH3Cell?.id || '']
      });

      // 9. Mission Nodes (Cape Town Gateway, Bharati Maritime Access, Maitri Maritime Access)
      const missionNodes = [
        {
          id: 'cape-town',
          name: 'Cape Town Gateway',
          role: 'ORIGIN / RETURN PORT',
          coords: [18.4241, -33.9249] as [number, number],
          iconColor: '#3b82f6',
          symbol: '⚓'
        },
        {
          id: 'bharati',
          name: 'Bharati Maritime Access',
          role: 'WAYPOINT 1 (48h Configured Dwell)',
          coords: [76.19, -69.41] as [number, number],
          iconColor: '#14b8a6',
          symbol: '◆'
        },
        {
          id: 'maitri',
          name: 'Maitri Maritime Access (India Bay)',
          role: 'WAYPOINT 2 (72h Configured Dwell)',
          coords: [11.73, -69.95] as [number, number],
          iconColor: '#22c55e',
          symbol: '◆'
        }
      ];

      missionNodes.forEach((node) => {
        const el = document.createElement('div');
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.gap = '5px';
        el.style.padding = '3px 7px';
        el.style.background = 'rgba(15, 23, 42, 0.94)';
        el.style.border = `1.5px solid ${node.iconColor}`;
        el.style.borderBottom = `3px solid ${node.iconColor}`;
        el.style.borderRadius = '3px';
        el.style.color = '#f8fafc';
        el.style.fontFamily = 'monospace';
        el.style.fontSize = '10px';
        el.style.fontWeight = '800';
        el.style.cursor = 'pointer';
        el.style.boxShadow = `0 2px 8px rgba(0,0,0,0.6), 0 0 6px ${node.iconColor}55`;
        el.innerHTML = `<span style="color:${node.iconColor};font-size:11px;">${node.symbol}</span><span>${node.name}</span>`;

        new maplibregl.Marker({ element: el })
          .setLngLat(node.coords)
          .setPopup(
            new maplibregl.Popup({ offset: 15 }).setHTML(`
              <div style="color: #0f172a; background: #ffffff; padding: 6px 10px; font-family: monospace; min-width: 220px;">
                <div style="font-size: 9px; color: ${node.iconColor}; font-weight: 800;">${node.role}</div>
                <strong style="font-size: 11px; color: #1e3a8a;">${node.name}</strong>
                <div style="margin-top: 5px; font-size: 9px; background: #eff6ff; padding: 3px 6px; border: 1px solid #bfdbfe;">
                  COORDINATES: ${Math.abs(node.coords[1]).toFixed(2)}°S, ${node.coords[0].toFixed(2)}°E
                </div>
              </div>
            `)
          )
          .addTo(mapInstance);
      });

      // ---------------------------------------------------------
      // Interactive Event Handlers
      // ---------------------------------------------------------

      // Hover Canonical H3 Cell: Tooltip H3: <id> | SIC: <sic>%
      mapInstance.on('mousemove', 'canonical-h3-hit', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const props = feat.properties || {};
        const cellId = props.id || props.cell_id;
        const sicVal = props.sic_pct ?? 0.0;

        mapInstance.getCanvas().style.cursor = 'pointer';

        if (!hoveredPopupRef.current) {
          hoveredPopupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10 });
        }
        hoveredPopupRef.current
          .setLngLat(e.lngLat)
          .setHTML(`<div style="background:#0f172a;color:#38bdf8;font-family:monospace;font-size:10.5px;font-weight:bold;padding:3px 8px;border:1px solid #0284c7;box-shadow:0 4px 12px rgba(0,0,0,0.7);">H3: ${cellId} | SIC: ${sicVal}%</div>`)
          .addTo(mapInstance);

        const dataObj = {
          ...props,
          displayId: cellId
        };
        setHoveredCellData(dataObj);
        if (onHoverCell) onHoverCell(dataObj);
      });

      mapInstance.on('mouseleave', 'canonical-h3-hit', () => {
        mapInstance.getCanvas().style.cursor = '';
        if (hoveredPopupRef.current) {
          hoveredPopupRef.current.remove();
          hoveredPopupRef.current = null;
        }
        setHoveredCellData(null);
        if (onHoverCell) onHoverCell(null);
      });

      // Click Canonical H3 Cell: Select cell & open Cell Inspector
      mapInstance.on('click', 'canonical-h3-hit', (e) => {
        // Prevent click conflict with icebergs, routes, or trajectories
        const hitIcebergs = mapInstance.queryRenderedFeatures(e.point, { layers: ['icebergs-hit', 'icebergs-point'] });
        if (hitIcebergs && hitIcebergs.length > 0) return;

        const hitRoutes = mapInstance.queryRenderedFeatures(e.point, { layers: ['routes-unselected-line', 'routes-selected-line'] });
        if (hitRoutes && hitRoutes.length > 0) return;

        const hitTraj = mapInstance.queryRenderedFeatures(e.point, { layers: ['iceberg-trajectories-all', 'iceberg-trajectory-selected-line'] });
        if (hitTraj && hitTraj.length > 0) return;

        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const props = feat.properties || {};
        const cellId = props.id || props.cell_id;

        const env = getCellEnvironment(cellId, currentHz) || {};
        const risk = getCellRisk(cellId, currentHz) || {};

        const cellObj = {
          id: cellId,
          properties: { ...props, ...env, ...risk }
        };

        setSelectedH3Cell(cellObj);
        setSelectedSegment(null);
        setSelectedIceberg(null);

        if (mapInstance.getLayer('canonical-h3-selected-line')) {
          mapInstance.setFilter('canonical-h3-selected-line', ['==', ['get', 'id'], cellId]);
        }

        if (onInspectPoint && (env.lat || props.lat)) {
          onInspectPoint([env.lat || props.lat, env.lon || props.lon]);
        }
      });

      // Hover Iceberg Hit / Point: cursor pointer & tooltip
      ['icebergs-hit', 'icebergs-point'].forEach((layerId) => {
        mapInstance.on('mouseenter', layerId, (e) => {
          mapInstance.getCanvas().style.cursor = 'pointer';
          if (!e.features || e.features.length === 0) return;
          const feat = e.features[0];
          const coords = (feat.geometry as any).coordinates.slice();
          const bergId = feat.properties?.id;

          if (!hoveredPopupRef.current) {
            hoveredPopupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10 });
          }
          hoveredPopupRef.current
            .setLngLat(coords)
            .setHTML(`<div style="background:#0d1117;color:#f97316;font-family:system-ui,-apple-system,sans-serif;font-size:11px;font-weight:700;padding:4px 8px;border:1px solid #f97316;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.5);">Iceberg: ${bergId}</div>`)
            .addTo(mapInstance);
        });

        mapInstance.on('mouseleave', layerId, () => {
          mapInstance.getCanvas().style.cursor = '';
          if (hoveredPopupRef.current) {
            hoveredPopupRef.current.remove();
            hoveredPopupRef.current = null;
          }
        });

        // Click Iceberg: select iceberg, highlight trajectory & open Iceberg Inspector
        mapInstance.on('click', layerId, (e) => {
          if (!e.features || e.features.length === 0) return;
          const feat = e.features[0];
          const bergId = feat.properties?.id;
          const coords = (feat.geometry as any).coordinates;
          const found = icebergsList.find((b: any) => b.id === bergId);
          if (found) {
            setSelectedIceberg({
              ...found,
              currentCoords: coords,
              speed_knots: feat.properties?.speed_knots,
              depth_m: feat.properties?.depth_m
            });
            setSelectedH3Cell(null);
            setSelectedSegment(null);
          }
        });
      });

      // Click / Hover Iceberg Trajectory Lines: selecting an iceberg by clicking its drift path
      ['iceberg-trajectories-all', 'iceberg-trajectory-selected-line'].forEach((layerId) => {
        mapInstance.on('mouseenter', layerId, () => {
          mapInstance.getCanvas().style.cursor = 'pointer';
        });
        mapInstance.on('mouseleave', layerId, () => {
          mapInstance.getCanvas().style.cursor = '';
        });
        mapInstance.on('click', layerId, (e) => {
          if (!e.features || e.features.length === 0) return;
          const bergId = e.features[0].properties?.id;
          const found = icebergsList.find((b: any) => b.id === bergId);
          if (found) {
            const coords = found.latestObservation
              ? [found.latestObservation.longitude, found.latestObservation.latitude]
              : [0, 0];
            setSelectedIceberg({
              ...found,
              currentCoords: coords,
              speed_knots: 0.24,
              depth_m: 3200
            });
            setSelectedH3Cell(null);
            setSelectedSegment(null);
          }
        });
      });

      // Click Route Line: Select route
      ['routes-unselected-line', 'routes-selected-line'].forEach((layerId) => {
        mapInstance.on('click', layerId, (e) => {
          if (!e.features || e.features.length === 0) return;
          const routeId = e.features[0].properties?.id;
          if (routeId) {
            setSelectedRouteId(routeId);
            if (onSelectRoute) onSelectRoute(routeId);
          }
        });

        mapInstance.on('mouseenter', layerId, () => {
          mapInstance.getCanvas().style.cursor = 'pointer';
        });
        mapInstance.on('mouseleave', layerId, () => {
          mapInstance.getCanvas().style.cursor = '';
        });
      });

      // Click Route Segment: Open Segment Inspector
      mapInstance.on('click', 'route-segments-line', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const segIdx = feat.properties?.segmentIndex;
        const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
        if (activeRoute && activeRoute.segments && activeRoute.segments[segIdx]) {
          setSelectedSegment(activeRoute.segments[segIdx]);
          setSelectedH3Cell(null);
          setSelectedIceberg(null);
        }
      });
    });

    return () => {
      mapInstance.remove();
      map.current = null;
    };
  }, [basemapStyle]);

  // -------------------------------------------------------------
  // Dynamic Source Updates
  // -------------------------------------------------------------

  // Update Display-Aggregated SIC Source on slider changes
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('display-aggregated-sic-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(displayAggregateSICGeoJSON);
    } catch {
      // source pending
    }
  }, [displayAggregateSICGeoJSON]);

  // Update Canonical H3 Source
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('canonical-h3-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(authenticH3GeoJSON);
    } catch {
      // source pending
    }
  }, [authenticH3GeoJSON]);

  // Update Canonical Routes Source
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('canonical-routes-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(canonicalRoutesGeoJSON);
    } catch {
      // source pending
    }
  }, [canonicalRoutesGeoJSON]);

  // Update Iceberg Positions Source on Slider Day
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('icebergs-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(currentIcebergsGeoJSON);
    } catch {
      // source pending
    }
  }, [currentIcebergsGeoJSON]);

  // Update Iceberg Trajectories Source
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('iceberg-trajectories-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(icebergTrajectoriesGeoJSON);
    } catch {
      // source pending
    }
  }, [icebergTrajectoriesGeoJSON]);

  // Update Vessel Position Source
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('vessel-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(vesselGeoJSON);
    } catch {
      // source pending
    }
  }, [vesselGeoJSON]);

  // Update Route Segment Inspection Source
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('route-segments-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(selectedRouteSegmentsGeoJSON);
    } catch {
      // source pending
    }
  }, [selectedRouteSegmentsGeoJSON]);

  // Update Route Selection Filters when activeRouteId changes
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    try {
      if (map.current.getLayer('routes-selected-line')) {
        map.current.setFilter('routes-selected-line', ['==', ['get', 'id'], activeRouteId]);
      }
      if (map.current.getLayer('routes-selected-glow')) {
        map.current.setFilter('routes-selected-glow', ['==', ['get', 'id'], activeRouteId]);
      }
      if (map.current.getLayer('routes-unselected-line')) {
        map.current.setFilter('routes-unselected-line', ['!=', ['get', 'id'], activeRouteId]);
      }
    } catch {
      // style pending
    }
  }, [activeRouteId]);



  // Update H3 Hexagon Grid Layer Visibility (includes SIC fill cells)
  useEffect(() => {
    if (!map.current) return;
    try {
      const vis = showH3Grid ? 'visible' : 'none';
      const h3Layers = [
        'canonical-h3-lines',
        'canonical-h3-hit',
        'canonical-h3-selected-line',
        'display-aggregated-sic-fill'
      ];
      h3Layers.forEach((layerId) => {
        if (map.current?.getLayer(layerId)) {
          map.current.setLayoutProperty(layerId, 'visibility', vis);
        }
      });
    } catch {
      // style pending
    }
  }, [showH3Grid]);


  // Update Icebergs Layer Visibility
  useEffect(() => {
    if (!map.current) return;
    try {
      const vis = showIcebergs ? 'visible' : 'none';
      if (map.current.getLayer('icebergs-point')) {
        map.current.setLayoutProperty('icebergs-point', 'visibility', vis);
      }
      if (map.current.getLayer('icebergs-hit')) {
        map.current.setLayoutProperty('icebergs-hit', 'visibility', vis);
      }
      if (map.current.getLayer('icebergs-selected-halo')) {
        map.current.setLayoutProperty('icebergs-selected-halo', 'visibility', selectedIceberg ? vis : 'none');
      }
    } catch {
      // style pending
    }
  }, [showIcebergs, selectedIceberg]);

  // Update Iceberg Drift Trajectory Lines Visibility (All 73 drift lines)
  useEffect(() => {
    if (!map.current) return;
    try {
      const vis = showTrajectories ? 'visible' : 'none';
      if (map.current.getLayer('iceberg-trajectories-all')) {
        map.current.setLayoutProperty('iceberg-trajectories-all', 'visibility', vis);
      }
    } catch {
      // style pending
    }
  }, [showTrajectories]);

  // Update Selected Iceberg Filter & Trajectory Highlights
  useEffect(() => {
    if (!map.current) return;
    try {
      const selId = selectedIceberg?.id || '';
      const isSelVisible = selId ? 'visible' : 'none';

      // 1. Highlight selected iceberg's 90-day drift trajectory with glowing halo & thick line
      if (map.current.getLayer('iceberg-trajectory-selected-glow')) {
        map.current.setFilter('iceberg-trajectory-selected-glow', ['==', ['get', 'id'], selId]);
        map.current.setLayoutProperty('iceberg-trajectory-selected-glow', 'visibility', isSelVisible);
      }
      if (map.current.getLayer('iceberg-trajectory-selected-line')) {
        map.current.setFilter('iceberg-trajectory-selected-line', ['==', ['get', 'id'], selId]);
        map.current.setLayoutProperty('iceberg-trajectory-selected-line', 'visibility', isSelVisible);
      }

      // 2. Highlight selected iceberg's point marker & halo
      if (map.current.getLayer('icebergs-selected-halo')) {
        map.current.setFilter('icebergs-selected-halo', ['==', ['get', 'id'], selId]);
        map.current.setLayoutProperty('icebergs-selected-halo', 'visibility', isSelVisible);
      }
      if (map.current.getLayer('icebergs-point')) {
        map.current.setPaintProperty('icebergs-point', 'circle-radius', [
          'case',
          ['==', ['get', 'id'], selId],
          9.0,
          5.5
        ] as any);
        map.current.setPaintProperty('icebergs-point', 'circle-stroke-width', [
          'case',
          ['==', ['get', 'id'], selId],
          2.5,
          1.5
        ] as any);
      }

      // 3. Smoothly pan to selected iceberg if available
      if (selectedIceberg) {
        const coords = selectedIceberg.currentCoords || (selectedIceberg.latestObservation ? [selectedIceberg.latestObservation.longitude, selectedIceberg.latestObservation.latitude] : null);
        if (coords && coords[0] !== 0 && coords[1] !== 0) {
          map.current.easeTo({
            center: coords,
            zoom: Math.max(map.current.getZoom(), 4.0),
            duration: 800
          });
        }
      }
    } catch {
      // style pending
    }
  }, [selectedIceberg]);

  // Update Selected Cell Filter
  useEffect(() => {
    if (!map.current) return;
    try {
      const selId = selectedH3Cell?.id || '';
      if (map.current.getLayer('canonical-h3-selected-line')) {
        map.current.setFilter('canonical-h3-selected-line', ['==', ['get', 'id'], selId]);
      }
    } catch {
      // style pending
    }
  }, [selectedH3Cell]);

  const quickJumpDays = [
    { label: 'Now', day: 0 },
    { label: '+1d', day: 1 },
    { label: '+3d', day: 3 },
    { label: '+7d', day: 7 },
    { label: '+14d', day: 14 },
    { label: '+30d', day: 30 },
    { label: '+60d', day: 60 },
    { label: '+90d', day: 90 }
  ];

  const activeInspector = selectedH3Cell ? 'cell' : selectedIceberg ? 'iceberg' : selectedSegment ? 'segment' : null;

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      
      {/* Central Map Canvas */}
      <div style={{ flex: 1, position: 'relative', minHeight: '380px' }}>
        <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

        {/* Top-Left Oceanographic Status Banner */}
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          pointerEvents: 'none',
          zIndex: 20
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(13, 17, 23, 0.92)',
            backdropFilter: 'blur(10px)',
            padding: '6px 12px',
            borderRadius: '6px',
            border: '1px solid #21262d',
            boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
            pointerEvents: 'auto'
          }}>
            <Compass size={14} color="#38bdf8" />
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#f0f6fc', letterSpacing: '0.2px' }}>
              ISE-44 Polar Navigation Mesh
            </span>
            <span style={{ fontSize: '10px', color: '#8b949e', borderLeft: '1px solid #30363d', paddingLeft: '8px' }}>
              Day T+{sliderDay} ({currentHz}) · {icebergsList.length} Tracked Icebergs
            </span>
          </div>

          {hoveredCellData && (
            <div style={{
              background: 'rgba(13, 17, 23, 0.92)',
              backdropFilter: 'blur(10px)',
              padding: '4px 10px',
              borderRadius: '4px',
              border: '1px solid #30363d',
              fontSize: '10px',
              color: '#8b949e',
              pointerEvents: 'auto'
            }}>
              Cell <strong style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>{hoveredCellData.displayId}</strong> · SIC: <strong style={{ color: '#38bdf8' }}>{hoveredCellData.sic_pct ?? 0}%</strong> · Depth: <strong style={{ color: '#f0f6fc' }}>{hoveredCellData.depth?.toFixed(0) ?? 3400}m</strong>
            </div>
          )}
        </div>

        {/* Route Selector & Individual Visibility Toggles */}
        <div style={{
          position: 'absolute',
          top: '60px',
          left: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          pointerEvents: 'auto',
          zIndex: 20
        }}>
          <div style={{
            background: 'rgba(13, 17, 23, 0.94)',
            backdropFilter: 'blur(12px)',
            border: '1px solid #21262d',
            borderRadius: '8px',
            padding: '10px',
            minWidth: '280px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', paddingBottom: '6px', borderBottom: '1px solid #21262d' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#f0f6fc', letterSpacing: '0.3px', textTransform: 'uppercase' }}>
                Voyage Alternatives
              </span>
              <span style={{ fontSize: '9.5px', color: '#8b949e' }}>
                5 Corridors
              </span>
            </div>

            {/* Route rows */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {routes.map((r) => {
                const isSelected = r.id === activeRouteId;
                const isVisible = enabledRoutes[r.id] !== false;
                const color = STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6';
                const sailDays = (r as any).sailingDays ?? r.transitDays ?? 0;
                return (
                  <div
                    key={r.id}
                    onClick={() => {
                      setSelectedRouteId(r.id);
                      if (onSelectRoute) onSelectRoute(r.id);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '7px 10px',
                      borderRadius: '5px',
                      borderLeft: `3px solid ${color}`,
                      background: isSelected ? 'rgba(56, 189, 248, 0.10)' : 'rgba(255, 255, 255, 0.02)',
                      border: isSelected ? `1px solid ${color}66` : '1px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      opacity: isVisible ? 1.0 : 0.40
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '11.5px', fontWeight: isSelected ? 700 : 600, color: isSelected ? '#ffffff' : '#c9d1d9' }}>
                          {(r.objective || r.id).replace('_', ' ')}
                        </span>
                        {isSelected && (
                          <span style={{ fontSize: '8.5px', background: color, color: '#090d16', padding: '1px 5px', borderRadius: '3px', fontWeight: 800 }}>
                            ACTIVE
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '10px', color: '#8b949e', marginTop: '2px' }}>
                        {sailDays.toFixed(1)}d sail · {(r.durationDays ?? 0).toFixed(1)}d total · {(r.estimatedFuelMT || 0).toFixed(0)} MT
                      </div>
                    </div>

                    {/* Eye toggle */}
                    <button
                      onClick={(ev) => toggleRouteVisibility(r.id, ev)}
                      title={isVisible ? `Hide ${r.name}` : `Show ${r.name}`}
                      style={{
                        background: isVisible ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.02)',
                        border: '1px solid #30363d',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        padding: '3px 6px',
                        display: 'flex',
                        alignItems: 'center',
                        color: isVisible ? '#f0f6fc' : '#484f58',
                        flexShrink: 0,
                        transition: 'all 0.12s ease'
                      }}
                    >
                      {isVisible ? <Eye size={13} color={color} /> : <EyeOff size={13} />}
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Selected Route summary metrics */}
            {selectedRoute && (
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #21262d', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px 8px' }}>
                {[
                  { label: 'Distance', value: `${(selectedRoute.distanceNM || 0).toLocaleString()} NM` },
                  { label: 'Sailing', value: `${((selectedRoute as any).sailingDays ?? selectedRoute.transitDays ?? 0).toFixed(1)} d` },
                  { label: 'Total', value: `${(selectedRoute.durationDays ?? 0).toFixed(1)} d` },
                  { label: 'Fuel', value: `${(selectedRoute.estimatedFuelMT || 0).toFixed(0)} MT` },
                  { label: 'Speed', value: `${((selectedRoute as any).meanSOG ?? 0).toFixed(1)} kt` },
                  { label: 'Risk', value: `${((selectedRoute.meanRisk || 0) * 100).toFixed(0)}%` },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div style={{ fontSize: '9px', color: '#8b949e', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#f0f6fc', marginTop: '1px' }}>{value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Bottom-Left Vertical SIC Legend & Source Label */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          pointerEvents: 'auto',
          zIndex: 20
        }}>
          {/* SIC Legend */}
          <div style={{
            background: 'rgba(13, 17, 23, 0.90)',
            backdropFilter: 'blur(8px)',
            border: '1px solid #21262d',
            borderRadius: '6px',
            padding: '8px 12px',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            fontSize: '11px',
            color: '#f0f6fc',
            minWidth: '170px'
          }}>
            <div style={{ fontWeight: 700, fontSize: '10px', letterSpacing: '0.4px', marginBottom: '6px', color: '#8b949e', textTransform: 'uppercase' }}>
              Sea Ice Concentration
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div style={{
                width: '10px',
                height: '80px',
                borderRadius: '2px',
                background: 'linear-gradient(to top, #0b1d3a 0%, #1e4d7b 5%, #2e7d9e 15%, #4a9bc7 30%, #6baed6 50%, #9ecae1 70%, #c6dbef 85%, #e6f2ff 95%, #ffffff 100%)',
                border: '1px solid rgba(255,255,255,0.15)'
              }} />
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '80px', fontSize: '9.5px', color: '#8b949e' }}>
                <div>100% Fast Ice</div>
                <div>75% Dense Pack</div>
                <div>50% Moderate Pack</div>
                <div>25% Marginal Ice</div>
                <div>0% Open Water</div>
              </div>
            </div>
          </div>

          {/* AMIP Source Label */}
          <div style={{
            background: 'rgba(13, 17, 23, 0.90)',
            backdropFilter: 'blur(8px)',
            border: '1px solid #21262d',
            borderRadius: '6px',
            padding: '6px 10px',
            fontSize: '9.5px',
            color: '#8b949e',
            lineHeight: '1.4'
          }}>
            <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '2px' }}>AMIP Polar Model</div>
            <div>Vessel: ORV Sagar Kanya (ISE-44)</div>
            <div>Bunker: 433 m³ (368 MT capacity)</div>
          </div>
        </div>

        {/* Dedicated Inspector Side Panel */}
        {activeInspector && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            bottom: '12px',
            width: '320px',
            background: '#0d1117',
            border: '1px solid #30363d',
            borderRadius: '8px',
            boxShadow: '0 12px 36px rgba(0,0,0,0.65)',
            zIndex: 40,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            color: '#f0f6fc'
          }}>
            {/* Inspector Header */}
            <div style={{
              padding: '10px 14px',
              background: '#161b22',
              borderBottom: '1px solid #21262d',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{ fontSize: '11.5px', fontWeight: 700, color: '#f0f6fc', letterSpacing: '0.3px', textTransform: 'uppercase' }}>
                {activeInspector === 'cell' ? 'H3 Cell Analysis' : activeInspector === 'iceberg' ? 'Iceberg Telemetry' : 'Segment Operational Profile'}
              </span>
              <button
                onClick={() => {
                  setSelectedH3Cell(null);
                  setSelectedIceberg(null);
                  setSelectedSegment(null);
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#8b949e',
                  cursor: 'pointer',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <X size={15} />
              </button>
            </div>

            {/* Inspector Body */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '11px' }}>
              
              {/* 1. H3 CELL INSPECTOR */}
              {activeInspector === 'cell' && selectedH3Cell && (
                <>
                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Cell Identity</div>
                    <div>H3 Index: <strong style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{selectedH3Cell.id}</strong></div>
                    <div>Coordinates: <span style={{ fontFamily: 'monospace' }}>{Math.abs(selectedH3Cell.properties.lat ?? 0).toFixed(4)}°S, {(selectedH3Cell.properties.lon ?? 0).toFixed(4)}°E</span></div>
                  </div>

                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Sea Ice Assessment</div>
                    <div>Concentration: <strong style={{ color: '#38bdf8' }}>{((selectedH3Cell.properties.sic ?? 0) * 100).toFixed(1)}%</strong></div>
                    <div>Ice Regime: <strong>{
                      (selectedH3Cell.properties.sic ?? 0) === 0 ? 'Open Water'
                      : (selectedH3Cell.properties.sic ?? 0) < 0.15 ? 'Marginal Ice Zone'
                      : (selectedH3Cell.properties.sic ?? 0) < 0.50 ? 'Moderate Pack Ice'
                      : (selectedH3Cell.properties.sic ?? 0) < 0.80 ? 'Dense Pack Ice'
                      : 'Fast Ice'
                    }</strong></div>
                    <div>Limit: 15.0% SIC (Vessel Operational Threshold)</div>
                  </div>

                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Navigational Clearance</div>
                    <div>Navigable: <strong style={{ color: selectedH3Cell.properties.is_land ? '#ef4444' : '#22c55e' }}>
                      {selectedH3Cell.properties.is_land ? 'No (Land Mass)' : (selectedH3Cell.properties.sic ?? 0) > 0.15 ? 'Ice Constrained (SIC > 15%)' : 'Yes (Open Water)'}
                    </strong></div>
                    <div>Depth: {selectedH3Cell.properties.depth?.toFixed(1) ?? '3400.0'} m</div>
                    <div>Under-Keel Clearance: {selectedH3Cell.properties.under_keel_clearance?.toFixed(1) ?? '3394.4'} m</div>
                  </div>

                  {/* Collapsible Ocean Physics */}
                  <div style={{ border: '1px solid #21262d', borderRadius: '5px', overflow: 'hidden' }}>
                    <div
                      onClick={() => toggleSection('ocean')}
                      style={{ padding: '8px 10px', background: '#161b22', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                    >
                      <span style={{ color: '#f0f6fc', fontWeight: 600, fontSize: '10.5px' }}>Oceanographic Metocean Data</span>
                      {expandedSections.ocean ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </div>
                    {expandedSections.ocean && (
                      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '4px', background: '#0d1117', fontSize: '10.5px', color: '#c9d1d9' }}>
                        <div>Waves: {selectedH3Cell.properties.wave_height?.toFixed(2) ?? '2.80'} m (Dir: {selectedH3Cell.properties.wave_direction?.toFixed(0) ?? '270'}°)</div>
                        <div>Wind: {selectedH3Cell.properties.wind_speed?.toFixed(2) ?? '8.50'} m/s (Dir: {selectedH3Cell.properties.wind_direction?.toFixed(0) ?? '225'}°)</div>
                        <div>Current: {selectedH3Cell.properties.current_magnitude?.toFixed(3) ?? '0.180'} m/s (Dir: {selectedH3Cell.properties.current_direction?.toFixed(0) ?? '240'}°)</div>
                        <div>Icebergs: {selectedH3Cell.properties.iceberg_count ?? 0} in proximity</div>
                      </div>
                    )}
                  </div>

                  {/* Collapsible Risk Components */}
                  <div style={{ border: '1px solid #21262d', borderRadius: '5px', overflow: 'hidden' }}>
                    <div
                      onClick={() => toggleSection('risk')}
                      style={{ padding: '8px 10px', background: '#161b22', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                    >
                      <span style={{ color: '#f0f6fc', fontWeight: 600, fontSize: '10.5px' }}>Environmental Risk Breakdown</span>
                      {expandedSections.risk ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </div>
                    {expandedSections.risk && (
                      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '4px', background: '#0d1117', fontSize: '10.5px', color: '#c9d1d9' }}>
                        <div>Composite Risk: <strong style={{ color: (selectedH3Cell.properties.composite_risk ?? 0) > 0.3 ? '#ef4444' : '#22c55e' }}>{((selectedH3Cell.properties.composite_risk ?? 0.12) * 100).toFixed(1)}%</strong></div>
                        <div>Sea-Ice Weight: {((selectedH3Cell.properties.sic_risk ?? 0.0) * 100).toFixed(1)}%</div>
                        <div>Wave Weight: {((selectedH3Cell.properties.wave_risk ?? 0.15) * 100).toFixed(1)}%</div>
                        <div>Wind Weight: {((selectedH3Cell.properties.wind_risk ?? 0.10) * 100).toFixed(1)}%</div>
                        <div>Iceberg Weight: {((selectedH3Cell.properties.iceberg_risk ?? 0.0) * 100).toFixed(1)}%</div>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* 2. ICEBERG INSPECTOR */}
              {activeInspector === 'iceberg' && selectedIceberg && (
                <>
                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase' }}>Target Classification</span>
                      <span style={{ color: '#f97316', fontSize: '9px', fontWeight: 700, fontFamily: 'monospace', background: 'rgba(249,115,22,0.15)', padding: '1px 5px', borderRadius: '3px', border: '1px solid rgba(249,115,22,0.4)' }}>
                        DAY T+{sliderDay}
                      </span>
                    </div>
                    <div>Target ID: <strong style={{ color: '#f97316', fontFamily: 'monospace' }}>{selectedIceberg.id}</strong></div>
                    <div>Live Position: <span style={{ fontFamily: 'monospace', color: '#f0f6fc' }}>{activeIcebergLive ? `${Math.abs(activeIcebergLive.coords[1]).toFixed(4)}°S, ${activeIcebergLive.coords[0].toFixed(4)}°E` : 'Active'}</span></div>
                    <div>Source: {selectedIceberg.source || 'NIC Antarctic Tracked Database'}</div>
                  </div>

                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Kinematics & Drift</div>
                    <div>Cumulative Drift: <strong style={{ color: '#38bdf8' }}>{activeIcebergLive?.driftedNM ?? 0.0} NM</strong> <span style={{ color: '#8b949e', fontSize: '9.5px' }}>(from T+0)</span></div>
                    <div>Drift Velocity: <strong>{activeIcebergLive?.speed ?? 0.24} kt</strong></div>
                    <div>Water Depth: <strong>{activeIcebergLive?.depth ?? 3200} m</strong></div>
                    <div>Dimensions: {(selectedIceberg.latestObservation?.length_km ?? 15).toFixed(0)} × {(selectedIceberg.latestObservation?.width_km ?? 8).toFixed(0)} km</div>
                    <div>Surface Area: {(selectedIceberg.latestObservation?.area_sqkm ?? 120).toFixed(0)} km²</div>
                  </div>

                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Trajectory & Marine Hazard</div>
                    <div>Horizon: <strong>90-Day High-Resolution Drift</strong></div>
                    <div>Drift Model Status: <span style={{ color: '#22c55e', fontWeight: 700 }}>{activeIcebergLive?.status || 'ACTIVE_DRIFT'}</span></div>
                    <div>Route Hazard: <span style={{ color: '#f97316', fontWeight: 600 }}>Tracked along Southern Ocean Route Corridor</span></div>
                  </div>
                </>
              )}

              {/* 3. ROUTE SEGMENT INSPECTOR */}
              {activeInspector === 'segment' && selectedSegment && (
                <>
                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Segment Navigation</div>
                    <div>From Cell: <strong style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{selectedSegment.from_cell || selectedSegment.from_h3 || '85ad3617fffffff'}</strong></div>
                    <div>To Cell: <strong style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{selectedSegment.to_cell || selectedSegment.to_h3 || '85bc6117fffffff'}</strong></div>
                    <div>Leg Distance: {(selectedSegment.distance_nm ?? selectedSegment.distanceNM ?? 0).toFixed(2)} NM</div>
                    <div>True Heading: {(selectedSegment.heading_deg ?? 0).toFixed(1)}°</div>
                  </div>

                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Propulsion & Effective Speed</div>
                    <div>Engine STW: <strong>{(selectedSegment.stw_kt ?? selectedSegment.vessel_stw_kt ?? 9.0).toFixed(2)} kt</strong></div>
                    <div>Ocean Current Along-Track: <strong>{(selectedSegment.current_along_track_kt ?? 0.0).toFixed(2)} kt</strong></div>
                    <div>Resulting SOG: <strong style={{ color: '#38bdf8' }}>{(selectedSegment.sog_kt ?? selectedSegment.effective_speed_kt ?? 9.0).toFixed(2)} kt</strong></div>
                    <div>Transit Duration: {(selectedSegment.duration_hours ?? selectedSegment.segment_duration_hours ?? 0).toFixed(2)} hours</div>
                  </div>

                  <div style={{ background: '#161b22', padding: '10px', borderRadius: '5px', border: '1px solid #21262d' }}>
                    <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Metocean & Fuel Burn</div>
                    <div>SIC: {(selectedSegment.sic_pct ?? selectedSegment.sic_percent ?? 0).toFixed(1)}%</div>
                    <div>Wave Height: {(selectedSegment.wave_height_m ?? 2.8).toFixed(2)} m</div>
                    <div>Wind Speed: {(selectedSegment.wind_speed_kt ?? selectedSegment.wind_speed_ms ?? 8.5).toFixed(1)} kt</div>
                    <div>Fuel Consumption: <strong style={{ color: '#f0f6fc' }}>{(selectedSegment.fuel_burn_mt ?? selectedSegment.fuel_mt ?? 0).toFixed(2)} MT</strong></div>
                    <div>Segment Risk: <strong style={{ color: (selectedSegment.risk_composite || selectedSegment.risk || 0) > 0.3 ? '#ef4444' : '#22c55e' }}>{(((selectedSegment.risk_composite ?? selectedSegment.risk ?? 0.1)) * 100).toFixed(1)}%</strong></div>
                  </div>
                </>
              )}

            </div>
          </div>
        )}

      </div>

      {/* 9. Time Slider & Playback Controls Bar (T+0 to T+90 Days) */}
      <div style={{
        padding: '8px 16px',
        background: '#0f172a',
        borderTop: '1px solid #334155',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        zIndex: 30
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          
          {/* Play / Pause & Horizon Readout */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => setIsTimelinePlaying(!isTimelinePlaying)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 12px',
                background: isTimelinePlaying ? '#ef4444' : '#2563eb',
                border: '1px solid',
                borderColor: isTimelinePlaying ? '#dc2626' : '#1d4ed8',
                color: '#ffffff',
                fontSize: '11px',
                fontFamily: 'monospace',
                fontWeight: 800,
                cursor: 'pointer'
              }}
            >
              {isTimelinePlaying ? <Pause size={13} /> : <Play size={13} />}
              <span>{isTimelinePlaying ? 'PAUSE' : 'PLAY 90D'}</span>
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Calendar size={13} color="#38bdf8" />
              <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'monospace', color: '#f8fafc' }}>
                TIMELINE: <span style={{ color: '#38bdf8' }}>T+{sliderDay} DAYS</span>
              </span>
              <span style={{ fontSize: '10px', color: '#94a3b8', fontFamily: 'monospace' }}>
                (Horizon: <strong style={{ color: '#22c55e' }}>{currentHz}</strong>)
              </span>
            </div>
          </div>

          {/* Quick-Jump Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '9px', color: '#64748b', fontFamily: 'monospace', marginRight: '4px' }}>
              QUICK JUMP:
            </span>
            {quickJumpDays.map((q) => {
              const isCurrent = sliderDay === q.day;
              return (
                <button
                  key={q.label}
                  onClick={() => handleSliderChange(q.day)}
                  style={{
                    padding: '3px 8px',
                    fontSize: '10px',
                    fontFamily: 'monospace',
                    fontWeight: isCurrent ? 800 : 500,
                    background: isCurrent ? '#2563eb' : 'rgba(30, 41, 59, 0.7)',
                    border: `1px solid ${isCurrent ? '#38bdf8' : '#334155'}`,
                    color: isCurrent ? '#ffffff' : '#cbd5e1',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {q.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Continuous 90-Day Range Slider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%' }}>
          <span style={{ fontSize: '9.5px', fontFamily: 'monospace', color: '#64748b' }}>T+0d</span>
          <input
            type="range"
            min={0}
            max={90}
            step={1}
            value={sliderDay}
            onChange={(e) => handleSliderChange(Number(e.target.value))}
            style={{
              flex: 1,
              height: '6px',
              accentColor: '#38bdf8',
              cursor: 'pointer'
            }}
          />
          <span style={{ fontSize: '9.5px', fontFamily: 'monospace', color: '#64748b' }}>T+90d</span>
        </div>
      </div>

    </div>
  );
};

export default AntarcticMap;

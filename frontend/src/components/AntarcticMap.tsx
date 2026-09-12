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
  ChevronRight,
  Ship
} from 'lucide-react';
import { useMission } from '../context/MissionContext';
import antarcticaFullH3GridData from '../data/antarctica_full_h3_grid.json';
import displayAggregateGeojsonData from '../data/display_aggregate_h3.json';
import antarcticaBordersData from '../data/antarctica_borders.json';
import { createSmoothFlowPath } from '../utils/routeGeometry';
import { RouteVoyageSimulatorHUD } from './RouteVoyageSimulatorHUD';
import {
  evaluateVoyageSimulationStep,
  GridDecisionStep
} from '../utils/voyageSimulator';
import { ANTARCTIC_STATIONS } from '../data/antarcticStations';

interface AntarcticMapProps {
  selectedHorizon: string;
  activeLayer?: 'sic' | 'icebergs' | 'risk' | 'weather';
  selectedRoute?: string;
  onHorizonChange?: (hz: string) => void;
  onInspectPoint?: (coords: [number, number]) => void;
  onSelectRoute?: (routeId: string) => void;
  showH3Grid?: boolean;
  showSIC?: boolean;
  showBorders?: boolean;
  showIcebergs?: boolean;
  showTrajectories?: boolean;
  basemapStyle?: 'google-earth' | 'google-hybrid' | 'google-terrain' | 'osm';
  onHoverCell?: (data: any | null) => void;
  theme?: 'dark' | 'light';
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
  showSIC: propShowSIC,
  showBorders: propShowBorders,
  showIcebergs: propShowIcebergs = true,
  showTrajectories: propShowTrajectories,
  basemapStyle: propBasemapStyle,
  onHoverCell,
  theme = 'dark'
}) => {
  const isLight = theme === 'light';
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
    toggleRouteEnabled,
    customOriginDest,
    setCustomOriginDest
  } = useMission();

  const dynamicMarkersRef = useRef<maplibregl.Marker[]>([]);
  const missionNodesRef = useRef<maplibregl.Marker[]>([]);

  // Controlled or context fallback states
  const showH3Grid = propShowH3Grid !== undefined ? propShowH3Grid : contextShowH3Grid;
  const showSIC = propShowSIC !== undefined ? propShowSIC : true;
  const showBorders = propShowBorders !== undefined ? propShowBorders : true;
  const showIcebergs = propShowIcebergs !== undefined ? propShowIcebergs : true;
  const showTrajectories = propShowTrajectories !== undefined ? propShowTrajectories : contextShowTrajectories;
  const basemapStyle = propBasemapStyle || 'google-earth';

  // Timeline slider state: T+0 to T+90 days
  const [sliderDay, setSliderDay] = useState<number>(0);
  const [isTimelinePlaying, setIsTimelinePlaying] = useState<boolean>(false);
  const [hoveredCellData, setHoveredCellData] = useState<any | null>(null);

  // Route Voyage Simulation State (Active Route Traveling with Grid Decisions)
  const [isVoyageSimOpen, setIsVoyageSimOpen] = useState<boolean>(false);
  const [isVoyagePlaying, setIsVoyagePlaying] = useState<boolean>(false);
  const [voyageProgress, setVoyageProgress] = useState<number>(0.0); // 0.0 to 1.0
  const [voyageSpeed, setVoyageSpeed] = useState<number>(1.0); // 1x, 2x, 5x, 10x
  const [followShip, setFollowShip] = useState<boolean>(true);

  // Collapsible inspector accordion state
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    ocean: true,
    risk: true,
    geo: true
  });

  const toggleSection = (s: string) => {
    setExpandedSections((prev) => ({ ...prev, [s]: !prev[s] }));
  };

  // Active route without hardcoding; when no route is chosen, activeRouteId is empty string
  const activeRouteId = propSelectedRoute !== undefined ? propSelectedRoute : selectedRouteId;
  const areRoutesActive = Boolean(activeRouteId) || Boolean(customOriginDest && (customOriginDest.origin || customOriginDest.dest));
  const currentHz = DAY_TO_NEAREST_HORIZON(sliderDay);

  // Global helper functions for interactive station popups to select starting and ending points directly
  useEffect(() => {
    (window as any).setAMIPOrigin = (stId: string) => {
      const st = ANTARCTIC_STATIONS.find((s) => s.id === stId);
      if (st) {
        setCustomOriginDest((prev) => ({
          origin: { name: st.name, coords: st.coords },
          dest: prev?.dest
        }));
      }
    };
    (window as any).setAMIPDest = (stId: string) => {
      const st = ANTARCTIC_STATIONS.find((s) => s.id === stId);
      if (st) {
        setCustomOriginDest((prev) => ({
          origin: prev?.origin,
          dest: { name: st.name, coords: st.coords }
        }));
      }
    };
    return () => {
      delete (window as any).setAMIPOrigin;
      delete (window as any).setAMIPDest;
    };
  }, [setCustomOriginDest]);

  // Station GeoJSON for native MapLibre WebGL rendering (Fixed permanently directly on the map surface)
  // When routes or starting/ending points are active, all other station names DISAPPEAR completely!
  const antarcticStationsGeoJSON: GeoJSON.FeatureCollection = useMemo(() => {
    if (areRoutesActive) {
      return { type: 'FeatureCollection', features: [] };
    }
    return {
      type: 'FeatureCollection',
      features: ANTARCTIC_STATIONS.map((st) => ({
        type: 'Feature',
        id: st.id,
        properties: {
          id: st.id,
          name: st.name,
          shortName: st.shortName,
          country: st.country,
          countryCode: st.countryCode,
          type: st.type,
          category: st.category,
          color: st.color,
          symbol: st.symbol,
          description: st.description,
          label: `${st.symbol}  ${st.shortName}`,
          isIndian: st.type === 'indian_station' || st.type === 'historic_base',
          isPort: st.type === 'gateway_port'
        },
        geometry: {
          type: 'Point',
          coordinates: st.coords
        }
      }))
    };
  }, [areRoutesActive]);

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

  const getTileUrls = (style: 'google-earth' | 'google-hybrid' | 'google-terrain' | 'osm') => {
    switch (style) {
      case 'osm':
        return [
          'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
        ];
      case 'google-terrain':
        return [
          'https://mt0.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
          'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
          'https://mt2.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
          'https://mt3.google.com/vt/lyrs=p&x={x}&y={y}&z={z}'
        ];
      case 'google-hybrid':
        return [
          'https://mt0.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
          'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
          'https://mt2.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
          'https://mt3.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
        ];
      case 'google-earth':
      default:
        // Pure Google Earth Satellite Imagery (lyrs=s) across parallel tile endpoints
        return [
          'https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
          'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
          'https://mt2.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
          'https://mt3.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        ];
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

  // Helper to split coordinates across the ±180° antimeridian so MapLibre renders clean paths without world-wrapping streaks
  const splitLineAtAntimeridian = (coords: [number, number][]): GeoJSON.Geometry => {
    if (!coords || coords.length < 2) {
      return { type: 'LineString', coordinates: coords || [] };
    }
    const lines: [number, number][][] = [];
    let currentLine: [number, number][] = [coords[0]];

    for (let i = 1; i < coords.length; i++) {
      const prev = coords[i - 1];
      const curr = coords[i];
      const dLon = curr[0] - prev[0];

      if (Math.abs(dLon) > 180) {
        const sign = dLon > 0 ? -1 : 1;
        const edgeLonPrev = sign > 0 ? 180 : -180;
        const edgeLonCurr = sign > 0 ? -180 : 180;
        const span = (sign > 0 ? (180 - prev[0]) + (curr[0] - (-180)) : (prev[0] - (-180)) + (180 - curr[0]));
        const frac = span > 0 ? Math.abs(edgeLonPrev - prev[0]) / span : 0.5;
        const crossLat = prev[1] + frac * (curr[1] - prev[1]);

        currentLine.push([edgeLonPrev, crossLat]);
        lines.push(currentLine);
        currentLine = [[edgeLonCurr, crossLat], curr];
      } else {
        currentLine.push(curr);
      }
    }
    lines.push(currentLine);

    if (lines.length === 1) {
      return { type: 'LineString', coordinates: lines[0] };
    }
    return { type: 'MultiLineString', coordinates: lines };
  };

  // 5. Canonical Routes GeoJSON - When active, shows ALL alternative routes simultaneously!
  const canonicalRoutesGeoJSON = useMemo(() => {
    if (!areRoutesActive) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }
    // Show all enabled routes simultaneously so user can compare them across the map
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
          geometry: splitLineAtAntimeridian(createSmoothFlowPath(r.waypoints, 6))
        };
      })
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId, enabledRoutes, areRoutesActive]);


  // 6. Route Segment Click Geometry (empty if no route chosen)
  const selectedRouteSegmentsGeoJSON = useMemo(() => {
    if (!activeRouteId) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }
    const activeRoute = routes.find((r) => r.id === activeRouteId);
    if (!activeRoute || !activeRoute.segments || activeRoute.segments.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = activeRoute.segments.map((seg: any, idx: number) => {
      const fromLon = seg.from_lon ?? seg.from_coords?.[0] ?? activeRoute.waypoints[idx]?.[0] ?? 0;
      const fromLat = seg.from_lat ?? seg.from_coords?.[1] ?? activeRoute.waypoints[idx]?.[1] ?? 0;
      const toLon = seg.to_lon ?? seg.to_coords?.[0] ?? activeRoute.waypoints[idx + 1]?.[0] ?? fromLon;
      const toLat = seg.to_lat ?? seg.to_coords?.[1] ?? activeRoute.waypoints[idx + 1]?.[1] ?? fromLat;

      let segGeometry: GeoJSON.Geometry;
      const dLon = toLon - fromLon;
      if (Math.abs(dLon) > 180) {
        const sign = dLon > 0 ? -1 : 1;
        const edgeLonPrev = sign > 0 ? 180 : -180;
        const edgeLonCurr = sign > 0 ? -180 : 180;
        const span = (sign > 0 ? (180 - fromLon) + (toLon - (-180)) : (fromLon - (-180)) + (180 - toLon));
        const frac = span > 0 ? Math.abs(edgeLonPrev - fromLon) / span : 0.5;
        const crossLat = fromLat + frac * (toLat - fromLat);
        segGeometry = {
          type: 'MultiLineString',
          coordinates: [
            [[fromLon, fromLat], [edgeLonPrev, crossLat]],
            [[edgeLonCurr, crossLat], [toLon, toLat]]
          ]
        };
      } else {
        segGeometry = {
          type: 'LineString',
          coordinates: [
            [fromLon, fromLat],
            [toLon, toLat]
          ]
        };
      }

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
          marginal_risk: seg.composite_risk || seg.marginal_risk || 0.1,
          arrival_hours: seg.arrival_hours,
          duration_hours: seg.segment_duration_hours || seg.duration_hours,
          isSelected: (selectedSegment?.from_cell === (seg.from_h3 || seg.from_cell)) ||
            (selectedSegment?.segmentIndex === idx)
        },
        geometry: segGeometry
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId, selectedSegment]);

  // Route Voyage Step Evaluation (Current grid explanation & adjacent rejections)
  const currentActiveRoute = routes.find((r) => r.id === activeRouteId) || selectedRoute;
  const voyageStep: GridDecisionStep | null = useMemo(() => {
    if (!currentActiveRoute) return null;
    return evaluateVoyageSimulationStep(currentActiveRoute, voyageProgress);
  }, [currentActiveRoute, voyageProgress]);

  // Voyage Simulation Map GeoJSON Sources
  const voyageSimGridGeoJSON = useMemo(() => {
    if (!isVoyageSimOpen || !voyageStep) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }
    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            gridId: voyageStep.gridCellId,
            sic: voyageStep.sicPercent
          },
          geometry: {
            type: 'Polygon',
            coordinates: [voyageStep.gridPolygon]
          }
        }
      ]
    } as GeoJSON.FeatureCollection;
  }, [isVoyageSimOpen, voyageStep]);

  const voyageSimArrowsGeoJSON = useMemo(() => {
    if (!isVoyageSimOpen || !voyageStep) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }
    return {
      type: 'FeatureCollection',
      features: voyageStep.vectorLines as any
    } as GeoJSON.FeatureCollection;
  }, [isVoyageSimOpen, voyageStep]);

  const voyageSimShipGeoJSON = useMemo(() => {
    if (!isVoyageSimOpen || !voyageStep) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }
    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            heading: voyageStep.headingDeg,
            sog: voyageStep.vesselSOGKt
          },
          geometry: {
            type: 'Point',
            coordinates: voyageStep.vesselCoords
          }
        }
      ]
    } as GeoJSON.FeatureCollection;
  }, [isVoyageSimOpen, voyageStep]);

  // Animation frame loop for continuous voyage simulation
  const voyageAnimRef = useRef<number | null>(null);
  const voyageLastTimeRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isVoyagePlaying || !isVoyageSimOpen) {
      if (voyageAnimRef.current) cancelAnimationFrame(voyageAnimRef.current);
      voyageLastTimeRef.current = null;
      return;
    }

    const animateVoyage = (timestamp: number) => {
      if (voyageLastTimeRef.current === null) voyageLastTimeRef.current = timestamp;
      const dtSeconds = (timestamp - voyageLastTimeRef.current) / 1000.0;
      voyageLastTimeRef.current = timestamp;

      // Entire 73-segment route takes ~60 seconds at 1x speed
      const deltaProgress = (dtSeconds / 60.0) * voyageSpeed;

      setVoyageProgress((prev) => {
        const next = prev + deltaProgress;
        if (next >= 1.0) {
          setIsVoyagePlaying(false);
          return 1.0;
        }
        return next;
      });

      voyageAnimRef.current = requestAnimationFrame(animateVoyage);
    };

    voyageAnimRef.current = requestAnimationFrame(animateVoyage);
    return () => {
      if (voyageAnimRef.current) cancelAnimationFrame(voyageAnimRef.current);
    };
  }, [isVoyagePlaying, isVoyageSimOpen, voyageSpeed]);

  // Camera tracking when followShip is enabled
  useEffect(() => {
    if (isVoyageSimOpen && followShip && voyageStep && map.current) {
      map.current.easeTo({
        center: voyageStep.vesselCoords,
        duration: 250,
        essential: false
      });
    }
  }, [isVoyageSimOpen, followShip, voyageStep?.segmentIndex]);

  const handleStepPrev = () => {
    const totalSegs = currentActiveRoute?.segments?.length || 73;
    setVoyageProgress((prev) => Math.max(0.0, prev - 1.0 / totalSegs));
  };

  const handleStepNext = () => {
    const totalSegs = currentActiveRoute?.segments?.length || 73;
    setVoyageProgress((prev) => Math.min(1.0, prev + 1.0 / totalSegs));
  };




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
        glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
        sources: {
          'satellite-basemap-tiles': {
            type: 'raster',
            tiles: getTileUrls(basemapStyle),
            tileSize: 256,
            attribution: '© Google Earth, NCPOR AMIP'
          }
        },
        layers: [
          {
            id: 'ocean-natural-base',
            type: 'background',
            paint: {
              'background-color': '#030712'
            }
          },
          // 1. Google Earth Satellite Basemap (True-color photorealistic satellite imagery)
          {
            id: 'satellite-basemap-layer',
            type: 'raster',
            source: 'satellite-basemap-tiles',
            paint: {
              'raster-opacity': 1.0,
              'raster-saturation': 0.0,
              'raster-brightness-max': 1.0,
              'raster-contrast': 0.05
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

      mapInstance.addSource('voyage-sim-grid-source', {
        type: 'geojson',
        data: voyageSimGridGeoJSON
      });

      mapInstance.addSource('voyage-sim-arrows-source', {
        type: 'geojson',
        data: voyageSimArrowsGeoJSON
      });

      mapInstance.addSource('voyage-sim-ship-source', {
        type: 'geojson',
        data: voyageSimShipGeoJSON
      });



      mapInstance.addSource('icebergs-source', {
        type: 'geojson',
        data: currentIcebergsGeoJSON
      });

      mapInstance.addSource('antarctica-borders-source', {
        type: 'geojson',
        data: antarcticaBordersData as any
      });

      // 2. Land Mask Fill (kept transparent so Google Earth Satellite land & ice shelf imagery is directly visible)
      mapInstance.addLayer({
        id: 'land-mask-fill',
        type: 'fill',
        source: 'display-aggregated-sic-source',
        filter: ['==', ['get', 'is_land'], true],
        paint: {
          'fill-color': '#1a1a1a',
          'fill-opacity': 0.0
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

      // 4. Circum-Antarctic Sea Ice Concentration Fill (all 10,664 hexagons across all 360° of Antarctica)
      mapInstance.addLayer({
        id: 'display-aggregated-sic-fill',
        type: 'fill',
        source: 'canonical-h3-source',
        filter: ['>', ['coalesce', ['get', 'sic'], 0], 0.005],
        layout: {
          visibility: showSIC ? 'visible' : 'none'
        },
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'sic'],
            0.01, '#38bdf8',  // Grease / marginal ice edge (vivid ice cyan)
            0.05, '#0ea5e9',  // Open drift (bright ocean cyan)
            0.10, '#38bdf8',  // Marginal Ice Zone (<15% ORV Sagar Kanya threshold)
            0.15, '#7dd3fc',  // Close pack ice
            0.20, '#a5f3fc',  // Frost blue pack ice
            0.25, '#cffafe',  // Consolidated pack ice
            0.30, '#e0f2fe',  // Very dense ice pack
            0.50, '#f0f9ff',  // Multi-year consolidated ice
            1.00, '#ffffff'   // Fast ice / permanent shelf
          ],
          'fill-opacity': [
            'interpolate',
            ['linear'],
            ['get', 'sic'],
            0.00, 0.00,
            0.01, 0.20,
            0.05, 0.32,
            0.15, 0.44,
            0.30, 0.54,
            0.60, 0.62,
            1.00, 0.68
          ]
        }
      });

      // 4b. Sea Ice Field Boundary Outlines (sharp crisp contour against ocean)
      mapInstance.addLayer({
        id: 'display-aggregated-sic-edge',
        type: 'line',
        source: 'canonical-h3-source',
        filter: ['>', ['coalesce', ['get', 'sic'], 0], 0.01],
        layout: {
          visibility: showSIC ? 'visible' : 'none'
        },
        paint: {
          'line-color': '#7dd3fc',
          'line-width': 1.0,
          'line-opacity': 0.60
        }
      });

      // =========================================================
      // 5. Antarctic Continental Borders & Coastlines (Luminous Overlay)
      // Rendered ABOVE sea ice concentration so coastlines and treaty
      // borders remain 100% visible and sharp across all 360 degrees.
      // =========================================================

      // 5a. Coastline and Ice Shelf Outer Glow (Luminous halo for high visibility over dark ocean & ice)
      mapInstance.addLayer({
        id: 'antarctica-coastline-glow',
        type: 'line',
        source: 'antarctica-borders-source',
        filter: ['in', ['get', 'type'], ['literal', ['antarctic_coastline', 'ice_shelf_edge']]],
        layout: {
          visibility: showBorders ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#0284c7',
          'line-width': 4.5,
          'line-opacity': 0.60,
          'line-blur': 2.0
        }
      });

      // 5b. Antarctic Continental Coastline Core (Crisp, high-contrast platinum line)
      mapInstance.addLayer({
        id: 'antarctica-coastline-core',
        type: 'line',
        source: 'antarctica-borders-source',
        filter: ['==', ['get', 'type'], 'antarctic_coastline'],
        layout: {
          visibility: showBorders ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#ffffff',
          'line-width': 2.2,
          'line-opacity': 0.95
        }
      });

      // 5c. Antarctic Ice Shelf Frontiers (Floating Ice Shelf Barrier: Ross, Ronne, Amery)
      mapInstance.addLayer({
        id: 'antarctica-ice-shelf-edge',
        type: 'line',
        source: 'antarctica-borders-source',
        filter: ['==', ['get', 'type'], 'ice_shelf_edge'],
        layout: {
          visibility: showBorders ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#38bdf8',
          'line-width': 1.8,
          'line-opacity': 0.90,
          'line-dasharray': [4, 2]
        }
      });

      // 5d. Antarctic Treaty Boundary (60°S Parallel - Official International Treaty Border)
      mapInstance.addLayer({
        id: 'antarctica-treaty-border',
        type: 'line',
        source: 'antarctica-borders-source',
        filter: ['==', ['get', 'type'], 'antarctic_treaty_border'],
        layout: {
          visibility: showBorders ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#f59e0b',
          'line-width': 2.0,
          'line-opacity': 0.90,
          'line-dasharray': [6, 4]
        }
      });

      // 5e. Antarctic Circle (66.56°S Polar Circle)
      mapInstance.addLayer({
        id: 'antarctica-circle-border',
        type: 'line',
        source: 'antarctica-borders-source',
        filter: ['==', ['get', 'type'], 'antarctic_circle'],
        layout: {
          visibility: showBorders ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#c084fc',
          'line-width': 1.4,
          'line-opacity': 0.75,
          'line-dasharray': [3, 3]
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
            'fastest', '#38bdf8',
            'shortest', '#f59e0b',
            'safest', '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced', '#14b8a6',
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
            'fastest', '#38bdf8',
            'shortest', '#f59e0b',
            'safest', '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced', '#14b8a6',
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
            'fastest', '#38bdf8',
            'shortest', '#f59e0b',
            'safest', '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced', '#14b8a6',
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
            'fastest', 'FASTEST',
            'shortest', 'SHORTEST',
            'safest', 'SAFEST',
            'fuel_efficient', 'FUEL-EFF',
            'balanced', 'BALANCED',
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
            'fastest', '#60a5fa',
            'shortest', '#fbbf24',
            'safest', '#4ade80',
            'fuel_efficient', '#c084fc',
            'balanced', '#2dd4bf',
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

      // ---------------------------------------------------------
      // Route Voyage Simulation Layers (Traversing Grids & Explaining Choices)
      // ---------------------------------------------------------

      // 1. Current Traversed Grid Hexagon Fill
      mapInstance.addLayer({
        id: 'voyage-sim-grid-fill',
        type: 'fill',
        source: 'voyage-sim-grid-source',
        paint: {
          'fill-color': '#0284c7',
          'fill-opacity': 0.35
        }
      });

      // 2. Current Traversed Grid Hexagon Outline (Luminous cyan)
      mapInstance.addLayer({
        id: 'voyage-sim-grid-line',
        type: 'line',
        source: 'voyage-sim-grid-source',
        paint: {
          'line-color': '#38bdf8',
          'line-width': 3.0
        }
      });

      // 3. Candidate Decision Vectors (Green for chosen, Amber/Red for rejected adjacent grids)
      mapInstance.addLayer({
        id: 'voyage-sim-arrows-line',
        type: 'line',
        source: 'voyage-sim-arrows-source',
        paint: {
          'line-color': [
            'case',
            ['==', ['get', 'isChosen'], true], '#22c55e',
            ['==', ['get', 'verdict'], 'REJECTED'], '#ef4444',
            '#f59e0b'
          ],
          'line-width': [
            'case',
            ['==', ['get', 'isChosen'], true], 4.0,
            2.0
          ],
          'line-dasharray': [
            'case',
            ['==', ['get', 'isChosen'], true], ['literal', [1, 0]],
            ['literal', [2, 2]]
          ],
          'line-opacity': 0.90
        }
      });

      // 4. Simulated Traveling Vessel Halo
      mapInstance.addLayer({
        id: 'voyage-sim-ship-halo',
        type: 'circle',
        source: 'voyage-sim-ship-source',
        paint: {
          'circle-radius': 18.0,
          'circle-color': '#38bdf8',
          'circle-opacity': 0.50,
          'circle-blur': 0.6
        }
      });

      // 5. Simulated Traveling Vessel Point
      mapInstance.addLayer({
        id: 'voyage-sim-ship-point',
        type: 'circle',
        source: 'voyage-sim-ship-source',
        paint: {
          'circle-radius': 8.0,
          'circle-color': '#ffffff',
          'circle-stroke-width': 3.5,
          'circle-stroke-color': '#0284c7'
        }
      });

      // 9. Antarctic Research Stations & Gateway Logistics Ports (Native WebGL layers, fixed permanently directly onto map)
      mapInstance.addSource('antarctic-stations-source', {
        type: 'geojson',
        data: antarcticStationsGeoJSON
      });

      // 9a. Station Glow Aura
      mapInstance.addLayer({
        id: 'antarctic-stations-glow',
        type: 'circle',
        source: 'antarctic-stations-source',
        paint: {
          'circle-radius': [
            'case',
            ['==', ['get', 'isIndian'], true], 12.0,
            ['==', ['get', 'isPort'], true], 9.0,
            7.0
          ],
          'circle-color': ['get', 'color'],
          'circle-opacity': 0.40,
          'circle-blur': 0.6
        }
      });

      // 9b. Station Core Dot
      mapInstance.addLayer({
        id: 'antarctic-stations-point',
        type: 'circle',
        source: 'antarctic-stations-source',
        paint: {
          'circle-radius': [
            'case',
            ['==', ['get', 'isIndian'], true], 6.0,
            ['==', ['get', 'isPort'], true], 5.0,
            4.0
          ],
          'circle-color': ['get', 'color'],
          'circle-stroke-width': 2.0,
          'circle-stroke-color': '#ffffff'
        }
      });

      // 9c. Station Name Labels — 100% Fixed directly on the map surface in WebGL
      mapInstance.addLayer({
        id: 'antarctic-stations-label',
        type: 'symbol',
        source: 'antarctic-stations-source',
        layout: {
          'text-field': ['get', 'label'],
          'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
          'text-size': [
            'case',
            ['==', ['get', 'isIndian'], true], 11.5,
            ['==', ['get', 'isPort'], true], 10.5,
            9.5
          ],
          'text-anchor': 'left',
          'text-offset': [0.9, 0],
          'text-allow-overlap': true,
          'text-ignore-placement': true,
          'text-keep-upright': true
        },
        paint: {
          'text-color': isLight ? '#0f172a' : '#f8fafc',
          'text-halo-color': isLight ? 'rgba(255, 255, 255, 0.95)' : 'rgba(3, 7, 18, 0.95)',
          'text-halo-width': 2.5
        }
      });

      // Interactive Click & Hover handlers for Stations
      ['antarctic-stations-point', 'antarctic-stations-label'].forEach((layerId) => {
        mapInstance.on('mouseenter', layerId, () => {
          mapInstance.getCanvas().style.cursor = 'pointer';
        });
        mapInstance.on('mouseleave', layerId, () => {
          mapInstance.getCanvas().style.cursor = '';
        });
        mapInstance.on('click', layerId, (e) => {
          if (!e.features || e.features.length === 0) return;
          const feat = e.features[0];
          const props = feat.properties || {};
          const coords = (feat.geometry as any).coordinates;
          const st = ANTARCTIC_STATIONS.find((s) => s.id === props.id);
          if (!st) return;

          new maplibregl.Popup({ offset: 14, closeButton: true, className: 'station-info-popup' })
            .setLngLat(coords)
            .setHTML(`
              <div style="color: ${isLight ? '#0f172a' : '#f8fafc'}; background: ${isLight ? '#ffffff' : '#0d1117'}; padding: 10px 14px; font-family: system-ui, -apple-system, sans-serif; min-width: 250px; border-radius: 6px; box-shadow: 0 8px 24px rgba(0,0,0,0.45);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                  <span style="font-size: 9.5px; color: ${st.color}; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
                    ${st.category}
                  </span>
                  <span style="font-size: 9.5px; background: ${isLight ? '#f1f5f9' : '#1e293b'}; color: ${isLight ? '#475569' : '#94a3b8'}; padding: 2px 6px; border-radius: 3px; font-weight: 700;">
                    ${st.country} (${st.countryCode})
                  </span>
                </div>
                <div style="font-size: 13px; font-weight: 800; color: ${isLight ? '#0f172a' : '#ffffff'}; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                  <span>${st.symbol}</span>
                  <span>${st.name}</span>
                </div>
                <div style="font-size: 10px; color: ${isLight ? '#475569' : '#94a3b8'}; line-height: 1.45; margin-bottom: 8px;">
                  ${st.description}
                </div>
                <div style="font-size: 9.5px; font-family: monospace; background: ${isLight ? '#f0f9ff' : '#161b22'}; padding: 4px 8px; border: 1px solid ${isLight ? '#bfdbfe' : '#30363d'}; border-radius: 4px; color: ${isLight ? '#0369a1' : '#38bdf8'}; display: flex; justify-content: space-between; margin-bottom: 8px;">
                  <span>POSITION:</span>
                  <span>${Math.abs(st.coords[1]).toFixed(2)}°S, ${st.coords[0] >= 0 ? `${st.coords[0].toFixed(2)}°E` : `${Math.abs(st.coords[0]).toFixed(2)}°W`}</span>
                </div>
                <div style="display: flex; gap: 6px; margin-top: 8px;">
                  <button onclick="window.setAMIPOrigin('${st.id}')" style="flex: 1; background: #22c55e; color: #000; border: none; padding: 5px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; cursor: pointer;">Set Starting Point (A)</button>
                  <button onclick="window.setAMIPDest('${st.id}')" style="flex: 1; background: #ef4444; color: #fff; border: none; padding: 5px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; cursor: pointer;">Set Ending Point (B)</button>
                </div>
              </div>
            `)
            .addTo(mapInstance);
        });
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

  // Update Voyage Simulation Sources
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('voyage-sim-grid-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(voyageSimGridGeoJSON);
    } catch {}
  }, [voyageSimGridGeoJSON]);

  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('voyage-sim-arrows-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(voyageSimArrowsGeoJSON);
    } catch {}
  }, [voyageSimArrowsGeoJSON]);

  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('voyage-sim-ship-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') source.setData(voyageSimShipGeoJSON);
    } catch {}
  }, [voyageSimShipGeoJSON]);

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

  // Dynamic Source Update: Stations (Disappear when routes/endpoints are active, reappear when cleared)
  useEffect(() => {
    if (!map.current) return;
    try {
      const source = map.current.getSource('antarctic-stations-source') as maplibregl.GeoJSONSource;
      if (source && typeof source.setData === 'function') {
        source.setData(antarcticStationsGeoJSON);
      }
    } catch {}
  }, [antarcticStationsGeoJSON]);

  // Update station label theme paint properties on theme change
  useEffect(() => {
    if (!map.current) return;
    try {
      if (map.current.getLayer('antarctic-stations-label')) {
        map.current.setPaintProperty('antarctic-stations-label', 'text-color', isLight ? '#0f172a' : '#f8fafc');
        map.current.setPaintProperty('antarctic-stations-label', 'text-halo-color', isLight ? 'rgba(255, 255, 255, 0.95)' : 'rgba(3, 7, 18, 0.95)');
      }
    } catch {}
  }, [isLight]);

  // Canonical Mission Nodes: Display Cape Town, Bharati, and Maitri ONLY when a canonical corridor is active
  useEffect(() => {
    if (!map.current) return;
    missionNodesRef.current.forEach((m) => m.remove());
    missionNodesRef.current = [];

    // Only render canonical nodes if routes are active and we are NOT in custom A->B mode
    if (areRoutesActive && (!customOriginDest || (!customOriginDest.origin && !customOriginDest.dest))) {
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
        el.style.background = isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(15, 23, 42, 0.94)';
        el.style.border = `1.5px solid ${node.iconColor}`;
        el.style.borderBottom = `3px solid ${node.iconColor}`;
        el.style.borderRadius = '3px';
        el.style.color = isLight ? '#0f172a' : '#f8fafc';
        el.style.fontFamily = 'monospace';
        el.style.fontSize = '10px';
        el.style.fontWeight = '800';
        el.style.cursor = 'pointer';
        el.style.boxShadow = `0 2px 8px rgba(0,0,0,0.5), 0 0 6px ${node.iconColor}55`;
        el.innerHTML = `<span style="color:${node.iconColor};font-size:11px;">${node.symbol}</span><span>${node.name}</span>`;

        const m = new maplibregl.Marker({ element: el })
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
          .addTo(map.current!);
        missionNodesRef.current.push(m);
      });
    }
  }, [areRoutesActive, customOriginDest, isLight]);

  // Dynamic Terminus Station Markers & Auto-Framing when Custom Voyage is Planned
  useEffect(() => {
    if (!map.current) return;

    // Clear any previous dynamic terminus markers
    dynamicMarkersRef.current.forEach((m) => m.remove());
    dynamicMarkersRef.current = [];

    if (!customOriginDest || (!customOriginDest.origin && !customOriginDest.dest)) {
      return;
    }

    const { origin, dest } = customOriginDest;
    const newMarkers: maplibregl.Marker[] = [];

    // Green Origin Marker (A)
    if (origin && origin.coords) {
      const el = document.createElement('div');
      el.style.display = 'flex';
      el.style.alignItems = 'center';
      el.style.gap = '6px';
      el.style.padding = '4px 8px';
      el.style.background = 'rgba(15, 23, 42, 0.95)';
      el.style.border = '2px solid #22c55e';
      el.style.borderRadius = '5px';
      el.style.color = '#ffffff';
      el.style.fontFamily = 'monospace';
      el.style.fontSize = '11px';
      el.style.fontWeight = 'bold';
      el.style.boxShadow = '0 4px 16px rgba(34, 197, 94, 0.6)';
      el.style.cursor = 'pointer';
      el.innerHTML = `<span style="background:#22c55e;color:#000;padding:1px 5px;border-radius:3px;font-weight:900;">A</span><span>${origin.name}</span>`;

      const m = new maplibregl.Marker({ element: el })
        .setLngLat(origin.coords)
        .addTo(map.current);
      newMarkers.push(m);
    }

    // Red Destination Marker (B)
    if (dest && dest.coords) {
      const el = document.createElement('div');
      el.style.display = 'flex';
      el.style.alignItems = 'center';
      el.style.gap = '6px';
      el.style.padding = '4px 8px';
      el.style.background = 'rgba(15, 23, 42, 0.95)';
      el.style.border = '2px solid #ef4444';
      el.style.borderRadius = '5px';
      el.style.color = '#ffffff';
      el.style.fontFamily = 'monospace';
      el.style.fontSize = '11px';
      el.style.fontWeight = 'bold';
      el.style.boxShadow = '0 4px 16px rgba(239, 68, 68, 0.6)';
      el.style.cursor = 'pointer';
      el.innerHTML = `<span style="background:#ef4444;color:#fff;padding:1px 5px;border-radius:3px;font-weight:900;">B</span><span>${dest.name}</span>`;

      const m = new maplibregl.Marker({ element: el })
        .setLngLat(dest.coords)
        .addTo(map.current);
      newMarkers.push(m);
    }

    dynamicMarkersRef.current = newMarkers;

    // Smoothly fly camera to encompass the new custom route geometry
    if (routes && routes.length > 0 && routes[0].waypoints && routes[0].waypoints.length > 0) {
      try {
        let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity;
        routes[0].waypoints.forEach(([lon, lat]) => {
          if (lon < minLon) minLon = lon;
          if (lon > maxLon) maxLon = lon;
          if (lat < minLat) minLat = lat;
          if (lat > maxLat) maxLat = lat;
        });

        if (origin?.coords) {
          minLon = Math.min(minLon, origin.coords[0]);
          maxLon = Math.max(maxLon, origin.coords[0]);
          minLat = Math.min(minLat, origin.coords[1]);
          maxLat = Math.max(maxLat, origin.coords[1]);
        }

        if (dest?.coords) {
          minLon = Math.min(minLon, dest.coords[0]);
          maxLon = Math.max(maxLon, dest.coords[0]);
          minLat = Math.min(minLat, dest.coords[1]);
          maxLat = Math.max(maxLat, dest.coords[1]);
        }

        if (isFinite(minLon) && isFinite(minLat) && isFinite(maxLon) && isFinite(maxLat)) {
          map.current.fitBounds(
            [
              [minLon, minLat],
              [maxLon, maxLat]
            ],
            {
              padding: { top: 90, bottom: 90, left: 90, right: 390 },
              maxZoom: 5.0,
              duration: 1200
            }
          );
        }
      } catch (err) {
        console.warn('Could not fit bounds to custom voyage:', err);
      }
    }
  }, [customOriginDest, routes]);

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



  // Update H3 Hexagon Grid Layer Visibility (lines and selection only, decoupled from SIC)
  useEffect(() => {
    if (!map.current) return;
    try {
      const vis = showH3Grid ? 'visible' : 'none';
      const h3Layers = [
        'canonical-h3-lines',
        'canonical-h3-hit',
        'canonical-h3-selected-line'
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

  // Update Dedicated Sea Ice Concentration (SIC) Layer Visibility across entire Antarctic grid
  useEffect(() => {
    if (!map.current) return;
    try {
      const vis = showSIC ? 'visible' : 'none';
      if (map.current.getLayer('display-aggregated-sic-fill')) {
        map.current.setLayoutProperty('display-aggregated-sic-fill', 'visibility', vis);
      }
      if (map.current.getLayer('display-aggregated-sic-edge')) {
        map.current.setLayoutProperty('display-aggregated-sic-edge', 'visibility', vis);
      }
    } catch {
      // style pending
    }
  }, [showSIC]);

  // Update Antarctic Borders & Coastline Layers Visibility
  useEffect(() => {
    if (!map.current) return;
    try {
      const vis = showBorders ? 'visible' : 'none';
      const borderLayers = [
        'antarctica-coastline-glow',
        'antarctica-coastline-core',
        'antarctica-ice-shelf-edge',
        'antarctica-treaty-border',
        'antarctica-circle-border'
      ];
      borderLayers.forEach((layerId) => {
        if (map.current?.getLayer(layerId)) {
          map.current.setLayoutProperty(layerId, 'visibility', vis);
        }
      });
    } catch {
      // style pending
    }
  }, [showBorders]);


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

        {/* Top-Left Oceanographic Status Banner & Voyage Simulator Button */}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: isLight ? 'rgba(255, 255, 255, 0.94)' : 'rgba(13, 17, 23, 0.92)',
              backdropFilter: 'blur(10px)',
              padding: '6px 12px',
              borderRadius: '6px',
              border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
              boxShadow: isLight ? '0 4px 16px rgba(14, 165, 233, 0.15)' : '0 4px 16px rgba(0,0,0,0.4)',
              pointerEvents: 'auto'
            }}>
              <Compass size={14} color={isLight ? '#0284c7' : '#38bdf8'} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: isLight ? '#0f172a' : '#f0f6fc', letterSpacing: '0.2px' }}>
                ISE-44 Polar Navigation Mesh
              </span>
              <span style={{ fontSize: '10px', color: isLight ? '#475569' : '#8b949e', borderLeft: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`, paddingLeft: '8px' }}>
                Day T+{sliderDay} ({currentHz}) · {icebergsList.length} Tracked Icebergs
              </span>
            </div>

            {/* Prominent Voyage & Grid Decision Simulator Button */}
            <button
              onClick={() => {
                if (!activeRouteId && routes.length > 0) {
                  setSelectedRouteId(routes[0].id);
                  if (onSelectRoute) onSelectRoute(routes[0].id);
                }
                setIsVoyageSimOpen((open) => {
                  if (!open) setIsVoyagePlaying(true);
                  return !open;
                });
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '7px',
                padding: '6px 12px',
                background: isVoyageSimOpen
                  ? (isLight ? '#0284c7' : '#1f6feb')
                  : (isLight ? 'rgba(255, 255, 255, 0.95)' : 'rgba(13, 17, 23, 0.92)'),
                backdropFilter: 'blur(10px)',
                border: `1px solid ${
                  isVoyageSimOpen
                    ? (isLight ? '#0369a1' : '#388bfd')
                    : (isLight ? '#bfdbfe' : '#30363d')
                }`,
                borderRadius: '6px',
                color: isVoyageSimOpen ? '#ffffff' : (isLight ? '#0f172a' : '#f0f6fc'),
                fontSize: '11px',
                fontWeight: 600,
                fontFamily: 'system-ui, -apple-system, sans-serif',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                pointerEvents: 'auto'
              }}
              onMouseEnter={(e) => {
                if (!isVoyageSimOpen) {
                  e.currentTarget.style.background = isLight ? '#f0f9ff' : '#21262d';
                  e.currentTarget.style.borderColor = isLight ? '#7dd3fc' : '#8b949e';
                }
              }}
              onMouseLeave={(e) => {
                if (!isVoyageSimOpen) {
                  e.currentTarget.style.background = isLight ? 'rgba(255, 255, 255, 0.95)' : 'rgba(13, 17, 23, 0.92)';
                  e.currentTarget.style.borderColor = isLight ? '#bfdbfe' : '#30363d';
                }
              }}
            >
              <Ship size={14} color={isVoyageSimOpen ? '#ffffff' : (isLight ? '#0284c7' : '#58a6ff')} />
              <span>
                {isVoyageSimOpen
                  ? (isVoyagePlaying ? 'Pause Simulation' : 'Resume Simulation')
                  : 'Simulate Route Voyage'}
              </span>
              <span
                style={{
                  fontSize: '9px',
                  background: isVoyageSimOpen
                    ? 'rgba(255, 255, 255, 0.25)'
                    : (isLight ? 'rgba(2, 132, 199, 0.12)' : 'rgba(56, 189, 248, 0.12)'),
                  color: isVoyageSimOpen ? '#ffffff' : (isLight ? '#0284c7' : '#38bdf8'),
                  border: `1px solid ${
                    isVoyageSimOpen
                      ? 'rgba(255, 255, 255, 0.3)'
                      : (isLight ? 'rgba(2, 132, 199, 0.25)' : 'rgba(56, 189, 248, 0.25)')
                  }`,
                  padding: '1px 5px',
                  borderRadius: '3px',
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  letterSpacing: '0.4px'
                }}
              >
                GRID EXPLAINABILITY
              </span>
            </button>
          </div>

          {hoveredCellData && (
            <div style={{
              background: isLight ? 'rgba(255, 255, 255, 0.94)' : 'rgba(13, 17, 23, 0.92)',
              backdropFilter: 'blur(10px)',
              padding: '4px 10px',
              borderRadius: '4px',
              border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`,
              fontSize: '10px',
              color: isLight ? '#475569' : '#8b949e',
              pointerEvents: 'auto'
            }}>
              Cell <strong style={{ color: isLight ? '#0f172a' : '#f0f6fc', fontFamily: 'monospace' }}>{hoveredCellData.displayId}</strong> · SIC: <strong style={{ color: isLight ? '#0284c7' : '#38bdf8' }}>{hoveredCellData.sic_pct ?? 0}%</strong> · Depth: <strong style={{ color: isLight ? '#0f172a' : '#f0f6fc' }}>{hoveredCellData.depth?.toFixed(0) ?? 3400}m</strong>
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
            background: isLight ? 'rgba(255, 255, 255, 0.95)' : 'rgba(13, 17, 23, 0.94)',
            backdropFilter: 'blur(12px)',
            border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
            borderRadius: '8px',
            padding: '10px',
            minWidth: '280px',
            boxShadow: isLight ? '0 8px 24px rgba(14, 165, 233, 0.12)' : '0 8px 24px rgba(0,0,0,0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', paddingBottom: '6px', borderBottom: `1px solid ${isLight ? '#e0f2fe' : '#21262d'}` }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, color: isLight ? '#0f172a' : '#f0f6fc', letterSpacing: '0.3px', textTransform: 'uppercase' }}>
                  Voyage Alternatives
                </span>
                <span style={{ fontSize: '9.5px', color: isLight ? '#64748b' : '#8b949e', marginLeft: '6px' }}>
                  5 Corridors
                </span>
              </div>
              {areRoutesActive ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedRouteId('');
                    setCustomOriginDest(null);
                    if (onSelectRoute) onSelectRoute('');
                  }}
                  style={{
                    fontSize: '9.5px',
                    padding: '2px 7px',
                    borderRadius: '4px',
                    background: isLight ? '#fee2e2' : 'rgba(239, 68, 68, 0.16)',
                    color: isLight ? '#b91c1c' : '#fca5a5',
                    border: `1px solid ${isLight ? '#fca5a5' : 'rgba(239, 68, 68, 0.4)'}`,
                    cursor: 'pointer',
                    fontWeight: 700,
                    transition: 'all 0.15s ease'
                  }}
                  title="Deselect route to return to clean station overview"
                >
                  Clear Route
                </button>
              ) : (
                <span style={{ fontSize: '9px', color: isLight ? '#0284c7' : '#38bdf8', fontWeight: 600 }}>
                  Station View
                </span>
              )}
            </div>

            {!areRoutesActive && (
              <div style={{
                fontSize: '10px',
                color: isLight ? '#475569' : '#8b949e',
                background: isLight ? '#f0f9ff' : 'rgba(56, 189, 248, 0.08)',
                border: `1px dashed ${isLight ? '#bae6fd' : '#1e3a5f'}`,
                borderRadius: '4px',
                padding: '5px 8px',
                marginBottom: '6px',
                lineHeight: 1.35
              }}>
                Displaying all Antarctic stations. Choose a corridor below or plan custom voyage to plot all route options.
              </div>
            )}

            {/* Route rows */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {routes.map((r) => {
                const isSelected = Boolean(activeRouteId) && r.id === activeRouteId;
                const isVisible = areRoutesActive ? (enabledRoutes[r.id] !== false) : false;
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
                      background: isSelected
                        ? (isLight ? 'rgba(2, 132, 199, 0.12)' : 'rgba(56, 189, 248, 0.10)')
                        : (isLight ? 'rgba(240, 249, 255, 0.6)' : 'rgba(255, 255, 255, 0.02)'),
                      border: isSelected
                        ? `1px solid ${color}88`
                        : (isLight ? '1px solid #e0f2fe' : '1px solid transparent'),
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      opacity: isVisible ? 1.0 : (activeRouteId ? 0.40 : 0.75)
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '11.5px', fontWeight: isSelected ? 700 : 600, color: isSelected ? (isLight ? '#0284c7' : '#ffffff') : (isLight ? '#0f172a' : '#c9d1d9') }}>
                          {(r.objective || r.id).replace('_', ' ')}
                        </span>
                        {isSelected && (
                          <span style={{ fontSize: '8.5px', background: color, color: '#090d16', padding: '1px 5px', borderRadius: '3px', fontWeight: 800 }}>
                            ACTIVE
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '10px', color: isLight ? '#475569' : '#8b949e', marginTop: '2px' }}>
                        {sailDays.toFixed(1)}d sail · {(r.durationDays ?? 0).toFixed(1)}d total · {(r.estimatedFuelMT || 0).toFixed(0)} MT
                      </div>
                    </div>

                    {/* Eye toggle */}
                    <button
                      onClick={(ev) => {
                        ev.stopPropagation();
                        if (!activeRouteId) {
                          setSelectedRouteId(r.id);
                          if (onSelectRoute) onSelectRoute(r.id);
                        } else {
                          toggleRouteVisibility(r.id, ev);
                        }
                      }}
                      title={isVisible ? `Hide ${r.name}` : `Show ${r.name}`}
                      style={{
                        background: isVisible ? (isLight ? 'rgba(2, 132, 199, 0.10)' : 'rgba(255,255,255,0.06)') : (isLight ? 'transparent' : 'rgba(255,255,255,0.02)'),
                        border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`,
                        borderRadius: '3px',
                        cursor: 'pointer',
                        padding: '3px 6px',
                        display: 'flex',
                        alignItems: 'center',
                        color: isVisible ? (isLight ? '#0284c7' : '#f0f6fc') : (isLight ? '#94a3b8' : '#484f58'),
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
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px 8px' }}>
                {[
                  { label: 'Distance', value: `${(selectedRoute.distanceNM || 0).toLocaleString()} NM` },
                  { label: 'Sailing', value: `${((selectedRoute as any).sailingDays ?? selectedRoute.transitDays ?? 0).toFixed(1)} d` },
                  { label: 'Total', value: `${(selectedRoute.durationDays ?? 0).toFixed(1)} d` },
                  { label: 'Fuel', value: `${(selectedRoute.estimatedFuelMT || 0).toFixed(0)} MT` },
                  { label: 'Speed', value: `${((selectedRoute as any).meanSOG ?? 0).toFixed(1)} kt` },
                  { label: 'Risk', value: `${((selectedRoute.meanRisk || 0) * 100).toFixed(0)}%` },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div style={{ fontSize: '9px', color: isLight ? '#64748b' : '#8b949e', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc', marginTop: '1px' }}>{value}</div>
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
            background: isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(13, 17, 23, 0.90)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
            borderRadius: '6px',
            boxShadow: isLight ? '0 4px 16px rgba(14, 116, 144, 0.12)' : '0 4px 16px rgba(0, 0, 0, 0.4)',
            padding: '8px 12px',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            fontSize: '11px',
            color: isLight ? '#0f172a' : '#f0f6fc',
            minWidth: '170px'
          }}>
            <div style={{ fontWeight: 700, fontSize: '10px', letterSpacing: '0.4px', marginBottom: '6px', color: isLight ? '#0284c7' : '#8b949e', textTransform: 'uppercase' }}>
              Sea Ice Concentration
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div style={{
                width: '10px',
                height: '80px',
                borderRadius: '2px',
                background: 'linear-gradient(to top, #0b1d3a 0%, #1e4d7b 5%, #2e7d9e 15%, #4a9bc7 30%, #6baed6 50%, #9ecae1 70%, #c6dbef 85%, #e6f2ff 95%, #ffffff 100%)',
                border: isLight ? '1px solid #cbd5e1' : '1px solid rgba(255,255,255,0.15)'
              }} />
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '80px', fontSize: '9.5px', color: isLight ? '#475569' : '#8b949e', fontWeight: isLight ? 600 : 400 }}>
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
            background: isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(13, 17, 23, 0.90)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
            borderRadius: '6px',
            boxShadow: isLight ? '0 4px 16px rgba(14, 116, 144, 0.12)' : '0 4px 16px rgba(0, 0, 0, 0.4)',
            padding: '6px 10px',
            fontSize: '9.5px',
            color: isLight ? '#475569' : '#8b949e',
            lineHeight: '1.4'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
              <img
                src="/amip_logo.jpg"
                alt="AMIP Logo"
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '4px',
                  objectFit: 'cover',
                  border: `1px solid ${isLight ? '#bfdbfe' : 'rgba(56,189,248,0.4)'}`
                }}
              />
              <div style={{ fontWeight: 700, color: isLight ? '#0284c7' : '#38bdf8' }}>AMIP Polar Model</div>
            </div>
            <div style={{ color: isLight ? '#0f172a' : '#c9d1d9' }}>Vessel: ORV Sagar Kanya (ISE-44)</div>
            <div style={{ color: isLight ? '#0f172a' : '#c9d1d9' }}>Bunker: 433 m³ (368 MT capacity)</div>
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
            background: isLight ? '#ffffff' : '#0d1117',
            border: `1px solid ${isLight ? '#bae6fd' : '#30363d'}`,
            borderRadius: '8px',
            boxShadow: isLight ? '0 12px 36px rgba(14, 165, 233, 0.15)' : '0 12px 36px rgba(0,0,0,0.65)',
            zIndex: 40,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            color: isLight ? '#0f172a' : '#f0f6fc'
          }}>
            {/* Inspector Header */}
            <div style={{
              padding: '10px 14px',
              background: isLight ? '#e0f2fe' : '#161b22',
              borderBottom: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Compass size={14} color={isLight ? '#0284c7' : '#38bdf8'} />
                <span style={{ fontSize: '12px', fontWeight: 700, color: isLight ? '#0f172a' : '#f0f6fc', letterSpacing: '0.2px' }}>
                  {activeInspector === 'cell' && 'H3 Hexagonal Cell Telemetry'}
                  {activeInspector === 'iceberg' && 'NIC Iceberg Target Telemetry'}
                  {activeInspector === 'segment' && 'Mission Route Segment Telemetry'}
                </span>
              </div>
              <button
                onClick={() => {
                  setSelectedH3Cell(null);
                  setSelectedIceberg(null);
                  setSelectedSegment(null);
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: isLight ? '#64748b' : '#8b949e',
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
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '11px', background: isLight ? '#ffffff' : 'transparent', color: isLight ? '#0f172a' : '#f0f6fc' }}>

              {/* 1. H3 CELL INSPECTOR */}
              {activeInspector === 'cell' && selectedH3Cell && (
                <>
                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Cell Identity</div>
                    <div>H3 Index: <strong style={{ color: isLight ? '#0284c7' : '#38bdf8', fontFamily: 'monospace' }}>{selectedH3Cell.id}</strong></div>
                    <div>Coordinates: <span style={{ fontFamily: 'monospace' }}>{Math.abs(selectedH3Cell.properties.lat ?? 0).toFixed(4)}°S, {(selectedH3Cell.properties.lon ?? 0).toFixed(4)}°E</span></div>
                  </div>

                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Sea Ice Assessment</div>
                    <div>Concentration: <strong style={{ color: isLight ? '#0284c7' : '#38bdf8' }}>{((selectedH3Cell.properties.sic ?? 0) * 100).toFixed(1)}%</strong></div>
                    <div>Ice Regime: <strong>{
                      (selectedH3Cell.properties.sic ?? 0) === 0 ? 'Open Water'
                        : (selectedH3Cell.properties.sic ?? 0) < 0.15 ? 'Marginal Ice Zone'
                          : (selectedH3Cell.properties.sic ?? 0) < 0.50 ? 'Moderate Pack Ice'
                            : (selectedH3Cell.properties.sic ?? 0) < 0.80 ? 'Dense Pack Ice'
                              : 'Fast Ice'
                    }</strong></div>
                    <div>Limit: 15.0% SIC (Vessel Operational Threshold)</div>
                  </div>

                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Navigational Clearance</div>
                    <div>Navigable: <strong style={{ color: selectedH3Cell.properties.is_land ? '#ef4444' : '#22c55e' }}>
                      {selectedH3Cell.properties.is_land ? 'No (Land Mass)' : (selectedH3Cell.properties.sic ?? 0) > 0.15 ? 'Ice Constrained (SIC > 15%)' : 'Yes (Open Water)'}
                    </strong></div>
                    <div>Depth: {selectedH3Cell.properties.depth?.toFixed(1) ?? '3400.0'} m</div>
                    <div>Under-Keel Clearance: {selectedH3Cell.properties.under_keel_clearance?.toFixed(1) ?? '3394.4'} m</div>
                  </div>

                  {/* Collapsible Ocean Physics */}
                  <div style={{ border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`, borderRadius: '5px', overflow: 'hidden' }}>
                    <div
                      onClick={() => toggleSection('ocean')}
                      style={{ padding: '8px 10px', background: isLight ? '#e0f2fe' : '#161b22', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                    >
                      <span style={{ color: isLight ? '#0f172a' : '#f0f6fc', fontWeight: 600, fontSize: '10.5px' }}>Oceanographic Metocean Data</span>
                      {expandedSections.ocean ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </div>
                    {expandedSections.ocean && (
                      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '4px', background: isLight ? '#f8fafc' : '#0d1117', fontSize: '10.5px', color: isLight ? '#334155' : '#c9d1d9' }}>
                        <div>Waves: {selectedH3Cell.properties.wave_height?.toFixed(2) ?? '2.80'} m (Dir: {selectedH3Cell.properties.wave_direction?.toFixed(0) ?? '270'}°)</div>
                        <div>Wind: {selectedH3Cell.properties.wind_speed?.toFixed(2) ?? '8.50'} m/s (Dir: {selectedH3Cell.properties.wind_direction?.toFixed(0) ?? '225'}°)</div>
                        <div>Current: {selectedH3Cell.properties.current_magnitude?.toFixed(3) ?? '0.180'} m/s (Dir: {selectedH3Cell.properties.current_direction?.toFixed(0) ?? '240'}°)</div>
                        <div>Icebergs: {selectedH3Cell.properties.iceberg_count ?? 0} in proximity</div>
                      </div>
                    )}
                  </div>

                  {/* Collapsible Risk Components */}
                  <div style={{ border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`, borderRadius: '5px', overflow: 'hidden' }}>
                    <div
                      onClick={() => toggleSection('risk')}
                      style={{ padding: '8px 10px', background: isLight ? '#e0f2fe' : '#161b22', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                    >
                      <span style={{ color: isLight ? '#0f172a' : '#f0f6fc', fontWeight: 600, fontSize: '10.5px' }}>Environmental Risk Breakdown</span>
                      {expandedSections.risk ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </div>
                    {expandedSections.risk && (
                      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '4px', background: isLight ? '#f8fafc' : '#0d1117', fontSize: '10.5px', color: isLight ? '#334155' : '#c9d1d9' }}>
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
                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase' }}>Target Classification</span>
                      <span style={{ color: '#f97316', fontSize: '9px', fontWeight: 700, fontFamily: 'monospace', background: 'rgba(249,115,22,0.15)', padding: '1px 5px', borderRadius: '3px', border: '1px solid rgba(249,115,22,0.4)' }}>
                        DAY T+{sliderDay}
                      </span>
                    </div>
                    <div>Target ID: <strong style={{ color: '#f97316', fontFamily: 'monospace' }}>{selectedIceberg.id}</strong></div>
                    <div>Live Position: <span style={{ fontFamily: 'monospace', color: isLight ? '#0f172a' : '#f0f6fc' }}>{activeIcebergLive ? `${Math.abs(activeIcebergLive.coords[1]).toFixed(4)}°S, ${activeIcebergLive.coords[0].toFixed(4)}°E` : 'Active'}</span></div>
                    <div>Source: {selectedIceberg.source || 'NIC Antarctic Tracked Database'}</div>
                  </div>

                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Kinematics & Drift</div>
                    <div>Cumulative Drift: <strong style={{ color: isLight ? '#0284c7' : '#38bdf8' }}>{activeIcebergLive?.driftedNM ?? 0.0} NM</strong> <span style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px' }}>(from T+0)</span></div>
                    <div>Drift Velocity: <strong>{activeIcebergLive?.speed ?? 0.24} kt</strong></div>
                    <div>Water Depth: <strong>{activeIcebergLive?.depth ?? 3200} m</strong></div>
                    <div>Dimensions: {(selectedIceberg.latestObservation?.length_km ?? 15).toFixed(0)} × {(selectedIceberg.latestObservation?.width_km ?? 8).toFixed(0)} km</div>
                    <div>Surface Area: {(selectedIceberg.latestObservation?.area_sqkm ?? 120).toFixed(0)} km²</div>
                  </div>

                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Trajectory & Marine Hazard</div>
                    <div>Horizon: <strong>90-Day High-Resolution Drift</strong></div>
                    <div>Drift Model Status: <span style={{ color: '#22c55e', fontWeight: 700 }}>{activeIcebergLive?.status || 'ACTIVE_DRIFT'}</span></div>
                    <div>Route Hazard: <span style={{ color: '#f97316', fontWeight: 600 }}>Tracked along Southern Ocean Route Corridor</span></div>
                  </div>
                </>
              )}

              {/* 3. ROUTE SEGMENT INSPECTOR */}
              {activeInspector === 'segment' && selectedSegment && (
                <>
                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Segment Navigation</div>
                    <div>From Cell: <strong style={{ color: isLight ? '#0284c7' : '#38bdf8', fontFamily: 'monospace' }}>{selectedSegment.from_cell || selectedSegment.from_h3 || '85ad3617fffffff'}</strong></div>
                    <div>To Cell: <strong style={{ color: isLight ? '#0284c7' : '#38bdf8', fontFamily: 'monospace' }}>{selectedSegment.to_cell || selectedSegment.to_h3 || '85bc6117fffffff'}</strong></div>
                    <div>Leg Distance: {(selectedSegment.distance_nm ?? selectedSegment.distanceNM ?? 0).toFixed(2)} NM</div>
                    <div>True Heading: {(selectedSegment.heading_deg ?? 0).toFixed(1)}°</div>
                  </div>

                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Propulsion & Effective Speed</div>
                    <div>Engine STW: <strong>{(selectedSegment.stw_kt ?? selectedSegment.vessel_stw_kt ?? 9.0).toFixed(2)} kt</strong></div>
                    <div>Ocean Current Along-Track: <strong>{(selectedSegment.current_along_track_kt ?? 0.0).toFixed(2)} kt</strong></div>
                    <div>Resulting SOG: <strong style={{ color: isLight ? '#0284c7' : '#38bdf8' }}>{(selectedSegment.sog_kt ?? selectedSegment.effective_speed_kt ?? 9.0).toFixed(2)} kt</strong></div>
                    <div>Transit Duration: {(selectedSegment.duration_hours ?? selectedSegment.segment_duration_hours ?? 0).toFixed(2)} hours</div>
                  </div>

                  <div style={{ background: isLight ? '#f0f9ff' : '#161b22', padding: '10px', borderRadius: '5px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
                    <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', marginBottom: '4px' }}>Metocean & Fuel Burn</div>
                    <div>SIC: {(selectedSegment.sic_pct ?? selectedSegment.sic_percent ?? 0).toFixed(1)}%</div>
                    <div>Wave Height: {(selectedSegment.wave_height_m ?? 2.8).toFixed(2)} m</div>
                    <div>Wind Speed: {(selectedSegment.wind_speed_kt ?? selectedSegment.wind_speed_ms ?? 8.5).toFixed(1)} kt</div>
                    <div>Fuel Consumption: <strong style={{ color: isLight ? '#0f172a' : '#f0f6fc' }}>{(selectedSegment.fuel_burn_mt ?? selectedSegment.fuel_mt ?? 0).toFixed(2)} MT</strong></div>
                    <div>Segment Risk: <strong style={{ color: (selectedSegment.risk_composite || selectedSegment.risk || 0) > 0.3 ? '#ef4444' : '#22c55e' }}>{(((selectedSegment.risk_composite ?? selectedSegment.risk ?? 0.1)) * 100).toFixed(1)}%</strong></div>
                  </div>
                </>
              )}

            </div>
          </div>
        )}

        {/* Floating Route Voyage Simulator HUD (Active when traveling along route) */}
        {isVoyageSimOpen && (
          <RouteVoyageSimulatorHUD
            step={voyageStep}
            isPlaying={isVoyagePlaying}
            playbackSpeed={voyageSpeed}
            followShip={followShip}
            onTogglePlay={() => {
              if (voyageProgress >= 1.0) setVoyageProgress(0.0);
              setIsVoyagePlaying((p) => !p);
            }}
            onStepPrev={handleStepPrev}
            onStepNext={handleStepNext}
            onReset={() => {
              setIsVoyagePlaying(false);
              setVoyageProgress(0.0);
            }}
            onScrub={(p) => {
              setIsVoyagePlaying(false);
              setVoyageProgress(p);
            }}
            onChangeSpeed={(spd) => setVoyageSpeed(spd)}
            onToggleFollow={() => setFollowShip((f) => !f)}
            onClose={() => {
              setIsVoyageSimOpen(false);
              setIsVoyagePlaying(false);
            }}
            theme={theme}
          />
        )}

      </div>

      {/* 9. Time Slider & Playback Controls Bar (T+0 to T+90 Days) */}
      <div style={{
        padding: '8px 16px',
        background: isLight ? '#ffffff' : '#0f172a',
        borderTop: `1px solid ${isLight ? '#bae6fd' : '#334155'}`,
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        zIndex: 30,
        boxShadow: isLight ? '0 -2px 10px rgba(14, 165, 233, 0.08)' : 'none'
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
                background: isTimelinePlaying ? '#ef4444' : (isLight ? '#0284c7' : '#2563eb'),
                border: '1px solid',
                borderColor: isTimelinePlaying ? '#dc2626' : (isLight ? '#0369a1' : '#1d4ed8'),
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
              <Calendar size={13} color={isLight ? '#0284c7' : '#38bdf8'} />
              <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'monospace', color: isLight ? '#0f172a' : '#f8fafc' }}>
                TIMELINE: <span style={{ color: isLight ? '#0284c7' : '#38bdf8' }}>T+{sliderDay} DAYS</span>
              </span>
              <span style={{ fontSize: '10px', color: isLight ? '#64748b' : '#94a3b8', fontFamily: 'monospace' }}>
                (Horizon: <strong style={{ color: '#22c55e' }}>{currentHz}</strong>)
              </span>
            </div>
          </div>

          {/* Quick-Jump Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '9px', color: isLight ? '#64748b' : '#8b949e', fontFamily: 'monospace', marginRight: '4px' }}>
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
                    background: isCurrent
                      ? (isLight ? '#0284c7' : '#2563eb')
                      : (isLight ? '#f0f9ff' : 'rgba(30, 41, 59, 0.7)'),
                    border: `1px solid ${
                      isCurrent
                        ? (isLight ? '#0369a1' : '#38bdf8')
                        : (isLight ? '#bfdbfe' : '#334155')
                    }`,
                    color: isCurrent ? '#ffffff' : (isLight ? '#0f172a' : '#cbd5e1'),
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
          <span style={{ fontSize: '9.5px', fontFamily: 'monospace', color: isLight ? '#64748b' : '#64748b' }}>T+0d</span>
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
              accentColor: isLight ? '#0284c7' : '#38bdf8',
              cursor: 'pointer'
            }}
          />
          <span style={{ fontSize: '9.5px', fontFamily: 'monospace', color: isLight ? '#64748b' : '#64748b' }}>T+90d</span>
        </div>
      </div>

    </div>
  );
};

export default AntarcticMap;

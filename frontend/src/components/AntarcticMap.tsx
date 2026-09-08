import React, { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import {
  Compass,
  Radio,
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

  // Sync external selectedHorizon changes into slider
  useEffect(() => {
    if (selectedHorizon && HORIZON_DAYS_MAP[selectedHorizon] !== undefined) {
      if (HORIZON_DAYS_MAP[selectedHorizon] !== sliderDay && !isTimelinePlaying) {
        setSliderDay(HORIZON_DAYS_MAP[selectedHorizon]);
      }
    }
  }, [selectedHorizon, isTimelinePlaying, sliderDay]);

  // Handle Play/Pause timer (800ms per day step)
  useEffect(() => {
    if (!isTimelinePlaying) return;
    const interval = setInterval(() => {
      setSliderDay((prev) => {
        const next = prev >= 90 ? 0 : prev + 1;
        const newHz = DAY_TO_NEAREST_HORIZON(next);
        if (newHz !== currentHz) {
          setTimeHorizon(newHz as any);
          if (onHorizonChange) onHorizonChange(newHz);
        }
        return next;
      });
    }, 800);
    return () => clearInterval(interval);
  }, [isTimelinePlaying, currentHz, setTimeHorizon, onHorizonChange]);

  const handleSliderChange = (day: number) => {
    setSliderDay(day);
    const newHz = DAY_TO_NEAREST_HORIZON(day);
    if (newHz !== currentHz) {
      setTimeHorizon(newHz as any);
      if (onHorizonChange) onHorizonChange(newHz);
    }
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
        geometry: feat.geometry
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

  // 5. Canonical Routes GeoJSON - Each route is a separate feature with its own color
  const canonicalRoutesGeoJSON = useMemo(() => {
    return {
      type: 'FeatureCollection',
      features: routes.map((r) => {
        const routeColor = STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6';
        const isSelected = r.id === activeRouteId;
        // Use numeric 1/0 for visibility so MapLibre filter works reliably
        const visibleNum = enabledRoutes[r.id] !== false ? 1 : 0;
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
            visibleNum,
            shortLabel: {
              fastest: 'FAST',
              shortest: 'SHORT',
              safest: 'SAFE',
              fuel_efficient: 'FUEL',
              balanced: 'BAL'
            }[r.id] || r.id.toUpperCase().slice(0, 4)
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

      // 6. Iceberg Trajectories (OFF by default, subtle 1px, selected 2px)
      mapInstance.addLayer({
        id: 'iceberg-trajectories-line',
        type: 'line',
        source: 'iceberg-trajectories-source',
        layout: {
          visibility: showTrajectories ? 'visible' : 'none',
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            'rgba(249, 115, 22, 0.60)',
            'rgba(249, 115, 22, 0.15)'
          ],
          'line-width': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            2.0,
            1.0
          ]
        }
      });

      // 7. Unselected Routes — subtle dashed lines, low opacity, no blur
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
            'fastest',        '#3b82f6',
            'shortest',       '#f59e0b',
            'safest',         '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced',       '#14b8a6',
            '#94a3b8'
          ],
          'line-width': 1.5,
          'line-opacity': 0.35,
          'line-dasharray': [5, 4]
        },
        filter: ['!=', ['get', 'id'], activeRouteId]
      });


      // 8. Selected Route Glow — white halo under the selected route
      mapInstance.addLayer({
        id: 'routes-selected-glow',
        type: 'line',
        source: 'canonical-routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#ffffff',
          'line-width': 10.0,
          'line-opacity': 0.55,
          'line-blur': 3.0
        },
        filter: ['==', ['get', 'id'], activeRouteId]
      });


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
            'fastest',        '#3b82f6',
            'shortest',       '#f59e0b',
            'safest',         '#22c55e',
            'fuel_efficient', '#a855f7',
            'balanced',       '#14b8a6',
            '#ffffff'
          ],
          'line-width': 5.0,
          'line-opacity': 1.0
        },
        filter: ['all', ['==', ['get', 'id'], activeRouteId], ['==', ['get', 'visibleNum'], 1]]

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
            'fuel_efficient', 'FUEL-EFFICIENT',
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
          'text-halo-color': '#000a1a',
          'text-halo-width': 2.0,
          'text-opacity': 1.0
        },
        filter: ['==', ['get', 'visibleNum'], 1]
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

      // 11. Iceberg Observation Points (~73 tracked bergs, 4px radius, #f97316, opacity 0.8)
      mapInstance.addLayer({
        id: 'icebergs-point',
        type: 'circle',
        source: 'icebergs-source',
        paint: {
          'circle-radius': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            8.0,
            4.0
          ],
          'circle-color': '#f97316',
          'circle-opacity': 0.80,
          'circle-stroke-width': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            2.0,
            0.5
          ],
          'circle-stroke-color': '#ffffff'
        }
      });

      // 13. Selected Iceberg Highlight (Yellow halo)
      mapInstance.addLayer({
        id: 'icebergs-selected-halo',
        type: 'circle',
        source: 'icebergs-source',
        paint: {
          'circle-radius': 16,
          'circle-color': '#fbbf24',
          'circle-opacity': 0.45,
          'circle-blur': 0.6
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

      // Hover Iceberg: 6px, opacity 1.0, tooltip ID: <id>
      mapInstance.on('mouseenter', 'icebergs-point', (e) => {
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
          .setHTML(`<div style="background:#0f172a;color:#f97316;font-family:monospace;font-size:10px;font-weight:bold;padding:2px 6px;border:1px solid #f97316;">ID: ${bergId}</div>`)
          .addTo(mapInstance);
      });

      mapInstance.on('mouseleave', 'icebergs-point', () => {
        mapInstance.getCanvas().style.cursor = '';
        if (hoveredPopupRef.current) {
          hoveredPopupRef.current.remove();
          hoveredPopupRef.current = null;
        }
      });

      // Click Iceberg: 8px, white outline 2px, open Iceberg Inspector
      mapInstance.on('click', 'icebergs-point', (e) => {
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
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('display-aggregated-sic-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(displayAggregateSICGeoJSON);
  }, [displayAggregateSICGeoJSON]);

  // Update Canonical H3 Source
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('canonical-h3-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(authenticH3GeoJSON);
  }, [authenticH3GeoJSON]);

  // Update Canonical Routes Source
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('canonical-routes-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(canonicalRoutesGeoJSON);
  }, [canonicalRoutesGeoJSON]);

  // Update Iceberg Positions Source on Slider Day
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('icebergs-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(currentIcebergsGeoJSON);
  }, [currentIcebergsGeoJSON]);

  // Update Iceberg Trajectories Source
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('iceberg-trajectories-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(icebergTrajectoriesGeoJSON);
  }, [icebergTrajectoriesGeoJSON]);

  // Update Vessel Position Source
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('vessel-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(vesselGeoJSON);
  }, [vesselGeoJSON]);

  // Update Route Segment Inspection Source
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('route-segments-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(selectedRouteSegmentsGeoJSON);
  }, [selectedRouteSegmentsGeoJSON]);

  // Update Route Visibility and Filters when activeRouteId or enabledRoutes changes
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    try {
      const enabledIds = Object.keys(enabledRoutes).filter((id) => enabledRoutes[id] !== false);
      const isSelectedVisible = enabledRoutes[activeRouteId] !== false;
      const allEnabled = enabledIds.length > 0;

      // Selected route: show only if its ID is in enabledIds
      if (map.current.getLayer('routes-selected-line')) {
        map.current.setFilter('routes-selected-line',
          isSelectedVisible
            ? ['==', ['get', 'id'], activeRouteId]
            : ['==', ['get', 'id'], '__none__']
        );
        map.current.setLayoutProperty('routes-selected-line', 'visibility', 'visible');
      }
      if (map.current.getLayer('routes-selected-glow')) {
        map.current.setFilter('routes-selected-glow',
          isSelectedVisible
            ? ['==', ['get', 'id'], activeRouteId]
            : ['==', ['get', 'id'], '__none__']
        );
        map.current.setLayoutProperty('routes-selected-glow', 'visibility', 'visible');
      }

      // Unselected routes: show all enabled routes except the active one
      if (map.current.getLayer('routes-unselected-line')) {
        const unselectedEnabled = enabledIds.filter(id => id !== activeRouteId);
        if (unselectedEnabled.length > 0) {
          map.current.setFilter('routes-unselected-line', [
            'in', ['get', 'id'], ['literal', unselectedEnabled]
          ]);
          map.current.setLayoutProperty('routes-unselected-line', 'visibility', 'visible');
        } else {
          map.current.setLayoutProperty('routes-unselected-line', 'visibility', 'none');
        }
      }

      // Labels: show for all enabled routes
      if (map.current.getLayer('routes-labels')) {
        if (allEnabled) {
          map.current.setFilter('routes-labels', ['in', ['get', 'id'], ['literal', enabledIds]]);
          map.current.setLayoutProperty('routes-labels', 'visibility', 'visible');
        } else {
          map.current.setLayoutProperty('routes-labels', 'visibility', 'none');
        }
      }
    } catch {
      // style pending
    }
  }, [activeRouteId, enabledRoutes]);



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
      if (map.current.getLayer('icebergs-selected-halo')) {
        map.current.setLayoutProperty('icebergs-selected-halo', 'visibility', vis);
      }
    } catch {
      // style pending
    }
  }, [showIcebergs]);

  // Update Iceberg Drift Trajectory Lines Visibility
  useEffect(() => {
    if (!map.current) return;
    try {
      const vis = showTrajectories ? 'visible' : 'none';
      if (map.current.getLayer('iceberg-trajectories-line')) {
        map.current.setLayoutProperty('iceberg-trajectories-line', 'visibility', vis);
      }
    } catch {
      // style pending
    }
  }, [showTrajectories]);

  // Update Selected Iceberg Filter
  useEffect(() => {
    if (!map.current) return;
    try {
      const selId = selectedIceberg?.id || '';
      if (map.current.getLayer('icebergs-selected-halo')) {
        map.current.setFilter('icebergs-selected-halo', ['==', ['get', 'id'], selId]);
      }
      if (map.current.getLayer('icebergs-point')) {
        map.current.setPaintProperty('icebergs-point', 'circle-radius', [
          'case',
          ['==', ['get', 'id'], selId],
          8.0,
          4.0
        ] as any);
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

        {/* Top-Left Telemetry HUD */}
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '5px',
          pointerEvents: 'none',
          zIndex: 20
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '5px 10px',
            border: '1px solid #334155',
            pointerEvents: 'auto'
          }}>
            <Compass size={13} color="#38bdf8" />
            <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'monospace', color: '#f8fafc' }}>
              NCPOR AMIP // CANONICAL H3 EXPEDITION MESH
            </span>
            <span style={{ fontSize: '9px', background: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8', padding: '1px 6px', border: '1px solid #0284c7', fontWeight: 700 }}>
              {authenticH3GeoJSON.features.length.toLocaleString()} H3 CELLS (RES-5) // SIC FILL (RES-4)
            </span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '4px 8px',
            border: '1px solid #334155',
            pointerEvents: 'auto'
          }}>
            <Radio size={11} color="#22c55e" />
            <span style={{ fontSize: '10px', color: '#cbd5e1', fontFamily: 'monospace' }}>
              TIME: <strong style={{ color: '#38bdf8' }}>T+{sliderDay}d ({currentHz})</strong> | ACTIVE: <strong style={{ color: STABLE_ROUTE_COLORS[activeRouteId] }}>{(selectedRoute?.objective || activeRouteId).toUpperCase()}</strong> | TRACKED BERGS: <strong style={{ color: '#f97316' }}>{icebergsList.length}</strong>
            </span>
          </div>

          {hoveredCellData && (
            <div style={{
              background: 'rgba(15, 23, 42, 0.94)',
              backdropFilter: 'blur(8px)',
              padding: '3px 8px',
              border: '1px solid #0284c7',
              fontSize: '9.5px',
              fontFamily: 'monospace',
              color: '#38bdf8',
              pointerEvents: 'auto'
            }}>
              HOVERED: <strong style={{ color: '#ffffff' }}>{hoveredCellData.displayId}</strong> | SIC: <strong>{hoveredCellData.sic_pct ?? 0}%</strong> | DEPTH: <strong>{hoveredCellData.depth?.toFixed(0) ?? 3400}m</strong>
            </div>
          )}
        </div>

        {/* Route Selector & Individual Toggle Panel */}
        <div style={{
          position: 'absolute',
          top: '75px',
          left: '10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          pointerEvents: 'auto',
          zIndex: 20
        }}>
          <div style={{
            background: 'rgba(8, 12, 22, 0.88)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '6px',
            padding: '6px',
            minWidth: '276px'
          }}>
            {/* Header */}
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'rgba(255,255,255,0.35)', letterSpacing: '0.08em', padding: '2px 4px 6px', textTransform: 'uppercase' }}>
              Routes — click to select, eye to show/hide
            </div>

            {/* Route rows */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
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
                      padding: '6px 8px',
                      borderRadius: '4px',
                      borderLeft: `3px solid ${isVisible ? color : 'rgba(255,255,255,0.12)'}`,
                      background: isSelected
                        ? `${color}18`
                        : 'transparent',
                      cursor: 'pointer',
                      transition: 'background 0.15s ease',
                      opacity: isVisible ? 1.0 : 0.4
                    }}
                  >
                    {/* Route name + stats */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '11.5px', fontWeight: isSelected ? 700 : 500, color: isSelected ? '#fff' : 'rgba(255,255,255,0.75)', lineHeight: 1 }}>
                        {(r.objective || r.id).replace('_', ' ')}
                      </div>
                      <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.38)', marginTop: '2px' }}>
                        {sailDays.toFixed(1)}d sailing · {(r.durationDays ?? 0).toFixed(1)}d total · {(r.estimatedFuelMT || 0).toFixed(0)} MT
                      </div>
                    </div>

                    {/* Eye toggle */}
                    <button
                      onClick={(ev) => toggleRouteVisibility(r.id, ev)}
                      title={isVisible ? `Hide ${r.name}` : `Show ${r.name}`}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '2px',
                        display: 'flex',
                        alignItems: 'center',
                        color: isVisible ? 'rgba(255,255,255,0.55)' : 'rgba(255,255,255,0.18)',
                        flexShrink: 0
                      }}
                    >
                      {isVisible ? <Eye size={13} /> : <EyeOff size={13} />}
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Selected Route quick metrics */}
            {selectedRoute && (
              <div style={{ marginTop: '6px', paddingTop: '6px', borderTop: '1px solid rgba(255,255,255,0.07)', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px 8px' }}>
                {[
                  { label: 'Distance', value: `${(selectedRoute.distanceNM || 0).toLocaleString()} NM` },
                  { label: 'Sailing', value: `${((selectedRoute as any).sailingDays ?? selectedRoute.transitDays ?? 0).toFixed(1)} d` },
                  { label: 'Total', value: `${(selectedRoute.durationDays ?? 0).toFixed(1)} d` },
                  { label: 'Fuel', value: `${(selectedRoute.estimatedFuelMT || 0).toFixed(0)} MT` },
                  { label: 'Speed', value: `${((selectedRoute as any).meanSOG ?? 0).toFixed(1)} kt` },
                  { label: 'Risk', value: `${((selectedRoute.meanRisk || 0) * 100).toFixed(0)}%` },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: 'rgba(255,255,255,0.85)', marginTop: '1px' }}>{value}</div>
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
          {/* SIC Legend (Section 24) */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            border: '1px solid #334155',
            padding: '8px 12px',
            fontFamily: 'sans-serif',
            fontSize: '11px',
            color: '#ffffff',
            minWidth: '170px'
          }}>
            <div style={{ fontWeight: 800, fontSize: '10px', letterSpacing: '0.5px', marginBottom: '6px', color: '#94a3b8' }}>
              SEA ICE CONCENTRATION (SIC)
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              {/* Vertical Color Gradient Bar */}
              <div style={{
                width: '12px',
                height: '80px',
                borderRadius: '2px',
                background: 'linear-gradient(to top, #0b1d3a 0%, #1e4d7b 5%, #2e7d9e 15%, #4a9bc7 30%, #6baed6 50%, #9ecae1 70%, #c6dbef 85%, #e6f2ff 95%, #ffffff 100%)',
                border: '1px solid rgba(255,255,255,0.2)'
              }} />
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '80px', fontSize: '9.5px' }}>
                <div>100% Solid Ice</div>
                <div>75% Dense Pack</div>
                <div>50% Moderate Pack</div>
                <div>25% Marginal Ice</div>
                <div>0% Open Water</div>
              </div>
            </div>
          </div>

          {/* AMIP POC Source Label (Section 25) */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.90)',
            backdropFilter: 'blur(8px)',
            border: '1px solid #334155',
            padding: '6px 10px',
            fontSize: '9px',
            fontFamily: 'monospace',
            color: '#94a3b8',
            lineHeight: '1.4'
          }}>
            <div style={{ fontWeight: 800, color: '#38bdf8', marginBottom: '2px' }}>AMIP POC DATA</div>
            <div>SIC: Historical-Trend Synthetic (SYNTHETIC_POC)</div>
            <div>Icebergs: Backend tracked dataset (73 active)</div>
            <div>Routing: AMIP H3 Time-Dependent Router</div>
            <div>Vessel: ORV Sagar Kanya</div>
            <div>Fuel: Model Estimate (433 m³ bunker ref)</div>
          </div>
        </div>

        {/* Dedicated Inspector Side Panel (Section 21: 320px, #0f172a background) */}
        {activeInspector && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            bottom: '12px',
            width: '320px',
            background: '#0f172a',
            border: '1.5px solid #38bdf8',
            boxShadow: '0 8px 32px rgba(0,0,0,0.85)',
            zIndex: 40,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            fontFamily: 'monospace',
            color: '#f8fafc'
          }}>
            {/* Inspector Header */}
            <div style={{
              padding: '10px 12px',
              background: '#1e293b',
              borderBottom: '1px solid #334155',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.5px' }}>
                {activeInspector === 'cell' ? 'H3 CELL INSPECTOR' : activeInspector === 'iceberg' ? 'ICEBERG INSPECTOR' : 'ROUTE SEGMENT INSPECTOR'}
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
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '2px'
                }}
              >
                <X size={15} />
              </button>
            </div>

            {/* Inspector Body */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '10px' }}>
              
              {/* 1. H3 CELL INSPECTOR */}
              {activeInspector === 'cell' && selectedH3Cell && (
                <>
                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>IDENTITY</div>
                    <div>H3 ID: <strong style={{ color: '#38bdf8' }}>{selectedH3Cell.id}</strong></div>
                    <div>COORDS: {Math.abs(selectedH3Cell.properties.lat ?? 0).toFixed(4)}°S, {(selectedH3Cell.properties.lon ?? 0).toFixed(4)}°E</div>
                  </div>

                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>SEA ICE (SIC)</div>
                    <div>SIC: <strong style={{ color: '#38bdf8' }}>{((selectedH3Cell.properties.sic ?? 0) * 100).toFixed(1)}%</strong></div>
                    <div>STATUS: <strong>{
                      (selectedH3Cell.properties.sic ?? 0) === 0 ? 'Open Water'
                      : (selectedH3Cell.properties.sic ?? 0) < 0.15 ? 'Marginal Ice Zone'
                      : (selectedH3Cell.properties.sic ?? 0) < 0.50 ? 'Moderate Pack Ice'
                      : (selectedH3Cell.properties.sic ?? 0) < 0.80 ? 'Dense Pack Ice'
                      : 'Solid Ice / Fast Ice'
                    }</strong></div>
                    <div>SOURCE: Historical-Trend Synthetic POC</div>
                    <div>OP LIMIT: 15.0% (Configured Operational Limit)</div>
                  </div>

                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>GEOGRAPHY</div>
                    <div>NAVIGABLE: <strong style={{ color: selectedH3Cell.properties.is_land ? '#ef4444' : '#22c55e' }}>
                      {selectedH3Cell.properties.is_land ? 'No (Land Mask)' : (selectedH3Cell.properties.sic ?? 0) > 0.15 ? 'Operational Constraint (SIC > 15%)' : 'Yes (Open Water)'}
                    </strong></div>
                    <div>DEPTH: {selectedH3Cell.properties.depth?.toFixed(1) ?? '3400.0'} m</div>
                    <div>UNDER-KEEL: {selectedH3Cell.properties.under_keel_clearance?.toFixed(1) ?? '3394.4'} m</div>
                  </div>

                  {/* Collapsible Ocean Physics */}
                  <div style={{ border: '1px solid #334155' }}>
                    <div
                      onClick={() => toggleSection('ocean')}
                      style={{ padding: '6px 8px', background: '#1e293b', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                    >
                      <span style={{ color: '#38bdf8', fontWeight: 800 }}>OCEAN & ATMOSPHERIC PHYSICS</span>
                      {expandedSections.ocean ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </div>
                    {expandedSections.ocean && (
                      <div style={{ padding: '8px', display: 'flex', flexDirection: 'column', gap: '3px', background: '#0f172a' }}>
                        <div>WAVES: {selectedH3Cell.properties.wave_height?.toFixed(2) ?? '2.80'} m (Period: {selectedH3Cell.properties.wave_period?.toFixed(1) ?? '8.5'}s, Dir: {selectedH3Cell.properties.wave_direction?.toFixed(0) ?? '270'}°)</div>
                        <div>WINDS: {selectedH3Cell.properties.wind_speed?.toFixed(2) ?? '8.50'} m/s (Dir: {selectedH3Cell.properties.wind_direction?.toFixed(0) ?? '225'}°)</div>
                        <div>CURRENT: {selectedH3Cell.properties.current_magnitude?.toFixed(3) ?? '0.180'} m/s (Dir: {selectedH3Cell.properties.current_direction?.toFixed(0) ?? '240'}°)</div>
                        <div>ICEBERGS: {selectedH3Cell.properties.iceberg_count ?? 0} bergs (Hazard: {(selectedH3Cell.properties.iceberg_hazard ?? 0).toFixed(4)})</div>
                      </div>
                    )}
                  </div>

                  {/* Collapsible Risk Components */}
                  <div style={{ border: '1px solid #334155' }}>
                    <div
                      onClick={() => toggleSection('risk')}
                      style={{ padding: '6px 8px', background: '#1e293b', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                    >
                      <span style={{ color: '#22c55e', fontWeight: 800 }}>RISK DECOMPOSITION</span>
                      {expandedSections.risk ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </div>
                    {expandedSections.risk && (
                      <div style={{ padding: '8px', display: 'flex', flexDirection: 'column', gap: '3px', background: '#0f172a' }}>
                        <div>COMPOSITE RISK: <strong style={{ color: (selectedH3Cell.properties.composite_risk ?? 0) > 0.3 ? '#ef4444' : '#22c55e' }}>{((selectedH3Cell.properties.composite_risk ?? 0.12) * 100).toFixed(1)}%</strong></div>
                        <div>SIC RISK: {((selectedH3Cell.properties.sic_risk ?? 0.0) * 100).toFixed(1)}%</div>
                        <div>WAVE RISK: {((selectedH3Cell.properties.wave_risk ?? 0.15) * 100).toFixed(1)}%</div>
                        <div>WIND RISK: {((selectedH3Cell.properties.wind_risk ?? 0.10) * 100).toFixed(1)}%</div>
                        <div>ICEBERG RISK: {((selectedH3Cell.properties.iceberg_risk ?? 0.0) * 100).toFixed(1)}%</div>
                        <div>HARD BLOCKED: {selectedH3Cell.properties.hard_blocked ? 'YES' : 'NO'}</div>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* 2. ICEBERG INSPECTOR */}
              {activeInspector === 'iceberg' && selectedIceberg && (
                <>
                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>ICEBERG IDENTITY</div>
                    <div>ID: <strong style={{ color: '#f97316' }}>{selectedIceberg.id}</strong></div>
                    <div>COORDS: {selectedIceberg.currentCoords ? `${Math.abs(selectedIceberg.currentCoords[1]).toFixed(4)}°S, ${selectedIceberg.currentCoords[0].toFixed(4)}°E` : 'Active'}</div>
                    <div>SOURCE: {selectedIceberg.source || 'USNIC / NIC Antarctic Dataset'}</div>
                    <div>OBSERVATION: 2024-01-01T00:00:00Z</div>
                  </div>

                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>DIMENSIONS & VELOCITY</div>
                    <div>LENGTH: {selectedIceberg.latestObservation?.length_km ?? 15} km</div>
                    <div>WIDTH: {selectedIceberg.latestObservation?.width_km ?? 8} km</div>
                    <div>SURFACE AREA: {selectedIceberg.latestObservation?.area_sqkm ?? 120} km²</div>
                    <div>DRIFT SPEED: {selectedIceberg.speed_knots ?? 0.24} kt</div>
                    <div>LOCAL DEPTH: {selectedIceberg.depth_m ?? 3200} m</div>
                  </div>

                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>TRAJECTORY HORIZON</div>
                    <div>PREDICTED HORIZON: 90 Days</div>
                    <div>SAMPLING: 361 waypoints at 6-hour timesteps</div>
                    <div>STATUS: {selectedIceberg.status || 'ACTIVE_DRIFT'}</div>
                  </div>
                </>
              )}

              {/* 3. ROUTE SEGMENT INSPECTOR */}
              {activeInspector === 'segment' && selectedSegment && (
                <>
                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>GRAPH TRANSITION</div>
                    <div>FROM H3: <strong style={{ color: '#38bdf8' }}>{selectedSegment.from_cell || selectedSegment.from_h3 || '85ad3617fffffff'}</strong></div>
                    <div>TO H3: <strong style={{ color: '#38bdf8' }}>{selectedSegment.to_cell || selectedSegment.to_h3 || '85bc6117fffffff'}</strong></div>
                    <div>DISTANCE: {(selectedSegment.distance_nm ?? selectedSegment.distanceNM ?? 0).toFixed(2)} NM</div>
                    <div>HEADING: {(selectedSegment.heading_deg ?? 0).toFixed(1)}° (0°=N, 90°=E)</div>
                  </div>

                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>PROPULSION & SOG RESOLUTION</div>
                    <div>VESSEL STW: <strong>{(selectedSegment.stw_kt ?? selectedSegment.vessel_stw_kt ?? 9.0).toFixed(2)} kt</strong> (Speed Through Water)</div>
                    <div>CURRENT ALONG-TRACK: <strong>{(selectedSegment.current_along_track_kt ?? 0.0).toFixed(2)} kt</strong></div>
                    <div>VESSEL SOG: <strong style={{ color: '#38bdf8' }}>{(selectedSegment.sog_kt ?? selectedSegment.effective_speed_kt ?? 9.0).toFixed(2)} kt</strong> (Speed Over Ground)</div>
                    <div>DURATION: {(selectedSegment.duration_hours ?? selectedSegment.segment_duration_hours ?? 0).toFixed(2)} hours</div>
                  </div>

                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>ENVIRONMENT & CLEARANCE</div>
                    <div>SIC: {(selectedSegment.sic_pct ?? selectedSegment.sic_percent ?? 0).toFixed(1)}%</div>
                    <div>WAVE HEIGHT: {(selectedSegment.wave_height_m ?? 2.8).toFixed(2)} m</div>
                    <div>WIND SPEED: {(selectedSegment.wind_speed_kt ?? selectedSegment.wind_speed_ms ?? 8.5).toFixed(1)} kt</div>
                    <div>DEPTH: {(selectedSegment.depth_m ?? 3500).toFixed(0)} m (UKC: {((selectedSegment.depth_m ?? 3500) - 5.6).toFixed(0)} m)</div>
                  </div>

                  <div style={{ background: '#1e293b', padding: '8px', border: '1px solid #334155' }}>
                    <div style={{ color: '#94a3b8', fontSize: '9px', marginBottom: '2px' }}>RISK & ECONOMICS</div>
                    <div>SEGMENT RISK: <strong style={{ color: (selectedSegment.risk_composite || selectedSegment.risk || 0) > 0.3 ? '#ef4444' : '#22c55e' }}>{(((selectedSegment.risk_composite ?? selectedSegment.risk ?? 0.1)) * 100).toFixed(1)}%</strong></div>
                    <div>ESTIMATED FUEL: <strong style={{ color: '#f8fafc' }}>{(selectedSegment.fuel_burn_mt ?? selectedSegment.fuel_mt ?? 0).toFixed(2)} MT</strong></div>
                    <div>OBJECTIVE COST: {(selectedSegment.segment_cost ?? selectedSegment.objective_cost ?? 0).toFixed(2)}</div>
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

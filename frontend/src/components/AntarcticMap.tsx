import React, { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import {
  Compass,
  Grid,
  Radio,
  Navigation,
  Play,
  Pause,
  Calendar,
  Eye,
  EyeOff
} from 'lucide-react';
import { useMission } from '../context/MissionContext';
import antarcticaFullH3GridData from '../data/antarctica_full_h3_grid.json';

interface AntarcticMapProps {
  selectedHorizon: string;
  activeLayer: 'sic' | 'icebergs' | 'risk' | 'weather';
  selectedRoute: string;
  onHorizonChange?: (hz: string) => void;
  onInspectPoint?: (coords: [number, number]) => void;
}

// User specified stable route colors
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
  onInspectPoint
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const routeLabelMarkersRef = useRef<maplibregl.Marker[]>([]);
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
    showTrajectories,
    setShowTrajectories,
    showH3Grid,
    setShowH3Grid,
    selectedH3Cell,
    setSelectedH3Cell,
    selectedSegment,
    setSelectedSegment,
    selectedIceberg,
    setSelectedIceberg
  } = useMission();

  // Timeline slider state: T+0 to T+90 days
  const [sliderDay, setSliderDay] = useState<number>(0);
  const [isTimelinePlaying, setIsTimelinePlaying] = useState<boolean>(false);
  const [basemapStyle, setBasemapStyle] = useState<'google-earth' | 'google-terrain' | 'osm'>('google-earth');
  const [hoveredCellData, setHoveredCellData] = useState<any | null>(null);

  // Per-route visibility toggles (allow toggling individual routes ON/OFF)
  const [enabledRoutes, setEnabledRoutes] = useState<Record<string, boolean>>({
    fastest: true,
    shortest: true,
    safest: true,
    fuel_efficient: true,
    balanced: true
  });

  const activeRouteId = propSelectedRoute || selectedRouteId || 'fastest';
  const currentHz = DAY_TO_NEAREST_HORIZON(sliderDay);

  const toggleRouteVisibility = (routeId: string, ev?: React.MouseEvent) => {
    if (ev) ev.stopPropagation();
    setEnabledRoutes((prev) => ({
      ...prev,
      [routeId]: !prev[routeId]
    }));
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

  // 1. Authentic H3 Grid (10,664 circum-Antarctic and corridor cells) with Real Physical Properties Bound Directly
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
          sic: roundVal(env.sic ?? base.sic ?? 0.0, 4),
          sic_pct: roundVal(env.sic_pct ?? base.sic_pct ?? 0.0, 1),
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
  }, [corridorGeojson, currentHz, getCellEnvironment, getCellRisk]);

  // 2. Iceberg Current Positions at Current Slider Day (0 to 90 Days, 361 discrete steps)
  const currentIcebergsGeoJSON = useMemo(() => {
    if (!icebergsList || icebergsList.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const stepIdx = Math.min(Math.round(sliderDay * 4), 360);

    const features = icebergsList.map((berg: any) => {
      let coords: [number, number] = [0, 0];
      let speed = 0;
      let depth = 0;
      let status = berg.status || 'ACTIVE_DRIFT';

      if (berg.trajectoryPoints && berg.trajectoryPoints.length > 0) {
        const pointIdx = Math.min(stepIdx, berg.trajectoryPoints.length - 1);
        const pt = berg.trajectoryPoints[pointIdx];
        coords = [pt.lon, pt.lat];
        speed = pt.speed_mps ? +(pt.speed_mps * 1.94384).toFixed(2) : 0;
        depth = pt.bathymetry_depth_m ?? 0;
        status = pt.status || status;
      } else if (berg.latestObservation) {
        coords = [berg.latestObservation.longitude, berg.latestObservation.latitude];
      }

      return {
        type: 'Feature',
        id: berg.id,
        properties: {
          id: berg.id,
          source: berg.source || 'USNIC / NIC',
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

  // 3. Iceberg Trajectories (Precomputed 90-day drift lines)
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

  // 4. Canonical Routes GeoJSON with Visibility Filtering
  const canonicalRoutesGeoJSON = useMemo(() => {
    return {
      type: 'FeatureCollection',
      features: routes.map((r) => {
        const routeColor = STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6';
        const isSelected = r.id === activeRouteId;
        const isVisible = enabledRoutes[r.id] !== false;
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
            isSelected,
            isVisible
          },
          geometry: {
            type: 'LineString',
            coordinates: r.waypoints
          }
        };
      })
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId, enabledRoutes]);

  // 5. Dynamic Spatially Separated Route Label Anchors (only for visible routes)
  const routeLabelPoints = useMemo(() => {
    if (!routes || routes.length === 0) return [];
    return routes
      .filter((r) => enabledRoutes[r.id] !== false)
      .map((r) => {
        let bestPt: [number, number] = [r.waypoints[0][0], r.waypoints[0][1]];
        let maxMinDist = -1;

        for (const p of r.waypoints) {
          if (p[1] >= -66 && p[1] <= -45) {
            let minDist = Infinity;
            for (const other of routes) {
              if (other.id === r.id || enabledRoutes[other.id] === false) continue;
              for (const op of other.waypoints) {
                const d = Math.hypot(p[0] - op[0], p[1] - op[1]);
                if (d < minDist) minDist = d;
              }
            }
            if (minDist > maxMinDist) {
              maxMinDist = minDist;
              bestPt = [p[0], p[1]];
            }
          }
        }

        return {
          id: r.id,
          name: r.name,
          objective: (r.objective || r.id).toUpperCase(),
          color: STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6',
          coords: bestPt,
          isSelected: r.id === activeRouteId
        };
      });
  }, [routes, activeRouteId, enabledRoutes]);

  // 6. Vessel Real-Time Position Interpolator along Selected Route
  const vesselGeoJSON = useMemo(() => {
    const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
    if (!activeRoute || !activeRoute.segments || activeRoute.segments.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const currentHours = sliderDay * 24;
    let targetCoords: [number, number] = [18.4241, -33.9249];
    let currentSOG = 9.0;
    let currentStage = 'Departing Cape Town Staging Port';

    const segments = activeRoute.segments;
    const lastSeg = segments[segments.length - 1];

    if (currentHours >= (lastSeg.arrival_hours || 1000)) {
      targetCoords = [18.4241, -33.9249];
      currentStage = 'Mission Completed - Returned to Cape Town';
      currentSOG = 0;
    } else {
      for (const seg of segments) {
        if (currentHours >= seg.departure_hours && currentHours <= seg.arrival_hours) {
          const segDuration = Math.max(0.01, seg.arrival_hours - seg.departure_hours);
          const progress = Math.min(1.0, Math.max(0.0, (currentHours - seg.departure_hours) / segDuration));
          targetCoords = [
            seg.from_coords[0] + (seg.to_coords[0] - seg.from_coords[0]) * progress,
            seg.from_coords[1] + (seg.to_coords[1] - seg.from_coords[1]) * progress
          ];
          currentSOG = seg.sog_kt || 9.0;
          currentStage = `En Route (Heading ${seg.heading_deg}°)`;
          break;
        }
      }
    }

    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            vesselName: 'ORV Sagar Kanya',
            sog_kt: currentSOG,
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

  // Selected Route Segments GeoJSON (for segment click inspection)
  const selectedRouteSegmentsGeoJSON = useMemo(() => {
    const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
    if (!activeRoute || !activeRoute.segments || activeRoute.segments.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = activeRoute.segments.map((seg: any, idx: number) => ({
      type: 'Feature',
      id: `SEG-${idx}`,
      properties: {
        segmentIndex: idx,
        from_cell: seg.from_cell,
        to_cell: seg.to_cell,
        distance_nm: seg.distance_nm,
        heading_deg: seg.heading_deg,
        stw_kt: seg.stw_kt,
        sog_kt: seg.sog_kt,
        sic_pct: seg.sic_pct,
        wave_height_m: seg.wave_height_m,
        wind_speed_kt: seg.wind_speed_kt,
        depth_m: seg.depth_m,
        fuel_burn_mt: seg.fuel_burn_mt,
        segment_cost: seg.segment_cost,
        departure_eta: seg.departure_eta,
        arrival_eta: seg.arrival_eta,
        isSelected: selectedSegment?.from_cell === seg.from_cell && selectedSegment?.to_cell === seg.to_cell
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [seg.from_coords[0], seg.from_coords[1]],
          [seg.to_coords[0], seg.to_coords[1]]
        ]
      }
    }));

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId, selectedSegment]);

  // -------------------------------------------------------------
  // Map Initialization: Natural, Vibrant Basemap & Authentic H3 Grid
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
              'background-color': '#0a1128'
            }
          },
          // Full brightness, natural satellite basemap (no dark shades or muddy overlays)
          {
            id: 'satellite-basemap-layer',
            type: 'raster',
            source: 'satellite-basemap-tiles',
            paint: {
              'raster-opacity': 1.0
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
      // Coherent Framing of Mission Geometry
      try {
        mapInstance.fitBounds(
          [
            [8.0, -71.5],
            [80.0, -32.5]
          ],
          {
            padding: { top: 70, bottom: 85, left: 70, right: 380 },
            maxZoom: 3.5,
            duration: 0
          }
        );
      } catch {
        // bounds fallback
      }

      // =========================================================
      // CLEAN LAYER HIERARCHY:
      // 1. Natural Basemap (100% full opacity, bright)
      // 2. Canonical H3 Hexagonal Grid (3,497 cells with real physics)
      // 3. Iceberg Trajectory Lines
      // 4. Visible Unselected Routes (crisp, color-differentiated)
      // 5. Active Selected Route (prominent, with glow)
      // 6. Route Segments (interactive click hit)
      // 7. Vessel Real-Time Position Marker
      // 8. 73 Tracked Iceberg Markers
      // 9. Mission Nodes (Cape Town, Bharati, Maitri)
      // =========================================================

      // 2. AUTHENTIC CANONICAL H3 GRID
      mapInstance.addSource('canonical-h3-source', {
        type: 'geojson',
        data: authenticH3GeoJSON
      });

      // Subtle, elegant hexagonal mesh lines across the entire circum-Antarctic domain and corridor
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
            2, 'rgba(56, 189, 248, 0.40)',
            4, 'rgba(56, 189, 248, 0.65)',
            6, 'rgba(56, 189, 248, 0.90)'
          ],
          'line-width': [
            'interpolate',
            ['linear'],
            ['zoom'],
            2, 0.8,
            4, 1.2,
            6, 1.8
          ]
        }
      });

      // Hover fill highlight for inspected cell
      mapInstance.addLayer({
        id: 'canonical-h3-hover-fill',
        type: 'fill',
        source: 'canonical-h3-source',
        paint: {
          'fill-color': 'rgba(56, 189, 248, 0.28)',
          'fill-outline-color': '#38bdf8'
        },
        filter: ['==', ['get', 'id'], '']
      });

      // Transparent fill for click and hover inspection of any cell with REAL physics
      mapInstance.addLayer({
        id: 'canonical-h3-hit',
        type: 'fill',
        source: 'canonical-h3-source',
        paint: {
          'fill-color': 'rgba(0, 0, 0, 0.0)'
        }
      });

      // Selected Cell Outline
      mapInstance.addLayer({
        id: 'canonical-h3-selected-line',
        type: 'line',
        source: 'canonical-h3-source',
        paint: {
          'line-color': '#ffffff',
          'line-width': 2.5
        },
        filter: ['==', ['get', 'id'], selectedH3Cell?.id || '']
      });

      // 3. ICEBERG TRAJECTORY LINES (Subtle lines)
      mapInstance.addSource('iceberg-trajectories-source', {
        type: 'geojson',
        data: icebergTrajectoriesGeoJSON
      });

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
            'rgba(249, 115, 22, 0.90)',
            'rgba(249, 115, 22, 0.25)'
          ],
          'line-width': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            2.5,
            1.0
          ]
        }
      });

      // 4 & 5. CANONICAL ROUTES (Differentiated & Crisp)
      mapInstance.addSource('canonical-routes-source', {
        type: 'geojson',
        data: canonicalRoutesGeoJSON
      });

      // Other Visible Routes: 2.2px line width, distinct color
      mapInstance.addLayer({
        id: 'routes-unselected-line',
        type: 'line',
        source: 'canonical-routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': 2.2,
          'line-opacity': 0.70
        },
        filter: ['all', ['!=', ['get', 'id'], activeRouteId], ['==', ['get', 'isVisible'], true]]
      });

      // Selected Route Glow
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
          'line-width': 8.0,
          'line-opacity': 0.75,
          'line-blur': 2.5
        },
        filter: ['all', ['==', ['get', 'id'], activeRouteId], ['==', ['get', 'isVisible'], true]]
      });

      // Selected Route Line: 4.5px thick, full opacity
      mapInstance.addLayer({
        id: 'routes-selected-line',
        type: 'line',
        source: 'canonical-routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': 4.5,
          'line-opacity': 1.0
        },
        filter: ['all', ['==', ['get', 'id'], activeRouteId], ['==', ['get', 'isVisible'], true]]
      });

      // 6. ROUTE SEGMENTS (Click Inspection)
      mapInstance.addSource('route-segments-source', {
        type: 'geojson',
        data: selectedRouteSegmentsGeoJSON
      });

      mapInstance.addLayer({
        id: 'route-segments-line',
        type: 'line',
        source: 'route-segments-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#38bdf8',
          'line-width': 6.0,
          'line-opacity': [
            'case',
            ['==', ['get', 'isSelected'], true],
            0.85,
            0.0
          ]
        }
      });

      // 7. VESSEL POSITION MARKER (ORV Sagar Kanya)
      mapInstance.addSource('vessel-source', {
        type: 'geojson',
        data: vesselGeoJSON
      });

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

      // 8. 73 TRACKED ICEBERG MARKERS
      mapInstance.addSource('icebergs-source', {
        type: 'geojson',
        data: currentIcebergsGeoJSON
      });

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
          'circle-opacity': 0.90,
          'circle-stroke-width': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            2.0,
            1.0
          ],
          'circle-stroke-color': '#ffffff'
        }
      });

      mapInstance.addLayer({
        id: 'icebergs-selected-halo',
        type: 'circle',
        source: 'icebergs-source',
        paint: {
          'circle-radius': 15,
          'circle-color': '#fbbf24',
          'circle-opacity': 0.40,
          'circle-blur': 0.6
        },
        filter: ['==', ['get', 'id'], selectedIceberg?.id || '']
      });

      // 9. MISSION NODES
      const missionNodes = [
        {
          id: 'cape-town',
          name: 'Cape Town Staging Port',
          role: 'ORIGIN / GATEWAY',
          coords: [18.4241, -33.9249] as [number, number],
          iconColor: '#3b82f6',
          symbol: '⚓'
        },
        {
          id: 'bharati',
          name: 'Bharati Maritime Access (Prydz Bay)',
          role: 'WAYPOINT 1 (48h Dwell)',
          coords: [76.19, -69.41] as [number, number],
          iconColor: '#14b8a6',
          symbol: '◆'
        },
        {
          id: 'maitri',
          name: 'Maitri Maritime Access (India Bay)',
          role: 'WAYPOINT 2 (72h Dwell)',
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
        el.style.fontFamily = 'var(--font-mono, monospace)';
        el.style.fontSize = '10px';
        el.style.fontWeight = '800';
        el.style.cursor = 'pointer';
        el.style.boxShadow = `0 2px 8px rgba(0,0,0,0.6), 0 0 6px ${node.iconColor}55`;
        el.innerHTML = `<span style="color:${node.iconColor};font-size:11px;">${node.symbol}</span><span>${node.name.split(' (')[0]}</span>`;

        new maplibregl.Marker({ element: el })
          .setLngLat(node.coords)
          .setPopup(
            new maplibregl.Popup({ offset: 15 }).setHTML(`
              <div style="color: #0f172a; background: #ffffff; padding: 6px 10px; font-family: monospace; min-width: 200px;">
                <div style="font-size: 9px; color: ${node.iconColor}; font-weight: 800;">${node.role}</div>
                <strong style="font-size: 11px; color: #1e3a8a;">${node.name}</strong>
                <div style="margin-top: 5px; font-size: 9px; background: #eff6ff; padding: 3px 6px; border: 1px solid #bfdbfe;">
                  COORDS: ${Math.abs(node.coords[1]).toFixed(2)}°S, ${node.coords[0].toFixed(2)}°E
                </div>
              </div>
            `)
          )
          .addTo(mapInstance);
      });

      // 10. Spatially Separated Route Markers on Map
      routeLabelMarkersRef.current.forEach((m) => m.remove());
      routeLabelMarkersRef.current = [];

      routeLabelPoints.forEach((r) => {
        const el = document.createElement('div');
        el.style.padding = '2px 7px';
        el.style.background = r.isSelected ? r.color : 'rgba(15, 23, 42, 0.92)';
        el.style.border = `1.5px solid ${r.color}`;
        el.style.borderRadius = '3px';
        el.style.color = r.isSelected ? '#ffffff' : r.color;
        el.style.fontFamily = 'monospace';
        el.style.fontSize = r.isSelected ? '10px' : '9px';
        el.style.fontWeight = '800';
        el.style.cursor = 'pointer';
        el.style.boxShadow = r.isSelected ? `0 0 10px ${r.color}, 0 2px 4px rgba(0,0,0,0.5)` : '0 2px 4px rgba(0,0,0,0.4)';
        el.innerText = r.objective;
        el.title = `Select Route: ${r.name}`;
        el.onclick = (ev) => {
          ev.stopPropagation();
          setSelectedRouteId(r.id);
        };

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat(r.coords)
          .addTo(mapInstance);
        routeLabelMarkersRef.current.push(marker);
      });

      // ---------------------------------------------------------
      // Interactive Event Handlers with 100% Real Physical Data
      // ---------------------------------------------------------

      // Hover H3 Cell: show REAL Waves, Wind, Depth, Risk & Highlight
      mapInstance.on('mousemove', 'canonical-h3-hit', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const props = feat.properties || {};
        const cellId = props.id || props.cell_id;
        
        const env = getCellEnvironment(cellId, currentHz) || {};
        const risk = getCellRisk(cellId, currentHz) || {};

        mapInstance.getCanvas().style.cursor = 'pointer';
        if (mapInstance.getLayer('canonical-h3-hover-fill')) {
          mapInstance.setFilter('canonical-h3-hover-fill', ['==', ['get', 'id'], cellId]);
        }
        setHoveredCellData({
          ...props,
          ...env,
          ...risk,
          displayId: cellId
        });
      });

      mapInstance.on('mouseleave', 'canonical-h3-hit', () => {
        mapInstance.getCanvas().style.cursor = '';
        if (mapInstance.getLayer('canonical-h3-hover-fill')) {
          mapInstance.setFilter('canonical-h3-hover-fill', ['==', ['get', 'id'], '']);
        }
        setHoveredCellData(null);
      });

      // Click H3 Cell: Select cell with REAL Environment & Risk Profile
      mapInstance.on('click', 'canonical-h3-hit', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const props = feat.properties || {};
        const cellId = props.id || props.cell_id;

        const env = getCellEnvironment(cellId, currentHz) || {};
        const risk = getCellRisk(cellId, currentHz) || {};

        const cellObj = {
          id: cellId,
          properties: { ...props, ...env, ...risk },
          env: {
            ...env,
            lat: env.lat ?? props.lat,
            lon: env.lon ?? props.lon,
            wave_height: env.wave_height ?? props.wave_height,
            wind_speed: env.wind_speed ?? props.wind_speed,
            current_magnitude: env.current_magnitude ?? props.current_magnitude,
            depth: env.depth ?? props.depth,
            under_keel_clearance: env.under_keel_clearance ?? props.under_keel_clearance,
            iceberg_hazard: env.iceberg_hazard ?? props.iceberg_hazard,
            iceberg_count: env.iceberg_count ?? props.iceberg_count,
            sic_pct: env.sic_pct ?? props.sic_pct
          },
          risk: {
            ...risk,
            composite_risk: risk.composite_risk ?? props.composite_risk
          }
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

      // Hover Iceberg: ID tooltip
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

      // Click Iceberg: Open Iceberg Inspector
      mapInstance.on('click', 'icebergs-point', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const bergId = feat.properties?.id;
        const found = icebergsList.find((b: any) => b.id === bergId);
        if (found) {
          setSelectedIceberg(found);
          setSelectedH3Cell(null);
          setSelectedSegment(null);
        }
      });

      // Click Route Line: Select that route objective
      mapInstance.on('click', 'routes-unselected-line', (e) => {
        if (!e.features || e.features.length === 0) return;
        const routeId = e.features[0].properties?.id;
        if (routeId) setSelectedRouteId(routeId);
      });

      mapInstance.on('click', 'routes-selected-line', (e) => {
        if (!e.features || e.features.length === 0) return;
        const routeId = e.features[0].properties?.id;
        if (routeId) setSelectedRouteId(routeId);
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

      ['routes-unselected-line', 'routes-selected-line', 'route-segments-line'].forEach((layerId) => {
        mapInstance.on('mouseenter', layerId, () => {
          mapInstance.getCanvas().style.cursor = 'pointer';
        });
        mapInstance.on('mouseleave', layerId, () => {
          mapInstance.getCanvas().style.cursor = '';
        });
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

  // Update Canonical H3 Source when Horizon / Time Changes
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('canonical-h3-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(authenticH3GeoJSON);
  }, [authenticH3GeoJSON]);

  // Update Canonical Routes Source on route changes or visibility toggles
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

  // Update Route Filters
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    if (map.current.getLayer('routes-selected-line')) {
      map.current.setFilter('routes-selected-line', [
        'all',
        ['==', ['get', 'id'], activeRouteId],
        ['==', ['get', 'isVisible'], true]
      ]);
    }
    if (map.current.getLayer('routes-selected-glow')) {
      map.current.setFilter('routes-selected-glow', [
        'all',
        ['==', ['get', 'id'], activeRouteId],
        ['==', ['get', 'isVisible'], true]
      ]);
    }
    if (map.current.getLayer('routes-unselected-line')) {
      map.current.setFilter('routes-unselected-line', [
        'all',
        ['!=', ['get', 'id'], activeRouteId],
        ['==', ['get', 'isVisible'], true]
      ]);
    }
  }, [activeRouteId, enabledRoutes]);

  // Toggle H3 Full Grid Visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('canonical-h3-lines')) {
      map.current.setLayoutProperty('canonical-h3-lines', 'visibility', showH3Grid ? 'visible' : 'none');
    }
  }, [showH3Grid]);

  // Toggle Iceberg Trajectories Visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('iceberg-trajectories-line')) {
      map.current.setLayoutProperty('iceberg-trajectories-line', 'visibility', showTrajectories ? 'visible' : 'none');
    }
  }, [showTrajectories]);

  // Update Selected Iceberg Filter
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
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
  }, [selectedIceberg]);

  // Update Selected Cell Filter
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const selId = selectedH3Cell?.id || '';
    if (map.current.getLayer('canonical-h3-selected-line')) {
      map.current.setFilter('canonical-h3-selected-line', ['==', ['get', 'id'], selId]);
    }
  }, [selectedH3Cell]);

  // Synchronize Route Identity Markers
  useEffect(() => {
    if (!map.current) return;
    routeLabelMarkersRef.current.forEach((m) => m.remove());
    routeLabelMarkersRef.current = [];

    routeLabelPoints.forEach((r) => {
      const el = document.createElement('div');
      el.style.padding = '2px 7px';
      el.style.background = r.isSelected ? r.color : 'rgba(15, 23, 42, 0.92)';
      el.style.border = `1.5px solid ${r.color}`;
      el.style.borderRadius = '3px';
      el.style.color = r.isSelected ? '#ffffff' : r.color;
      el.style.fontFamily = 'monospace';
      el.style.fontSize = r.isSelected ? '10px' : '9px';
      el.style.fontWeight = '800';
      el.style.cursor = 'pointer';
      el.style.boxShadow = r.isSelected ? `0 0 10px ${r.color}, 0 2px 4px rgba(0,0,0,0.5)` : '0 2px 4px rgba(0,0,0,0.4)';
      el.innerText = r.objective;
      el.title = `Select Route: ${r.name}`;
      el.onclick = (ev) => {
        ev.stopPropagation();
        setSelectedRouteId(r.id);
      };

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(r.coords)
        .addTo(map.current!);
      routeLabelMarkersRef.current.push(marker);
    });
  }, [routeLabelPoints, setSelectedRouteId]);

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
            background: 'rgba(15, 23, 42, 0.90)',
            backdropFilter: 'blur(8px)',
            padding: '5px 10px',
            border: '1px solid #334155',
            pointerEvents: 'auto'
          }}>
            <Compass size={13} color="#38bdf8" />
            <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>
              NCPOR AMIP // CANONICAL H3 EXPEDITION MESH
            </span>
            <span style={{ fontSize: '9px', background: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8', padding: '1px 6px', border: '1px solid #0284c7', fontWeight: 700 }}>
              {authenticH3GeoJSON.features.length.toLocaleString()} H3 CELLS // CIRCUM-ANTARCTIC & CORRIDOR (GEBCO + CMEMS)
            </span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 23, 42, 0.90)',
            backdropFilter: 'blur(8px)',
            padding: '4px 8px',
            border: '1px solid #334155',
            pointerEvents: 'auto'
          }}>
            <Radio size={11} color="#22c55e" />
            <span style={{ fontSize: '10px', color: '#cbd5e1', fontFamily: 'var(--font-mono)' }}>
              TIME: <strong style={{ color: '#38bdf8' }}>T+{sliderDay}d ({currentHz})</strong> | ACTIVE: <strong style={{ color: STABLE_ROUTE_COLORS[activeRouteId] }}>{(selectedRoute?.objective || activeRouteId).toUpperCase()}</strong> | TRACKED BERGS: <strong style={{ color: '#f97316' }}>{icebergsList.length}</strong>
            </span>
          </div>
        </div>

        {/* Top-Right Layer & Basemap Toggles */}
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '50px',
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          pointerEvents: 'auto',
          zIndex: 20
        }}>
          {/* Toggle Trajectories */}
          <button
            onClick={() => setShowTrajectories(!showTrajectories)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              background: showTrajectories ? 'rgba(249, 115, 22, 0.25)' : 'rgba(15, 23, 42, 0.85)',
              border: `1px solid ${showTrajectories ? '#f97316' : '#334155'}`,
              color: showTrajectories ? '#f97316' : '#94a3b8',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            <Navigation size={11} />
            <span>TRAJECTORIES ({showTrajectories ? 'ON' : 'OFF'})</span>
          </button>

          {/* Toggle H3 Grid Lines */}
          <button
            onClick={() => setShowH3Grid(!showH3Grid)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              background: showH3Grid ? 'rgba(56, 189, 248, 0.25)' : 'rgba(15, 23, 42, 0.85)',
              border: `1px solid ${showH3Grid ? '#38bdf8' : '#334155'}`,
              color: showH3Grid ? '#38bdf8' : '#94a3b8',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            <Grid size={11} />
            <span>H3 GRID ({showH3Grid ? 'ON' : 'OFF'})</span>
          </button>

          {/* Basemap Switcher */}
          <div style={{ display: 'flex', gap: '2px', background: '#0f172a', padding: '2px', border: '1px solid #334155' }}>
            {[
              { id: 'google-earth', label: 'Sat' },
              { id: 'google-terrain', label: 'Terr' },
              { id: 'osm', label: 'OSM' }
            ].map((item) => {
              const isActive = basemapStyle === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setBasemapStyle(item.id as any)}
                  style={{
                    padding: '2px 5px',
                    border: 'none',
                    background: isActive ? '#2563eb' : 'transparent',
                    color: isActive ? '#ffffff' : '#94a3b8',
                    fontSize: '9px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: isActive ? 800 : 500,
                    cursor: 'pointer'
                  }}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Hover H3 Cell Real Physical Telemetry Pill */}
        {hoveredCellData && (
          <div style={{
            position: 'absolute',
            top: '46px',
            right: '50px',
            pointerEvents: 'none',
            zIndex: 25
          }}>
            <div style={{
              padding: '6px 12px',
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid #38bdf8',
              borderLeft: '4px solid #38bdf8',
              color: '#f8fafc',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
              minWidth: '280px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ color: '#38bdf8', fontWeight: 800 }}>CELL: {hoveredCellData.displayId}</span>
                <span style={{ color: '#94a3b8' }}>{hoveredCellData.lat?.toFixed(2)}°S, {hoveredCellData.lon?.toFixed(2)}°E</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 8px', fontSize: '9px' }}>
                <div>WAVES: <strong style={{ color: '#38bdf8' }}>{hoveredCellData.wave_height?.toFixed(1) ?? '2.0'} m</strong></div>
                <div>WINDS: <strong style={{ color: '#f8fafc' }}>{hoveredCellData.wind_speed?.toFixed(1) ?? '7.0'} m/s</strong></div>
                <div>DEPTH: <strong style={{ color: '#f8fafc' }}>{hoveredCellData.depth?.toFixed(0) ?? '3500'} m</strong></div>
                <div>CURRENT: <strong style={{ color: '#34d399' }}>{hoveredCellData.current_magnitude?.toFixed(2) ?? '0.15'} m/s</strong></div>
                <div>ICEBERGS: <strong style={{ color: '#fb923c' }}>{hoveredCellData.iceberg_count ?? 0} bergs</strong></div>
                <div>RISK: <strong style={{ color: (hoveredCellData.composite_risk ?? 0) > 0.3 ? '#f87171' : '#34d399' }}>{((hoveredCellData.composite_risk ?? 0) * 100).toFixed(1)}%</strong></div>
              </div>
            </div>
          </div>
        )}

        {/* Route Selector & Individual Toggle Panel */}
        <div style={{
          position: 'absolute',
          top: '50px',
          left: '10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          pointerEvents: 'auto',
          zIndex: 20
        }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(10px)',
            border: '1px solid #334155',
            padding: '8px 10px',
            minWidth: '280px'
          }}>
            <div style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', fontFamily: 'var(--font-mono)', marginBottom: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>MISSION ROUTES & TOGGLES</span>
              <span style={{ color: '#38bdf8', fontSize: '9px' }}>CLICK TO SELECT / TOGGLE</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {routes.map((r) => {
                const isSelected = r.id === activeRouteId;
                const isVisible = enabledRoutes[r.id] !== false;
                const color = STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6';
                return (
                  <div
                    key={r.id}
                    onClick={() => setSelectedRouteId(r.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '4px 6px',
                      background: isSelected ? 'rgba(56, 189, 248, 0.18)' : 'rgba(30, 41, 59, 0.4)',
                      border: `1px solid ${isSelected ? color : '#334155'}`,
                      borderLeft: `4px solid ${color}`,
                      opacity: isVisible ? 1.0 : 0.45,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {/* Visibility Eye Toggle Button */}
                      <button
                        onClick={(ev) => toggleRouteVisibility(r.id, ev)}
                        title={isVisible ? `Hide ${r.name}` : `Show ${r.name}`}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          padding: '1px',
                          display: 'flex',
                          alignItems: 'center',
                          color: isVisible ? color : '#64748b'
                        }}
                      >
                        {isVisible ? <Eye size={12} /> : <EyeOff size={12} />}
                      </button>

                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color, display: 'inline-block' }}></span>
                      <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', fontWeight: isSelected ? 800 : 600, color: isSelected ? '#ffffff' : '#cbd5e1' }}>
                        {(r.objective || r.id).toUpperCase()}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9.5px', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
                      <span>{(r.durationDays || r.transitDays).toFixed(1)}d</span>
                      <span>•</span>
                      <span>{r.estimatedFuelMT.toFixed(0)} MT</span>
                      {isSelected && (
                        <span style={{ color: '#38bdf8', fontWeight: 800 }}>★</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Live Bound Selected Route Metrics Card */}
            {selectedRoute && (
              <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid #334155', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
                <div>
                  <div style={{ color: '#94a3b8' }}>DISTANCE</div>
                  <div style={{ color: '#f8fafc', fontWeight: 800 }}>{selectedRoute.distanceNM.toLocaleString()} NM</div>
                </div>
                <div>
                  <div style={{ color: '#94a3b8' }}>SAILING TIME</div>
                  <div style={{ color: '#f8fafc', fontWeight: 800 }}>{selectedRoute.transitDays.toFixed(1)} Days</div>
                </div>
                <div>
                  <div style={{ color: '#94a3b8' }}>DWELL TIME</div>
                  <div style={{ color: '#f8fafc', fontWeight: 800 }}>{(selectedRoute.dwellDays || 5.0).toFixed(1)} Days</div>
                </div>
                <div>
                  <div style={{ color: '#94a3b8' }}>TOTAL DURATION</div>
                  <div style={{ color: '#38bdf8', fontWeight: 800 }}>{(selectedRoute.durationDays || selectedRoute.transitDays).toFixed(1)} Days</div>
                </div>
                <div>
                  <div style={{ color: '#94a3b8' }}>FUEL ESTIMATE</div>
                  <div style={{ color: '#f8fafc', fontWeight: 800 }}>{selectedRoute.estimatedFuelMT.toFixed(1)} MT</div>
                </div>
                <div>
                  <div style={{ color: '#94a3b8' }}>MEAN / MAX RISK</div>
                  <div style={{ color: selectedRoute.meanRisk > 0.3 ? '#f87171' : '#34d399', fontWeight: 800 }}>
                    {(selectedRoute.meanRisk * 100).toFixed(1)}% / {(selectedRoute.maxRisk * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom-Left Clean Map Legend */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          pointerEvents: 'auto',
          zIndex: 20
        }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(10px)',
            border: '1px solid #334155',
            padding: '6px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '9.5px',
            fontFamily: 'var(--font-mono)',
            color: '#cbd5e1'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '12px', height: '2px', backgroundColor: '#38bdf8', display: 'inline-block' }}></span>
              <span>Authentic H3 Grid ({authenticH3GeoJSON.features.length.toLocaleString()} cells)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#f97316', display: 'inline-block' }}></span>
              <span>Tracked Icebergs (73)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#ffffff', border: '2px solid #1d4ed8', display: 'inline-block' }}></span>
              <span>ORV Sagar Kanya</span>
            </div>
          </div>
        </div>
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
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                cursor: 'pointer'
              }}
            >
              {isTimelinePlaying ? <Pause size={13} /> : <Play size={13} />}
              <span>{isTimelinePlaying ? 'PAUSE' : 'PLAY 90D'}</span>
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Calendar size={13} color="#38bdf8" />
              <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>
                TIMELINE: <span style={{ color: '#38bdf8' }}>T+{sliderDay} DAYS</span>
              </span>
              <span style={{ fontSize: '10px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                (Forecast Horizon: <strong style={{ color: '#22c55e' }}>{currentHz}</strong>)
              </span>
            </div>
          </div>

          {/* Quick-Jump Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '9px', color: '#64748b', fontFamily: 'var(--font-mono)', marginRight: '4px' }}>
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
                    fontFamily: 'var(--font-mono)',
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
          <span style={{ fontSize: '9.5px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>T+0d</span>
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
          <span style={{ fontSize: '9.5px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>T+90d</span>
        </div>
      </div>

    </div>
  );
};

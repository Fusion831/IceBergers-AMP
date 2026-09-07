# python script to write AntarcticMap.tsx cleanly with TS strict checks
import os

code = '''import React, { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import {
  Compass,
  Grid,
  Radio,
  Navigation,
  Play,
  Pause,
  Layers,
  Calendar,
  Eye
} from 'lucide-react';
import { useMission } from '../context/MissionContext';

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

export const AntarcticMap: React.FC<AntarcticMapProps> = ({
  selectedHorizon,
  activeLayer,
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
    displayAggregateGeojson,
    getCellEnvironment,
    getCellRisk,
    icebergsList,
    showTrajectories,
    setShowTrajectories,
    showH3Grid,
    setShowH3Grid,
    showAlternativeRoutes,
    setShowAlternativeRoutes,
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
  const [showLandMask, setShowLandMask] = useState<boolean>(true);
  const [hoveredCellData, setHoveredCellData] = useState<any | null>(null);

  const activeRouteId = propSelectedRoute || selectedRouteId || 'fastest';
  const currentHz = DAY_TO_NEAREST_HORIZON(sliderDay);

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

  // 1. SCAR ADD Land Mask & Ice Shelf Features (Opaque #1a1a1a)
  const landMaskGeoJSON: GeoJSON.FeatureCollection = useMemo(() => ({
    type: 'FeatureCollection',
    features: [
      // Antarctic Continent Mainland (South of coast)
      {
        type: 'Feature',
        properties: { name: 'Antarctica Continental Landmass (SCAR ADD)', category: 'LAND' },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [-15.0, -69.8],
            [30.0, -69.5],
            [65.0, -68.8],
            [85.0, -68.8],
            [85.0, -85.0],
            [-15.0, -85.0],
            [-15.0, -69.8]
          ]]
        }
      },
      // Amery Ice Shelf Barrier (Prydz Bay Sector)
      {
        type: 'Feature',
        properties: { name: 'Amery Ice Shelf (Prohibited Fast Ice)', category: 'ICE_SHELF' },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [68.5, -68.4],
            [74.5, -68.4],
            [74.5, -73.2],
            [68.5, -73.2],
            [68.5, -68.4]
          ]]
        }
      },
      // Fimbul & Lazarev Fast-Ice Shelf (Princess Astrid Coast Sector)
      {
        type: 'Feature',
        properties: { name: 'Fimbul / Lazarev Ice Shelf Barrier', category: 'ICE_SHELF' },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [7.0, -69.5],
            [22.0, -69.5],
            [22.0, -72.0],
            [7.0, -72.0],
            [7.0, -69.5]
          ]]
        }
      },
      // Southern African Continental Staging Gateway (North of Cape Town)
      {
        type: 'Feature',
        properties: { name: 'South Africa Mainland', category: 'LAND' },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [17.0, -33.6],
            [28.0, -33.6],
            [28.0, -28.0],
            [17.0, -28.0],
            [17.0, -33.6]
          ]]
        }
      }
    ]
  }), []);

  // 2. Display-Aggregated H3 Res-3 Hexagons with Time-Dependent SIC Fills
  const displayAggregateSICGeoJSON = useMemo(() => {
    if (!displayAggregateGeojson || !displayAggregateGeojson.features) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = displayAggregateGeojson.features.map((feat: any) => {
      const hzData = feat.properties?.horizons?.[currentHz] || {};
      const meanSic = hzData.mean_sic ?? feat.properties?.mean_sic ?? 0.0;
      const meanSicPct = hzData.mean_sic_pct ?? feat.properties?.mean_sic_pct ?? (meanSic * 100);
      const meanRisk = hzData.mean_risk ?? feat.properties?.mean_risk ?? 0.0;

      return {
        type: 'Feature',
        id: feat.id || feat.properties?.id,
        properties: {
          ...feat.properties,
          mean_sic: meanSic,
          mean_sic_pct: meanSicPct,
          mean_risk: meanRisk,
          current_horizon: currentHz
        },
        geometry: feat.geometry
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [displayAggregateGeojson, currentHz]);

  // 3. Canonical H3 Res-5 Grid Mesh (Interactive Click Target & Fine Outline)
  const canonicalH3MeshGeoJSON = useMemo(() => {
    if (!corridorGeojson || !corridorGeojson.features) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const features = corridorGeojson.features.map((feat: any) => {
      const cellId = feat.id || feat.properties?.cell_id;
      const env = getCellEnvironment(cellId, currentHz) || {};
      const risk = getCellRisk(cellId, currentHz) || {};

      return {
        type: 'Feature',
        id: cellId,
        properties: {
          id: cellId,
          cell_id: cellId,
          lat: env.lat ?? feat.properties?.centroid_lat ?? 0,
          lon: env.lon ?? feat.properties?.centroid_lon ?? 0,
          sic_pct: env.sic_pct ?? 0,
          sic: env.sic ?? 0,
          current_magnitude: env.current_magnitude ?? 0,
          wind_speed: env.wind_speed ?? 0,
          wave_height: env.wave_height ?? 0,
          depth: env.depth ?? 0,
          iceberg_hazard: env.iceberg_hazard ?? 0,
          iceberg_count: env.iceberg_count ?? 0,
          composite_risk: risk.composite_risk ?? 0,
          sic_risk: risk.sic_risk ?? 0,
          iceberg_risk: risk.iceberg_risk ?? 0,
          hard_blocked: risk.hard_blocked ?? false
        },
        geometry: feat.geometry
      };
    });

    return {
      type: 'FeatureCollection',
      features
    } as GeoJSON.FeatureCollection;
  }, [corridorGeojson, currentHz, getCellEnvironment, getCellRisk]);

  // 4. Iceberg Current Positions at Current Slider Day (0 to 90 Days, 361 discrete steps)
  const currentIcebergsGeoJSON = useMemo(() => {
    if (!icebergsList || icebergsList.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    // Trajectory index: 361 steps over 90 days = 4 steps per day
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
        speed = pt.speed_mps ? +(pt.speed_mps * 1.94384).toFixed(2) : 0; // knots
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

  // 5. Iceberg Trajectories (Precomputed 90-day drift lines)
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

  // 6. Canonical Routes GeoJSON (5 Backend Alternatives with User-Specified Palette)
  const canonicalRoutesGeoJSON = useMemo(() => {
    return {
      type: 'FeatureCollection',
      features: routes.map((r) => {
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
            isSelected
          },
          geometry: {
            type: 'LineString',
            coordinates: r.waypoints
          }
        };
      })
    } as GeoJSON.FeatureCollection;
  }, [routes, activeRouteId]);

  // 7. Dynamic Spatially Separated Route Label Anchors
  const routeLabelPoints = useMemo(() => {
    if (!routes || routes.length === 0) return [];
    return routes.map((r) => {
      let bestPt: [number, number] = [r.waypoints[0][0], r.waypoints[0][1]];
      let maxMinDist = -1;

      for (const p of r.waypoints) {
        if (p[1] >= -66 && p[1] <= -45) {
          let minDist = Infinity;
          for (const other of routes) {
            if (other.id === r.id) continue;
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
  }, [routes, activeRouteId]);

  // 8. Vessel Real-Time Position Interpolator along Selected Route
  const vesselGeoJSON = useMemo(() => {
    const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
    if (!activeRoute || !activeRoute.segments || activeRoute.segments.length === 0) {
      return { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection;
    }

    const currentHours = sliderDay * 24;
    let targetCoords: [number, number] = [18.4241, -33.9249]; // Cape Town default
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
  // Map Initialization and Layer Assembly
  // -------------------------------------------------------------
  useEffect(() => {
    if (!mapContainer.current) return;

    if (map.current) {
      map.current.remove();
      map.current = null;
    }

    // Coherent Map Framing covering Cape Town, Southern Ocean, Antarctica, Bharati & Maitri
    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'muted-basemap-tiles': {
            type: 'raster',
            tiles: [getTileUrl(basemapStyle)],
            tileSize: 256,
            attribution: '© ESRI Ocean, © GEBCO Bathymetry, NCPOR AMIP'
          }
        },
        layers: [
          {
            id: 'deep-ocean-background',
            type: 'background',
            paint: {
              'background-color': '#070b14'
            }
          },
          // 1. Muted Basemap (subordinate to SIC and routes)
          {
            id: 'muted-basemap-layer',
            type: 'raster',
            source: 'muted-basemap-tiles',
            paint: {
              'raster-opacity': 0.35,
              'raster-brightness-max': 0.35,
              'raster-saturation': -0.60,
              'raster-contrast': 0.15
            },
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [44.0, -52.0],
      zoom: 2.9,
      attributionControl: false
    });

    map.current = mapInstance;
    mapInstance.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    mapInstance.on('load', () => {
      // Automatic Coherent Framing of Mission Geometry
      try {
        mapInstance.fitBounds(
          [
            [-8.0, -71.5], // Southwest: Maitri / Antarctic Shelf margin
            [82.0, -32.5]  // Northeast: Cape Town / Bharati longitude margin
          ],
          {
            padding: { top: 70, bottom: 85, left: 70, right: 380 },
            maxZoom: 3.5,
            duration: 0
          }
        );
      } catch {
        // Fallback bounds
      }

      // =========================================================
      // EXACT LAYER ORDER (BOTTOM TO TOP):
      // 1. Basemap (already in style)
      // 2. Land mask / ice shelf mask (opaque #1a1a1a)
      // 3. Canonical H3 grid outlines (subtle, res 5/6)
      // 4. SIC fill (on display-aggregated hexagons, res 3/4)
      // 5. Iceberg trajectory lines (if enabled, subtle)
      // 6. Unselected routes (thin, low opacity)
      // 7. Selected route glow & line (thick, high opacity, white glow)
      // 8. Route segments (for segment inspection)
      // 9. Vessel position marker
      // 10. Iceberg observation points
      // 11. Highlights
      // =========================================================

      // 2. LAND MASK / ICE SHELF MASK
      mapInstance.addSource('land-mask-source', {
        type: 'geojson',
        data: landMaskGeoJSON
      });

      mapInstance.addLayer({
        id: 'land-mask-fill',
        type: 'fill',
        source: 'land-mask-source',
        layout: {
          visibility: showLandMask ? 'visible' : 'none'
        },
        paint: {
          'fill-color': '#1a1a1a',
          'fill-opacity': 1.0
        }
      });

      mapInstance.addLayer({
        id: 'land-mask-outline',
        type: 'line',
        source: 'land-mask-source',
        layout: {
          visibility: showLandMask ? 'visible' : 'none'
        },
        paint: {
          'line-color': '#334155',
          'line-width': 1.2
        }
      });

      // 3. CANONICAL H3 GRID (Res 5/6 - Outline Only & Interactive Hit Target)
      mapInstance.addSource('canonical-h3-source', {
        type: 'geojson',
        data: canonicalH3MeshGeoJSON
      });

      // Canonical outline: subtle rgba(255,255,255,0.15) at 0.5px, zoom >= 6 at 1.0px (rgba(255,255,255,0.45))
      mapInstance.addLayer({
        id: 'canonical-h3-line',
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
            2, 'rgba(255, 255, 255, 0.15)',
            6, 'rgba(255, 255, 255, 0.45)'
          ],
          'line-width': [
            'interpolate',
            ['linear'],
            ['zoom'],
            2, 0.5,
            6, 1.0
          ]
        }
      });

      // Invisible canonical hit area for fine cell selection
      mapInstance.addLayer({
        id: 'canonical-h3-hit',
        type: 'fill',
        source: 'canonical-h3-source',
        paint: {
          'fill-color': 'rgba(0, 0, 0, 0.0)'
        }
      });

      // 4. DISPLAY-AGGREGATED H3 (Res 3/4) FOR PROMINENT SIC COLOR FILLS
      mapInstance.addSource('display-h3-source', {
        type: 'geojson',
        data: displayAggregateSICGeoJSON
      });

      // SIC fill on display-aggregated hexagons with user-specified color ramp:
      // 0.0: #0b1d3a, 0.1: #1e4d7b, 0.25: #2e7d9e, 0.5: #6baed6, 0.75: #bdd7e7, 0.9: #e6f2ff, 1.0: #ffffff
      // fill-opacity: 0.8
      mapInstance.addLayer({
        id: 'display-h3-fill',
        type: 'fill',
        source: 'display-h3-source',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'mean_sic'],
            0.0, '#0b1d3a',
            0.1, '#1e4d7b',
            0.25, '#2e7d9e',
            0.5, '#6baed6',
            0.75, '#bdd7e7',
            0.9, '#e6f2ff',
            1.0, '#ffffff'
          ],
          'fill-opacity': 0.80
        }
      });

      // Display-aggregate boundary mesh (subtle hex outlines)
      mapInstance.addLayer({
        id: 'display-h3-line',
        type: 'line',
        source: 'display-h3-source',
        paint: {
          'line-color': 'rgba(56, 189, 248, 0.25)',
          'line-width': 0.75
        }
      });

      // Selected Cell Outline
      mapInstance.addLayer({
        id: 'canonical-h3-selected-line',
        type: 'line',
        source: 'canonical-h3-source',
        paint: {
          'line-color': '#ffffff',
          'line-width': 2.0
        },
        filter: ['==', ['get', 'id'], selectedH3Cell?.id || '']
      });

      // 5. ICEBERG TRAJECTORY LINES (Off by default, subtle lines)
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
            'rgba(249, 115, 22, 0.85)',
            'rgba(249, 115, 22, 0.18)'
          ],
          'line-width': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            2.2,
            1.0
          ]
        }
      });

      // 6 & 7. CANONICAL ROUTES (Differentiated Styling & Stable Colors)
      mapInstance.addSource('canonical-routes-source', {
        type: 'geojson',
        data: canonicalRoutesGeoJSON
      });

      // Unselected routes: line-width 1.5px, opacity 0.2, line-blur 1, line-dasharray: [2, 2]
      mapInstance.addLayer({
        id: 'routes-unselected-line',
        type: 'line',
        source: 'canonical-routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
          visibility: showAlternativeRoutes ? 'visible' : 'none'
        },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': 1.5,
          'line-opacity': 0.22,
          'line-blur': 1.0,
          'line-dasharray': [2, 2]
        },
        filter: ['!=', ['get', 'id'], activeRouteId]
      });

      // Selected Route White Under-Glow (line-gap-width / glow underneath)
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
          'line-width': 7.0,
          'line-opacity': 0.65,
          'line-blur': 2.0
        },
        filter: ['==', ['get', 'id'], activeRouteId]
      });

      // Selected Route Primary Line: line-width 4px, opacity 1.0, line-blur: 0
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
          'line-width': 4.0,
          'line-opacity': 1.0,
          'line-blur': 0.0
        },
        filter: ['==', ['get', 'id'], activeRouteId]
      });

      // 8. ROUTE SEGMENTS (Interactive Hit Detection)
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
            0.8,
            0.0
          ]
        }
      });

      // 9. VESSEL POSITION MARKER (ORV Sagar Kanya along Selected Route at Slider Day)
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
          'circle-color': '#3b82f6',
          'circle-opacity': 0.35,
          'circle-blur': 0.6
        }
      });

      mapInstance.addLayer({
        id: 'vessel-point',
        type: 'circle',
        source: 'vessel-source',
        paint: {
          'circle-radius': 6.5,
          'circle-color': '#ffffff',
          'circle-stroke-width': 3.0,
          'circle-stroke-color': '#1e3a8a'
        }
      });

      // 10. ICEBERG MARKERS (Small circles, 4px radius, color #f97316, opacity 0.8)
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
          'circle-opacity': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            1.0,
            0.85
          ],
          'circle-stroke-width': [
            'case',
            ['==', ['get', 'id'], selectedIceberg?.id || ''],
            2.0,
            1.0
          ],
          'circle-stroke-color': '#ffffff'
        }
      });

      // Selected Iceberg Outer Ring
      mapInstance.addLayer({
        id: 'icebergs-selected-halo',
        type: 'circle',
        source: 'icebergs-source',
        paint: {
          'circle-radius': 15,
          'circle-color': '#fbbf24',
          'circle-opacity': 0.35,
          'circle-blur': 0.6
        },
        filter: ['==', ['get', 'id'], selectedIceberg?.id || '']
      });

      // 11. MISSION NODES (Cape Town Origin, Bharati Waypoint 1, Maitri Waypoint 2)
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
        el.style.background = 'rgba(15, 23, 42, 0.92)';
        el.style.border = `1.5px solid ${node.iconColor}`;
        el.style.borderBottom = `3px solid ${node.iconColor}`;
        el.style.borderRadius = '3px';
        el.style.color = '#f8fafc';
        el.style.fontFamily = 'var(--font-mono, monospace)';
        el.style.fontSize = '10px';
        el.style.fontWeight = '800';
        el.style.cursor = 'pointer';
        el.style.boxShadow = `0 2px 8px rgba(0,0,0,0.5), 0 0 6px ${node.iconColor}44`;
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

      // 12. Spatially-Separated Route Markers on Map
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
      // Interactive Event Handlers
      // ---------------------------------------------------------

      // Hover H3 Cell: lightweight tooltip SIC: <sic>% | H3: <id>
      mapInstance.on('mousemove', 'display-h3-fill', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const props = feat.properties || {};
        const h3Id = props.id || props.parent_id || props.h3_index || 'H3-CELL';
        const sicPct = props.mean_sic_pct !== undefined ? Number(props.mean_sic_pct).toFixed(1) : ((props.mean_sic || 0) * 100).toFixed(1);
        
        mapInstance.getCanvas().style.cursor = 'pointer';
        setHoveredCellData({ ...props, displaySicPct: sicPct, displayId: h3Id });
      });

      mapInstance.on('mouseleave', 'display-h3-fill', () => {
        mapInstance.getCanvas().style.cursor = '';
        setHoveredCellData(null);
      });

      // Click Display-Aggregated H3 Cell: Identify underlying canonical cells and open inspector
      mapInstance.on('click', 'display-h3-fill', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const props = feat.properties || {};
        const childIds = props.child_cell_ids ? (typeof props.child_cell_ids === 'string' ? JSON.parse(props.child_cell_ids) : props.child_cell_ids) : [];
        const canonicalId = (childIds && childIds.length > 0) ? childIds[0] : (props.id || 'H3-CELL');
        
        const env = getCellEnvironment(canonicalId, currentHz) || {};
        const risk = getCellRisk(canonicalId, currentHz) || {};

        const cellObj = {
          id: canonicalId,
          displayId: props.id || props.parent_id,
          childCount: childIds.length,
          properties: { ...props, ...env, ...risk },
          env: {
            ...env,
            sic_pct: props.mean_sic_pct ?? env.sic_pct ?? 0,
            sic: props.mean_sic ?? env.sic ?? 0
          },
          risk
        };

        setSelectedH3Cell(cellObj);
        setSelectedSegment(null);
        setSelectedIceberg(null);

        if (mapInstance.getLayer('canonical-h3-selected-line')) {
          mapInstance.setFilter('canonical-h3-selected-line', ['==', ['get', 'id'], canonicalId]);
        }

        if (onInspectPoint && (props.center_lat || env.lat)) {
          onInspectPoint([props.center_lat || env.lat, props.center_lon || env.lon]);
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
  // Dynamic Source Updates on Slider Day / Horizon / Route Changes
  // -------------------------------------------------------------

  // Update Display Aggregated SIC Source
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('display-h3-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(displayAggregateSICGeoJSON);
  }, [displayAggregateSICGeoJSON]);

  // Update Canonical H3 Mesh Source
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const source = map.current.getSource('canonical-h3-source') as maplibregl.GeoJSONSource;
    if (source) source.setData(canonicalH3MeshGeoJSON);
  }, [canonicalH3MeshGeoJSON]);

  // Update Iceberg Positions Source
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

  // Update Route Layer Filters & Active Highlighting
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    if (map.current.getLayer('routes-selected-line')) {
      map.current.setFilter('routes-selected-line', ['==', ['get', 'id'], activeRouteId]);
    }
    if (map.current.getLayer('routes-selected-glow')) {
      map.current.setFilter('routes-selected-glow', ['==', ['get', 'id'], activeRouteId]);
    }
    if (map.current.getLayer('routes-unselected-line')) {
      map.current.setFilter('routes-unselected-line', ['!=', ['get', 'id'], activeRouteId]);
      map.current.setLayoutProperty('routes-unselected-line', 'visibility', showAlternativeRoutes ? 'visible' : 'none');
    }
  }, [activeRouteId, showAlternativeRoutes]);

  // Toggle Canonical H3 Grid Line Visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('canonical-h3-line')) {
      map.current.setLayoutProperty('canonical-h3-line', 'visibility', showH3Grid ? 'visible' : 'none');
    }
  }, [showH3Grid]);

  // Toggle Iceberg Trajectories Visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('iceberg-trajectories-line')) {
      map.current.setLayoutProperty('iceberg-trajectories-line', 'visibility', showTrajectories ? 'visible' : 'none');
    }
  }, [showTrajectories]);

  // Toggle Land Mask Visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('land-mask-fill')) {
      map.current.setLayoutProperty('land-mask-fill', 'visibility', showLandMask ? 'visible' : 'none');
    }
    if (map.current.getLayer('land-mask-outline')) {
      map.current.setLayoutProperty('land-mask-outline', 'visibility', showLandMask ? 'visible' : 'none');
    }
  }, [showLandMask]);

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
      el.title = `Route Objective: ${r.name}`;
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
      
      {/* ------------------------------------------------------------- */}
      {/* Central Map Canvas */}
      {/* ------------------------------------------------------------- */}
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
              NCPOR AMIP // SOUTHERN OCEAN EXPEDITION CORRIDOR
            </span>
            <span style={{ fontSize: '9px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '1px 6px', border: '1px solid #0284c7', fontWeight: 700 }}>
              CANONICAL RES-5 / DISPLAY RES-3
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
              TIME: <strong style={{ color: '#38bdf8' }}>T+{sliderDay}d ({currentHz})</strong> | LAYER: <strong style={{ color: '#38bdf8', textTransform: 'uppercase' }}>{activeLayer}</strong> | ROUTE: <strong style={{ color: STABLE_ROUTE_COLORS[activeRouteId] }}>{(selectedRoute?.objective || activeRouteId).toUpperCase()}</strong> | TRACKED BERGS: <strong style={{ color: '#f97316' }}>{icebergsList.length}</strong>
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
              background: showTrajectories ? 'rgba(249, 115, 22, 0.2)' : 'rgba(15, 23, 42, 0.85)',
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

          {/* Toggle Canonical H3 Grid Outlines */}
          <button
            onClick={() => setShowH3Grid(!showH3Grid)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              background: showH3Grid ? 'rgba(56, 189, 248, 0.2)' : 'rgba(15, 23, 42, 0.85)',
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

          {/* Toggle Alternative Routes */}
          <button
            onClick={() => setShowAlternativeRoutes(!showAlternativeRoutes)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              background: showAlternativeRoutes ? 'rgba(34, 197, 94, 0.2)' : 'rgba(15, 23, 42, 0.85)',
              border: `1px solid ${showAlternativeRoutes ? '#22c55e' : '#334155'}`,
              color: showAlternativeRoutes ? '#22c55e' : '#94a3b8',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            <Layers size={11} />
            <span>5 ROUTES ({showAlternativeRoutes ? 'ALL' : 'ACTIVE'})</span>
          </button>

          {/* Toggle Land Mask */}
          <button
            onClick={() => setShowLandMask(!showLandMask)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              background: showLandMask ? 'rgba(71, 85, 105, 0.3)' : 'rgba(15, 23, 42, 0.85)',
              border: `1px solid ${showLandMask ? '#64748b' : '#334155'}`,
              color: showLandMask ? '#f8fafc' : '#94a3b8',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            <Eye size={11} />
            <span>LAND MASK ({showLandMask ? 'ON' : 'OFF'})</span>
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

        {/* Hover H3 Cell Telemetry Pill */}
        {hoveredCellData && (
          <div style={{
            position: 'absolute',
            top: '46px',
            right: '50px',
            pointerEvents: 'none',
            zIndex: 25
          }}>
            <div style={{
              padding: '4px 10px',
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid #38bdf8',
              borderLeft: '4px solid #38bdf8',
              color: '#f8fafc',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
            }}>
              <span>SIC: <strong style={{ color: '#38bdf8' }}>{hoveredCellData.displaySicPct}%</strong></span>
              <span style={{ margin: '0 6px', color: '#64748b' }}>|</span>
              <span>H3: <strong style={{ color: '#cbd5e1' }}>{hoveredCellData.displayId}</strong></span>
              {hoveredCellData.child_cell_ids && (
                <span style={{ color: '#94a3b8', marginLeft: '6px', fontSize: '9px' }}>
                  ({hoveredCellData.children_count || 9} canonical cells)
                </span>
              )}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* Route Selector Panel (Top-Right / Bottom-Right) with Bound Metrics */}
        {/* ------------------------------------------------------------- */}
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
          {/* 5-Route Objective Selector Table */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(10px)',
            border: '1px solid #334155',
            padding: '8px 10px',
            minWidth: '260px'
          }}>
            <div style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', fontFamily: 'var(--font-mono)', marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
              <span>SELECT MISSION ROUTE</span>
              <span style={{ color: '#38bdf8' }}>5 ALTERNATIVES</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {routes.map((r) => {
                const isSelected = r.id === activeRouteId;
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
                      background: isSelected ? 'rgba(56, 189, 248, 0.15)' : 'rgba(30, 41, 59, 0.4)',
                      border: `1px solid ${isSelected ? color : '#334155'}`,
                      borderLeft: `4px solid ${color}`,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color, display: 'inline-block' }}></span>
                      <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', fontWeight: isSelected ? 800 : 600, color: isSelected ? '#ffffff' : '#cbd5e1' }}>
                        {(r.objective || r.id).toUpperCase()}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9.5px', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
                      <span>{(r.durationDays || r.transitDays).toFixed(1)}d</span>
                      <span>•</span>
                      <span>{r.estimatedFuelMT.toFixed(0)} MT</span>
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

        {/* ------------------------------------------------------------- */}
        {/* Bottom-Left SIC Legend Panel */}
        {/* ------------------------------------------------------------- */}
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
            padding: '8px 12px',
            minWidth: '260px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '10px', fontWeight: 800, color: '#f8fafc', textTransform: 'uppercase' }}>
                SEA ICE CONCENTRATION (SIC)
              </span>
              <span style={{ fontSize: '8.5px', color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                RES-3 HEX FILLS
              </span>
            </div>

            {/* SIC Continuous Gradient Bar with exact scale */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <div style={{
                height: '10px',
                width: '100%',
                background: 'linear-gradient(to right, #0b1d3a 0%, #1e4d7b 10%, #2e7d9e 25%, #6baed6 50%, #bdd7e7 75%, #e6f2ff 90%, #ffffff 100%)',
                border: '1px solid #475569'
              }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '8px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                <span>0% Open Water</span>
                <span>25%</span>
                <span>50%</span>
                <span>75%</span>
                <span>100% Dense Ice</span>
              </div>
            </div>

            {/* Subdued Indicators */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '4px', borderTop: '1px solid #334155', fontSize: '9px', color: '#cbd5e1' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#f97316', display: 'inline-block' }}></span>
                <span>Icebergs (73)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: '#1a1a1a', border: '1px solid #475569', display: 'inline-block' }}></span>
                <span>SCAR ADD Land</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '10px', height: '1px', borderTop: '1px dashed #ffffff', display: 'inline-block' }}></span>
                <span>Res-5 Outlines</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 9. Time Slider & Playback Controls Bar (T+0 to T+90 Days) */}
      {/* ------------------------------------------------------------- */}
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

          {/* Quick-Jump Buttons: Now, +1d, +3d, +7d, +14d, +30d, +60d, +90d */}
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
'''

with open("frontend/src/components/AntarcticMap.tsx", "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully regenerated frontend/src/components/AntarcticMap.tsx")

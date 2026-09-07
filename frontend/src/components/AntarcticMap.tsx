import React, { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import { Compass, Grid, AlertOctagon, Radio } from 'lucide-react';
import { useMission } from '../context/MissionContext';
import { GridCell } from '../types/mission';
import { createSmoothFlowPath } from '../utils/routeGeometry';

interface AntarcticMapProps {
  selectedHorizon: string;
  activeLayer: 'sic' | 'icebergs' | 'risk' | 'weather';
  selectedRoute: string;
  onHorizonChange?: (hz: string) => void;
  onInspectPoint?: (coords: [number, number]) => void;
}

export const AntarcticMap: React.FC<AntarcticMapProps> = ({
  selectedHorizon,
  activeLayer,
  selectedRoute,
  onHorizonChange,
  onInspectPoint
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const { routes, timeHorizon, setTimeHorizon } = useMission();
  const [basemapStyle, setBasemapStyle] = useState<'google-earth' | 'google-terrain' | 'osm'>('google-earth');
  const [showGridMesh, setShowGridMesh] = useState<boolean>(true);
  const [showHardConstraints, setShowHardConstraints] = useState<boolean>(true);
  const [hoveredCell, setHoveredCell] = useState<GridCell | null>(null);

  const discreteHorizons = ['Now', '+1d', '+3d', '+7d', '+14d', '+30d', '+60d', '+90d'] as const;

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

  // 1. Generate Polar Navigation Grid Mesh
  const polarGridData = useMemo(() => {
    const cells: GridCell[] = [];
    const features: GeoJSON.Feature[] = [];

    const lonStep = 3.0;
    const latStep = 2.5;

    for (let lat = -32.5; lat >= -71.5; lat -= latStep) {
      for (let lon = 10.0; lon <= 85.0; lon += lonStep) {
        const id = `GRID-${Math.abs(Math.round(lat))}-${Math.round(lon)}`;
        const center: [number, number] = [lon + lonStep / 2, lat - latStep / 2];
        const bounds: [[number, number], [number, number], [number, number], [number, number]] = [
          [lon, lat],
          [lon + lonStep, lat],
          [lon + lonStep, lat - latStep],
          [lon, lat - latStep]
        ];

        const isAfricanLand = lat > -34.8 && lon > 18.5 && lon < 32.5;

        let sicPct = 0;
        let status: GridCell['status'] = 'Open Water';
        let cost = 1.0;
        let passable = true;
        let icebergCount = 0;
        let waveHeightM = 2.5;

        if (isAfricanLand) {
          status = 'Land / Ice Shelf';
          passable = false;
          cost = 99.0;
          sicPct = 0;
        } else if (lat < -69.0 && (lon < 30.0 || lon > 78.0)) {
          status = 'Land / Ice Shelf';
          sicPct = 95;
          cost = 9.5;
          passable = false;
          icebergCount = 8;
          waveHeightM = 0.5;
        } else if (lat < -66.5) {
          status = 'Heavy Pack';
          sicPct = 68;
          cost = 5.2;
          icebergCount = 4;
          waveHeightM = 1.4;
        } else if (lat < -60.0) {
          status = 'Marginal Ice';
          sicPct = Math.min(45, Math.round(Math.abs(lat + 60) * 6));
          cost = 2.4 + (sicPct / 25);
          icebergCount = Math.floor(Math.random() * 4) + 1;
          waveHeightM = 3.2;
        } else if (lat < -40.0) {
          status = 'Open Water';
          sicPct = 0;
          cost = 1.4;
          waveHeightM = 4.8;
        }

        const cell: GridCell = {
          id,
          bounds,
          center,
          passable,
          sicPct,
          iceThicknessM: sicPct > 0 ? +(sicPct * 0.015).toFixed(2) : 0,
          icebergCount,
          waveHeightM,
          traversalCost: +cost.toFixed(1),
          status
        };

        cells.push(cell);

        features.push({
          type: 'Feature',
          properties: {
            id: cell.id,
            sicPct: cell.sicPct,
            cost: cell.traversalCost,
            status: cell.status,
            passable: cell.passable,
            icebergs: cell.icebergCount,
            waves: cell.waveHeightM
          },
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [bounds[0][0], bounds[0][1]],
              [bounds[1][0], bounds[1][1]],
              [bounds[2][0], bounds[2][1]],
              [bounds[3][0], bounds[3][1]],
              [bounds[0][0], bounds[0][1]]
            ]]
          }
        });
      }
    }

    return {
      cells,
      geojson: {
        type: 'FeatureCollection',
        features
      } as GeoJSON.FeatureCollection
    };
  }, []);

  // 2. Hard Navigational Constraints GeoJSON (Crisp Red #dc2626 Hazard Zones)
  const hardConstraintsGeoJSON: GeoJSON.FeatureCollection = useMemo(() => ({
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: {
          name: 'PROHIBITED HEAVY FAST-ICE ZONE (LAZAREV APPROACH)',
          type: 'HARD_CONSTRAINT',
          severity: 'NO-GO'
        },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [8.0, -68.5],
            [22.0, -68.5],
            [22.0, -71.5],
            [8.0, -71.5],
            [8.0, -68.5]
          ]]
        }
      },
      {
        type: 'Feature',
        properties: {
          name: 'AMERY ICE SHELF CALVING HAZARD & DENSE MULTI-YEAR PACK',
          type: 'HARD_CONSTRAINT',
          severity: 'NO-GO'
        },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [68.0, -68.0],
            [74.0, -68.0],
            [74.0, -71.5],
            [68.0, -71.5],
            [68.0, -68.0]
          ]]
        }
      },
      {
        type: 'Feature',
        properties: {
          name: 'SHALLOW VOLCANIC SHOAL & ICEBERG PINNING REEF',
          type: 'HARD_CONSTRAINT',
          severity: 'NO-GO'
        },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [48.0, -47.0],
            [53.0, -47.0],
            [53.0, -49.5],
            [48.0, -49.5],
            [48.0, -47.0]
          ]]
        }
      }
    ]
  }), []);

  // 3. Ice-Edge Boundary Line GeoJSON (15% SIC Marginal Ice Boundary)
  const iceEdgeBoundaryGeoJSON: GeoJSON.FeatureCollection = useMemo(() => ({
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: {
          name: '15% SIC Marginal Sea-Ice Extent (SAR-Derived)',
          type: 'ICE_EDGE'
        },
        geometry: {
          type: 'LineString',
          coordinates: [
            [10.0, -60.2],
            [20.0, -59.8],
            [30.0, -60.5],
            [40.0, -61.2],
            [50.0, -60.8],
            [60.0, -61.5],
            [70.0, -62.0],
            [80.0, -61.8],
            [85.0, -62.4]
          ]
        }
      }
    ]
  }), []);

  // 4. Observed Iceberg Radar Scatter Points GeoJSON (Solid Orange #ea580c)
  const icebergScatterGeoJSON: GeoJSON.FeatureCollection = useMemo(() => ({
    type: 'FeatureCollection',
    features: [
      { type: 'Feature', properties: { id: 'BERG-A23A-T1', size: 'Giant Tabular (>20km)', drift: '0.6 kts @ 045°' }, geometry: { type: 'Point', coordinates: [42.5, -58.2] } },
      { type: 'Feature', properties: { id: 'BERG-B15-FRAG', size: 'Medium Tabular (5km)', drift: '0.4 kts @ 060°' }, geometry: { type: 'Point', coordinates: [48.2, -59.5] } },
      { type: 'Feature', properties: { id: 'BERG-PB-088', size: 'Small Pinnacled', drift: '0.8 kts @ 030°' }, geometry: { type: 'Point', coordinates: [68.4, -64.1] } },
      { type: 'Feature', properties: { id: 'BERG-PB-092', size: 'Bergy Bit Cluster', drift: '0.5 kts @ 040°' }, geometry: { type: 'Point', coordinates: [72.1, -65.3] } },
      { type: 'Feature', properties: { id: 'BERG-MA-014', size: 'Large Blocky (8km)', drift: '0.3 kts @ 080°' }, geometry: { type: 'Point', coordinates: [18.8, -65.2] } },
      { type: 'Feature', properties: { id: 'BERG-CROZET-04', size: 'Growler Swarm', drift: '1.1 kts @ 090°' }, geometry: { type: 'Point', coordinates: [52.3, -48.8] } },
      { type: 'Feature', properties: { id: 'BERG-SO-209', size: 'Medium Tabular (3km)', drift: '0.7 kts @ 055°' }, geometry: { type: 'Point', coordinates: [34.5, -55.4] } }
    ]
  }), []);

  useEffect(() => {
    if (!mapContainer.current) return;

    if (map.current) {
      map.current.remove();
      map.current = null;
    }

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'light-ocean-tiles': {
            type: 'raster',
            tiles: [getTileUrl(basemapStyle)],
            tileSize: 256,
            attribution: '© ESRI Ocean, © GEBCO Bathymetry, NCPOR AMIP'
          }
        },
        layers: [
          {
            id: 'light-ocean-layer',
            type: 'raster',
            source: 'light-ocean-tiles',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [48.0, -52.0],
      zoom: 3.2,
      attributionControl: false
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    map.current.on('load', () => {
      if (!map.current) return;

      // 1. Add Polar Navigation Grid Mesh
      map.current.addSource('polar-grid-source', {
        type: 'geojson',
        data: polarGridData.geojson
      });

      // Grid Fill (Scientific Stepped Scale Overlay)
      map.current.addLayer({
        id: 'polar-grid-fill',
        type: 'fill',
        source: 'polar-grid-source',
        layout: {
          visibility: showGridMesh ? 'visible' : 'none'
        },
        paint: {
          'fill-color': [
            'case',
            ['==', ['get', 'passable'], false], 'rgba(51, 65, 85, 0.85)',
            [
              'interpolate',
              ['linear'],
              ['get', 'cost'],
              1.0, 'rgba(68, 1, 84, 0.45)',   // Viridis Low (#440154)
              2.5, 'rgba(59, 82, 139, 0.50)', // Viridis Med-Low (#3b528b)
              4.5, 'rgba(33, 145, 140, 0.55)', // Viridis Med (#21918c)
              6.5, 'rgba(94, 201, 98, 0.60)', // Viridis Med-High (#5ec962)
              9.0, 'rgba(253, 231, 37, 0.70)'  // Viridis High (#fde725)
            ]
          ],
          'fill-opacity': 0.85
        }
      });

      // Grid Outline (Crisp Blue-Gray)
      map.current.addLayer({
        id: 'polar-grid-line',
        type: 'line',
        source: 'polar-grid-source',
        layout: {
          visibility: showGridMesh ? 'visible' : 'none'
        },
        paint: {
          'line-color': '#94a3b8',
          'line-width': 1.0,
          'line-dasharray': [1, 2]
        }
      });

      // Grid Hover Highlight (Solid Maritime Blue)
      map.current.addLayer({
        id: 'polar-grid-hover',
        type: 'line',
        source: 'polar-grid-source',
        paint: {
          'line-color': '#2563eb',
          'line-width': 2.5
        },
        filter: ['==', ['get', 'id'], '']
      });

      // 2. Hard Navigational Constraints Layers (Crisp Red #dc2626 Hazard Zones)
      map.current.addSource('hard-constraints-source', {
        type: 'geojson',
        data: hardConstraintsGeoJSON
      });

      map.current.addLayer({
        id: 'hard-constraints-fill',
        type: 'fill',
        source: 'hard-constraints-source',
        layout: {
          visibility: showHardConstraints ? 'visible' : 'none'
        },
        paint: {
          'fill-color': '#dc2626',
          'fill-opacity': 0.25
        }
      });

      map.current.addLayer({
        id: 'hard-constraints-line',
        type: 'line',
        source: 'hard-constraints-source',
        layout: {
          visibility: showHardConstraints ? 'visible' : 'none'
        },
        paint: {
          'line-color': '#dc2626',
          'line-width': 2.0,
          'line-dasharray': [3, 2]
        }
      });

      // 3. Ice-Edge Boundary Layer (15% SIC Extent - Solid Dark Blue #1e3a8a)
      map.current.addSource('ice-edge-source', {
        type: 'geojson',
        data: iceEdgeBoundaryGeoJSON
      });

      map.current.addLayer({
        id: 'ice-edge-line',
        type: 'line',
        source: 'ice-edge-source',
        paint: {
          'line-color': '#1e3a8a',
          'line-width': 2.0,
          'line-dasharray': [4, 3]
        }
      });

      // 4. Observed Iceberg Scatter Layer (Solid Orange #ea580c)
      map.current.addSource('icebergs-source', {
        type: 'geojson',
        data: icebergScatterGeoJSON
      });

      map.current.addLayer({
        id: 'icebergs-point',
        type: 'circle',
        source: 'icebergs-source',
        paint: {
          'circle-radius': 4.5,
          'circle-color': '#ea580c',
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#ffffff'
        }
      });

      // 5. Stations & Gateways
      const stations = [
        { name: 'Bharati Station', coords: [76.19, -69.41] as [number, number], desc: 'Larsemann Hills (69°24′S, 76°11′E)', color: '#0d9488' },
        { name: 'Maitri Gateway (India Bay)', coords: [11.73, -69.95] as [number, number], desc: 'Princess Astrid Coast (70°46′S, 11°44′E)', color: '#0d9488' },
        { name: 'Cape Town Staging Port', coords: [18.42, -33.92] as [number, number], desc: 'Table Bay Marine Supply Base', color: '#ea580c' },
        { name: 'Mormugao Port (NCPOR HQ)', coords: [73.82, 15.40] as [number, number], desc: 'National Polar Operations HQ', color: '#2563eb' }
      ];

      stations.forEach(st => {
        const el = document.createElement('div');
        el.style.width = '14px';
        el.style.height = '14px';
        el.style.borderRadius = '0px';
        el.style.backgroundColor = st.color;
        el.style.border = '1.5px solid #ffffff';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.fontSize = '8px';
        el.style.fontWeight = 'bold';
        el.style.color = '#ffffff';
        el.style.cursor = 'pointer';
        el.innerText = '■';

        new maplibregl.Marker({ element: el })
          .setLngLat(st.coords)
          .setPopup(
            new maplibregl.Popup({ offset: 15 }).setHTML(`
              <div style="color: #0f172a; background: #ffffff; border: 1.5px solid #bfdbfe; padding: 6px 10px; font-family: monospace; min-width: 180px; border-radius: 0px;">
                <strong style="font-size: 11px; color: ${st.color};">${st.name}</strong>
                <p style="font-size: 9.5px; margin: 3px 0 0 0; color: #64748b;">${st.desc}</p>
                <div style="margin-top: 4px; font-size: 9px; color: #0f172a; font-family: monospace; background: #f0f7ff; padding: 2px 6px; border: 1px solid #bfdbfe;">
                  LAT: ${Math.abs(st.coords[1])}°S | LON: ${st.coords[0]}°E
                </div>
              </div>
            `)
          )
          .addTo(map.current!);
      });

      // 6. Navigation Route Lines - Smooth Hydrodynamic Flow Curves
      const routesGeoJSON: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: routes.map(r => ({
          type: 'Feature',
          properties: {
            id: r.id,
            name: r.name,
            color: r.type === 'safest' ? '#1e3a8a' : r.type === 'fastest' ? '#ea580c' : '#0d9488',
            distance: r.distanceNM,
            eta: r.transitDays,
            fuel: r.estimatedFuelMT
          },
          geometry: {
            type: 'LineString',
            coordinates: createSmoothFlowPath(r.waypoints, 32)
          }
        }))
      };

      map.current.addSource('routes-source', {
        type: 'geojson',
        data: routesGeoJSON
      });

      // Soft ambient halo layer for active selected route
      map.current.addLayer({
        id: 'routes-halo',
        type: 'line',
        source: 'routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['get', 'color'] as any,
          'line-width': [
            'case',
            ['==', ['get', 'id'], selectedRoute],
            9.0,
            0.0
          ] as any,
          'line-opacity': 0.25,
          'line-blur': 3.0
        }
      });

      // Core crisp flowing route line
      map.current.addLayer({
        id: 'routes-line',
        type: 'line',
        source: 'routes-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['get', 'color'] as any,
          'line-width': [
            'case',
            ['==', ['get', 'id'], selectedRoute],
            4.5,
            2.5
          ] as any,
          'line-opacity': 0.95
        }
      });

      // Waypoint clicks
      map.current.on('click', (e) => {
        if (onInspectPoint) {
          onInspectPoint([+e.lngLat.lat.toFixed(2), +e.lngLat.lng.toFixed(2)]);
        }
      });

      // Grid Cell Hover
      map.current.on('mousemove', 'polar-grid-fill', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const cellId = feat.properties?.id;
        if (cellId && map.current) {
          map.current.setFilter('polar-grid-hover', ['==', ['get', 'id'], cellId]);
          const found = polarGridData.cells.find(c => c.id === cellId);
          if (found) {
            setHoveredCell(found);
          }
        }
      });

      map.current.on('mouseleave', 'polar-grid-fill', () => {
        if (map.current) {
          map.current.setFilter('polar-grid-hover', ['==', ['get', 'id'], '']);
          setHoveredCell(null);
        }
      });
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, [basemapStyle, polarGridData, hardConstraintsGeoJSON, iceEdgeBoundaryGeoJSON, icebergScatterGeoJSON]);

  // Update route highlight and halo when selectedRoute changes
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('routes-line')) {
      map.current.setPaintProperty('routes-line', 'line-width', [
        'case',
        ['==', ['get', 'id'], selectedRoute],
        4.5,
        2.5
      ] as any);
    }
    if (map.current.getLayer('routes-halo')) {
      map.current.setPaintProperty('routes-halo', 'line-width', [
        'case',
        ['==', ['get', 'id'], selectedRoute],
        9.0,
        0.0
      ] as any);
    }
  }, [selectedRoute]);

  // Toggle Grid Mesh Layer Visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('polar-grid-fill')) {
      map.current.setLayoutProperty('polar-grid-fill', 'visibility', showGridMesh ? 'visible' : 'none');
    }
    if (map.current.getLayer('polar-grid-line')) {
      map.current.setLayoutProperty('polar-grid-line', 'visibility', showGridMesh ? 'visible' : 'none');
    }
  }, [showGridMesh]);

  // Toggle Hard Constraints Visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    if (map.current.getLayer('hard-constraints-fill')) {
      map.current.setLayoutProperty('hard-constraints-fill', 'visibility', showHardConstraints ? 'visible' : 'none');
    }
    if (map.current.getLayer('hard-constraints-line')) {
      map.current.setLayoutProperty('hard-constraints-line', 'visibility', showHardConstraints ? 'visible' : 'none');
    }
  }, [showHardConstraints]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      
      {/* Central Map Canvas */}
      <div style={{ flex: 1, position: 'relative', minHeight: '380px' }}>
        <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

        {/* Top-Left Telemetry HUD Strip */}
        <div style={{
          position: 'absolute',
          top: '8px',
          left: '8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          pointerEvents: 'none'
        }}>
          <div className="ws-panel" style={{ padding: '4px 8px', pointerEvents: 'auto', flexDirection: 'row', alignItems: 'center', gap: '6px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <Compass size={13} color="#2563eb" />
            <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#172554' }}>
              POLAR ROUTE MESH // CAPE TOWN ➔ PRYDZ BAY (BHARATI)
            </span>
          </div>

          <div className="ws-panel" style={{ padding: '3px 8px', pointerEvents: 'auto', flexDirection: 'row', alignItems: 'center', gap: '6px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <Radio size={11} color="#0d9488" />
            <span style={{ fontSize: '10px', color: '#1e293b', fontFamily: 'var(--font-mono)' }}>
              HORIZON: <strong style={{ color: '#2563eb' }}>{selectedHorizon}</strong> | LAYER: <strong style={{ color: '#0d9488', textTransform: 'uppercase' }}>{activeLayer}</strong> | DATUM: WGS84
            </span>
          </div>
        </div>

        {/* Top-Right Basemap & Constraint Controls */}
        <div style={{
          position: 'absolute',
          top: '8px',
          right: '50px',
          pointerEvents: 'auto',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          {/* Toggle Hard Constraints */}
          <button
            onClick={() => setShowHardConstraints(!showHardConstraints)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              borderRadius: '0px',
              background: showHardConstraints ? '#fef2f2' : '#ffffff',
              border: '1px solid',
              borderColor: showHardConstraints ? '#dc2626' : '#bfdbfe',
              borderBottom: showHardConstraints ? '3px solid #b91c1c' : '3px solid #93c5fd',
              color: showHardConstraints ? '#dc2626' : '#1e293b',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: showHardConstraints ? '0 2px 0 #b91c1c, 0 2px 4px rgba(220,38,38,0.2)' : '0 2px 0 #93c5fd, 0 2px 4px rgba(37,99,235,0.08)'
            }}
          >
            <AlertOctagon size={11} />
            <span>HARD CONSTRAINTS ({showHardConstraints ? 'ON' : 'OFF'})</span>
          </button>

          {/* Toggle Grid Mesh */}
          <button
            onClick={() => setShowGridMesh(!showGridMesh)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              borderRadius: '0px',
              background: showGridMesh ? '#eff6ff' : '#ffffff',
              border: '1px solid',
              borderColor: showGridMesh ? '#2563eb' : '#bfdbfe',
              borderBottom: showGridMesh ? '3px solid #1d4ed8' : '3px solid #93c5fd',
              color: showGridMesh ? '#2563eb' : '#1e293b',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: showGridMesh ? '0 2px 0 #1d4ed8, 0 2px 4px rgba(37,99,235,0.2)' : '0 2px 0 #93c5fd, 0 2px 4px rgba(37,99,235,0.08)'
            }}
          >
            <Grid size={11} />
            <span>GRID MESH ({showGridMesh ? 'ON' : 'OFF'})</span>
          </button>

          {/* Basemap Switcher */}
          <div style={{ display: 'flex', gap: '3px', background: '#e0f2fe', padding: '3px', borderRadius: '0px', border: '1px solid #bfdbfe' }}>
            {[
              { id: 'google-earth', label: 'Google Satellite' },
              { id: 'google-terrain', label: 'Google Territorial' },
              { id: 'osm', label: 'OpenStreetMap' }
            ].map((item) => {
              const isActive = basemapStyle === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setBasemapStyle(item.id as any)}
                  style={{
                    padding: '4px 8px',
                    borderRadius: '0px',
                    border: '1px solid',
                    borderColor: isActive ? '#1d4ed8' : 'transparent',
                    borderBottom: isActive ? '2px solid #1e3a8a' : 'none',
                    background: isActive ? '#2563eb' : 'transparent',
                    color: isActive ? '#ffffff' : '#1e293b',
                    fontSize: '10px',
                    fontFamily: 'var(--font-sans)',
                    fontWeight: isActive ? 800 : 600,
                    cursor: 'pointer',
                    boxShadow: isActive ? '0 2px 0 #1e3a8a, 0 2px 4px rgba(30,58,138,0.25)' : 'none'
                  }}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Hover Grid Cell Telemetry Card */}
        {hoveredCell && (
          <div style={{
            position: 'absolute',
            top: '48px',
            right: '50px',
            pointerEvents: 'none',
            zIndex: 10
          }}>
            <div className="ws-card" style={{ padding: '8px 12px', minWidth: '230px', borderLeft: '4px solid #2563eb', background: '#ffffff', border: '1px solid #bfdbfe' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11.5px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#2563eb' }}>{hoveredCell.id}</span>
                <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>{hoveredCell.center[1].toFixed(1)}°S, {hoveredCell.center[0].toFixed(1)}°E</span>
              </div>
              <div style={{ marginTop: '6px', fontSize: '10.5px', fontFamily: 'var(--font-sans)', display: 'flex', flexDirection: 'column', gap: '3px', color: '#1e293b' }}>
                <div>STATUS: <strong style={{ color: hoveredCell.status === 'Open Water' ? '#0d9488' : hoveredCell.status === 'Marginal Ice' ? '#ea580c' : '#dc2626' }}>{hoveredCell.status.toUpperCase()}</strong></div>
                <div>SEA ICE CONC: <strong style={{ color: '#0f172a', fontFamily: 'var(--font-mono)' }}>{hoveredCell.sicPct}%</strong> (THICKNESS: <span style={{ color: '#0f172a', fontFamily: 'var(--font-mono)' }}>{hoveredCell.iceThicknessM}m</span>)</div>
                <div>ICEBERGS: <strong style={{ color: '#0f172a', fontFamily: 'var(--font-mono)' }}>{hoveredCell.icebergCount} / 100km²</strong></div>
                <div>WAVE HEIGHT: <strong style={{ color: '#0f172a', fontFamily: 'var(--font-mono)' }}>{hoveredCell.waveHeightM} m</strong></div>
                <div>POLAR ROUTE COST: <strong style={{ color: '#2563eb', fontFamily: 'var(--font-mono)' }}>{hoveredCell.traversalCost}x</strong></div>
              </div>
            </div>
          </div>
        )}

        {/* Bottom-Left Map Legend */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          pointerEvents: 'auto'
        }}>
          <div className="ws-panel" style={{ padding: '8px 12px', fontSize: '10.5px', fontFamily: 'var(--font-sans)', display: 'flex', flexDirection: 'column', gap: '4px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <div style={{ fontWeight: 800, color: '#172554', textTransform: 'uppercase', marginBottom: '2px', fontSize: '11px' }}>
              MARITIME LAYERS & ROUTES
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '14px', height: '3.5px', backgroundColor: '#0d9488', display: 'inline-block' }}></span>
              <span style={{ color: '#1e293b' }}>Balanced Route (Solid Teal #0d9488)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '14px', height: '3.5px', backgroundColor: '#1e3a8a', display: 'inline-block' }}></span>
              <span style={{ color: '#1e293b' }}>Safest Route (Solid Dark Blue #1e3a8a)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '14px', height: '3.5px', backgroundColor: '#ea580c', display: 'inline-block' }}></span>
              <span style={{ color: '#1e293b' }}>Fastest Route (Solid Orange #ea580c)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '14px', height: '2px', borderTop: '2px dashed #1e3a8a', display: 'inline-block' }}></span>
              <span style={{ color: '#1e293b' }}>15% SIC Marginal Ice Edge</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '0px', backgroundColor: '#ea580c', border: '1px solid #fff', display: 'inline-block' }}></span>
              <span style={{ color: '#1e293b' }}>Observed Iceberg Radar Scatter</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '14px', height: '10px', background: 'rgba(220, 38, 38, 0.25)', border: '1px dashed #dc2626', display: 'inline-block' }}></span>
              <span style={{ color: '#dc2626', fontWeight: 700 }}>Hard Navigational Constraint</span>
            </div>
          </div>
        </div>
      </div>

      {/* Discrete Forecast Horizon Stepper directly Below Map */}
      <div className="ws-panel" style={{ padding: '8px 14px', marginTop: '6px', borderTop: '1px solid #bfdbfe', background: '#f0f7ff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-sans)', color: '#172554' }}>
              ENVIRONMENTAL TIMELINE (DISCRETE LEAD HORIZONS):
            </span>
            <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-sans)' }}>
              *Deterministic step transitions without arbitrary interpolations
            </span>
          </div>

          <div style={{ display: 'flex', gap: '4px' }}>
            {discreteHorizons.map((hz) => {
              const isActive = (selectedHorizon || timeHorizon) === hz;
              return (
                <button
                  key={hz}
                  onClick={() => {
                    if (onHorizonChange) onHorizonChange(hz);
                    setTimeHorizon(hz);
                  }}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '0px',
                    fontSize: '10.5px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: isActive ? 800 : 500,
                    border: '1px solid',
                    borderColor: isActive ? '#1d4ed8' : '#bfdbfe',
                    borderBottom: isActive ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                    background: isActive ? '#2563eb' : 'rgba(255, 255, 255, 0.9)',
                    color: isActive ? '#ffffff' : '#1e293b',
                    cursor: 'pointer',
                    boxShadow: isActive ? '0 2px 0 #1e3a8a, 0 3px 5px rgba(30, 58, 138, 0.25)' : '0 2px 0 #93c5fd, 0 2px 4px rgba(37, 99, 235, 0.08)'
                  }}
                >
                  {hz}
                </button>
              );
            })}
          </div>
        </div>
      </div>

    </div>
  );
};

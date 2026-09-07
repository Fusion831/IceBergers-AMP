import React from 'react';
import { Layers, Grid, Navigation, Radio, X, Shield, Eye, EyeOff } from 'lucide-react';
import { useMission } from '../context/MissionContext';

interface MapLayersMenuProps {
  isOpen: boolean;
  onClose: () => void;
  showH3Grid: boolean;
  onToggleH3Grid: () => void;
  showIcebergs: boolean;
  onToggleIcebergs: () => void;
  showTrajectories: boolean;
  onToggleTrajectories: () => void;
  basemapStyle: 'google-earth' | 'google-terrain' | 'osm';
  onChangeBasemap: (style: 'google-earth' | 'google-terrain' | 'osm') => void;
  hoveredCellData: any | null;
  onOpenRiskVisualizer?: () => void;
}

const ROUTE_INFO: Array<{ id: string; name: string; color: string; objective: string }> = [
  { id: 'fastest', name: 'Fastest Corridor', color: '#3b82f6', objective: 'Transit Time' },
  { id: 'shortest', name: 'Shortest Corridor', color: '#f59e0b', objective: 'Least Distance' },
  { id: 'safest', name: 'Safest Corridor', color: '#10b981', objective: 'Lowest Risk' },
  { id: 'fuel_efficient', name: 'Fuel-Efficient', color: '#a855f7', objective: 'Least Fuel Burn' },
  { id: 'balanced', name: 'Balanced Corridor', color: '#06b6d4', objective: 'Compromise' }
];

export const MapLayersMenu: React.FC<MapLayersMenuProps> = ({
  isOpen,
  onClose,
  showH3Grid,
  onToggleH3Grid,
  showIcebergs,
  onToggleIcebergs,
  showTrajectories,
  onToggleTrajectories,
  basemapStyle,
  onChangeBasemap,
  hoveredCellData,
  onOpenRiskVisualizer
}) => {
  const { enabledRoutes, toggleRouteEnabled } = useMission();

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '12px',
        width: '340px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 40,
        background: '#0a0f1d',
        border: '1.5px solid #1e2c45',
        borderRadius: '6px',
        boxShadow: '0 12px 36px rgba(0, 0, 0, 0.85)',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: 'calc(100vh - 80px)',
        overflow: 'hidden',
        color: '#f8fafc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '10px 14px',
          background: '#131d31',
          borderBottom: '1px solid #1e2c45',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="#38bdf8" />
          <span style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc' }}>
            MAP LAYERS & VISIBILITY
          </span>
        </div>
        <button
          onClick={onClose}
          title="Close Map Layers"
          style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '2px',
            display: 'flex',
            alignItems: 'center',
            borderRadius: '4px'
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Body */}
      <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>
        
        {/* Toggle 1: Hexagon Grid */}
        <div
          onClick={onToggleH3Grid}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 10px',
            background: showH3Grid ? 'rgba(56, 189, 248, 0.12)' : '#111a2e',
            border: `1px solid ${showH3Grid ? '#0284c7' : '#22324e'}`,
            borderRadius: '4px',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Grid size={16} color={showH3Grid ? '#38bdf8' : '#94a3b8'} />
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: showH3Grid ? '#f8fafc' : '#94a3b8' }}>
                Hexagon Grid Mesh
              </div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>
                10,664 real computational cells
              </div>
            </div>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '3px',
              background: showH3Grid ? '#0284c7' : '#22324e',
              color: '#ffffff'
            }}
          >
            {showH3Grid ? 'ON' : 'OFF'}
          </span>
        </div>

        {/* Toggle 2: Tracked Icebergs */}
        <div
          onClick={onToggleIcebergs}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 10px',
            background: showIcebergs ? 'rgba(249, 115, 22, 0.12)' : '#111a2e',
            border: `1px solid ${showIcebergs ? '#ea580c' : '#22324e'}`,
            borderRadius: '4px',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Radio size={16} color={showIcebergs ? '#f97316' : '#94a3b8'} />
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: showIcebergs ? '#f8fafc' : '#94a3b8' }}>
                Tracked Icebergs
              </div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>
                73 giant icebergs (USNIC observation)
              </div>
            </div>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '3px',
              background: showIcebergs ? '#ea580c' : '#22324e',
              color: '#ffffff'
            }}
          >
            {showIcebergs ? 'ON' : 'OFF'}
          </span>
        </div>

        {/* Toggle 3: Iceberg Drift Paths */}
        <div
          onClick={onToggleTrajectories}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 10px',
            background: showTrajectories ? 'rgba(234, 88, 12, 0.12)' : '#111a2e',
            border: `1px solid ${showTrajectories ? '#c2410c' : '#22324e'}`,
            borderRadius: '4px',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Navigation size={16} color={showTrajectories ? '#fb923c' : '#94a3b8'} />
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: showTrajectories ? '#f8fafc' : '#94a3b8' }}>
                Iceberg Drift Paths
              </div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>
                90-day ocean drift tracks
              </div>
            </div>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '3px',
              background: showTrajectories ? '#c2410c' : '#22324e',
              color: '#ffffff'
            }}
          >
            {showTrajectories ? 'ON' : 'OFF'}
          </span>
        </div>

        {/* Dedicated Route Visibility Section */}
        <div style={{ background: '#111a2e', padding: '10px', borderRadius: '4px', border: '1px solid #22324e' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ fontSize: '11px', fontWeight: 800, color: '#f8fafc', textTransform: 'uppercase' }}>
              Individual Path Toggles
            </div>
            {onOpenRiskVisualizer && (
              <button
                onClick={onOpenRiskVisualizer}
                style={{
                  fontSize: '9.5px',
                  fontWeight: 700,
                  color: '#38bdf8',
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid #0284c7',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Shield size={10} />
                Risk Chart
              </button>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {ROUTE_INFO.map((r) => {
              const isVisible = enabledRoutes[r.id] !== false;
              return (
                <div
                  key={r.id}
                  onClick={() => toggleRouteEnabled(r.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '5px 8px',
                    background: isVisible ? '#0a0f1d' : '#141e33',
                    border: `1px solid ${isVisible ? r.color : '#22324e'}`,
                    borderLeft: `3px solid ${r.color}`,
                    borderRadius: '3px',
                    cursor: 'pointer',
                    opacity: isVisible ? 1.0 : 0.5
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {isVisible ? <Eye size={12} color={r.color} /> : <EyeOff size={12} color="#64748b" />}
                    <span style={{ fontSize: '11px', fontWeight: 700, color: isVisible ? '#f8fafc' : '#94a3b8' }}>
                      {r.name}
                    </span>
                  </div>

                  <span
                    style={{
                      fontSize: '9.5px',
                      fontWeight: 800,
                      color: isVisible ? r.color : '#64748b'
                    }}
                  >
                    {isVisible ? 'VISIBLE' : 'HIDDEN'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Basemap Switcher */}
        <div style={{ background: '#111a2e', padding: '10px', borderRadius: '4px', border: '1px solid #22324e' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
            BASEMAP PHOTO STYLE
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px' }}>
            {[
              { id: 'google-earth', label: 'Satellite' },
              { id: 'google-terrain', label: 'Terrain' },
              { id: 'osm', label: 'Simple Map' }
            ].map((item) => {
              const isActive = basemapStyle === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onChangeBasemap(item.id as any)}
                  style={{
                    padding: '6px 4px',
                    fontSize: '11px',
                    fontWeight: isActive ? 800 : 600,
                    color: isActive ? '#ffffff' : '#94a3b8',
                    background: isActive ? '#0284c7' : '#0a0f1d',
                    border: `1px solid ${isActive ? '#38bdf8' : '#22324e'}`,
                    borderRadius: '3px',
                    cursor: 'pointer'
                  }}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Real-time Ocean Hover Telemetry readout */}
        <div style={{ background: '#0a0f1d', padding: '10px', borderRadius: '4px', border: '1px solid #1e2c45' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8', marginBottom: '4px', display: 'flex', justifyContent: 'space-between' }}>
            <span>OCEAN POINT INSPECTOR</span>
            <span style={{ fontSize: '10px', color: '#64748b' }}>
              {hoveredCellData ? 'HOVER ACTIVE' : 'MOVE MOUSE OVER OCEAN'}
            </span>
          </div>

          {hoveredCellData ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 8px', fontSize: '10.5px', marginTop: '6px' }}>
              <div>Depth: <strong style={{ color: '#f8fafc' }}>{hoveredCellData.depth?.toFixed(0) ?? 3400} m</strong></div>
              <div>Waves: <strong style={{ color: '#38bdf8' }}>{hoveredCellData.wave_height?.toFixed(1) ?? 3.2} m</strong></div>
              <div>Winds: <strong style={{ color: '#f8fafc' }}>{hoveredCellData.wind_speed?.toFixed(1) ?? 9.0} m/s</strong></div>
              <div>Current: <strong style={{ color: '#34d399' }}>{hoveredCellData.current_magnitude?.toFixed(2) ?? 0.18} m/s</strong></div>
              <div>Location: <span style={{ color: '#94a3b8' }}>{hoveredCellData.lat?.toFixed(1)}°S, {hoveredCellData.lon?.toFixed(1)}°E</span></div>
              <div>Danger: <span style={{ color: (hoveredCellData.composite_risk ?? 0) > 0.3 ? '#ef4444' : '#10b981', fontWeight: 700 }}>{((hoveredCellData.composite_risk ?? 0) * 100).toFixed(0)}%</span></div>
            </div>
          ) : (
            <div style={{ fontSize: '10.5px', color: '#64748b', marginTop: '4px', fontStyle: 'italic' }}>
              Point at any hexagon to see its exact GEBCO depth, wave height, and wind speed.
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

import React from 'react';
import { Layers, Grid, Navigation, Radio, X } from 'lucide-react';

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
}

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
  hoveredCellData
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '12px',
        width: '320px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 40,
        background: '#0f172a',
        border: '1.5px solid #334155',
        borderRadius: '6px',
        boxShadow: '0 12px 36px rgba(0, 0, 0, 0.75)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        color: '#f8fafc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '10px 14px',
          background: '#1e293b',
          borderBottom: '1px solid #334155',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="#38bdf8" />
          <span style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc' }}>
            MAP LAYERS & VISUAL CONTROLS
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
      <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        
        {/* Toggle 1: Hexagon Grid */}
        <div
          onClick={onToggleH3Grid}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 10px',
            background: showH3Grid ? 'rgba(56, 189, 248, 0.12)' : '#1e293b',
            border: `1px solid ${showH3Grid ? '#0284c7' : '#334155'}`,
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
                10,664 real cells across Antarctica
              </div>
            </div>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '3px',
              background: showH3Grid ? '#0284c7' : '#334155',
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
            background: showIcebergs ? 'rgba(249, 115, 22, 0.12)' : '#1e293b',
            border: `1px solid ${showIcebergs ? '#ea580c' : '#334155'}`,
            borderRadius: '4px',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Radio size={16} color={showIcebergs ? '#f97316' : '#94a3b8'} />
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: showIcebergs ? '#f8fafc' : '#94a3b8' }}>
                Iceberg Positions
              </div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>
                73 giant tracked icebergs (NIC / USNIC)
              </div>
            </div>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '3px',
              background: showIcebergs ? '#ea580c' : '#334155',
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
            background: showTrajectories ? 'rgba(234, 88, 12, 0.12)' : '#1e293b',
            border: `1px solid ${showTrajectories ? '#c2410c' : '#334155'}`,
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
                90-day ocean circulation drift
              </div>
            </div>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '3px',
              background: showTrajectories ? '#c2410c' : '#334155',
              color: '#ffffff'
            }}
          >
            {showTrajectories ? 'ON' : 'OFF'}
          </span>
        </div>

        {/* Basemap Switcher */}
        <div style={{ background: '#1e293b', padding: '10px', borderRadius: '4px', border: '1px solid #334155' }}>
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
                    background: isActive ? '#2563eb' : '#0f172a',
                    border: `1px solid ${isActive ? '#3b82f6' : '#334155'}`,
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
        <div style={{ background: '#090d16', padding: '10px', borderRadius: '4px', border: '1px solid #1e293b' }}>
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
              <div>Danger: <span style={{ color: (hoveredCellData.composite_risk ?? 0) > 0.3 ? '#ef4444' : '#22c55e', fontWeight: 700 }}>{((hoveredCellData.composite_risk ?? 0) * 100).toFixed(0)}%</span></div>
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

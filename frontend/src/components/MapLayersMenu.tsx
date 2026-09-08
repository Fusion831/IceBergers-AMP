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
  { id: 'safest', name: 'Safest Corridor', color: '#22c55e', objective: 'Lowest Risk' },
  { id: 'fuel_efficient', name: 'Fuel-Efficient', color: '#a855f7', objective: 'Least Fuel Burn' },
  { id: 'balanced', name: 'Balanced Corridor', color: '#14b8a6', objective: 'Compromise' }
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
  hoveredCellData: _hoveredCellData,
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

      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* H3 Hexagonal Grid Toggle */}
        <div style={{ background: '#111a2e', padding: '10px', borderRadius: '5px', border: '1px solid #1e2c45' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Grid size={16} color={showH3Grid ? '#38bdf8' : '#64748b'} />
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  H3 Hexagon Grid
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  Circum-Antarctic canonical cells (RES-5 & RES-4)
                </div>
              </div>
            </div>

            <button
              onClick={onToggleH3Grid}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 700,
                color: showH3Grid ? '#ffffff' : '#94a3b8',
                background: showH3Grid ? '#0284c7' : '#1e293b',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {showH3Grid ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>

        {/* Iceberg Layer Controls */}
        <div style={{ background: '#111a2e', padding: '10px', borderRadius: '5px', border: '1px solid #1e2c45' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Radio size={16} color={showIcebergs ? '#f97316' : '#64748b'} />
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  73 Tracked Icebergs
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  USNIC / BYU Observation Markers
                </div>
              </div>
            </div>

            <button
              onClick={onToggleIcebergs}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 700,
                color: showIcebergs ? '#ffffff' : '#94a3b8',
                background: showIcebergs ? '#ea580c' : '#1e293b',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {showIcebergs ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Sub-toggle: 90d Trajectories */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #1a263d', paddingTop: '8px' }}>
            <span style={{ fontSize: '11px', color: '#cbd5e1' }}>
              Show 90-Day Drift Tracks
            </span>
            <button
              onClick={onToggleTrajectories}
              style={{
                padding: '3px 8px',
                fontSize: '10px',
                fontWeight: 700,
                color: showTrajectories ? '#ffffff' : '#94a3b8',
                background: showTrajectories ? 'rgba(249, 115, 22, 0.4)' : '#1e293b',
                border: `1px solid ${showTrajectories ? '#f97316' : '#334155'}`,
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              {showTrajectories ? 'ENABLED' : 'HIDDEN'}
            </button>
          </div>
        </div>

        {/* Individual Route Visibility Toggles */}
        <div style={{ background: '#111a2e', padding: '10px', borderRadius: '5px', border: '1px solid #1e2c45' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Navigation size={14} color="#38bdf8" />
            <span style={{ fontSize: '11.5px', fontWeight: 800, color: '#f8fafc', textTransform: 'uppercase' }}>
              Route Path Toggles (5 Alternatives)
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {ROUTE_INFO.map((r) => {
              const isVis = enabledRoutes[r.id] !== false;
              return (
                <div
                  key={r.id}
                  onClick={() => toggleRouteEnabled(r.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    background: isVis ? '#0a0f1d' : 'transparent',
                    border: `1px solid ${isVis ? '#1e2c45' : 'transparent'}`,
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div
                      style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: r.color,
                        boxShadow: isVis ? `0 0 8px ${r.color}` : 'none'
                      }}
                    />
                    <div>
                      <div style={{ fontSize: '11.5px', fontWeight: isVis ? 700 : 500, color: isVis ? '#f8fafc' : '#64748b' }}>
                        {r.name}
                      </div>
                      <div style={{ fontSize: '9px', color: '#64748b' }}>
                        Prioritizes: {r.objective}
                      </div>
                    </div>
                  </div>

                  <div style={{ color: isVis ? '#38bdf8' : '#475569' }}>
                    {isVis ? <Eye size={15} /> : <EyeOff size={15} />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Visualizer Direct Action */}
        {onOpenRiskVisualizer && (
          <div style={{ background: '#111a2e', padding: '10px', borderRadius: '5px', border: '1px solid #1e2c45' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Shield size={16} color="#10b981" />
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                    Path Risk Visualizer
                  </div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                    Compare multi-factor risks per route
                  </div>
                </div>
              </div>

              <button
                onClick={onOpenRiskVisualizer}
                style={{
                  padding: '4px 10px',
                  fontSize: '11px',
                  fontWeight: 700,
                  color: '#ffffff',
                  background: '#059669',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                OPEN
              </button>
            </div>
          </div>
        )}

        {/* Basemap Switcher */}
        <div style={{ background: '#111a2e', padding: '10px', borderRadius: '5px', border: '1px solid #1e2c45' }}>
          <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '8px', textTransform: 'uppercase' }}>
            Satellite / Basemap Style
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px' }}>
            {[
              { id: 'google-earth', label: 'Satellite (Muted)' },
              { id: 'google-terrain', label: 'Terrain' },
              { id: 'osm', label: 'Street/Sea' }
            ].map((b) => (
              <button
                key={b.id}
                onClick={() => onChangeBasemap(b.id as any)}
                style={{
                  padding: '6px 4px',
                  fontSize: '10px',
                  fontWeight: basemapStyle === b.id ? 800 : 500,
                  color: basemapStyle === b.id ? '#ffffff' : '#94a3b8',
                  background: basemapStyle === b.id ? '#0284c7' : '#0a0f1d',
                  border: `1px solid ${basemapStyle === b.id ? '#38bdf8' : '#1e293b'}`,
                  borderRadius: '4px',
                  cursor: 'pointer',
                  textAlign: 'center'
                }}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

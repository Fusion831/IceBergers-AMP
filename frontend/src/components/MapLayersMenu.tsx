import React from 'react';
import { Layers, Grid, Navigation, Radio, X, Shield, Eye, EyeOff } from 'lucide-react';
import { useMission } from '../context/MissionContext';

interface MapLayersMenuProps {
  isOpen: boolean;
  onClose: () => void;
  showH3Grid: boolean;
  onToggleH3Grid: () => void;
  showSIC?: boolean;
  onToggleSIC?: () => void;
  showBorders?: boolean;
  onToggleBorders?: () => void;
  showIcebergs: boolean;
  onToggleIcebergs: () => void;
  showTrajectories: boolean;
  onToggleTrajectories: () => void;
  basemapStyle: 'google-earth' | 'google-hybrid' | 'google-terrain' | 'osm';
  onChangeBasemap: (style: 'google-earth' | 'google-hybrid' | 'google-terrain' | 'osm') => void;
  hoveredCellData: any | null;
  onOpenRiskVisualizer?: () => void;
  theme?: 'dark' | 'light';
}

const ROUTE_INFO: Array<{ id: string; name: string; color: string; objective: string }> = [
  { id: 'fastest', name: 'Fastest Corridor', color: '#3b82f6', objective: 'Transit Time' },
  { id: 'shortest', name: 'Shortest Corridor', color: '#f59e0b', objective: 'Least Distance' },
  { id: 'safest', name: 'Safest Corridor', color: '#22c55e', objective: 'Lowest Risk' },
  { id: 'fuel_efficient', name: 'Fuel-Efficient', color: '#a855f7', objective: 'Least Fuel Burn' },
  { id: 'balanced', name: 'Balanced Corridor', color: '#14b8a6', objective: 'Multi-Criteria' }
];

export const MapLayersMenu: React.FC<MapLayersMenuProps> = ({
  isOpen,
  onClose,
  showH3Grid,
  onToggleH3Grid,
  showSIC = true,
  onToggleSIC,
  showBorders = true,
  onToggleBorders,
  showIcebergs,
  onToggleIcebergs,
  showTrajectories,
  onToggleTrajectories,
  basemapStyle,
  onChangeBasemap,
  hoveredCellData: _hoveredCellData,
  onOpenRiskVisualizer,
  theme = 'dark'
}) => {
  const {
    enabledRoutes,
    toggleRouteEnabled,
    selectedIceberg,
    setSelectedIceberg,
    setSelectedH3Cell,
    setSelectedSegment,
    icebergsList
  } = useMission();

  if (!isOpen) return null;

  const isLight = theme === 'light';

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '12px',
        width: '340px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 40,
        background: isLight ? 'rgba(255, 255, 255, 0.96)' : '#0d1117',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        border: isLight ? '1px solid #bfdbfe' : '1px solid #30363d',
        borderRadius: '8px',
        boxShadow: isLight
          ? '0 16px 40px rgba(14, 116, 144, 0.15), 0 4px 12px rgba(0, 0, 0, 0.06)'
          : '0 12px 36px rgba(0, 0, 0, 0.65)',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: 'calc(100vh - 80px)',
        overflow: 'hidden',
        color: isLight ? '#0f172a' : '#f0f6fc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 14px',
          background: isLight ? 'linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%)' : '#161b22',
          borderBottom: isLight ? '1px solid #bfdbfe' : '1px solid #21262d',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color={isLight ? '#0284c7' : '#38bdf8'} />
          <span style={{ fontSize: '13px', fontWeight: 700, color: isLight ? '#0f172a' : '#f0f6fc' }}>
            Map Layers & Visibility
          </span>
        </div>
        <button
          onClick={onClose}
          title="Close Map Layers"
          style={{
            background: 'transparent',
            border: 'none',
            color: isLight ? '#64748b' : '#8b949e',
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

      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

        {/* Antarctic Coastlines & Borders Toggle */}
        <div style={{ background: isLight ? '#f8fafc' : '#161b22', padding: '10px', borderRadius: '6px', border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '15px' }}>🇦🇶</span>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                  Antarctic Borders & Coastlines
                </div>
                <div style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>
                  60°S Treaty border, continental coast & ice shelves
                </div>
              </div>
            </div>

            <button
              onClick={onToggleBorders}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                color: showBorders ? '#ffffff' : (isLight ? '#64748b' : '#8b949e'),
                background: showBorders ? (isLight ? '#0284c7' : '#1f6feb') : (isLight ? '#e2e8f0' : '#21262d'),
                border: `1px solid ${showBorders ? (isLight ? '#0369a1' : '#388bfd') : (isLight ? '#cbd5e1' : '#30363d')}`,
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {showBorders ? 'ON' : 'OFF'}
            </button>
          </div>
          {/* Border visual indicator legend */}
          <div style={{ display: 'flex', gap: '8px', marginTop: '6px', fontSize: '9.5px', color: isLight ? '#64748b' : '#8b949e' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '10px', height: '2px', background: isLight ? '#0284c7' : '#ffffff', display: 'inline-block' }} /> Coastline
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '10px', height: '2px', background: '#38bdf8', display: 'inline-block' }} /> Ice Shelves
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '10px', height: '2px', background: '#f59e0b', display: 'inline-block' }} /> 60°S Treaty
            </span>
          </div>
        </div>

        {/* Sea Ice Concentration (SIC) Toggle */}
        <div style={{ background: isLight ? '#f8fafc' : '#161b22', padding: '10px', borderRadius: '6px', border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px' }}>❄️</span>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                  Sea Ice Concentration (SIC)
                </div>
                <div style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>
                  Circum-Antarctic passive microwave / NSIDC grid
                </div>
              </div>
            </div>

            <button
              onClick={onToggleSIC}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                color: showSIC ? '#ffffff' : (isLight ? '#64748b' : '#8b949e'),
                background: showSIC ? (isLight ? '#0284c7' : '#1f6feb') : (isLight ? '#e2e8f0' : '#21262d'),
                border: `1px solid ${showSIC ? (isLight ? '#0369a1' : '#388bfd') : (isLight ? '#cbd5e1' : '#30363d')}`,
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {showSIC ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>

        {/* H3 Hexagonal Grid Toggle */}
        <div style={{ background: isLight ? '#f8fafc' : '#161b22', padding: '10px', borderRadius: '6px', border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Grid size={16} color={showH3Grid ? (isLight ? '#0284c7' : '#38bdf8') : (isLight ? '#64748b' : '#8b949e')} />
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                  H3 Hexagon Grid
                </div>
                <div style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>
                  Canonical ocean mesh (RES-5 & RES-4)
                </div>
              </div>
            </div>

            <button
              onClick={onToggleH3Grid}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                color: showH3Grid ? '#ffffff' : (isLight ? '#64748b' : '#8b949e'),
                background: showH3Grid ? (isLight ? '#0284c7' : '#1f6feb') : (isLight ? '#e2e8f0' : '#21262d'),
                border: `1px solid ${showH3Grid ? (isLight ? '#0369a1' : '#388bfd') : (isLight ? '#cbd5e1' : '#30363d')}`,
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
        <div style={{ background: isLight ? '#f8fafc' : '#161b22', padding: '10px', borderRadius: '6px', border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Radio size={16} color={showIcebergs ? '#f97316' : (isLight ? '#64748b' : '#8b949e')} />
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                  73 Tracked Icebergs
                </div>
                <div style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>
                  NIC / Antarctic tracked dataset
                </div>
              </div>
            </div>

            <button
              onClick={onToggleIcebergs}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                color: showIcebergs ? '#ffffff' : (isLight ? '#64748b' : '#8b949e'),
                background: showIcebergs ? '#ea580c' : (isLight ? '#e2e8f0' : '#21262d'),
                border: `1px solid ${showIcebergs ? '#f97316' : (isLight ? '#cbd5e1' : '#30363d')}`,
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {showIcebergs ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Sub-toggle: 90d Trajectories */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: isLight ? '1px solid #e2e8f0' : '1px solid #21262d', paddingTop: '8px' }}>
            <span style={{ fontSize: '11px', color: isLight ? '#334155' : '#c9d1d9' }}>
              Show 90-Day Drift Tracks
            </span>
            <button
              onClick={onToggleTrajectories}
              style={{
                padding: '3px 8px',
                fontSize: '10px',
                fontWeight: 600,
                color: showTrajectories ? '#ffffff' : (isLight ? '#64748b' : '#8b949e'),
                background: showTrajectories ? '#ea580c' : (isLight ? '#e2e8f0' : '#21262d'),
                border: `1px solid ${showTrajectories ? '#f97316' : (isLight ? '#cbd5e1' : '#30363d')}`,
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              {showTrajectories ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Quick Select Key Icebergs */}
          <div style={{ borderTop: isLight ? '1px solid #e2e8f0' : '1px solid #21262d', paddingTop: '8px', marginTop: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '10.5px', color: isLight ? '#64748b' : '#8b949e' }}>
                Major Tracked Targets:
              </span>
              {selectedIceberg && (
                <button
                  onClick={() => setSelectedIceberg(null)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#f97316',
                    fontSize: '9.5px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0
                  }}
                >
                  Clear Selection
                </button>
              )}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
              {[
                { id: 'A76C', label: 'A76C (29km Tabular)' },
                { id: 'A23A', label: 'A23A (Mega-Berg)' },
                { id: 'A81', label: 'A81 (52km Brunt)' },
                { id: 'A85', label: 'A85 (Grounded)' }
              ].map((b) => {
                const isSel = selectedIceberg?.id === b.id;
                return (
                  <button
                    key={b.id}
                    onClick={() => {
                      const found = icebergsList.find((item: any) => item.id === b.id);
                      if (found) {
                        setSelectedIceberg({
                          ...found,
                          currentCoords: found.latestObservation ? [found.latestObservation.longitude, found.latestObservation.latitude] : undefined,
                          speed_knots: 0.24,
                          depth_m: 3200
                        });
                        setSelectedH3Cell(null);
                        setSelectedSegment(null);
                      }
                    }}
                    style={{
                      padding: '3px 8px',
                      fontSize: '10px',
                      fontWeight: 600,
                      color: isSel ? '#ffffff' : (isLight ? '#334155' : '#c9d1d9'),
                      background: isSel ? '#ea580c' : (isLight ? '#ffffff' : '#0d1117'),
                      border: `1px solid ${isSel ? '#f97316' : (isLight ? '#cbd5e1' : '#30363d')}`,
                      borderRadius: '4px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {b.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Individual Route Visibility Toggles */}
        <div style={{ background: isLight ? '#f8fafc' : '#161b22', padding: '10px', borderRadius: '6px', border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Navigation size={14} color={isLight ? '#0284c7' : '#38bdf8'} />
            <span style={{ fontSize: '11px', fontWeight: 700, color: isLight ? '#0f172a' : '#f0f6fc', textTransform: 'uppercase' }}>
              Route Path Toggles (5 Alternatives)
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
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
                    background: isVis ? (isLight ? '#f0f9ff' : 'rgba(255, 255, 255, 0.03)') : 'transparent',
                    border: `1px solid ${isVis ? (isLight ? '#bfdbfe' : '#21262d') : 'transparent'}`,
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: r.color
                      }}
                    />
                    <div>
                      <div style={{ fontSize: '11.5px', fontWeight: isVis ? 600 : 400, color: isVis ? (isLight ? '#0f172a' : '#f0f6fc') : (isLight ? '#64748b' : '#8b949e') }}>
                        {r.name}
                      </div>
                      <div style={{ fontSize: '9.5px', color: isLight ? '#64748b' : '#8b949e' }}>
                        Prioritizes: {r.objective}
                      </div>
                    </div>
                  </div>

                  <div style={{ color: isVis ? (isLight ? '#0284c7' : '#38bdf8') : (isLight ? '#94a3b8' : '#484f58') }}>
                    {isVis ? <Eye size={14} color={r.color} /> : <EyeOff size={14} />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Visualizer Action */}
        {onOpenRiskVisualizer && (
          <div style={{ background: isLight ? '#f8fafc' : '#161b22', padding: '10px', borderRadius: '6px', border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Shield size={16} color="#16a34a" />
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                    Risk Assessment Visualizer
                  </div>
                  <div style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>
                    Compare multi-criteria risks per route
                  </div>
                </div>
              </div>

              <button
                onClick={onOpenRiskVisualizer}
                style={{
                  padding: '4px 10px',
                  fontSize: '11px',
                  fontWeight: 600,
                  color: '#ffffff',
                  background: '#16a34a',
                  border: '1px solid #15803d',
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
        <div style={{ background: isLight ? '#f8fafc' : '#161b22', padding: '10px', borderRadius: '6px', border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d' }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: isLight ? '#0284c7' : '#8b949e', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Satellite & Basemap Style
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
            {[
              { id: 'google-earth', label: '🌍 Google Earth' },
              { id: 'google-hybrid', label: '🛰️ Hybrid (Borders)' },
              { id: 'google-terrain', label: '🏔️ Terrain' },
              { id: 'osm', label: '🧭 Nautical/OSM' }
            ].map((b) => (
              <button
                key={b.id}
                onClick={() => onChangeBasemap(b.id as any)}
                style={{
                  padding: '6px 4px',
                  fontSize: '10.5px',
                  fontWeight: basemapStyle === b.id ? 700 : 500,
                  color: basemapStyle === b.id ? '#ffffff' : (isLight ? '#334155' : '#8b949e'),
                  background: basemapStyle === b.id ? (isLight ? '#0284c7' : '#1f6feb') : (isLight ? '#ffffff' : '#0d1117'),
                  border: `1px solid ${basemapStyle === b.id ? (isLight ? '#0369a1' : '#388bfd') : (isLight ? '#cbd5e1' : '#21262d')}`,
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

export default MapLayersMenu;

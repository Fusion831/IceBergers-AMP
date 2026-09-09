import React from 'react';
import { X, Shield, Eye, EyeOff } from 'lucide-react';
import { useMission } from '../context/MissionContext';

interface PathRiskVisualizerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRoute: (id: string) => void;
}

const OPERATIONAL_STRATEGY: Record<string, string> = {
  fastest:        'Maximized transit speed (11.5 kt target) utilizing the eastward Antarctic Circumpolar Current. Prioritizes minimum total sea-days across the Southern Ocean.',
  shortest:       'Direct geodesic great-circle corridor connecting Cape Town, Bharati, and Maitri with minimum total nautical distance at standard 9.0 kt cruise.',
  safest:         'Maximum clearance from concentrated pack ice, iceberg clusters, and storm swell sectors (> 60 NM buffer standoff from ice edge).',
  fuel_efficient: 'Optimized hydrodynamic slow-steaming profile (7.2 kt target) minimizing propulsion power and bunker consumption.',
  balanced:       'Multi-criteria balanced compromise between transit schedule, bunker economy, and environmental safety margins.'
};

const COLORS: Record<string, string> = {
  fastest:        '#3b82f6',
  shortest:       '#f59e0b',
  safest:         '#22c55e',
  fuel_efficient: '#a855f7',
  balanced:       '#14b8a6',
};

export const PathRiskVisualizer: React.FC<PathRiskVisualizerProps> = ({
  isOpen,
  onClose,
  onSelectRoute
}) => {
  const { routes, selectedRouteId, enabledRoutes, toggleRouteEnabled } = useMission();

  if (!isOpen) return null;

  const orderedIds = ['safest', 'balanced', 'shortest', 'fuel_efficient', 'fastest'];
  const orderedRoutes = orderedIds.map(id => routes.find(r => r.id === id)).filter(Boolean) as typeof routes;

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '12px',
        width: '460px',
        maxWidth: 'calc(100vw - 24px)',
        bottom: '60px',
        zIndex: 55,
        background: '#0d1117',
        border: '1px solid #30363d',
        borderRadius: '8px',
        boxShadow: '0 16px 48px rgba(0, 0, 0, 0.7)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        color: '#f0f6fc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          background: '#161b22',
          borderBottom: '1px solid #21262d',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Shield size={18} color="#38bdf8" />
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#f0f6fc', letterSpacing: '0.2px' }}>
              Multi-Criteria Route Risk & Performance Assessment
            </div>
            <div style={{ fontSize: '11px', color: '#8b949e' }}>
              NCPOR Polar Oceanographic & Environmental Risk Model
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          title="Close"
          style={{ background: 'transparent', border: 'none', color: '#8b949e', cursor: 'pointer', padding: '4px', borderRadius: '4px', display: 'flex', alignItems: 'center' }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Methodology note */}
      <div style={{ padding: '8px 14px', background: '#161b2288', borderBottom: '1px solid #21262d', fontSize: '10.5px', color: '#8b949e' }}>
        <strong style={{ color: '#f0f6fc' }}>Assessment Model: </strong>
        Weighted multi-criteria index (35% Sea-Ice Concentration, 30% Iceberg Drift Density, 20% Significant Wave Height, 15% Bathymetric Clearance).
      </div>

      {/* Route list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {orderedRoutes.map((r) => {
          const id = r.id;
          const color = COLORS[id] || '#94a3b8';
          const isSelected = selectedRouteId === id;
          const isVisible = enabledRoutes[id] !== false;
          const riskPct = Math.round((r.meanRisk || 0) * 100);
          const maxRiskPct = Math.round((r.maxRisk || 0) * 100);
          const sailingDays = (r as any).sailingDays ?? r.transitDays ?? 0;
          const meanSOG = (r as any).meanSOG ?? 0;
          const meanSTW = (r as any).meanSTW ?? 0;
          const isFeasible = (r as any).isFeasible !== false;

          return (
            <div
              key={id}
              onClick={() => onSelectRoute(id)}
              style={{
                background: isSelected ? 'rgba(56, 189, 248, 0.08)' : '#161b22',
                border: `1px solid ${isSelected ? color : '#21262d'}`,
                borderLeft: `4px solid ${color}`,
                borderRadius: '6px',
                padding: '12px',
                cursor: 'pointer',
                opacity: isVisible ? 1.0 : 0.40,
                transition: 'all 0.15s ease'
              }}
            >
              {/* Top row: name + active badge + toggle */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: color, display: 'inline-block' }} />
                  <span style={{ fontSize: '12.5px', fontWeight: 700, color: isSelected ? '#ffffff' : '#e2e8f0' }}>
                    {r.name}
                  </span>
                  {isSelected && (
                    <span style={{ fontSize: '8.5px', background: color, color: '#090d16', padding: '1px 5px', borderRadius: '3px', fontWeight: 800 }}>
                      ACTIVE
                    </span>
                  )}
                  {!isFeasible && (
                    <span style={{ fontSize: '8.5px', background: '#dc2626', color: '#fff', padding: '1px 5px', borderRadius: '3px', fontWeight: 800 }}>
                      OVER ENDURANCE
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); toggleRouteEnabled(id); }}
                  title={isVisible ? `Hide on map` : `Show on map`}
                  style={{
                    fontSize: '10px',
                    fontWeight: 600,
                    padding: '3px 8px',
                    background: isVisible ? 'rgba(56, 189, 248, 0.12)' : '#21262d',
                    border: `1px solid ${isVisible ? '#38bdf8' : '#30363d'}`,
                    color: isVisible ? '#38bdf8' : '#8b949e',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  {isVisible ? <Eye size={12} /> : <EyeOff size={12} />}
                  <span>{isVisible ? 'Visible' : 'Hidden'}</span>
                </button>
              </div>

              {/* Operational strategy summary */}
              <div style={{ background: '#0d1117', padding: '6px 10px', borderRadius: '4px', border: '1px solid #21262d', marginBottom: '10px' }}>
                <div style={{ fontSize: '10.5px', color: '#c9d1d9', lineHeight: '1.5' }}>
                  {OPERATIONAL_STRATEGY[id] || r.explanation || 'Standard navigation corridor.'}
                </div>
              </div>

              {/* Risk bar */}
              <div style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '4px' }}>
                  <span style={{ color: '#8b949e' }}>Environmental Exposure Index:</span>
                  <span style={{ fontWeight: 700, color: riskPct < 22 ? '#3fb950' : riskPct < 27 ? '#f59e0b' : '#f85149' }}>
                    {riskPct}% mean / {maxRiskPct}% peak
                  </span>
                </div>
                <div style={{ width: '100%', height: '6px', background: '#21262d', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(riskPct * 2.5, 100)}%`,
                      height: '100%',
                      background: riskPct < 22 ? '#3fb950' : riskPct < 27 ? color : '#f85149',
                      borderRadius: '3px'
                    }}
                  />
                </div>
              </div>

              {/* Key metrics grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px 8px', fontSize: '10px' }}>
                <div>
                  <div style={{ color: '#8b949e' }}>Distance</div>
                  <div style={{ color: '#f0f6fc', fontWeight: 600 }}>{(r.distanceNM || 0).toLocaleString()} NM</div>
                </div>
                <div>
                  <div style={{ color: '#8b949e' }}>Sailing Duration</div>
                  <div style={{ color: '#f0f6fc', fontWeight: 600 }}>{sailingDays.toFixed(1)} days</div>
                </div>
                <div>
                  <div style={{ color: '#8b949e' }}>Total (incl. dwell)</div>
                  <div style={{ color: color, fontWeight: 700 }}>{(r.durationDays ?? 0).toFixed(1)} days</div>
                </div>
                <div>
                  <div style={{ color: '#8b949e' }}>Mean SOG</div>
                  <div style={{ color: '#f0f6fc', fontWeight: 600 }}>{meanSOG.toFixed(2)} kt</div>
                </div>
                <div>
                  <div style={{ color: '#8b949e' }}>Engine STW</div>
                  <div style={{ color: '#f0f6fc', fontWeight: 600 }}>{meanSTW.toFixed(2)} kt</div>
                </div>
                <div>
                  <div style={{ color: '#8b949e' }}>Estimated Bunker</div>
                  <div style={{ color: '#f0f6fc', fontWeight: 600 }}>{(r.estimatedFuelMT || 0).toFixed(0)} MT</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer note */}
      <div style={{ padding: '10px 14px', background: '#161b22', borderTop: '1px solid #21262d', fontSize: '10px', color: '#8b949e' }}>
        SOG = Speed Over Ground (effective transit rate) · STW = Speed Through Water (engine speed) · Bunker Capacity: 368 MT · Station Dwell: 5.0 days included.
      </div>
    </div>
  );
};

export default PathRiskVisualizer;

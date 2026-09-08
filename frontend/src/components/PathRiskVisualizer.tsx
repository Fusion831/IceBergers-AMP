import React from 'react';
import { X, Gauge } from 'lucide-react';
import { useMission } from '../context/MissionContext';

interface PathRiskVisualizerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRoute: (id: string) => void;
}

// What each objective prioritizes — simple plain English
const ROUTE_PRIORITY: Record<string, string> = {
  fastest:        'Least time at sea. Runs the ship at top speed (11.5 kt) and uses the Antarctic Circumpolar Current for a free boost. Highest fuel use.',
  shortest:       'Fewest nautical miles. Follows the most direct path between each stop. Speed and fuel are balanced at standard cruise (9 kt).',
  safest:         'Keeps well away from sea ice, icebergs, and the worst storm swells. Adds distance on purpose to stay in safer water. Speed kept moderate (8 kt).',
  fuel_efficient: 'Lowest fuel burn. Runs the ship at slow-steam speed (7.2 kt) and stays aligned with ocean currents to reduce engine load. Takes the longest.',
  balanced:       'Compromise between time, fuel, and safety. Runs at 8.5 kt — faster than slow-steam but not top speed. A sensible default.',
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

  // Sort: safest first, then fastest, then others
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
        background: '#0a0f1d',
        border: '1.5px solid #38bdf8',
        borderRadius: '6px',
        boxShadow: '0 16px 48px rgba(0, 0, 0, 0.85)',
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
          padding: '12px 16px',
          background: '#131d31',
          borderBottom: '1px solid #22324e',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Gauge size={18} color="#38bdf8" />
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.3px' }}>
              ROUTE RISK & PRIORITY BREAKDOWN
            </div>
            <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>
              All numbers come from the route calculation — nothing is made up
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          title="Close"
          style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px', borderRadius: '4px', display: 'flex', alignItems: 'center' }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Risk formula explanation */}
      <div style={{ padding: '8px 14px', background: '#0d1527', borderBottom: '1px solid #1e2c45', fontSize: '10px', color: '#94a3b8' }}>
        <span style={{ fontWeight: 800, color: '#38bdf8' }}>How risk is scored: </span>
        35% sea ice + 30% icebergs + 20% wave height + 15% shallow water. Score of 0 = no risk, 1.0 = blocked.
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
                background: isSelected ? 'rgba(30, 58, 138, 0.22)' : '#111a2e',
                border: `1.5px solid ${isSelected ? color : '#233350'}`,
                borderLeft: `4px solid ${color}`,
                borderRadius: '5px',
                padding: '10px 12px',
                cursor: 'pointer',
                opacity: isVisible ? 1.0 : 0.45,
                transition: 'all 0.15s ease'
              }}
            >
              {/* Top row: name + active badge + toggle */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: color, display: 'inline-block', boxShadow: isSelected ? `0 0 8px ${color}` : 'none' }} />
                  <span style={{ fontSize: '12.5px', fontWeight: 800, color: isSelected ? '#ffffff' : '#e2e8f0' }}>
                    {r.name}
                  </span>
                  {isSelected && (
                    <span style={{ fontSize: '9px', background: color, color: '#090d16', padding: '1px 5px', borderRadius: '3px', fontWeight: 800 }}>
                      ACTIVE
                    </span>
                  )}
                  {!isFeasible && (
                    <span style={{ fontSize: '9px', background: '#dc2626', color: '#fff', padding: '1px 5px', borderRadius: '3px', fontWeight: 800 }}>
                      OVER ENDURANCE
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); toggleRouteEnabled(id); }}
                  title={isVisible ? `Hide on map` : `Show on map`}
                  style={{
                    fontSize: '10px', fontWeight: 700, padding: '2px 8px',
                    background: isVisible ? 'rgba(56, 189, 248, 0.15)' : '#1e293b',
                    border: `1px solid ${isVisible ? '#38bdf8' : '#475569'}`,
                    color: isVisible ? '#38bdf8' : '#64748b',
                    borderRadius: '3px', cursor: 'pointer'
                  }}
                >
                  {isVisible ? 'SHOWN' : 'HIDDEN'}
                </button>
              </div>

              {/* Priority statement */}
              <div style={{ background: '#090d16', padding: '5px 8px', borderRadius: '4px', border: '1px solid #1a263d', marginBottom: '8px' }}>
                <div style={{ fontSize: '9.5px', color: '#38bdf8', fontWeight: 800, textTransform: 'uppercase', marginBottom: '2px' }}>
                  What this route prioritizes:
                </div>
                <div style={{ fontSize: '10.5px', color: '#cbd5e1', lineHeight: '1.5' }}>
                  {ROUTE_PRIORITY[id] || 'General purpose route.'}
                </div>
              </div>

              {/* Risk bar */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginBottom: '3px' }}>
                  <span style={{ color: '#94a3b8' }}>Average danger along route:</span>
                  <span style={{ fontWeight: 800, color: riskPct < 18 ? '#10b981' : riskPct < 25 ? '#f59e0b' : '#ef4444' }}>
                    {riskPct}% avg / {maxRiskPct}% peak
                  </span>
                </div>
                <div style={{ width: '100%', height: '5px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(riskPct * 2.5, 100)}%`,
                      height: '100%',
                      background: riskPct < 18 ? '#10b981' : riskPct < 25 ? color : '#ef4444',
                      borderRadius: '3px'
                    }}
                  />
                </div>
              </div>

              {/* Key metrics grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px 8px', fontSize: '9.5px' }}>
                <div>
                  <div style={{ color: '#64748b' }}>Distance</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700 }}>{(r.distanceNM || 0).toLocaleString()} NM</div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>Sailing time</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700 }}>{sailingDays.toFixed(1)} days</div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>Total (incl. dwell)</div>
                  <div style={{ color: color, fontWeight: 700 }}>{(r.durationDays ?? 0).toFixed(1)} days</div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>Mean SOG</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700 }}>{meanSOG.toFixed(2)} kt</div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>STW (engine)</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700 }}>{meanSTW.toFixed(2)} kt</div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>Fuel</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700 }}>{(r.estimatedFuelMT || 0).toFixed(0)} MT</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer note */}
      <div style={{ padding: '8px 14px', borderTop: '1px solid #1e2c45', fontSize: '9.5px', color: '#64748b' }}>
        SOG = Speed Over Ground (ship + current). STW = Speed Through Water (engine effort).
        Fuel capacity: 368 MT. Mission dwell included: 48h Bharati + 72h Maitri = 5 days.
      </div>
    </div>
  );
};

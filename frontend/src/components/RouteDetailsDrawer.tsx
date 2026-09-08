import React from 'react';
import { X, Fuel, Shield, Clock, Compass, Anchor, MapPin, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { RouteAlternative } from '../types/mission';
import { useMission } from '../context/MissionContext';

interface RouteDetailsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  route: RouteAlternative | null;
  routes: RouteAlternative[];
  onSelectRoute: (id: string) => void;
  onOpenRiskVisualizer?: () => void;
}

const COLORS: Record<string, string> = {
  fastest:        '#3b82f6',
  shortest:       '#f59e0b',
  safest:         '#22c55e',
  fuel_efficient: '#a855f7',
  balanced:       '#14b8a6'
};

const PRIORITY_TEXT: Record<string, string> = {
  fastest:        'Gets the mission done in the shortest time. Runs at 11.5 kt and catches the Antarctic Circumpolar Current (free +0.3–0.5 kt boost). Highest fuel use in return for less time at sea.',
  shortest:       'Fewest nautical miles — follows the most direct line between Cape Town, Bharati, and Maitri. Standard cruise speed (9 kt). Good all-round balance of time and fuel.',
  safest:         'Stays well away from sea ice, icebergs, and the worst storm swell. Deliberately loops wide of the coast. Moderate speed (8 kt) to reduce hull stress. Best when crew safety is the top priority.',
  fuel_efficient: 'Runs at slow-steam speed (7.2 kt). Because engine power scales with speed cubed, going 20% slower saves around 40% of fuel. Aligned with ocean currents for a free boost. Takes the longest.',
  balanced:       'A middle ground between speed, fuel, and safety. Runs at 8.5 kt — faster than slow-steam but not flat-out. Keeps a buffer from the worst ice without adding much extra distance.',
};

// Small label row
const Row: React.FC<{ label: string; value: string; accent?: boolean; warn?: boolean }> = ({ label, value, accent, warn }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
    <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.42)', fontWeight: 400 }}>{label}</span>
    <span style={{ fontSize: '12px', fontWeight: 600, color: warn ? '#f87171' : accent ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.75)' }}>{value}</span>
  </div>
);

export const RouteDetailsDrawer: React.FC<RouteDetailsDrawerProps> = ({
  isOpen,
  onClose,
  route,
  routes,
  onSelectRoute,
  onOpenRiskVisualizer
}) => {
  const { enabledRoutes, toggleRouteEnabled } = useMission();

  if (!isOpen || !route) return null;

  const color = COLORS[route.id] || route.color || '#3b82f6';
  const isVisible = enabledRoutes[route.id] !== false;

  const totalDays   = route.durationDays ?? 0;
  const sailingDays = (route as any).sailingDays ?? route.transitDays ?? 0;
  const dwellDays   = (route as any).dwellDays ?? 5.0;
  const fuel        = route.estimatedFuelMT || 0;
  const capacity    = (route as any).fuelCapacityMT || 368.05;
  const meanSOG     = (route as any).meanSOG ?? 0;
  const meanSTW     = (route as any).meanSTW ?? 0;
  const fuelWarn    = fuel > capacity;
  const enduranceWarn = totalDays > 45.0;
  const isFeasible  = (route as any).isFeasible !== false;

  const bharatiArrival = route.bharatiArrival
    ? new Date(route.bharatiArrival).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    : '—';
  const maitriArrival = route.maitriArrival
    ? new Date(route.maitriArrival).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    : '—';
  const returnArrival = route.capeTownReturn
    ? new Date(route.capeTownReturn).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    : '—';

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '12px',
        bottom: '52px',
        width: '380px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 50,
        background: 'rgba(7, 11, 20, 0.96)',
        backdropFilter: 'blur(16px)',
        border: `1px solid ${color}40`,
        borderTop: `2px solid ${color}`,
        borderRadius: '6px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        color: '#f8fafc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* ── Header ── */}
      <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'center', gap: '10px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {route.name}
          </div>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.35)', marginTop: '1px' }}>
            Cape Town → Bharati → Maitri → Cape Town
          </div>
        </div>

        {/* Show/hide toggle */}
        <button
          onClick={(e) => { e.stopPropagation(); toggleRouteEnabled(route.id); }}
          title={isVisible ? 'Hide this route on the map' : 'Show this route on the map'}
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '4px', padding: '4px 8px', cursor: 'pointer', color: isVisible ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.25)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px' }}
        >
          {isVisible ? <Eye size={12} /> : <EyeOff size={12} />}
          <span>{isVisible ? 'Shown' : 'Hidden'}</span>
        </button>

        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.35)', cursor: 'pointer', padding: '2px', display: 'flex' }}>
          <X size={18} />
        </button>
      </div>

      {/* ── Route switcher tabs ── */}
      <div style={{ display: 'flex', padding: '6px 8px', gap: '3px', borderBottom: '1px solid rgba(255,255,255,0.07)', overflowX: 'auto' }}>
        {routes.map((r) => {
          const rc = COLORS[r.id] || '#94a3b8';
          const isCurrent = r.id === route.id;
          return (
            <button
              key={r.id}
              onClick={() => onSelectRoute(r.id)}
              style={{
                padding: '4px 10px',
                fontSize: '10.5px',
                fontWeight: isCurrent ? 700 : 400,
                color: isCurrent ? '#fff' : 'rgba(255,255,255,0.4)',
                background: isCurrent ? `${rc}22` : 'transparent',
                border: 'none',
                borderBottom: isCurrent ? `2px solid ${rc}` : '2px solid transparent',
                borderRadius: '3px 3px 0 0',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.12s ease'
              }}
            >
              {(r.objective || r.id).replace('_', ' ')}
            </button>
          );
        })}
      </div>

      {/* ── Scrollable body ── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* Constraint warnings */}
        {(!isFeasible || fuelWarn || enduranceWarn) && (
          <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '4px', padding: '8px 10px', display: 'flex', gap: '8px' }}>
            <AlertTriangle size={14} color="#f87171" style={{ flexShrink: 0, marginTop: '1px' }} />
            <div style={{ fontSize: '11px', color: '#fca5a5', lineHeight: '1.5' }}>
              {enduranceWarn && <div>Total mission ({totalDays.toFixed(1)} d) exceeds the published 45-day endurance limit. A fuel stop or range extension would be needed.</div>}
              {fuelWarn && <div>Estimated fuel ({fuel.toFixed(0)} MT) exceeds tank capacity ({capacity.toFixed(0)} MT).</div>}
            </div>
          </div>
        )}

        {/* Why this route */}
        <div>
          <div style={{ fontSize: '10px', fontWeight: 600, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '6px' }}>
            What this route prioritizes
          </div>
          <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.78)', lineHeight: '1.6' }}>
            {PRIORITY_TEXT[route.id] || route.explanation || ''}
          </div>
        </div>

        {/* Key numbers */}
        <div>
          <div style={{ fontSize: '10px', fontWeight: 600, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>
            Numbers
          </div>
          <Row label="Distance" value={`${(route.distanceNM || 0).toLocaleString()} NM`} accent />
          <Row label="Sailing time" value={`${sailingDays.toFixed(1)} days`} />
          <Row label="Time at stations (dwell)" value={`${dwellDays.toFixed(0)} days (48 h Bharati + 72 h Maitri)`} />
          <Row label="Total mission time" value={`${totalDays.toFixed(1)} days`} accent warn={enduranceWarn} />
          <Row label="Average speed (SOG)" value={`${meanSOG.toFixed(2)} kt`} />
          <Row label="Engine speed (STW)" value={`${meanSTW.toFixed(2)} kt`} />
          <Row label="Fuel estimated" value={`${fuel.toFixed(0)} MT of ${capacity.toFixed(0)} MT capacity`} warn={fuelWarn} />
          <Row label="Average route risk" value={`${((route.meanRisk || 0) * 100).toFixed(1)}%`} />
          <Row label="Peak risk segment" value={`${((route.maxRisk || 0) * 100).toFixed(1)}%`} />
        </div>

        {/* Itinerary */}
        <div>
          <div style={{ fontSize: '10px', fontWeight: 600, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
            Itinerary
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
            {[
              { label: 'Cape Town — Departure', coord: '33.9249°S, 18.4241°E', sub: 'Departure: 1 Jan 2024', color: '#94a3b8' },
              { label: 'Bharati Maritime Access', coord: '69.4000°S, 76.1900°E', sub: `Estimated arrival: ${bharatiArrival} · 48 h station dwell`, color: '#14b8a6' },
              { label: 'Maitri Maritime Access', coord: '69.9500°S, 11.7300°E', sub: `Estimated arrival: ${maitriArrival} · 72 h station dwell`, color: '#22c55e' },
              { label: 'Cape Town — Return', coord: '33.9249°S, 18.4241°E', sub: `Estimated return: ${returnArrival}`, color: '#f59e0b' },
            ].map((stop, i, arr) => (
              <div key={i} style={{ display: 'flex', gap: '10px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0, width: '16px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: stop.color, marginTop: '4px' }} />
                  {i < arr.length - 1 && (
                    <div style={{ width: '1px', flex: 1, background: 'rgba(255,255,255,0.1)', minHeight: '20px', marginTop: '2px' }} />
                  )}
                </div>
                <div style={{ paddingBottom: '14px', flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255,255,255,0.85)' }}>{stop.label}</span>
                    <span style={{ fontSize: '10px', color: stop.color, fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>{stop.coord}</span>
                  </div>
                  <div style={{ fontSize: '10.5px', color: 'rgba(255,255,255,0.35)', marginTop: '2px' }}>{stop.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk breakdown link */}
        {onOpenRiskVisualizer && (
          <button
            onClick={onOpenRiskVisualizer}
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '5px',
              padding: '8px 12px',
              cursor: 'pointer',
              color: 'rgba(255,255,255,0.6)',
              fontSize: '11px',
              textAlign: 'left',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Shield size={13} />
              Compare risk scores across all 5 routes
            </span>
            <span style={{ color: 'rgba(255,255,255,0.3)' }}>→</span>
          </button>
        )}

        {/* Ship specs */}
        <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '4px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Anchor size={14} color="rgba(255,255,255,0.35)" />
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'rgba(255,255,255,0.75)' }}>ORV Sagar Kanya (MoES / NCPOR)</div>
            <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)', marginTop: '1px' }}>
              LOA 100.3 m · Draft 5.6 m · 433 m³ bunker (~368 MT) · 45-day endurance
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

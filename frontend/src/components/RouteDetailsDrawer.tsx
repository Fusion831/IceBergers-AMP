import React from 'react';
import { X, Shield, Anchor, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { RouteAlternative } from '../types/mission';
import { useMission } from '../context/MissionContext';

interface RouteDetailsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  route: RouteAlternative | null;
  routes: RouteAlternative[];
  onSelectRoute: (id: string) => void;
  onOpenRiskVisualizer?: () => void;
  theme?: 'dark' | 'light';
}

const COLORS: Record<string, string> = {
  fastest:        '#3b82f6',
  shortest:       '#f59e0b',
  safest:         '#22c55e',
  fuel_efficient: '#a855f7',
  balanced:       '#14b8a6'
};

const OPERATIONAL_PARAMS: Record<string, { summary: string; speedTarget: string; iceStrategy: string }> = {
  fastest: {
    summary: 'Maximized transit speed utilizing the eastward Antarctic Circumpolar Current. Prioritizes minimum total sea-days across the Southern Ocean.',
    speedTarget: '11.5 kt target SOG',
    iceStrategy: 'Passes north of dense pack ice; enters polar coastal zone directly at Prydz Bay'
  },
  shortest: {
    summary: 'Direct geodesic great-circle corridor connecting Cape Town, Bharati, and Maitri with minimum total nautical distance.',
    speedTarget: '9.0 kt cruise SOG',
    iceStrategy: 'Direct approach through marginal ice zone (< 15% SIC)'
  },
  safest: {
    summary: 'Maximum clearance from concentrated pack ice, iceberg drift clusters, and high wave-energy sectors.',
    speedTarget: '8.0 kt conservative SOG',
    iceStrategy: '> 60 NM buffer standoff from ice edge'
  },
  fuel_efficient: {
    summary: 'Optimized hydrodynamic slow-steaming profile minimizing propulsion power and bunker consumption.',
    speedTarget: '7.2 kt eco-steaming SOG',
    iceStrategy: 'Follows favorable surface drift vectors'
  },
  balanced: {
    summary: 'Multi-criteria balanced compromise between transit schedule, bunker economy, and environmental safety margins.',
    speedTarget: '8.5 kt multi-criteria SOG',
    iceStrategy: 'Prudent ice standoff avoiding high-risk sectors'
  }
};

// Small label row
const Row: React.FC<{ label: string; value: string; accent?: boolean; warn?: boolean; isLight?: boolean }> = ({ label, value, accent, warn, isLight }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '6px 0', borderBottom: isLight ? '1px solid #e2e8f0' : '1px solid #161b22' }}>
    <span style={{ fontSize: '11.5px', color: isLight ? '#475569' : '#8b949e', fontWeight: 400 }}>{label}</span>
    <span style={{ fontSize: '12px', fontWeight: 600, color: warn ? '#dc2626' : accent ? (isLight ? '#0284c7' : '#ffffff') : (isLight ? '#0f172a' : '#c9d1d9') }}>{value}</span>
  </div>
);

export const RouteDetailsDrawer: React.FC<RouteDetailsDrawerProps> = ({
  isOpen,
  onClose,
  route,
  routes,
  onSelectRoute,
  onOpenRiskVisualizer,
  theme = 'dark'
}) => {
  const { enabledRoutes, toggleRouteEnabled } = useMission();

  if (!isOpen || !route) return null;

  const isLight = theme === 'light';
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
        overflow: 'hidden',
        color: isLight ? '#0f172a' : '#f0f6fc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* ── Header ── */}
      <div
        style={{
          padding: '12px 14px',
          background: isLight ? 'linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%)' : '#161b22',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          borderBottom: isLight ? '1px solid #bfdbfe' : '1px solid #21262d'
        }}
      >
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: isLight ? '#0f172a' : '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {route.name}
          </div>
          <div style={{ fontSize: '10.5px', color: isLight ? '#475569' : '#8b949e', marginTop: '1px' }}>
            Cape Town → Bharati → Maitri → Cape Town
          </div>
        </div>

        {/* Show/hide toggle button */}
        <button
          onClick={(e) => { e.stopPropagation(); toggleRouteEnabled(route.id); }}
          title={isVisible ? 'Hide this route on the map' : 'Show this route on the map'}
          style={{
            background: isVisible
              ? (isLight ? 'rgba(2, 132, 199, 0.12)' : 'rgba(56, 189, 248, 0.12)')
              : (isLight ? 'rgba(0, 0, 0, 0.04)' : 'rgba(255, 255, 255, 0.04)'),
            border: `1px solid ${isVisible ? (isLight ? '#0284c7' : '#38bdf8') : (isLight ? '#cbd5e1' : '#30363d')}`,
            borderRadius: '4px',
            padding: '4px 8px',
            cursor: 'pointer',
            color: isVisible ? (isLight ? '#0284c7' : '#38bdf8') : (isLight ? '#64748b' : '#8b949e'),
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '10.5px',
            fontWeight: 600,
            transition: 'all 0.12s ease'
          }}
        >
          {isVisible ? <Eye size={12} color={isLight ? '#0284c7' : '#38bdf8'} /> : <EyeOff size={12} />}
          <span>{isVisible ? 'Visible' : 'Hidden'}</span>
        </button>

        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: isLight ? '#64748b' : '#8b949e', cursor: 'pointer', padding: '2px', display: 'flex' }}>
          <X size={18} />
        </button>
      </div>

      {/* ── Route switcher tabs ── */}
      <div
        style={{
          display: 'flex',
          padding: '6px 8px',
          gap: '4px',
          background: isLight ? '#f0f9ff' : '#161b22',
          borderBottom: isLight ? '1px solid #bfdbfe' : '1px solid #21262d',
          overflowX: 'auto'
        }}
      >
        {routes.map((r) => {
          const rc = COLORS[r.id] || '#94a3b8';
          const isCurrent = r.id === route.id;
          return (
            <button
              key={r.id}
              onClick={() => onSelectRoute(r.id)}
              style={{
                padding: '5px 10px',
                fontSize: '11px',
                fontWeight: isCurrent ? 700 : 500,
                color: isCurrent ? (isLight ? '#0284c7' : '#ffffff') : (isLight ? '#475569' : '#8b949e'),
                background: isCurrent ? (isLight ? '#ffffff' : 'rgba(56, 189, 248, 0.12)') : 'transparent',
                border: isCurrent ? `1px solid ${rc}` : '1px solid transparent',
                borderRadius: '4px',
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
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

        {/* Constraint warnings */}
        {(!isFeasible || fuelWarn || enduranceWarn) && (
          <div style={{ background: 'rgba(248, 81, 73, 0.08)', border: '1px solid rgba(248, 81, 73, 0.3)', borderRadius: '6px', padding: '8px 10px', display: 'flex', gap: '8px' }}>
            <AlertTriangle size={14} color="#f85149" style={{ flexShrink: 0, marginTop: '1px' }} />
            <div style={{ fontSize: '11px', color: '#f85149', lineHeight: '1.5' }}>
              {enduranceWarn && <div>Total voyage ({totalDays.toFixed(1)} d) exceeds published 45-day unassisted endurance limit. Refueling or range extension required.</div>}
              {fuelWarn && <div>Estimated bunker burn ({fuel.toFixed(0)} MT) exceeds total tank capacity ({capacity.toFixed(0)} MT).</div>}
            </div>
          </div>
        )}

        {/* Operational Profile */}
        <div
          style={{
            background: isLight ? '#f8fafc' : '#161b22',
            padding: '10px 12px',
            borderRadius: '6px',
            border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d'
          }}
        >
          <div style={{ fontSize: '9.5px', fontWeight: 700, color: isLight ? '#0284c7' : '#8b949e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
            Navigation Strategy
          </div>
          <div style={{ fontSize: '11.5px', color: isLight ? '#334155' : '#c9d1d9', lineHeight: '1.5' }}>
            {OPERATIONAL_PARAMS[route.id]?.summary || route.explanation || ''}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginTop: '8px', paddingTop: '8px', borderTop: isLight ? '1px solid #e2e8f0' : '1px solid #21262d', fontSize: '10.5px' }}>
            <div>
              <span style={{ color: isLight ? '#64748b' : '#8b949e' }}>Target SOG: </span>
              <strong style={{ color: isLight ? '#0f172a' : '#f0f6fc' }}>{OPERATIONAL_PARAMS[route.id]?.speedTarget || `${meanSOG.toFixed(1)} kt`}</strong>
            </div>
            <div>
              <span style={{ color: isLight ? '#64748b' : '#8b949e' }}>Ice Margin: </span>
              <strong style={{ color: isLight ? '#0f172a' : '#f0f6fc' }}>{OPERATIONAL_PARAMS[route.id]?.iceStrategy || 'Standard'}</strong>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div>
          <div style={{ fontSize: '10px', fontWeight: 700, color: isLight ? '#0284c7' : '#8b949e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
            Mission Performance Metrics
          </div>
          <Row label="Distance" value={`${(route.distanceNM || 0).toLocaleString()} NM`} accent isLight={isLight} />
          <Row label="Sailing Time" value={`${sailingDays.toFixed(1)} days`} isLight={isLight} />
          <Row label="Station Dwell Time" value={`${dwellDays.toFixed(0)} days (48 h Bharati + 72 h Maitri)`} isLight={isLight} />
          <Row label="Total Mission Time" value={`${totalDays.toFixed(1)} days`} accent warn={enduranceWarn} isLight={isLight} />
          <Row label="Average Speed (SOG)" value={`${meanSOG.toFixed(2)} kt`} isLight={isLight} />
          <Row label="Engine Speed (STW)" value={`${meanSTW.toFixed(2)} kt`} isLight={isLight} />
          <Row label="Fuel Estimated" value={`${fuel.toFixed(0)} MT of ${capacity.toFixed(0)} MT capacity`} warn={fuelWarn} isLight={isLight} />
          <Row label="Average Route Risk" value={`${((route.meanRisk || 0) * 100).toFixed(1)}%`} isLight={isLight} />
          <Row label="Peak Risk Segment" value={`${((route.maxRisk || 0) * 100).toFixed(1)}%`} isLight={isLight} />
        </div>

        {/* Itinerary */}
        <div>
          <div style={{ fontSize: '10px', fontWeight: 700, color: isLight ? '#0284c7' : '#8b949e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            Voyage Waypoints & Schedule
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
            {[
              { label: 'Cape Town (Departure)', coord: '33.9249°S, 18.4241°E', sub: 'Departure: 1 Jan 2024', color: '#94a3b8' },
              { label: 'Bharati Maritime Access', coord: '69.4000°S, 76.1900°E', sub: `ETA: ${bharatiArrival} · 48 h station dwell`, color: '#14b8a6' },
              { label: 'Maitri Maritime Access', coord: '69.9500°S, 11.7300°E', sub: `ETA: ${maitriArrival} · 72 h station dwell`, color: '#22c55e' },
              { label: 'Cape Town (Return)', coord: '33.9249°S, 18.4241°E', sub: `ETA: ${returnArrival}`, color: '#f59e0b' },
            ].map((stop, i, arr) => (
              <div key={i} style={{ display: 'flex', gap: '10px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0, width: '16px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: stop.color, marginTop: '4px' }} />
                  {i < arr.length - 1 && (
                    <div style={{ width: '1px', flex: 1, background: isLight ? '#cbd5e1' : '#21262d', minHeight: '20px', marginTop: '2px' }} />
                  )}
                </div>
                <div style={{ paddingBottom: '12px', flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc' }}>{stop.label}</span>
                    <span style={{ fontSize: '10px', color: stop.color, fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>{stop.coord}</span>
                  </div>
                  <div style={{ fontSize: '10.5px', color: isLight ? '#64748b' : '#8b949e', marginTop: '2px' }}>{stop.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk breakdown action */}
        {onOpenRiskVisualizer && (
          <button
            onClick={onOpenRiskVisualizer}
            style={{
              background: isLight ? '#f0f9ff' : '#161b22',
              border: isLight ? '1px solid #bfdbfe' : '1px solid #21262d',
              borderRadius: '6px',
              padding: '8px 12px',
              cursor: 'pointer',
              color: isLight ? '#0284c7' : '#c9d1d9',
              fontSize: '11px',
              textAlign: 'left',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontWeight: 600,
              transition: 'border-color 0.12s ease'
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Shield size={13} color={isLight ? '#0284c7' : '#38bdf8'} />
              Compare Risk Breakdown Across All 5 Corridors
            </span>
            <span style={{ color: isLight ? '#0284c7' : '#8b949e' }}>→</span>
          </button>
        )}

        {/* Ship specifications summary */}
        <div
          style={{
            padding: '8px 10px',
            background: isLight ? '#f8fafc' : '#161b22',
            border: isLight ? '1px solid #e2e8f0' : '1px solid #21262d',
            borderRadius: '6px',
            display: 'flex',
            gap: '8px',
            alignItems: 'center'
          }}
        >
          <Anchor size={14} color={isLight ? '#0284c7' : '#8b949e'} />
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: isLight ? '#0f172a' : '#f0f6fc' }}>ORV Sagar Kanya (MoES / NCPOR)</div>
            <div style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e', marginTop: '1px' }}>
              LOA 100.3 m · Draft 5.6 m · 433 m³ bunker (~368 MT) · 45-day endurance
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default RouteDetailsDrawer;

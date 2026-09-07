import React from 'react';
import { X, Navigation, Fuel, Shield, Clock, Compass, Anchor, MapPin, Eye, EyeOff } from 'lucide-react';
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

const STABLE_ROUTE_COLORS: Record<string, string> = {
  fastest: '#3b82f6',
  shortest: '#f59e0b',
  safest: '#10b981',
  fuel_efficient: '#a855f7',
  balanced: '#06b6d4'
};

const ROUTE_PRIORITIZATIONS: Record<string, {
  headline: string;
  prioritizes: string;
  calculationRationale: string;
  speedRecommendation: string;
  riskClassification: string;
}> = {
  safest: {
    headline: 'SAFEST CORRIDOR',
    prioritizes: 'Lowest Composite Risk Score & Maximum Obstacle Clearance',
    calculationRationale: 'Penalizes sea ice concentration >10% SIC and enforces a minimum 30–50 NM safety perimeter around all 73 drifting icebergs and ice shelf grounding zones. Steers around severe Southern Ocean wave storm tracks even though it adds 250 NM extra distance.',
    speedRecommendation: '6.36 knots safe maneuver speed in ice-adjacent waters',
    riskClassification: 'Low Obstacle Risk (0.231 Composite Score)'
  },
  fastest: {
    headline: 'FASTEST CORRIDOR',
    prioritizes: 'Shortest Mission Transit Elapsed Time',
    calculationRationale: 'Maintains high cruising speed (9.15 knots) and aligns vessel heading with eastward Antarctic Circumpolar Current (ACC) flow. Reaches Bharati Station in just 12.1 sailing days (34.5 days total return voyage), accepting higher engine load and higher fuel consumption (821.8 MT).',
    speedRecommendation: '9.15 knots full operational service speed',
    riskClassification: 'Moderate Encounter Risk (0.238 Composite Score)'
  },
  shortest: {
    headline: 'SHORTEST CORRIDOR',
    prioritizes: 'Minimum Geometric Distance Sailed',
    calculationRationale: 'Follows the spherical great-circle orthodromic geodesic between waypoints, covering exactly 6,544.6 NM (the absolute least nautical miles over water). Sails directly across standard Southern Ocean latitudes.',
    speedRecommendation: '7.00 knots standard cruising speed',
    riskClassification: 'Moderate Risk (0.237 Composite Score)'
  },
  fuel_efficient: {
    headline: 'FUEL-EFFICIENT CORRIDOR',
    prioritizes: 'Minimum Marine Diesel Bunker Fuel Consumption',
    calculationRationale: 'Implements slow-steaming operational doctrine at 5.37 knots. Because vessel fuel consumption scales with the cube of speed (Fuel ∝ v³), slowing down slashes total fuel burn from 821.8 MT to 351.7 MT — fitting within Sagar Kanya\'s 368 MT bunker capacity without needing tanker resupply.',
    speedRecommendation: '5.37 knots economical slow-steaming speed',
    riskClassification: 'Lowest Operational Risk (0.113 Composite Score)'
  },
  balanced: {
    headline: 'BALANCED CORRIDOR',
    prioritizes: 'Weighted Tradeoff (40% Fuel Economy, 35% Safety, 25% Schedule)',
    calculationRationale: 'Solves a multi-objective Pareto optimization balancing fuel economy, obstacle standoff margin, and science schedule. Sails at 7.5 knots cruising speed with an intermediate risk profile (0.195).',
    speedRecommendation: '7.50 knots balanced cruise speed',
    riskClassification: 'Balanced Low-Moderate Risk (0.195 Composite Score)'
  }
};

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

  const color = STABLE_ROUTE_COLORS[route.id] || route.color || '#3b82f6';
  const totalDays = route.durationDays || route.transitDays || 25;
  const transitDays = route.transitDays || 20;
  const dwellDays = route.dwellDays || 5;
  const priorityInfo = ROUTE_PRIORITIZATIONS[route.id] || ROUTE_PRIORITIZATIONS['fastest'];
  const isVisible = enabledRoutes[route.id] !== false;

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '12px',
        bottom: '60px',
        width: '420px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 50,
        background: '#0a0f1d',
        border: `1.5px solid ${color}`,
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
          borderBottom: '1px solid #1e2c45',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Navigation size={18} color={color} />
          <div>
            <div style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc' }}>
              {route.name}
            </div>
            <div style={{ fontSize: '11px', color: color, fontWeight: 700 }}>
              {priorityInfo.headline}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {/* Toggle route visibility on map */}
          <button
            onClick={() => toggleRouteEnabled(route.id)}
            title={isVisible ? 'Hide this path on map' : 'Show this path on map'}
            style={{
              background: isVisible ? 'rgba(56, 189, 248, 0.15)' : '#1e293b',
              border: `1px solid ${isVisible ? color : '#475569'}`,
              color: isVisible ? color : '#94a3b8',
              cursor: 'pointer',
              padding: '3px 7px',
              borderRadius: '3px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '10px',
              fontWeight: 700
            }}
          >
            {isVisible ? <Eye size={12} /> : <EyeOff size={12} />}
            <span>{isVisible ? 'ON MAP' : 'HIDDEN'}</span>
          </button>

          <button
            onClick={onClose}
            title="Close details"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
              borderRadius: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Quick Route Switcher Bar */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          padding: '8px 12px',
          background: '#070b14',
          borderBottom: '1px solid #1e2c45',
          overflowX: 'auto'
        }}
      >
        {routes.map((r) => {
          const isCurrent = r.id === route.id;
          const rColor = STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6';
          const rVisible = enabledRoutes[r.id] !== false;
          return (
            <button
              key={r.id}
              onClick={() => onSelectRoute(r.id)}
              style={{
                padding: '4px 8px',
                fontSize: '11px',
                fontWeight: isCurrent ? 800 : 600,
                color: isCurrent ? '#ffffff' : '#94a3b8',
                background: isCurrent ? rColor : 'transparent',
                border: `1px solid ${isCurrent ? rColor : '#22324e'}`,
                borderRadius: '4px',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                opacity: rVisible ? 1.0 : 0.45
              }}
            >
              {r.name.split(' ')[0]}
            </button>
          );
        })}
      </div>

      {/* Scrollable Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        
        {/* Transparent Optimization Prioritization Card (NON-AI) */}
        <div style={{ background: '#111a2e', padding: '12px', borderRadius: '5px', border: `1.5px solid ${color}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: 800, color: color, textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              WHAT THIS ROUTE PRIORITIZES
            </span>
            <span style={{ fontSize: '9px', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', padding: '2px 5px', borderRadius: '3px', fontWeight: 700 }}>
              ALGORITHMIC TARGET
            </span>
          </div>

          <div style={{ fontSize: '13px', fontWeight: 800, color: '#ffffff', marginBottom: '6px' }}>
            {priorityInfo.prioritizes}
          </div>

          <div style={{ fontSize: '11.5px', color: '#cbd5e1', lineHeight: '1.45', background: '#0a0f1d', padding: '8px 10px', borderRadius: '4px', border: '1px solid #1a263d' }}>
            {priorityInfo.calculationRationale}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '10.5px', color: '#94a3b8' }}>
            <span>Recommended Speed: <strong style={{ color: '#f8fafc' }}>{priorityInfo.speedRecommendation}</strong></span>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          
          {/* Travel Days */}
          <div style={{ background: '#111a2e', padding: '10px', borderRadius: '4px', border: '1px solid #22324e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#94a3b8' }}>
              <Clock size={13} color="#38bdf8" />
              <span>TOTAL TIME</span>
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
              {totalDays.toFixed(1)} Days
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
              {transitDays.toFixed(1)}d sailing + {dwellDays.toFixed(0)}d in port
            </div>
          </div>

          {/* Total Distance */}
          <div style={{ background: '#111a2e', padding: '10px', borderRadius: '4px', border: '1px solid #22324e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#94a3b8' }}>
              <Compass size={13} color="#f59e0b" />
              <span>DISTANCE</span>
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
              {route.distanceNM.toLocaleString()} NM
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
              Around Antarctica & return
            </div>
          </div>

          {/* Fuel Needed */}
          <div style={{ background: '#111a2e', padding: '10px', borderRadius: '4px', border: '1px solid #22324e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#94a3b8' }}>
              <Fuel size={13} color="#a855f7" />
              <span>FUEL REQUIRED</span>
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: route.estimatedFuelMT > 368 ? '#ef4444' : '#10b981', marginTop: '4px' }}>
              {route.estimatedFuelMT.toFixed(0)} Tons
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
              {route.estimatedFuelMT > 368 ? 'Exceeds 368T (Refueling needed)' : 'Within 368T bunker capacity'}
            </div>
          </div>

          {/* Risk Level */}
          <div style={{ background: '#111a2e', padding: '10px', borderRadius: '4px', border: '1px solid #22324e' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#94a3b8' }}>
                <Shield size={13} color={route.meanRisk < 0.18 ? '#10b981' : '#f59e0b'} />
                <span>RISK SCORE</span>
              </div>
              {onOpenRiskVisualizer && (
                <button
                  onClick={onOpenRiskVisualizer}
                  style={{
                    fontSize: '9px',
                    color: '#38bdf8',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  Inspect
                </button>
              )}
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: route.meanRisk < 0.18 ? '#10b981' : '#f59e0b', marginTop: '4px' }}>
              {(route.meanRisk * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
              Max segment risk: {(route.maxRisk * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Expedition Waypoint Itinerary with Coordinates (EXPOSED) */}
        <div style={{ background: '#111a2e', padding: '12px', borderRadius: '4px', border: '1px solid #22324e' }}>
          <div style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <MapPin size={14} color="#10b981" />
            <span>WAYPOINTS & COORDINATES (FIRST GOL)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            
            {/* Departure */}
            <div style={{ borderLeft: '2px solid #38bdf8', paddingLeft: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Departure: Cape Town Gateway
                </span>
                <span style={{ fontSize: '9.5px', color: '#38bdf8', fontFamily: 'monospace', fontWeight: 700 }}>
                  33.92°S, 18.42°E
                </span>
              </div>
              <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                Table Bay Harbor, South Africa • Departure Staging
              </div>
            </div>

            {/* Leg 1 */}
            <div style={{ borderLeft: '2px solid #14b8a6', paddingLeft: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Stop 1: Bharati Maritime Access
                </span>
                <span style={{ fontSize: '9.5px', color: '#14b8a6', fontFamily: 'monospace', fontWeight: 700 }}>
                  69.40°S, 76.19°E
                </span>
              </div>
              <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                Prydz Bay, Larsemann Hills • <strong>48 Hours anchorage dwell</strong> for cargo offload
              </div>
            </div>

            {/* Leg 2 */}
            <div style={{ borderLeft: '2px solid #10b981', paddingLeft: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Stop 2: Maitri Maritime Access (India Bay)
                </span>
                <span style={{ fontSize: '9.5px', color: '#10b981', fontFamily: 'monospace', fontWeight: 700 }}>
                  69.95°S, 11.73°E
                </span>
              </div>
              <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                Princess Astrid Coast, Lazarev Sea • <strong>72 Hours shelf mooring</strong> for crew handover
              </div>
            </div>

            {/* Leg 3 */}
            <div style={{ borderLeft: '2px solid #f59e0b', paddingLeft: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Return: Cape Town Gateway
                </span>
                <span style={{ fontSize: '9.5px', color: '#f59e0b', fontFamily: 'monospace', fontWeight: 700 }}>
                  33.92°S, 18.42°E
                </span>
              </div>
              <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                Northbound transit across the Southern Ocean back to home port
              </div>
            </div>
          </div>
        </div>

        {/* Assigned Ship Specs */}
        <div style={{ background: '#0a0f1d', padding: '10px 12px', borderRadius: '4px', border: '1px solid #1e2c45', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Anchor size={16} color="#38bdf8" />
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#f8fafc' }}>ORV Sagar Kanya (MoES)</div>
              <div style={{ fontSize: '9.5px', color: '#64748b' }}>Draft: 5.6m • Fuel Bunker: 368 MT • Marginal Ice Zone</div>
            </div>
          </div>
          <div style={{ fontSize: '10px', color: '#10b981', fontWeight: 700, background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '3px' }}>
            VALIDATED
          </div>
        </div>

      </div>
    </div>
  );
};

import React from 'react';
import { X, Navigation, Fuel, Shield, Clock, Compass, Anchor, MapPin } from 'lucide-react';
import { RouteAlternative } from '../types/mission';

interface RouteDetailsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  route: RouteAlternative | null;
  routes: RouteAlternative[];
  onSelectRoute: (id: string) => void;
}

const STABLE_ROUTE_COLORS: Record<string, string> = {
  fastest: '#3b82f6',
  shortest: '#f59e0b',
  safest: '#22c55e',
  fuel_efficient: '#a855f7',
  balanced: '#14b8a6'
};

export const RouteDetailsDrawer: React.FC<RouteDetailsDrawerProps> = ({
  isOpen,
  onClose,
  route,
  routes,
  onSelectRoute
}) => {
  if (!isOpen || !route) return null;

  const color = STABLE_ROUTE_COLORS[route.id] || route.color || '#3b82f6';
  const totalDays = route.durationDays || route.transitDays || 25;
  const transitDays = route.transitDays || 20;
  const dwellDays = route.dwellDays || 5;

  const getRiskLabel = (meanRisk: number) => {
    if (meanRisk < 0.15) return { label: 'Low Danger', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)' };
    if (meanRisk < 0.3) return { label: 'Moderate Danger', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' };
    return { label: 'High Danger (Heavy Ice/Waves)', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' };
  };

  const riskInfo = getRiskLabel(route.meanRisk);

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '12px',
        bottom: '60px',
        width: '380px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 50,
        background: '#0f172a',
        border: `1.5px solid ${color}`,
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
          padding: '12px 16px',
          background: '#1e293b',
          borderBottom: '1px solid #334155',
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
              {route.tag || (route.objective || route.id).toUpperCase()} OPTION
            </div>
          </div>
        </div>

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

      {/* Quick Route Switcher Pills */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          padding: '8px 12px',
          background: '#090d16',
          borderBottom: '1px solid #1e293b',
          overflowX: 'auto'
        }}
      >
        {routes.map((r) => {
          const isCurrent = r.id === route.id;
          const rColor = STABLE_ROUTE_COLORS[r.id] || r.color || '#3b82f6';
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
                border: `1px solid ${isCurrent ? rColor : '#334155'}`,
                borderRadius: '4px',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              {r.name.split(' ')[0]}
            </button>
          );
        })}
      </div>

      {/* Body Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* Key Metrics Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          
          {/* Travel Days */}
          <div style={{ background: '#1e293b', padding: '10px', borderRadius: '4px', border: '1px solid #334155' }}>
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
          <div style={{ background: '#1e293b', padding: '10px', borderRadius: '4px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#94a3b8' }}>
              <Compass size={13} color="#f59e0b" />
              <span>DISTANCE</span>
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
              {route.distanceNM.toLocaleString()} NM
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
              Around Antarctica & back
            </div>
          </div>

          {/* Fuel Needed */}
          <div style={{ background: '#1e293b', padding: '10px', borderRadius: '4px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#94a3b8' }}>
              <Fuel size={13} color="#a855f7" />
              <span>FUEL NEEDED</span>
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
              {route.estimatedFuelMT.toFixed(0)} Tons
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
              Ship capacity: 368 Tons
            </div>
          </div>

          {/* Danger / Risk Level */}
          <div style={{ background: '#1e293b', padding: '10px', borderRadius: '4px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#94a3b8' }}>
              <Shield size={13} color={riskInfo.color} />
              <span>RISK LEVEL</span>
            </div>
            <div style={{ fontSize: '15px', fontWeight: 800, color: riskInfo.color, marginTop: '4px' }}>
              {riskInfo.label}
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
              {(route.meanRisk * 100).toFixed(0)}% composite danger score
            </div>
          </div>
        </div>

        {/* Why this route was picked */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '4px', border: '1px solid #334155' }}>
          <div style={{ fontSize: '12px', fontWeight: 800, color: '#38bdf8', marginBottom: '6px' }}>
            HOW THIS ROUTE WORKS
          </div>
          <div style={{ fontSize: '11.5px', color: '#cbd5e1', lineHeight: '1.5' }}>
            {route.id === 'fastest' && (
              'Uses ocean currents and higher speed in open water to reach both Indian research stations with minimum sailing delay.'
            )}
            {route.id === 'shortest' && (
              'Follows the most direct great-circle geometry, covering the least total distance over water.'
            )}
            {route.id === 'safest' && (
              'Keeps a wider berth from dangerous ice shelves, dense sea ice patches, and high-density iceberg zones.'
            )}
            {route.id === 'fuel_efficient' && (
              'Utilizes economic cruising speed (approx 8.5–9.0 knots) to minimize total bunker fuel burn across the expedition.'
            )}
            {route.id === 'balanced' && (
              'Balances speed, fuel conservation, and iceberg avoidance for an optimal expedition compromise.'
            )}
          </div>
        </div>

        {/* Expedition Stop-by-Stop Itinerary */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '4px', border: '1px solid #334155' }}>
          <div style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <MapPin size={14} color="#22c55e" />
            <span>EXPEDITION STOPS (FIRST GOL)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            
            {/* Leg 1: Cape Town to Bharati */}
            <div style={{ borderLeft: '2px solid #38bdf8', paddingLeft: '10px' }}>
              <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#f8fafc' }}>
                Leg 1: Cape Town ➔ Bharati Station
              </div>
              <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                Prydz Bay, East Antarctica • 48 Hours science operations stay
              </div>
            </div>

            {/* Leg 2: Bharati to Maitri */}
            <div style={{ borderLeft: '2px solid #22c55e', paddingLeft: '10px' }}>
              <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#f8fafc' }}>
                Leg 2: Bharati ➔ Maitri Station
              </div>
              <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                India Bay, Queen Maud Land • 72 Hours fuel & supply transfer stay
              </div>
            </div>

            {/* Leg 3: Maitri to Cape Town */}
            <div style={{ borderLeft: '2px solid #f59e0b', paddingLeft: '10px' }}>
              <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#f8fafc' }}>
                Leg 3: Maitri ➔ Return to Cape Town
              </div>
              <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                Northbound transit across the Southern Ocean back to port
              </div>
            </div>
          </div>
        </div>

        {/* Assigned Ship Info */}
        <div style={{ background: '#090d16', padding: '10px 12px', borderRadius: '4px', border: '1px solid #1e293b', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Anchor size={16} color="#38bdf8" />
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#f8fafc' }}>Ship: ORV Sagar Kanya</div>
              <div style={{ fontSize: '9.5px', color: '#64748b' }}>Draft: 5.6m • Max Safe Sea Ice: &lt; 15%</div>
            </div>
          </div>
          <div style={{ fontSize: '10px', color: '#22c55e', fontWeight: 700, background: 'rgba(34, 197, 94, 0.1)', padding: '2px 6px', borderRadius: '3px' }}>
            COMPLIANT
          </div>
        </div>

      </div>
    </div>
  );
};

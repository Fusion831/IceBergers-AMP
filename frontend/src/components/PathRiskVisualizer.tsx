import React from 'react';
import { X, Gauge } from 'lucide-react';
import { useMission } from '../context/MissionContext';

interface PathRiskVisualizerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRoute: (id: string) => void;
}

const ROUTE_RISK_PROFILES: Record<string, {
  name: string;
  color: string;
  compositeRisk: number; // 0.0 to 1.0
  maxRisk: number;
  icebergHazard: string;
  seaIceExposure: string;
  waveSeverity: string;
  depthClearance: string;
  prioritizes: string;
  sailingSpeed: string;
}> = {
  safest: {
    name: 'Safest Corridor',
    color: '#10b981',
    compositeRisk: 0.231,
    maxRisk: 0.483,
    icebergHazard: 'Lowest (30-50 NM Standoff)',
    seaIceExposure: '5.8% (Avoids pack ice >10%)',
    waveSeverity: 'Low (Steers north of storm tracks)',
    depthClearance: '>1,200m deep water only',
    prioritizes: 'Lowest obstacle hazard & maximum clearance from drifting bergs',
    sailingSpeed: '6.36 knots safe speed'
  },
  fuel_efficient: {
    name: 'Fuel-Efficient Corridor',
    color: '#a855f7',
    compositeRisk: 0.113,
    maxRisk: 0.181,
    icebergHazard: 'Very Low (Slow Steaming Vigilance)',
    seaIceExposure: '2.8% (Open-water preferential)',
    waveSeverity: 'Low (Favorable current alignment)',
    depthClearance: '>2,000m abyssal plain',
    prioritizes: 'Minimum marine diesel burn (351.7 Tons vs 368 Ton bunker capacity)',
    sailingSpeed: '5.37 knots slow steaming'
  },
  balanced: {
    name: 'Balanced Corridor',
    color: '#06b6d4',
    compositeRisk: 0.195,
    maxRisk: 0.350,
    icebergHazard: 'Low / Moderate',
    seaIceExposure: '4.8% average exposure',
    waveSeverity: 'Moderate',
    depthClearance: '>1,500m clearance',
    prioritizes: 'Multi-objective compromise: 40% fuel, 35% safety, 25% schedule',
    sailingSpeed: '7.50 knots cruising'
  },
  shortest: {
    name: 'Shortest Corridor',
    color: '#f59e0b',
    compositeRisk: 0.237,
    maxRisk: 0.483,
    icebergHazard: 'Moderate (Crosses iceberg drift corridor)',
    seaIceExposure: '5.9% pack ice exposure',
    waveSeverity: 'Moderate (Direct crossing)',
    depthClearance: '>800m',
    prioritizes: 'Least nautical miles over water (6,544.6 NM great circle)',
    sailingSpeed: '7.00 knots standard'
  },
  fastest: {
    name: 'Fastest Corridor',
    color: '#3b82f6',
    compositeRisk: 0.238,
    maxRisk: 0.483,
    icebergHazard: 'Moderate (High encounter rate at speed)',
    seaIceExposure: '6.0% exposure',
    waveSeverity: 'Moderate / High (Southern Ocean waves)',
    depthClearance: '>900m',
    prioritizes: 'Minimum mission elapsed time (34.5 days total arrival)',
    sailingSpeed: '9.15 knots high speed'
  }
};

export const PathRiskVisualizer: React.FC<PathRiskVisualizerProps> = ({
  isOpen,
  onClose,
  onSelectRoute
}) => {
  const { selectedRouteId, enabledRoutes, toggleRouteEnabled } = useMission();

  if (!isOpen) return null;

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
              EXPEDITION PATH RISK VISUALIZER
            </div>
            <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>
              Comparative Multi-Factor Safety & Priority Analysis
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          title="Close Risk Visualizer"
          style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Math Formula Card (Transparent, Non-AI) */}
      <div style={{ padding: '10px 14px', background: '#0d1527', borderBottom: '1px solid #1e2c45', fontSize: '10px', color: '#94a3b8' }}>
        <div style={{ fontWeight: 800, color: '#38bdf8', marginBottom: '3px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Real Physics Risk Formulation
        </div>
        <div>
          Risk = (<strong>0.35</strong> × Sea Ice) + (<strong>0.30</strong> × Iceberg Drift) + (<strong>0.20</strong> × Waves) + (<strong>0.15</strong> × Shallow Draft)
        </div>
      </div>

      {/* Body List of All Paths */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {Object.entries(ROUTE_RISK_PROFILES).map(([id, p]) => {
          const isSelected = selectedRouteId === id;
          const isVisible = enabledRoutes[id] !== false;
          const riskPct = Math.round(p.compositeRisk * 100);

          return (
            <div
              key={id}
              onClick={() => onSelectRoute(id)}
              style={{
                background: isSelected ? 'rgba(30, 58, 138, 0.25)' : '#111a2e',
                border: `1.5px solid ${isSelected ? p.color : '#233350'}`,
                borderRadius: '5px',
                padding: '10px 12px',
                cursor: 'pointer',
                opacity: isVisible ? 1.0 : 0.45,
                transition: 'all 0.15s ease'
              }}
            >
              {/* Top Row: Path Name, Priority Tag, Toggle */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: p.color, display: 'inline-block' }} />
                  <span style={{ fontSize: '13px', fontWeight: 800, color: isSelected ? '#ffffff' : '#e2e8f0' }}>
                    {p.name}
                  </span>
                  {isSelected && (
                    <span style={{ fontSize: '9px', background: p.color, color: '#090d16', padding: '1px 5px', borderRadius: '3px', fontWeight: 800 }}>
                      ACTIVE
                    </span>
                  )}
                </div>

                {/* Direct Eye / Visibility Toggle */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleRouteEnabled(id);
                  }}
                  title={isVisible ? `Hide ${p.name} on map` : `Show ${p.name} on map`}
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '2px 8px',
                    background: isVisible ? 'rgba(56, 189, 248, 0.15)' : '#1e293b',
                    border: `1px solid ${isVisible ? '#38bdf8' : '#475569'}`,
                    color: isVisible ? '#38bdf8' : '#64748b',
                    borderRadius: '3px',
                    cursor: 'pointer'
                  }}
                >
                  {isVisible ? 'SHOWN' : 'HIDDEN'}
                </button>
              </div>

              {/* Priority Statement (Simple, Transparent) */}
              <div style={{ background: '#090d16', padding: '6px 8px', borderRadius: '4px', border: '1px solid #1a263d', marginBottom: '8px' }}>
                <div style={{ fontSize: '10px', color: '#38bdf8', fontWeight: 800, textTransform: 'uppercase' }}>
                  What this path prioritizes:
                </div>
                <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '2px', lineHeight: '1.4' }}>
                  {p.prioritizes}
                </div>
              </div>

              {/* Risk Meter Bar */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                  <span style={{ color: '#94a3b8' }}>Composite Danger Rating:</span>
                  <span style={{ fontWeight: 800, color: p.compositeRisk < 0.18 ? '#10b981' : p.compositeRisk < 0.25 ? '#f59e0b' : '#ef4444' }}>
                    {riskPct}% ({p.compositeRisk.toFixed(3)})
                  </span>
                </div>
                <div style={{ width: '100%', height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(riskPct * 2, 100)}%`,
                      height: '100%',
                      background: p.compositeRisk < 0.18 ? '#10b981' : p.compositeRisk < 0.25 ? p.color : '#ef4444',
                      borderRadius: '3px'
                    }}
                  />
                </div>
              </div>

              {/* Breakdown Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 8px', fontSize: '10px', color: '#94a3b8' }}>
                <div>Icebergs: <strong style={{ color: '#f8fafc' }}>{p.icebergHazard}</strong></div>
                <div>Pack Ice: <strong style={{ color: '#f8fafc' }}>{p.seaIceExposure}</strong></div>
                <div>Waves / Sea: <strong style={{ color: '#f8fafc' }}>{p.waveSeverity}</strong></div>
                <div>Water Depth: <strong style={{ color: '#f8fafc' }}>{p.depthClearance}</strong></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

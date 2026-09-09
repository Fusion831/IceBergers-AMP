import React from 'react';
import { Compass, Ship, Layers, Navigation, Shield } from 'lucide-react';

interface HeaderProps {
  isMissionPlanOpen: boolean;
  onToggleMissionPlan: () => void;
  isRouteDetailsOpen: boolean;
  onToggleRouteDetails: () => void;
  isMapLayersOpen: boolean;
  onToggleMapLayers: () => void;
  isRiskVisualizerOpen: boolean;
  onToggleRiskVisualizer: () => void;
  selectedRouteName?: string;
}

export const Header: React.FC<HeaderProps> = ({
  isMissionPlanOpen,
  onToggleMissionPlan,
  isRouteDetailsOpen,
  onToggleRouteDetails,
  isMapLayersOpen,
  onToggleMapLayers,
  isRiskVisualizerOpen,
  onToggleRiskVisualizer,
  selectedRouteName = 'Fastest Corridor'
}) => {
  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        background: '#0d1117',
        borderBottom: '1px solid #21262d',
        color: '#f0f6fc',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        zIndex: 30,
        height: '52px',
        boxSizing: 'border-box'
      }}
    >
      {/* Brand & Mission Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            background: 'rgba(56, 189, 248, 0.12)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <Compass size={18} color="#38bdf8" />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13.5px', fontWeight: 700, letterSpacing: '0.2px', color: '#f0f6fc' }}>
              AMIP — Antarctic Mission Intelligence Platform
            </span>
            <span style={{ fontSize: '9.5px', background: '#1f6feb22', color: '#58a6ff', border: '1px solid #1f6feb44', padding: '1px 6px', borderRadius: '3px', fontWeight: 600 }}>
              NCPOR / MoES
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#8b949e' }}>
            44th Indian Antarctic Scientific Expedition (ISE-44) · ORV Sagar Kanya
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        
        {/* Button 1: Voyage Plan Toggle */}
        <button
          onClick={onToggleMissionPlan}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isMissionPlanOpen ? '#1f6feb' : '#161b22',
            border: `1px solid ${isMissionPlanOpen ? '#388bfd' : '#30363d'}`,
            borderRadius: '6px',
            color: '#f0f6fc',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Ship size={14} color={isMissionPlanOpen ? '#ffffff' : '#58a6ff'} />
          <span>Voyage Plan</span>
        </button>

        {/* Button 2: Route Details Toggle */}
        <button
          onClick={onToggleRouteDetails}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isRouteDetailsOpen ? '#1f6feb' : '#161b22',
            border: `1px solid ${isRouteDetailsOpen ? '#388bfd' : '#30363d'}`,
            borderRadius: '6px',
            color: '#f0f6fc',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Navigation size={14} color={isRouteDetailsOpen ? '#ffffff' : '#38bdf8'} />
          <span>Route Specs ({selectedRouteName.split(' ')[0]})</span>
        </button>

        {/* Button 3: Path Risk Visualizer */}
        <button
          onClick={onToggleRiskVisualizer}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isRiskVisualizerOpen ? '#238636' : '#161b22',
            border: `1px solid ${isRiskVisualizerOpen ? '#2ea043' : '#30363d'}`,
            borderRadius: '6px',
            color: '#f0f6fc',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Shield size={14} color={isRiskVisualizerOpen ? '#ffffff' : '#3fb950'} />
          <span>Risk Assessment</span>
        </button>

        {/* Button 4: Map Layers Toggle */}
        <button
          onClick={onToggleMapLayers}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isMapLayersOpen ? '#1f6feb' : '#161b22',
            border: `1px solid ${isMapLayersOpen ? '#388bfd' : '#30363d'}`,
            borderRadius: '6px',
            color: '#f0f6fc',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Layers size={14} color={isMapLayersOpen ? '#ffffff' : '#8b949e'} />
          <span>Map Layers</span>
        </button>

      </div>
    </header>
  );
};

export default Header;

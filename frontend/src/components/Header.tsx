import React from 'react';
import { Compass, Ship, Layers, Navigation } from 'lucide-react';

interface HeaderProps {
  isMissionPlanOpen: boolean;
  onToggleMissionPlan: () => void;
  isRouteDetailsOpen: boolean;
  onToggleRouteDetails: () => void;
  isMapLayersOpen: boolean;
  onToggleMapLayers: () => void;
  selectedRouteName?: string;
}

export const Header: React.FC<HeaderProps> = ({
  isMissionPlanOpen,
  onToggleMissionPlan,
  isRouteDetailsOpen,
  onToggleRouteDetails,
  isMapLayersOpen,
  onToggleMapLayers,
  selectedRouteName = 'Fastest Route'
}) => {
  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 16px',
        background: '#090d16',
        borderBottom: '1.5px solid #1e293b',
        color: '#f8fafc',
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
            borderRadius: '4px',
            background: 'rgba(56, 189, 248, 0.15)',
            border: '1px solid #0284c7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <Compass size={18} color="#38bdf8" />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13.5px', fontWeight: 800, letterSpacing: '0.5px', color: '#f8fafc' }}>
              AMIP // ANTARCTIC EXPEDITION MAP
            </span>
            <span style={{ fontSize: '9.5px', background: '#1e3a8a', color: '#93c5fd', padding: '1px 6px', borderRadius: '3px', fontWeight: 700 }}>
              NCPOR / MoES
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>
            44th Indian Antarctic Scientific Expedition (ISE-44) • ORV Sagar Kanya
          </div>
        </div>
      </div>

      {/* Action Buttons (Non-technical, clear visual feedback) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        
        {/* Button 1: Mission Plan Toggle */}
        <button
          onClick={onToggleMissionPlan}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isMissionPlanOpen ? '#0284c7' : '#1e293b',
            border: `1px solid ${isMissionPlanOpen ? '#38bdf8' : '#334155'}`,
            borderRadius: '4px',
            color: '#f8fafc',
            fontSize: '11.5px',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Ship size={14} color={isMissionPlanOpen ? '#ffffff' : '#38bdf8'} />
          <span>Mission Plan</span>
        </button>

        {/* Button 2: Route Details Toggle */}
        <button
          onClick={onToggleRouteDetails}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isRouteDetailsOpen ? '#2563eb' : '#1e293b',
            border: `1px solid ${isRouteDetailsOpen ? '#60a5fa' : '#334155'}`,
            borderRadius: '4px',
            color: '#f8fafc',
            fontSize: '11.5px',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Navigation size={14} color={isRouteDetailsOpen ? '#ffffff' : '#60a5fa'} />
          <span>Route Details ({selectedRouteName.split(' ')[0]})</span>
        </button>

        {/* Button 3: Map Layers Toggle */}
        <button
          onClick={onToggleMapLayers}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isMapLayersOpen ? '#0d9488' : '#1e293b',
            border: `1px solid ${isMapLayersOpen ? '#2dd4bf' : '#334155'}`,
            borderRadius: '4px',
            color: '#f8fafc',
            fontSize: '11.5px',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Layers size={14} color={isMapLayersOpen ? '#ffffff' : '#2dd4bf'} />
          <span>Map Layers</span>
        </button>

      </div>
    </header>
  );
};

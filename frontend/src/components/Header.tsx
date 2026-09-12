import React from 'react';
import { Ship, Layers, Navigation, Shield, Sparkles, Sun, Moon } from 'lucide-react';

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
  isDynamicVoyageOpen?: boolean;
  onToggleDynamicVoyage?: () => void;
  theme?: 'dark' | 'light';
  onToggleTheme?: () => void;
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
  selectedRouteName = 'Fastest Corridor',
  isDynamicVoyageOpen = false,
  onToggleDynamicVoyage,
  theme = 'dark',
  onToggleTheme
}) => {
  const isLight = theme === 'light';

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        background: isLight ? '#ffffff' : '#0d1117',
        borderBottom: `1px solid ${isLight ? '#bae6fd' : '#21262d'}`,
        color: isLight ? '#0f172a' : '#f0f6fc',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        zIndex: 30,
        height: '52px',
        boxSizing: 'border-box',
        transition: 'background 0.2s ease, border-color 0.2s ease, color 0.2s ease',
        boxShadow: isLight ? '0 2px 10px rgba(14, 165, 233, 0.08)' : 'none'
      }}
    >
      {/* Brand & Mission Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            overflow: 'hidden',
            background: '#ffffff',
            border: `1.5px solid ${isLight ? '#bfdbfe' : '#38bdf844'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: isLight ? '0 2px 8px rgba(14, 165, 233, 0.15)' : '0 2px 8px rgba(0, 0, 0, 0.5)',
            flexShrink: 0
          }}
        >
          <img
            src="/amip_logo.jpg"
            alt="AMIP Logo"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13.5px', fontWeight: 700, letterSpacing: '0.2px', color: isLight ? '#0f172a' : '#f0f6fc' }}>
              AMIP — Antarctica Mission Intelligence Planner
            </span>
            <span
              style={{
                fontSize: '9.5px',
                background: isLight ? '#e0f2fe' : '#1f6feb22',
                color: isLight ? '#0369a1' : '#58a6ff',
                border: `1px solid ${isLight ? '#bae6fd' : '#1f6feb44'}`,
                padding: '1px 6px',
                borderRadius: '3px',
                fontWeight: 600
              }}
            >
              NCPOR / MoES
            </span>
          </div>
          <div style={{ fontSize: '11px', color: isLight ? '#475569' : '#8b949e' }}>
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
            background: isMissionPlanOpen
              ? (isLight ? '#0284c7' : '#1f6feb')
              : (isLight ? '#f0f9ff' : '#161b22'),
            border: `1px solid ${
              isMissionPlanOpen
                ? (isLight ? '#0369a1' : '#388bfd')
                : (isLight ? '#bfdbfe' : '#30363d')
            }`,
            borderRadius: '6px',
            color: isMissionPlanOpen ? '#ffffff' : (isLight ? '#0f172a' : '#f0f6fc'),
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Ship size={14} color={isMissionPlanOpen ? '#ffffff' : (isLight ? '#0284c7' : '#58a6ff')} />
          <span>ISE-44 Plan</span>
        </button>

        {/* Button: Dynamic Voyage Planner (Custom Terminus Engine) */}
        <button
          onClick={onToggleDynamicVoyage}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isDynamicVoyageOpen
              ? (isLight ? '#16a34a' : '#238636')
              : (isLight ? '#f0f9ff' : '#161b22'),
            border: `1px solid ${
              isDynamicVoyageOpen
                ? (isLight ? '#15803d' : '#3fb950')
                : (isLight ? '#bfdbfe' : '#30363d')
            }`,
            borderRadius: '6px',
            color: isDynamicVoyageOpen ? '#ffffff' : (isLight ? '#0f172a' : '#f0f6fc'),
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
          title="Open Dynamic Voyage Planner to select custom origin and destination stations"
        >
          <Sparkles size={14} color={isDynamicVoyageOpen ? '#ffffff' : (isLight ? '#16a34a' : '#3fb950')} />
          <span>Dynamic Voyage Planner</span>
          <span
            style={{
              fontSize: '9px',
              background: isDynamicVoyageOpen
                ? 'rgba(255,255,255,0.25)'
                : (isLight ? 'rgba(22, 163, 74, 0.15)' : 'rgba(46, 160, 67, 0.25)'),
              color: isDynamicVoyageOpen ? '#ffffff' : (isLight ? '#15803d' : '#7ee787'),
              padding: '1px 5px',
              borderRadius: '3px',
              fontWeight: 700
            }}
          >
            CUSTOM
          </span>
        </button>

        {/* Button 2: Route Details Toggle */}
        <button
          onClick={onToggleRouteDetails}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isRouteDetailsOpen
              ? (isLight ? '#0284c7' : '#1f6feb')
              : (isLight ? '#f0f9ff' : '#161b22'),
            border: `1px solid ${
              isRouteDetailsOpen
                ? (isLight ? '#0369a1' : '#388bfd')
                : (isLight ? '#bfdbfe' : '#30363d')
            }`,
            borderRadius: '6px',
            color: isRouteDetailsOpen ? '#ffffff' : (isLight ? '#0f172a' : '#f0f6fc'),
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Navigation size={14} color={isRouteDetailsOpen ? '#ffffff' : (isLight ? '#0284c7' : '#38bdf8')} />
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
            background: isRiskVisualizerOpen
              ? (isLight ? '#16a34a' : '#238636')
              : (isLight ? '#f0f9ff' : '#161b22'),
            border: `1px solid ${
              isRiskVisualizerOpen
                ? (isLight ? '#15803d' : '#2ea043')
                : (isLight ? '#bfdbfe' : '#30363d')
            }`,
            borderRadius: '6px',
            color: isRiskVisualizerOpen ? '#ffffff' : (isLight ? '#0f172a' : '#f0f6fc'),
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Shield size={14} color={isRiskVisualizerOpen ? '#ffffff' : (isLight ? '#16a34a' : '#3fb950')} />
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
            background: isMapLayersOpen
              ? (isLight ? '#0284c7' : '#1f6feb')
              : (isLight ? '#f0f9ff' : '#161b22'),
            border: `1px solid ${
              isMapLayersOpen
                ? (isLight ? '#0369a1' : '#388bfd')
                : (isLight ? '#bfdbfe' : '#30363d')
            }`,
            borderRadius: '6px',
            color: isMapLayersOpen ? '#ffffff' : (isLight ? '#0f172a' : '#f0f6fc'),
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <Layers size={14} color={isMapLayersOpen ? '#ffffff' : (isLight ? '#64748b' : '#8b949e')} />
          <span>Map Layers</span>
        </button>

        {/* Button 5: Theme Toggle (Dark vs Light Blue & White) */}
        <button
          onClick={onToggleTheme}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: isLight ? '#e0f2fe' : '#161b22',
            border: `1px solid ${isLight ? '#7dd3fc' : '#30363d'}`,
            borderRadius: '6px',
            color: isLight ? '#0369a1' : '#f0f6fc',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
          title={isLight ? 'Switch to Dark Navy Theme' : 'Switch to Light Maritime Theme (Light Blue & White)'}
        >
          {isLight ? <Sun size={14} color="#0284c7" /> : <Moon size={14} color="#38bdf8" />}
          <span>{isLight ? 'Light Theme' : 'Dark Theme'}</span>
          <span
            style={{
              fontSize: '9px',
              background: isLight ? 'rgba(2, 132, 199, 0.15)' : 'rgba(56, 189, 248, 0.15)',
              color: isLight ? '#0284c7' : '#38bdf8',
              border: `1px solid ${isLight ? 'rgba(2, 132, 199, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
              padding: '1px 5px',
              borderRadius: '3px',
              fontWeight: 700,
              fontFamily: 'monospace'
            }}
          >
            {isLight ? 'ICE BLUE' : 'NAVY'}
          </span>
        </button>

      </div>
    </header>
  );
};

export default Header;

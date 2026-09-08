import React, { useState } from 'react';
import { useMission } from '../context/MissionContext';
import { AntarcticMap } from '../components/AntarcticMap';
import { ExplainabilityCard } from '../components/ExplainabilityCard';
import { PathfinderExplainabilityHUD } from '../components/PathfinderExplainabilityHUD';
import { EnvironmentalTimelineView } from './EnvironmentalTimelineView';
import { LocationComparisonView } from './LocationComparisonView';
import { RouteComparisonView } from './RouteComparisonView';
import { PredictionInspectorView } from './PredictionInspectorView';
import { MissionSetupView } from './MissionSetupView';
import {
  Layers,
  Navigation,
  ExternalLink,
  X,
  Cpu,
  Anchor,
  Eye,
  Compass,
  TrendingUp,
  MapPin,
  Crosshair,
  Sliders,
  Maximize2,
  Minimize2,
  Clock,
  Radio,
  Play
} from 'lucide-react';

export const AntarcticMapView: React.FC = () => {
  const {
    timeHorizon,
    setTimeHorizon,
    activeMapLayer,
    setActiveMapLayer,
    selectedRouteId,
    setActiveView,
    selectedH3Cell,
    setSelectedH3Cell,
    selectedSegment,
    setSelectedSegment,
    selectedIceberg,
    setSelectedIceberg,
    showH3Grid,
    setShowH3Grid,
    showTrajectories,
    setShowTrajectories,
    isPathfinderMode,
    setIsPathfinderMode
  } = useMission();

  // On-map HUD views toggles
  const [showTelemetryHeader, setShowTelemetryHeader] = useState<boolean>(true);
  const [showRoutePanel, setShowRoutePanel] = useState<boolean>(true);
  const [showLegend, setShowLegend] = useState<boolean>(true);
  const [showTimelineBar, setShowTimelineBar] = useState<boolean>(true);
  const [showLayerControls, setShowLayerControls] = useState<boolean>(true);
  const [isZenMode, setIsZenMode] = useState<boolean>(false);

  // Workstation View Overlays
  type OverlayViewType = 'timeline' | 'routes' | 'locations' | 'prediction' | 'setup' | 'vessel' | null;
  const [activeOverlayView, setActiveOverlayView] = useState<OverlayViewType>(null);
  const [isOverlayMaximized, setIsOverlayMaximized] = useState<boolean>(false);

  const toggleZenMode = () => {
    setIsZenMode((prev) => !prev);
  };

  // Helper to close all inspectors
  const closeAllInspectors = () => {
    setSelectedH3Cell(null);
    setSelectedSegment(null);
    setSelectedIceberg(null);
  };

  const isAnyInspectorOpen = !!(selectedH3Cell || selectedSegment || selectedIceberg);

  return (
    <div style={{ position: 'relative', height: '100%', width: '100%', overflow: 'hidden' }}>

      {/* Floating Buttons Directly on Map (No background container box) */}
      <div style={{
        position: 'absolute',
        top: '8px',
        left: '10px',
        right: '10px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '8px',
        flexWrap: 'wrap',
        pointerEvents: 'none',
        zIndex: 35
      }}>
        {/* Left: Environmental Overlays Layer Switcher */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          flexWrap: 'wrap',
          pointerEvents: 'auto'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            marginRight: '2px',
            background: 'rgba(255, 255, 255, 0.94)',
            backdropFilter: 'blur(10px)',
            border: '1px solid #bfdbfe',
            borderBottom: '2px solid #93c5fd',
            padding: '4px 7px',
            boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
          }}>
            <Layers size={13} color="#2563eb" />
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#1e3a8a', fontFamily: 'var(--font-mono)' }}>
              OVERLAYS
            </span>
          </div>

          {[
            { id: 'icebergs', label: 'Icebergs' },
            { id: 'sic', label: 'Sea-Ice (SIC)' },
            { id: 'risk', label: 'Composite Risk' },
            { id: 'weather', label: 'Ocean Dynamics' }
          ].map((layer) => {
            const isActive = activeMapLayer === layer.id;
            return (
              <button
                key={layer.id}
                onClick={() => {
                  setActiveMapLayer(layer.id as any);
                  if (layer.id === 'icebergs') {
                    setShowTrajectories(true);
                  }
                }}
                style={{
                  padding: '4px 9px',
                  borderRadius: '0px',
                  border: '1px solid',
                  borderColor: isActive ? '#1d4ed8' : '#bfdbfe',
                  borderBottom: isActive ? '2px solid #1e3a8a' : '2px solid #93c5fd',
                  background: isActive ? '#2563eb' : 'rgba(255, 255, 255, 0.94)',
                  backdropFilter: 'blur(10px)',
                  color: isActive ? '#ffffff' : '#1e3a8a',
                  fontSize: '10.5px',
                  fontWeight: isActive ? 800 : 600,
                  cursor: 'pointer',
                  boxShadow: isActive ? '0 2px 0 #1e3a8a, 0 3px 5px rgba(30, 58, 138, 0.25)' : '0 2px 5px rgba(15, 23, 42, 0.12)'
                }}
              >
                {layer.label}
              </button>
            );
          })}
        </div>

        {/* Center: HUD Panel Toggles */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          flexWrap: 'wrap',
          pointerEvents: 'auto'
        }}>
          <button
            onClick={() => setShowRoutePanel(!showRoutePanel)}
            title="Toggle Route Alternatives HUD on Map"
            style={{
              padding: '4px 8px',
              background: showRoutePanel && !isZenMode ? '#eff6ff' : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: '1px solid #bfdbfe',
              borderBottom: showRoutePanel && !isZenMode ? '2px solid #2563eb' : '2px solid #93c5fd',
              color: showRoutePanel && !isZenMode ? '#1e3a8a' : '#64748b',
              fontSize: '10.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
            }}
          >
            <Navigation size={12} color={showRoutePanel && !isZenMode ? '#2563eb' : '#94a3b8'} />
            <span>ROUTES HUD</span>
          </button>

          <button
            onClick={() => setShowTimelineBar(!showTimelineBar)}
            title="Toggle 90-Day Timeline Bar on Map"
            style={{
              padding: '4px 8px',
              background: showTimelineBar && !isZenMode ? '#eff6ff' : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: '1px solid #bfdbfe',
              borderBottom: showTimelineBar && !isZenMode ? '2px solid #2563eb' : '2px solid #93c5fd',
              color: showTimelineBar && !isZenMode ? '#1e3a8a' : '#64748b',
              fontSize: '10.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
            }}
          >
            <Clock size={12} color={showTimelineBar && !isZenMode ? '#2563eb' : '#94a3b8'} />
            <span>TIMELINE</span>
          </button>

          <button
            onClick={() => setShowLegend(!showLegend)}
            title="Toggle Map Legend"
            style={{
              padding: '4px 8px',
              background: showLegend && !isZenMode ? '#eff6ff' : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: '1px solid #bfdbfe',
              borderBottom: showLegend && !isZenMode ? '2px solid #2563eb' : '2px solid #93c5fd',
              color: showLegend && !isZenMode ? '#1e3a8a' : '#64748b',
              fontSize: '10.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
            }}
          >
            <Compass size={12} color={showLegend && !isZenMode ? '#2563eb' : '#94a3b8'} />
            <span>LEGEND</span>
          </button>

          <button
            onClick={() => setShowTelemetryHeader(!showTelemetryHeader)}
            title="Toggle Telemetry Strip"
            style={{
              padding: '4px 8px',
              background: showTelemetryHeader && !isZenMode ? '#eff6ff' : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: '1px solid #bfdbfe',
              borderBottom: showTelemetryHeader && !isZenMode ? '2px solid #2563eb' : '2px solid #93c5fd',
              color: showTelemetryHeader && !isZenMode ? '#1e3a8a' : '#64748b',
              fontSize: '10.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
            }}
          >
            <Radio size={12} color={showTelemetryHeader && !isZenMode ? '#2563eb' : '#94a3b8'} />
            <span>TELEMETRY</span>
          </button>

          <button
            onClick={toggleZenMode}
            title={isZenMode ? "Exit Zen Mode (Restore Panels)" : "Zen Mode (Hide All HUD Overlays)"}
            style={{
              padding: '4px 10px',
              background: isZenMode ? '#1e3a8a' : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: '1px solid',
              borderColor: isZenMode ? '#172554' : '#bfdbfe',
              borderBottom: isZenMode ? '2px solid #0f172a' : '2px solid #93c5fd',
              color: isZenMode ? '#ffffff' : '#0f172a',
              fontSize: '10.5px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
            }}
          >
            <Eye size={12} color={isZenMode ? '#38bdf8' : '#2563eb'} />
            <span>{isZenMode ? "EXIT ZEN MODE" : "ZEN MAP"}</span>
          </button>

          {/* Direct H3 Grid Toggle */}
          <button
            onClick={() => setShowH3Grid(!showH3Grid)}
            title={showH3Grid ? "Hide H3 Grid Mesh Lines" : "Show H3 Grid Mesh Lines"}
            style={{
              padding: '4px 8px',
              background: showH3Grid && !isZenMode ? '#eff6ff' : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: '1px solid #bfdbfe',
              borderBottom: showH3Grid && !isZenMode ? '2px solid #2563eb' : '2px solid #93c5fd',
              color: showH3Grid && !isZenMode ? '#1e3a8a' : '#64748b',
              fontSize: '10.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
            }}
          >
            <Layers size={12} color={showH3Grid && !isZenMode ? '#2563eb' : '#94a3b8'} />
            <span>H3 GRID: {showH3Grid ? 'ON' : 'OFF'}</span>
          </button>

          {/* Direct Iceberg Trajectories Toggle */}
          <button
            onClick={() => setShowTrajectories(!showTrajectories)}
            title={showTrajectories ? "Hide 90-Day Iceberg Trajectories" : "Show 90-Day Iceberg Trajectories"}
            style={{
              padding: '4px 8px',
              background: showTrajectories && !isZenMode ? '#fff7ed' : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: '1px solid #fed7aa',
              borderBottom: showTrajectories && !isZenMode ? '2px solid #ea580c' : '2px solid #fdba74',
              color: showTrajectories && !isZenMode ? '#c2410c' : '#64748b',
              fontSize: '10.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
            }}
          >
            <Navigation size={12} color={showTrajectories && !isZenMode ? '#ea580c' : '#94a3b8'} />
            <span>TRAJECTORIES: {showTrajectories ? 'ON' : 'OFF'}</span>
          </button>

          {/* Direct Pathfinder Simulator Toggle */}
          <button
            onClick={() => setIsPathfinderMode(!isPathfinderMode)}
            title={isPathfinderMode ? "Exit Grid-by-Grid Pathfinder Simulation" : "Step-by-Step Route Creation & Decision Explainability Simulator"}
            style={{
              padding: '4px 10px',
              background: isPathfinderMode
                ? 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)'
                : 'rgba(255, 255, 255, 0.94)',
              backdropFilter: 'blur(10px)',
              border: isPathfinderMode ? '1px solid #38bdf8' : '1px solid #bfdbfe',
              borderBottom: isPathfinderMode ? '2px solid #0284c7' : '2px solid #93c5fd',
              color: isPathfinderMode ? '#ffffff' : '#0369a1',
              fontSize: '10.5px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: isPathfinderMode
                ? '0 0 14px rgba(56, 189, 248, 0.6), 0 2px 5px rgba(15, 23, 42, 0.2)'
                : '0 2px 5px rgba(15, 23, 42, 0.12)',
              letterSpacing: '0.02em',
              transition: 'all 0.2s ease'
            }}
          >
            <Play size={12} color={isPathfinderMode ? '#ffffff' : '#0284c7'} />
            <span>GRID PATHFINDER: {isPathfinderMode ? 'ACTIVE' : 'SIMULATE'}</span>
          </button>
        </div>

        {/* Right: Workstation View Overlays */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          flexWrap: 'wrap',
          pointerEvents: 'auto'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            background: 'rgba(255, 255, 255, 0.94)',
            backdropFilter: 'blur(10px)',
            border: '1px solid #bfdbfe',
            borderBottom: '2px solid #93c5fd',
            padding: '4px 7px',
            boxShadow: '0 2px 5px rgba(15, 23, 42, 0.12)'
          }}>
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#1e3a8a', fontFamily: 'var(--font-mono)' }}>
              VIEWS
            </span>
          </div>

          {[
            { id: 'timeline', label: 'Timeline', icon: <TrendingUp size={11} /> },
            { id: 'routes', label: 'Route Compare', icon: <Navigation size={11} /> },
            { id: 'locations', label: 'Locations', icon: <MapPin size={11} /> },
            { id: 'prediction', label: 'ML Inspector', icon: <Crosshair size={11} /> },
            { id: 'setup', label: 'Setup', icon: <Sliders size={11} /> },
            { id: 'vessel', label: 'Vessel & AI', icon: <Anchor size={11} /> }
          ].map((vw) => {
            const isViewActive = activeOverlayView === vw.id;
            return (
              <button
                key={vw.id}
                onClick={() => setActiveOverlayView(isViewActive ? null : (vw.id as any))}
                title={`Toggle ${vw.label} overlay`}
                style={{
                  padding: '4px 8px',
                  borderRadius: '0px',
                  border: '1px solid',
                  borderColor: isViewActive ? '#1d4ed8' : '#bfdbfe',
                  borderBottom: isViewActive ? '2px solid #1e3a8a' : '2px solid #93c5fd',
                  background: isViewActive ? '#2563eb' : 'rgba(255, 255, 255, 0.94)',
                  backdropFilter: 'blur(10px)',
                  color: isViewActive ? '#ffffff' : '#1e3a8a',
                  fontSize: '10.5px',
                  fontWeight: isViewActive ? 800 : 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  boxShadow: isViewActive ? '0 2px 0 #1e3a8a, 0 3px 6px rgba(30, 58, 138, 0.25)' : '0 2px 5px rgba(15, 23, 42, 0.12)'
                }}
              >
                {vw.icon}
                <span>{vw.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Full-bleed Map & Overlays Container */}
      <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
        <AntarcticMap
          selectedHorizon={timeHorizon}
          activeLayer={activeMapLayer}
          selectedRoute={selectedRouteId}
          onHorizonChange={(hz) => setTimeHorizon(hz as any)}
          showTelemetryHeader={!isZenMode && showTelemetryHeader}
          showLayerToggles={!isZenMode && showLayerControls}
          showRoutePanel={!isZenMode && showRoutePanel}
          showLegend={!isZenMode && showLegend}
          showTimelineBar={!isZenMode && showTimelineBar}
          onToggleRoutePanel={() => setShowRoutePanel(!showRoutePanel)}
          onToggleLegend={() => setShowLegend(!showLegend)}
          onToggleTimelineBar={() => setShowTimelineBar(!showTimelineBar)}
          onToggleTelemetryHeader={() => setShowTelemetryHeader(!showTelemetryHeader)}
          onToggleLayerToggles={() => setShowLayerControls(!showLayerControls)}
        />

        {/* Togglable Workstation View Overlay Modal / Window */}
        {activeOverlayView && (
          <div style={{
            position: 'absolute',
            top: isOverlayMaximized ? '0' : '50px',
            left: isOverlayMaximized ? '0' : '10px',
            right: isOverlayMaximized ? '0' : (isAnyInspectorOpen ? '396px' : '10px'),
            bottom: isOverlayMaximized ? '0' : '10px',
            zIndex: 45,
          background: 'rgba(255, 255, 255, 0.97)',
          backdropFilter: 'blur(20px)',
          border: '2px solid #2563eb',
          boxShadow: '0 20px 50px rgba(15, 23, 42, 0.35)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          transition: 'all 0.15s ease'
        }}>
          {/* Overlay Header */}
          <div style={{
            background: '#e0f2fe',
            borderBottom: '1.5px solid #bfdbfe',
            padding: '6px 12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '8px'
          }}>
            {/* Left Title and View Switcher Tabs */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Cpu size={15} color="#2563eb" />
                <span style={{ color: '#172554', fontWeight: 800, fontSize: '11.5px', fontFamily: 'var(--font-mono)' }}>
                  OVERLAY VIEW: {activeOverlayView.toUpperCase()}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '3px', background: 'rgba(255,255,255,0.7)', padding: '2px', border: '1px solid #bfdbfe' }}>
                {[
                  { id: 'timeline', label: 'Timeline' },
                  { id: 'routes', label: 'Route Compare' },
                  { id: 'locations', label: 'Locations' },
                  { id: 'prediction', label: 'ML Inspector' },
                  { id: 'setup', label: 'Setup' },
                  { id: 'vessel', label: 'Vessel & AI' }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveOverlayView(tab.id as any)}
                    style={{
                      padding: '2px 6px',
                      border: 'none',
                      background: activeOverlayView === tab.id ? '#2563eb' : 'transparent',
                      color: activeOverlayView === tab.id ? '#ffffff' : '#334155',
                      fontSize: '9.5px',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: activeOverlayView === tab.id ? 800 : 500,
                      cursor: 'pointer'
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Right Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {/* Full Screen / Full Page Navigate */}
              {activeOverlayView !== 'vessel' && (
                <button
                  onClick={() => {
                    const viewIdMap: Record<string, any> = {
                      timeline: 'environmental-timeline',
                      routes: 'route-comparison',
                      locations: 'location-comparison',
                      prediction: 'prediction-inspector',
                      setup: 'mission-setup'
                    };
                    if (viewIdMap[activeOverlayView]) {
                      setActiveView(viewIdMap[activeOverlayView]);
                    }
                  }}
                  title="Open as Full Page View"
                  style={{
                    padding: '3px 8px',
                    background: '#ffffff',
                    border: '1px solid #bfdbfe',
                    color: '#2563eb',
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <ExternalLink size={11} />
                  <span>FULL VIEW</span>
                </button>
              )}

              {/* Maximize / Restore Toggle */}
              <button
                onClick={() => setIsOverlayMaximized(!isOverlayMaximized)}
                title={isOverlayMaximized ? "Restore size" : "Maximize view"}
                style={{
                  padding: '3px 6px',
                  background: '#ffffff',
                  border: '1px solid #bfdbfe',
                  color: '#475569',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                {isOverlayMaximized ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
              </button>

              {/* Close Button */}
              <button
                onClick={() => setActiveOverlayView(null)}
                title="Close Overlay View"
                style={{
                  padding: '3px 6px',
                  background: '#ffffff',
                  border: '1px solid #fca5a5',
                  color: '#dc2626',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Overlay Content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
            {activeOverlayView === 'timeline' && <EnvironmentalTimelineView />}
            {activeOverlayView === 'routes' && <RouteComparisonView />}
            {activeOverlayView === 'locations' && <LocationComparisonView />}
            {activeOverlayView === 'prediction' && <PredictionInspectorView />}
            {activeOverlayView === 'setup' && <MissionSetupView onClose={() => setActiveOverlayView(null)} />}
            {activeOverlayView === 'vessel' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '700px', margin: '0 auto' }}>
                <div className="ws-panel" style={{ padding: '12px 14px', background: 'rgba(255, 255, 255, 0.95)', border: '1px solid #bfdbfe' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Anchor size={15} color="#1e3a8a" />
                      <span style={{ fontSize: '12px', fontWeight: 800, color: '#1e3a8a', fontFamily: 'var(--font-mono)' }}>
                        ORV SAGAR KANYA CONFIGURATION
                      </span>
                    </div>
                    <span style={{ fontSize: '10px', background: '#eff6ff', color: '#1d4ed8', padding: '2px 6px', fontWeight: 700 }}>
                      CRUISE: 9.0 KT
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: '#475569' }}>
                    <div>LENGTH OVERALL (LOA): <strong style={{ color: '#0f172a' }}>100.34 m</strong></div>
                    <div>BEAM: <strong style={{ color: '#0f172a' }}>16.39 m</strong></div>
                    <div>DESIGN DRAFT: <strong style={{ color: '#0f172a' }}>5.60 m</strong></div>
                    <div>MAX OPERATIONAL SIC: <strong style={{ color: '#0284c7' }}>&lt; 15% (MIZ)</strong></div>
                    <div>DAILY CRUISE FUEL: <strong style={{ color: '#0f172a' }}>8.16 MT/d</strong></div>
                    <div>BUNKER CAPACITY: <strong style={{ color: '#0f172a' }}>368.0 MT</strong></div>
                  </div>
                </div>

                <ExplainabilityCard />
              </div>
            )}
          </div>
        </div>
      )}

        {/* Dynamic Multi-State Inspector Drawer (Floating Right Panel) */}
        {isAnyInspectorOpen && (
          <div style={{
            position: 'absolute',
            top: '50px',
            right: '8px',
            bottom: '48px',
            width: '380px',
            zIndex: 40,
            background: 'rgba(255, 255, 255, 0.96)',
            backdropFilter: 'blur(16px)',
            border: '1.5px solid #2563eb',
            boxShadow: '0 8px 30px rgba(15, 23, 42, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>

            {/* Inspector Header */}
            <div className="ws-panel-header" style={{ background: '#e0f2fe', borderBottom: '1.5px solid #bfdbfe', padding: '8px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Cpu size={15} color="#2563eb" />
                <span style={{ color: '#172554', fontWeight: 800, fontSize: '11.5px', fontFamily: 'var(--font-mono)' }}>
                  {selectedIceberg
                    ? `ICEBERG INSPECTOR: #${selectedIceberg.id}`
                    : selectedSegment
                    ? `SEGMENT INSPECTOR: H3 STEP`
                    : `H3 CELL: #${selectedH3Cell?.id}`}
                </span>
              </div>
              <button
                onClick={closeAllInspectors}
                title="Close Inspector"
                style={{ background: 'transparent', border: 'none', color: '#1e293b', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '2px' }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Inspector Body Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>

              {/* 1. ICEBERG INSPECTOR CONTENT */}
              {selectedIceberg && (
                <>
                  <div style={{ padding: '8px 10px', background: '#fff7ed', border: '1px solid #fed7aa', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '13px', fontWeight: 800, color: '#c2410c', fontFamily: 'var(--font-mono)' }}>
                        {selectedIceberg.id}
                      </span>
                      <span style={{ fontSize: '10px', background: '#ffedd5', color: '#c2410c', padding: '2px 6px', fontWeight: 700, border: '1px solid #fdba74' }}>
                        {selectedIceberg.status || 'ACTIVE_DRIFT'}
                      </span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#7c2d12', fontFamily: 'var(--font-mono)' }}>
                      Source Agency: <strong>{selectedIceberg.source || 'USNIC / BYU / NIC'}</strong>
                    </div>
                  </div>

                  <div className="ws-panel" style={{ padding: '10px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#1e3a8a', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                      OBSERVED DIMENSIONS & METRICS
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div>LENGTH: <strong style={{ color: '#0f172a' }}>{selectedIceberg.latestObservation?.length_km ?? 15} km</strong></div>
                      <div>WIDTH: <strong style={{ color: '#0f172a' }}>{selectedIceberg.latestObservation?.width_km ?? 8} km</strong></div>
                      <div>SURFACE AREA: <strong style={{ color: '#0f172a' }}>{selectedIceberg.latestObservation?.area_sqkm ?? 120} km²</strong></div>
                      <div>DRIFT TRAJECTORY: <strong style={{ color: '#ea580c' }}>90 Days Persisted</strong></div>
                    </div>
                  </div>

                  <div className="ws-panel" style={{ padding: '10px', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#0f172a', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                      CURRENT HORIZON POSITION ({timeHorizon}):
                    </div>
                    <p style={{ fontSize: '10px', color: '#475569', margin: 0, fontFamily: 'var(--font-mono)' }}>
                      Dynamically projected along Antarctic Coastal Current and ACC ocean circulation forcing. Trajectory line visible on map.
                    </p>
                  </div>
                </>
              )}

              {/* 2. ROUTE SEGMENT INSPECTOR CONTENT */}
              {selectedSegment && (
                <>
                  <div style={{ padding: '8px 10px', background: '#eff6ff', border: '1px solid #bfdbfe', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', fontWeight: 800, color: '#1d4ed8', fontFamily: 'var(--font-mono)' }}>
                        {selectedSegment.from_cell} ➔ {selectedSegment.to_cell}
                      </span>
                      <span style={{ fontSize: '10px', background: '#dbeafe', color: '#1e3a8a', padding: '2px 6px', fontWeight: 800 }}>
                        {selectedSegment.distance_nm.toFixed(1)} NM
                      </span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#1e293b', fontFamily: 'var(--font-mono)' }}>
                      HEADING: <strong>{selectedSegment.heading_deg.toFixed(1)}°</strong> | TIME: <strong>{selectedSegment.departure_eta} ➔ {selectedSegment.arrival_eta}</strong>
                    </div>
                  </div>

                  {/* Vessel Performance on Segment */}
                  <div className="ws-panel" style={{ padding: '10px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#1e3a8a', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                      HYDRODYNAMIC VESSEL PERFORMANCE
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div>STW (THROUGH WATER): <strong style={{ color: '#0f172a' }}>{selectedSegment.stw_kt.toFixed(2)} kt</strong></div>
                      <div>CURRENT ALONG-TRACK: <strong style={{ color: selectedSegment.current_along_track_kt >= 0 ? '#0d9488' : '#dc2626' }}>{selectedSegment.current_along_track_kt >= 0 ? '+' : ''}{selectedSegment.current_along_track_kt.toFixed(2)} kt</strong></div>
                      <div>SOG (OVER GROUND): <strong style={{ color: '#2563eb' }}>{selectedSegment.sog_kt.toFixed(2)} kt</strong></div>
                      <div>ESTIMATED FUEL BURN: <strong style={{ color: '#ea580c' }}>{selectedSegment.fuel_burn_mt.toFixed(2)} MT</strong></div>
                    </div>
                  </div>

                  {/* Environmental Factors along Segment */}
                  <div className="ws-panel" style={{ padding: '10px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#1e3a8a', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                      ENVIRONMENTAL CONSTRAINTS
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div>SEA-ICE CONC: <strong style={{ color: '#0284c7' }}>{selectedSegment.sic_pct.toFixed(1)}%</strong></div>
                      <div>SIGNIFICANT WAVE (Hs): <strong style={{ color: '#0f172a' }}>{selectedSegment.wave_height_m.toFixed(1)} m</strong></div>
                      <div>WIND SPEED: <strong style={{ color: '#0f172a' }}>{selectedSegment.wind_speed_kt.toFixed(1)} kt</strong></div>
                      <div>DEPTH / UKC: <strong style={{ color: '#0f172a' }}>{selectedSegment.depth_m.toFixed(0)}m / {selectedSegment.ukc_m.toFixed(0)}m</strong></div>
                    </div>
                  </div>

                  {/* Segment Objective Cost */}
                  <div style={{ padding: '8px 10px', background: '#f0fdf4', border: '1px solid #bbf7d0', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                    <div>OBJECTIVE STEP COST: <strong style={{ color: '#15803d' }}>{selectedSegment.segment_cost.toFixed(3)}</strong></div>
                    <div style={{ color: '#166534', fontSize: '9px', marginTop: '2px' }}>
                      Calculated from time penalty, fuel burn curve, and composite risk gradient.
                    </div>
                  </div>
                </>
              )}

              {/* 3. H3 CELL INSPECTOR CONTENT */}
              {selectedH3Cell && (
                <>
                  {/* Status Banner */}
                  <div style={{
                    padding: '8px 10px',
                    background: selectedH3Cell.risk?.hard_blocked ? '#fef2f2' : '#f0fdf4',
                    border: '1px solid',
                    borderColor: selectedH3Cell.risk?.hard_blocked ? '#f87171' : '#86efac',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{ fontSize: '11px', fontWeight: 800, color: selectedH3Cell.risk?.hard_blocked ? '#dc2626' : '#16a34a', fontFamily: 'var(--font-mono)' }}>
                      {selectedH3Cell.risk?.hard_blocked ? 'NO-GO / HARD BLOCKED' : 'NAVIGABLE / PASSABLE'}
                    </span>
                    <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                      {selectedH3Cell.env?.lat ? Math.abs(selectedH3Cell.env.lat).toFixed(2) : '0'}°S, {selectedH3Cell.env?.lon ? selectedH3Cell.env.lon.toFixed(2) : '0'}°E
                    </span>
                  </div>

                  {/* Sea Ice Breakdown */}
                  <div className="ws-panel" style={{ padding: '10px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#0284c7', marginBottom: '6px', fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>SEA ICE CONCENTRATION (SIC)</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div>MEDIAN SIC: <strong style={{ color: '#0284c7' }}>{selectedH3Cell.env?.sic_pct ?? 0}%</strong></div>
                      <div>5%-95% SPREAD: <strong style={{ color: '#0f172a' }}>{((selectedH3Cell.env?.sic_q05 ?? 0) * 100).toFixed(0)}% - {((selectedH3Cell.env?.sic_q95 ?? 0) * 100).toFixed(0)}%</strong></div>
                      <div>UNCERTAINTY: <strong style={{ color: '#64748b' }}>±{((selectedH3Cell.env?.sic_uncertainty ?? 0) * 100).toFixed(1)}%</strong></div>
                      <div>DATA SOURCE: <strong style={{ color: '#1e3a8a' }}>{selectedH3Cell.env?.sic_source || 'Synthetic POC'}</strong></div>
                    </div>
                  </div>

                  {/* Ocean & Waves Breakdown */}
                  <div className="ws-panel" style={{ padding: '10px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#0d9488', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                      OCEAN CURRENTS & WAVES
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div>CURRENT MAG: <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.current_magnitude ?? 0} m/s</strong></div>
                      <div>CURRENT DIR: <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.current_direction ?? 0}°</strong></div>
                      <div>WAVE HEIGHT (Hs): <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.wave_height ?? 0} m</strong></div>
                      <div>WAVE PERIOD: <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.wave_period ?? 0} s</strong></div>
                      <div>WIND SPEED: <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.wind_speed ?? 0} kt</strong></div>
                      <div>WIND DIR: <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.wind_direction ?? 0}°</strong></div>
                    </div>
                  </div>

                  {/* Bathymetry & Sagar Kanya UKC */}
                  <div className="ws-panel" style={{ padding: '10px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#1e3a8a', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                      GEBCO BATHYMETRY & UNDER-KEEL CLEARANCE
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div>SEABED DEPTH: <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.depth ? selectedH3Cell.env.depth.toFixed(0) : 0} m</strong></div>
                      <div>VESSEL DRAFT: <strong style={{ color: '#0f172a' }}>5.60 m</strong></div>
                      <div>CLEARANCE (UKC): <strong style={{ color: '#059669' }}>{selectedH3Cell.env?.under_keel_clearance ? selectedH3Cell.env.under_keel_clearance.toFixed(0) : 0} m</strong></div>
                      <div>BATHY STATUS: <strong style={{ color: '#059669' }}>Deep Water Safe</strong></div>
                    </div>
                  </div>

                  {/* Iceberg Hazard in Cell */}
                  <div className="ws-panel" style={{ padding: '10px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#ea580c', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                      ICEBERG OCCUPANCY & HAZARD
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div>HAZARD SCORE: <strong style={{ color: '#ea580c' }}>{((selectedH3Cell.env?.iceberg_hazard ?? 0) * 100).toFixed(1)}%</strong></div>
                      <div>NEARBY ICEBERGS: <strong style={{ color: '#0f172a' }}>{selectedH3Cell.env?.iceberg_count ?? 0} count</strong></div>
                    </div>
                  </div>

                  {/* 7 Risk Engine Decomposition */}
                  <div className="ws-panel" style={{ padding: '10px', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#1e293b', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                      COMPOSITE RISK DECOMPOSITION
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>TOTAL COMPOSITE RISK:</span>
                        <strong style={{ color: (selectedH3Cell.risk?.composite_risk ?? 0) > 0.4 ? '#dc2626' : '#0d9488' }}>
                          {((selectedH3Cell.risk?.composite_risk ?? 0) * 100).toFixed(1)}%
                        </strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b' }}>
                        <span>Sea-Ice Factor:</span>
                        <span>{((selectedH3Cell.risk?.sic_risk ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b' }}>
                        <span>Iceberg Drift Factor:</span>
                        <span>{((selectedH3Cell.risk?.iceberg_risk ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b' }}>
                        <span>Wave / Swell Factor:</span>
                        <span>{((selectedH3Cell.risk?.wave_risk ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b' }}>
                        <span>Wind / Katabatic Factor:</span>
                        <span>{((selectedH3Cell.risk?.wind_risk ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b' }}>
                        <span>Bathymetric Hazard:</span>
                        <span>{((selectedH3Cell.risk?.bathymetric_risk ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                </>
              )}

            </div>
          </div>
        )}

        {/* 4D A* Pathfinder Grid-by-Grid Simulator HUD */}
        <PathfinderExplainabilityHUD />

      </div>
    </div>
  );
};

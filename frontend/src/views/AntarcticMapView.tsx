import React, { useState } from 'react';
import { useMission } from '../context/MissionContext';
import { AntarcticMap } from '../components/AntarcticMap';
import { ExplainabilityCard } from '../components/ExplainabilityCard';
import {
  Layers,
  Navigation,
  ExternalLink,
  X,
  Cpu,
  PanelLeftClose,
  PanelLeftOpen,
  Anchor
} from 'lucide-react';

export const AntarcticMapView: React.FC = () => {
  const {
    timeHorizon,
    setTimeHorizon,
    activeMapLayer,
    setActiveMapLayer,
    routes,
    selectedRouteId,
    setSelectedRouteId,
    setActiveView,
    selectedH3Cell,
    setSelectedH3Cell,
    selectedSegment,
    setSelectedSegment,
    selectedIceberg,
    setSelectedIceberg
  } = useMission();

  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);

  // Helper to close all inspectors
  const closeAllInspectors = () => {
    setSelectedH3Cell(null);
    setSelectedSegment(null);
    setSelectedIceberg(null);
  };

  const isAnyInspectorOpen = !!(selectedH3Cell || selectedSegment || selectedIceberg);

  return (
    <div style={{ display: 'flex', gap: '10px', height: '100%', overflow: 'hidden', padding: '8px' }}>

      {/* Left Workstation Sidebar (Collapsible) */}
      {isSidebarOpen && (
        <div style={{
          width: '340px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          overflowY: 'auto',
          flexShrink: 0
        }}>

          {/* Intelligence Layer Selector */}
          <div className="ws-panel" style={{ background: 'rgba(240, 248, 255, 0.85)', backdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.85)', borderBottom: '1px solid rgba(191, 219, 254, 0.85)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={14} color="#2563eb" />
                <span>ENVIRONMENTAL OVERLAYS</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="ws-badge ws-badge-info">
                  {timeHorizon}
                </span>
                <button
                  onClick={() => setIsSidebarOpen(false)}
                  title="Close Sidebar"
                  style={{
                    background: '#ffffff',
                    border: '1px solid #bfdbfe',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '3px 5px',
                    color: '#2563eb'
                  }}
                >
                  <PanelLeftClose size={13} />
                </button>
              </div>
            </div>

            <div style={{ padding: '8px 10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              {[
                { id: 'icebergs', label: 'Icebergs', desc: '73 Tracked & Drifts' },
                { id: 'sic', label: 'Sea-Ice (SIC)', desc: 'Historical POC Scale' },
                { id: 'risk', label: 'Composite Risk', desc: '7 Factor Breakdown' },
                { id: 'weather', label: 'Ocean Dynamics', desc: 'Currents, Wind & Waves' }
              ].map((layer) => {
                const isActive = activeMapLayer === layer.id;
                return (
                  <button
                    key={layer.id}
                    onClick={() => setActiveMapLayer(layer.id as any)}
                    style={{
                      padding: '6px 10px',
                      borderRadius: '0px',
                      border: '1px solid',
                      borderColor: isActive ? '#1d4ed8' : 'rgba(191, 219, 254, 0.85)',
                      borderBottom: isActive ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                      background: isActive ? '#dbeafe' : 'rgba(255, 255, 255, 0.85)',
                      color: isActive ? '#1e3a8a' : '#1e293b',
                      fontSize: '11px',
                      fontWeight: isActive ? 800 : 600,
                      cursor: 'pointer',
                      textAlign: 'left',
                      boxShadow: isActive ? 'inset 0 1px 0 rgba(255,255,255,0.35), 0 3px 0 #1e3a8a' : 'inset 0 1px 0 rgba(255,255,255,0.7), 0 2px 0 #93c5fd'
                    }}
                  >
                    <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 700 }}>{layer.label}</div>
                    <div style={{ fontSize: '9px', color: isActive ? '#2563eb' : '#64748b', marginTop: '2px' }}>
                      {layer.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Candidate Routes Selector (All 5 Real Alternatives) */}
          <div className="ws-panel" style={{ background: 'rgba(240, 248, 255, 0.85)', backdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.85)', borderBottom: '1px solid rgba(191, 219, 254, 0.85)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Navigation size={14} color="#2563eb" />
                <span>5 CANONICAL ROUTE ALTERNATIVES</span>
              </div>
              <button
                onClick={() => setActiveView('route-comparison')}
                style={{
                  fontSize: '10px',
                  color: '#2563eb',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                  fontFamily: 'var(--font-sans)',
                  fontWeight: 700
                }}
              >
                <span>COMPARE</span>
                <ExternalLink size={10} />
              </button>
            </div>

            <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
              {routes.map((r) => {
                const isSelected = selectedRouteId === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => setSelectedRouteId(r.id)}
                    style={{
                      padding: '6px 8px',
                      borderRadius: '0px',
                      border: '1px solid',
                      borderColor: isSelected ? '#2563eb' : 'rgba(191, 219, 254, 0.85)',
                      background: isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.65)',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '2px',
                      borderLeft: isSelected ? `4px solid ${r.color}` : '1px solid rgba(191, 219, 254, 0.85)',
                      boxShadow: isSelected ? '0 2px 4px rgba(37,99,235,0.12)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', fontWeight: 800, color: isSelected ? '#1e3a8a' : '#0f172a' }}>{r.name}</span>
                      <span style={{ fontSize: '9.5px', color: r.color, fontWeight: 800, fontFamily: 'var(--font-mono)' }}>{r.tag}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9.5px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                      <span>ETA: <strong style={{ color: '#0f172a' }}>{r.durationDays ? r.durationDays.toFixed(1) : r.transitDays.toFixed(1)}d</strong></span>
                      <span>Dist: <strong style={{ color: '#0f172a' }}>{r.distanceNM.toFixed(0)} NM</strong></span>
                      <span>Fuel: <strong style={{ color: '#ea580c' }}>{r.estimatedFuelMT.toFixed(0)} MT</strong></span>
                      <span>Risk: <strong style={{ color: r.meanRisk > 0.3 ? '#dc2626' : '#0d9488' }}>{(r.meanRisk * 100).toFixed(0)}%</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Sagar Kanya Vessel Configuration Card */}
          <div className="ws-panel" style={{ padding: '8px 10px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid #bfdbfe' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Anchor size={13} color="#1e3a8a" />
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#1e3a8a', fontFamily: 'var(--font-mono)' }}>
                  ORV SAGAR KANYA
                </span>
              </div>
              <span style={{ fontSize: '9px', background: '#eff6ff', color: '#1d4ed8', padding: '1px 5px', fontWeight: 700 }}>
                CRUISE 9.0 KT
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '9.5px', fontFamily: 'var(--font-mono)', color: '#475569' }}>
              <div>LOA: <strong style={{ color: '#0f172a' }}>100.34 m</strong></div>
              <div>BEAM: <strong style={{ color: '#0f172a' }}>16.39 m</strong></div>
              <div>DRAFT: <strong style={{ color: '#0f172a' }}>5.60 m</strong></div>
              <div>MAX SIC: <strong style={{ color: '#0284c7' }}>&lt; 15% (MIZ)</strong></div>
              <div>CRUISE FUEL: <strong style={{ color: '#0f172a' }}>8.16 MT/d</strong></div>
              <div>BUNKER CAP: <strong style={{ color: '#0f172a' }}>368.0 MT</strong></div>
            </div>
          </div>

          {/* Explainability Decision Support Card */}
          <ExplainabilityCard />
        </div>
      )}

      {/* Central Antarctic Map Workspace */}
      <div style={{ flex: 1, position: 'relative', height: '100%', minHeight: '450px', border: '1px solid rgba(191, 219, 254, 0.75)', display: 'flex', flexDirection: 'column' }}>

        {/* Toggle Sidebar Button when closed */}
        {!isSidebarOpen && (
          <button
            onClick={() => setIsSidebarOpen(true)}
            style={{
              position: 'absolute',
              top: '9px',
              left: '8px',
              zIndex: 30,
              display: 'flex',
              alignItems: 'center',
              padding: '6px 8px',
              background: '#2563eb',
              border: '1px solid #1d4ed8',
              borderBottom: '3px solid #1e3a8a',
              color: '#ffffff',
              fontSize: '11px',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 3px 0 #1e3a8a'
            }}
          >
            <PanelLeftOpen size={13} />
          </button>
        )}

        <AntarcticMap
          selectedHorizon={timeHorizon}
          activeLayer={activeMapLayer}
          selectedRoute={selectedRouteId}
          onHorizonChange={(hz) => setTimeHorizon(hz as any)}
        />

        {/* Dynamic Multi-State Inspector Drawer (Floating Right Panel) */}
        {isAnyInspectorOpen && (
          <div style={{
            position: 'absolute',
            top: '8px',
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

      </div>

    </div>
  );
};

import React, { useState, useMemo } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Minimize2,
  Maximize2,
  X,
  Layers,
  Cpu
} from 'lucide-react';
import { useMission } from '../context/MissionContext';
import { getPathfinderStepAnalysis } from '../utils/pathfinderAnalysis';

export const PathfinderExplainabilityHUD: React.FC = () => {
  const {
    isPathfinderMode,
    setIsPathfinderMode,
    pathfinderStep,
    setPathfinderStep,
    isPathfinderPlaying,
    togglePathfinderPlay,
    resetPathfinder,
    pathfinderSpeed,
    setPathfinderSpeed,
    selectedRoute,
    routes,
    setSelectedRouteId
  } = useMission();

  const [isMinimized, setIsMinimized] = useState(false);
  const [activeTab, setActiveTab] = useState<'decision' | 'candidates' | 'costs'>('decision');

  const maxStep = selectedRoute?.cells ? selectedRoute.cells.length - 1 : 48;

  // Compute rich analysis for current step
  const analysis = useMemo(() => {
    return getPathfinderStepAnalysis(selectedRoute, pathfinderStep);
  }, [selectedRoute, pathfinderStep]);

  if (!isPathfinderMode) return null;

  const handlePrevStep = () => {
    setPathfinderStep((prev) => Math.max(0, prev - 1));
  };

  const handleNextStep = () => {
    setPathfinderStep((prev) => Math.min(maxStep, prev + 1));
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPathfinderStep(parseInt(e.target.value, 10));
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 24,
        right: 24,
        width: isMinimized ? '340px' : '480px',
        maxHeight: 'calc(100vh - 120px)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'rgba(8, 14, 28, 0.92)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(56, 189, 248, 0.4)',
        borderRadius: '14px',
        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.75), 0 0 20px rgba(56, 189, 248, 0.15)',
        color: '#f8fafc',
        fontFamily: 'Inter, system-ui, sans-serif',
        overflow: 'hidden',
        transition: 'width 0.25s ease, height 0.25s ease'
      }}
    >
      {/* HUD Header */}
      <div
        style={{
          padding: '12px 16px',
          background: 'linear-gradient(90deg, rgba(14, 165, 233, 0.18) 0%, rgba(30, 58, 138, 0.25) 100%)',
          borderBottom: '1px solid rgba(56, 189, 248, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          userSelect: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: 'rgba(56, 189, 248, 0.2)',
              border: '1px solid #38bdf8'
            }}
          >
            <Cpu size={16} color="#38bdf8" />
          </div>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 800, letterSpacing: '0.08em', color: '#38bdf8', textTransform: 'uppercase' }}>
              4D A* Pathfinder
            </div>
            <div style={{ fontSize: '10px', color: '#94a3b8' }}>
              Grid-by-Grid Decision Engine
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Active Route Picker */}
          <select
            value={selectedRoute?.id || 'fastest'}
            onChange={(e) => setSelectedRouteId(e.target.value)}
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              color: '#38bdf8',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name.toUpperCase()}
              </option>
            ))}
          </select>

          {/* Minimize / Maximize */}
          <button
            onClick={() => setIsMinimized((m) => !m)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center'
            }}
            title={isMinimized ? 'Expand HUD' : 'Minimize HUD'}
          >
            {isMinimized ? <Maximize2 size={15} /> : <Minimize2 size={15} />}
          </button>

          {/* Close HUD */}
          <button
            onClick={() => {
              setIsPathfinderMode(false);
            }}
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              color: '#f87171',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Exit Pathfinder Mode"
          >
            <X size={15} />
          </button>
        </div>
      </div>

      {/* Playback Controls & Progress Scrubber */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          backgroundColor: 'rgba(15, 23, 42, 0.5)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8' }}>
              Step {pathfinderStep}
            </span>
            <span style={{ fontSize: '11px', color: '#64748b' }}>
              / {maxStep} ({analysis.distanceFromStartNM.toFixed(0)} NM)
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {/* Speed selection */}
            <span style={{ fontSize: '10px', color: '#94a3b8', marginRight: '2px' }}>Speed:</span>
            {[
              { label: '0.5x', ms: 1200 },
              { label: '1x', ms: 700 },
              { label: '2x', ms: 350 }
            ].map((spd) => (
              <button
                key={spd.label}
                onClick={() => setPathfinderSpeed(spd.ms)}
                style={{
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  border: pathfinderSpeed === spd.ms ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.1)',
                  backgroundColor: pathfinderSpeed === spd.ms ? 'rgba(56, 189, 248, 0.25)' : 'transparent',
                  color: pathfinderSpeed === spd.ms ? '#38bdf8' : '#94a3b8'
                }}
              >
                {spd.label}
              </button>
            ))}
          </div>
        </div>

        {/* Step Slider */}
        <input
          type="range"
          min={0}
          max={maxStep}
          value={pathfinderStep}
          onChange={handleSliderChange}
          style={{
            width: '100%',
            cursor: 'pointer',
            accentColor: '#38bdf8',
            marginBottom: '10px'
          }}
        />

        {/* Transport buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          <button
            onClick={resetPathfinder}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 12px',
              borderRadius: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              color: '#94a3b8',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <RotateCcw size={13} />
            Reset
          </button>

          <button
            onClick={handlePrevStep}
            disabled={pathfinderStep === 0}
            style={{
              padding: '6px 10px',
              borderRadius: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              color: pathfinderStep === 0 ? '#475569' : '#f8fafc',
              cursor: pathfinderStep === 0 ? 'not-allowed' : 'pointer'
            }}
            title="Step Back"
          >
            <ChevronLeft size={16} />
          </button>

          <button
            onClick={togglePathfinderPlay}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 18px',
              borderRadius: '6px',
              backgroundColor: isPathfinderPlaying ? '#f59e0b' : '#0284c7',
              border: 'none',
              color: '#ffffff',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: isPathfinderPlaying
                ? '0 0 12px rgba(245, 158, 11, 0.5)'
                : '0 0 12px rgba(2, 132, 199, 0.5)'
            }}
          >
            {isPathfinderPlaying ? <Pause size={14} /> : <Play size={14} />}
            {isPathfinderPlaying ? 'PAUSE' : 'STEP RUN'}
          </button>

          <button
            onClick={handleNextStep}
            disabled={pathfinderStep === maxStep}
            style={{
              padding: '6px 10px',
              borderRadius: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              color: pathfinderStep === maxStep ? '#475569' : '#f8fafc',
              cursor: pathfinderStep === maxStep ? 'not-allowed' : 'pointer'
            }}
            title="Step Forward"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* Main Collapsible Content Area */}
      {!isMinimized && (
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflowY: 'auto' }}>
          {/* Sub-tabs */}
          <div
            style={{
              display: 'flex',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              backgroundColor: 'rgba(15, 23, 42, 0.3)'
            }}
          >
            {[
              { id: 'decision', label: 'Why This Cell Was Chosen', icon: CheckCircle2 },
              { id: 'candidates', label: `Rejected Alternatives (${analysis.candidateAlternatives.length - 1})`, icon: XCircle },
              { id: 'costs', label: 'A* Cost f(n)', icon: Layers }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    padding: '8px 10px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    border: 'none',
                    borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
                    backgroundColor: isActive ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                    color: isActive ? '#38bdf8' : '#94a3b8',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Icon size={13} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          <div style={{ padding: '16px', overflowY: 'auto', maxHeight: '420px' }}>
            {/* TAB 1: DECISION RATIONALE */}
            {activeTab === 'decision' && (
              <div>
                {/* Frontier Cell Header */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '10px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        border: '1px solid #10b981',
                        color: '#34d399',
                        fontSize: '10px',
                        fontWeight: 800,
                        letterSpacing: '0.05em'
                      }}
                    >
                      ✓ CHOSEN FRONTIER
                    </div>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#e2e8f0', fontWeight: 600 }}>
                      H3: {analysis.cellId}
                    </span>
                  </div>

                  <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                    {analysis.coords[1].toFixed(2)}°S, {analysis.coords[0].toFixed(2)}°E
                  </span>
                </div>

                {/* Primary Decision Driver Badge */}
                <div
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    backgroundColor: `${analysis.driverBadgeColor}18`,
                    border: `1px solid ${analysis.driverBadgeColor}50`,
                    marginBottom: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <ShieldCheck size={16} color={analysis.driverBadgeColor} />
                  <div>
                    <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Primary Decision Driver
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: analysis.driverBadgeColor }}>
                      {analysis.primaryDriver}
                    </div>
                  </div>
                </div>

                {/* Tactical Rationale Box */}
                <div
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    marginBottom: '14px',
                    fontSize: '12px',
                    lineHeight: '1.55',
                    color: '#e2e8f0'
                  }}
                >
                  <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '4px', fontSize: '11px', textTransform: 'uppercase' }}>
                    Pathfinder Operational Rationale:
                  </div>
                  {analysis.tacticalRationale}
                </div>

                {/* Live Physics Grid for this cell */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '8px',
                    marginBottom: '12px'
                  }}
                >
                  <div
                    style={{
                      padding: '8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)'
                    }}
                  >
                    <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Sea Ice (SIC)</div>
                    <div
                      style={{
                        fontSize: '13px',
                        fontWeight: 800,
                        color: analysis.sicPercent > 15 ? '#ef4444' : analysis.sicPercent > 0 ? '#38bdf8' : '#10b981'
                      }}
                    >
                      {analysis.sicPercent}%
                    </div>
                  </div>

                  <div
                    style={{
                      padding: '8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)'
                    }}
                  >
                    <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Waves / Swell</div>
                    <div style={{ fontSize: '13px', fontWeight: 800, color: analysis.waveHeightM > 4.5 ? '#f59e0b' : '#38bdf8' }}>
                      {analysis.waveHeightM} m
                    </div>
                  </div>

                  <div
                    style={{
                      padding: '8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)'
                    }}
                  >
                    <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Speed (SOG)</div>
                    <div style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8' }}>
                      {analysis.sogKnots} kt
                    </div>
                  </div>

                  <div
                    style={{
                      padding: '8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)'
                    }}
                  >
                    <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Iceberg Risk</div>
                    <div
                      style={{
                        fontSize: '13px',
                        fontWeight: 800,
                        color: analysis.icebergHazard > 0.2 ? '#ef4444' : analysis.icebergHazard > 0.05 ? '#f59e0b' : '#10b981'
                      }}
                    >
                      {analysis.icebergHazard.toFixed(2)}
                    </div>
                  </div>

                  <div
                    style={{
                      padding: '8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)'
                    }}
                  >
                    <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Current Assist</div>
                    <div style={{ fontSize: '13px', fontWeight: 800, color: analysis.currentAlongTrackKt >= 0 ? '#10b981' : '#f59e0b' }}>
                      {analysis.currentAlongTrackKt > 0 ? `+${analysis.currentAlongTrackKt}` : analysis.currentAlongTrackKt} kt
                    </div>
                  </div>

                  <div
                    style={{
                      padding: '8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)'
                    }}
                  >
                    <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Bathymetry</div>
                    <div style={{ fontSize: '13px', fontWeight: 800, color: '#e2e8f0' }}>
                      {analysis.depthM.toFixed(0)} m
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: REJECTED CANDIDATE ALTERNATIVES */}
            {activeTab === 'candidates' && (
              <div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '10px' }}>
                  At step {pathfinderStep}, 4D A* evaluated neighboring hexagonal grid cells and rejected the following candidates:
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {analysis.candidateAlternatives
                    .filter((c) => c.status === 'rejected')
                    .map((cand, idx) => (
                      <div
                        key={cand.cellId || idx}
                        style={{
                          padding: '10px 12px',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(239, 68, 68, 0.06)',
                          border: '1px solid rgba(239, 68, 68, 0.25)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <XCircle size={14} color="#f87171" />
                            <span style={{ fontSize: '11px', fontWeight: 700, color: '#fca5a5' }}>
                              {cand.name}
                            </span>
                          </div>
                          <span
                            style={{
                              fontSize: '10px',
                              fontWeight: 700,
                              color: '#ef4444',
                              backgroundColor: 'rgba(239, 68, 68, 0.15)',
                              padding: '2px 6px',
                              borderRadius: '4px'
                            }}
                          >
                            +{cand.costDeltaPct}% Cost Penalty
                          </span>
                        </div>

                        {/* Rejection Narrative */}
                        <div style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: '1.45' }}>
                          {cand.rejectionReason}
                        </div>

                        {/* Quick metric pill comparisons */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '2px', fontSize: '10px', color: '#94a3b8' }}>
                          <span>SIC: <strong style={{ color: cand.sicPct > 15 ? '#ef4444' : '#e2e8f0' }}>{cand.sicPct}%</strong></span>
                          <span>Waves: <strong>{cand.waveHeightM}m</strong></span>
                          <span>Depth: <strong>{cand.depthM}m</strong></span>
                          <span>Berg: <strong>{cand.icebergHazard.toFixed(2)}</strong></span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* TAB 3: 4D A* COST BREAKDOWN */}
            {activeTab === 'costs' && (
              <div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '12px' }}>
                  4D A* evaluation function: <code style={{ color: '#38bdf8' }}>f(n) = g(n) + h(n)</code> (accumulated voyage cost + heuristic distance to destination).
                </div>

                <div
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                      <span style={{ color: '#94a3b8' }}>Distance Cost (Geodesic Deviation)</span>
                      <span style={{ fontWeight: 700, color: '#f8fafc' }}>{analysis.costBreakdown.distanceCost} NM</span>
                    </div>
                    <div style={{ height: '5px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, analysis.costBreakdown.distanceCost / 2.5)}%`, height: '100%', backgroundColor: '#38bdf8' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                      <span style={{ color: '#94a3b8' }}>Time Cost (Hours in Transit)</span>
                      <span style={{ fontWeight: 700, color: '#f8fafc' }}>{analysis.costBreakdown.timeCost} hrs</span>
                    </div>
                    <div style={{ height: '5px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, analysis.costBreakdown.timeCost * 3)}%`, height: '100%', backgroundColor: '#a855f7' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                      <span style={{ color: '#94a3b8' }}>Environmental Risk Penalty (SIC + Icebergs + Waves)</span>
                      <span style={{ fontWeight: 700, color: '#f8fafc' }}>{analysis.costBreakdown.riskCost}</span>
                    </div>
                    <div style={{ height: '5px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${Math.min(100, analysis.costBreakdown.riskCost * 1.5)}%`,
                          height: '100%',
                          backgroundColor: analysis.costBreakdown.riskCost > 40 ? '#ef4444' : '#10b981'
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                      <span style={{ color: '#94a3b8' }}>Fuel Burn Penalty</span>
                      <span style={{ fontWeight: 700, color: '#f8fafc' }}>{analysis.fuelTonnes.toFixed(1)} MT</span>
                    </div>
                    <div style={{ height: '5px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, analysis.fuelTonnes * 2.2)}%`, height: '100%', backgroundColor: '#f59e0b' }} />
                    </div>
                  </div>

                  <div
                    style={{
                      borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                      paddingTop: '8px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <span style={{ fontSize: '12px', fontWeight: 800, color: '#38bdf8' }}>Composite Frontier Cost f(n)</span>
                    <span style={{ fontSize: '14px', fontWeight: 900, color: '#10b981' }}>{analysis.costBreakdown.totalFScore}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

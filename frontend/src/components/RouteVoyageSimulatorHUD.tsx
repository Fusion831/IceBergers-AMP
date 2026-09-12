import React from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  XCircle,
  CheckCircle2,
  Ship,
  Eye,
  EyeOff,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { GridDecisionStep } from '../utils/voyageSimulator';

interface RouteVoyageSimulatorHUDProps {
  step: GridDecisionStep | null;
  isPlaying: boolean;
  playbackSpeed: number;
  followShip: boolean;
  onTogglePlay: () => void;
  onStepPrev: () => void;
  onStepNext: () => void;
  onReset: () => void;
  onScrub: (progress: number) => void;
  onChangeSpeed: (speed: number) => void;
  onToggleFollow: () => void;
  onClose: () => void;
  theme?: 'dark' | 'light';
}

export const RouteVoyageSimulatorHUD: React.FC<RouteVoyageSimulatorHUDProps> = ({
  step,
  isPlaying,
  playbackSpeed,
  followShip,
  onTogglePlay,
  onStepPrev,
  onStepNext,
  onReset,
  onScrub,
  onChangeSpeed,
  onToggleFollow,
  onClose,
  theme = 'dark'
}) => {
  const [isExpanded, setIsExpanded] = React.useState<boolean>(true);
  const isLight = theme === 'light';

  if (!step) return null;

  const currentPercent = Math.round(step.progressTotal * 100);

  return (
    <div
      style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        width: '380px',
        maxHeight: 'calc(100% - 24px)',
        zIndex: 50,
        background: isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(13, 17, 23, 0.94)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`,
        borderRadius: '8px',
        boxShadow: isLight
          ? '0 16px 48px rgba(14, 165, 233, 0.16), 0 0 20px rgba(14, 165, 233, 0.1)'
          : '0 16px 48px rgba(0, 0, 0, 0.75), 0 0 20px rgba(56, 189, 248, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        color: isLight ? '#0f172a' : '#f0f6fc',
        transition: 'background 0.2s ease, border-color 0.2s ease, color 0.2s ease'
      }}
    >
      {/* 1. Header Bar */}
      <div
        style={{
          padding: '10px 14px',
          background: isLight ? '#e0f2fe' : '#161b22',
          borderBottom: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '6px',
              background: isLight ? 'rgba(2, 132, 199, 0.15)' : 'rgba(56, 189, 248, 0.12)',
              border: `1px solid ${isLight ? 'rgba(2, 132, 199, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Ship size={14} color={isLight ? '#0284c7' : '#38bdf8'} />
          </div>
          <div>
            <div style={{ fontSize: '11.5px', fontWeight: 700, color: isLight ? '#0f172a' : '#f0f6fc', letterSpacing: '0.2px' }}>
              Voyage Simulator
            </div>
            <div style={{ fontSize: '9px', color: isLight ? '#0284c7' : '#58a6ff', fontFamily: 'monospace', fontWeight: 600 }}>
              GRID EXPLAINABILITY ENGINE
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            onClick={() => setIsExpanded((e) => !e)}
            title={isExpanded ? 'Collapse HUD' : 'Expand HUD'}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8b949e',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '4px'
            }}
          >
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <button
            onClick={onClose}
            title="Close Simulator"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8b949e',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '4px'
            }}
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* 2. Controls & Scrub Bar (Always Visible) */}
      <div
        style={{
          padding: '8px 12px',
          background: isLight ? '#f0f9ff' : '#161b22',
          borderBottom: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
          display: 'flex',
          flexDirection: 'column',
          gap: '6px'
        }}
      >
        {/* Stage & Progress Readout */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '9.5px', fontFamily: 'monospace' }}>
          <span style={{ color: isLight ? '#0284c7' : '#38bdf8', fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '240px' }}>
            {step.stageName}
          </span>
          <span style={{ color: isLight ? '#64748b' : '#94a3b8' }}>
            Grid {step.segmentIndex + 1}/{step.totalSegments} ({currentPercent}%)
          </span>
        </div>

        {/* Progress Slider */}
        <input
          type="range"
          min={0}
          max={100}
          value={currentPercent}
          onChange={(e) => onScrub(Number(e.target.value) / 100.0)}
          style={{
            width: '100%',
            height: '5px',
            accentColor: isLight ? '#0284c7' : '#38bdf8',
            cursor: 'pointer'
          }}
        />

        {/* Playback Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '2px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <button
              onClick={onStepPrev}
              title="Previous Grid Hexagon"
              style={{
                padding: '4px 7px',
                background: isLight ? '#ffffff' : '#161b22',
                border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`,
                borderRadius: '5px',
                color: isLight ? '#0f172a' : '#c9d1d9',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <SkipBack size={12} />
            </button>

            <button
              onClick={onTogglePlay}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 12px',
                background: isPlaying ? '#da3633' : (isLight ? '#0284c7' : '#1f6feb'),
                border: `1px solid ${isPlaying ? '#f85149' : (isLight ? '#0369a1' : '#388bfd')}`,
                borderRadius: '5px',
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {isPlaying ? <Pause size={12} /> : <Play size={12} />}
              <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
            </button>

            <button
              onClick={onStepNext}
              title="Next Grid Hexagon"
              style={{
                padding: '4px 7px',
                background: isLight ? '#ffffff' : '#161b22',
                border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`,
                borderRadius: '5px',
                color: isLight ? '#0f172a' : '#c9d1d9',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <SkipForward size={12} />
            </button>

            <button
              onClick={onReset}
              title="Reset to Voyage Start"
              style={{
                padding: '4px 7px',
                background: isLight ? '#ffffff' : '#161b22',
                border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`,
                borderRadius: '5px',
                color: isLight ? '#64748b' : '#8b949e',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <RotateCcw size={12} />
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {/* Speed Multiplier */}
            {[1, 2, 5, 10].map((spd) => (
              <button
                key={spd}
                onClick={() => onChangeSpeed(spd)}
                style={{
                  padding: '3px 6px',
                  background: playbackSpeed === spd
                    ? (isLight ? '#0284c7' : '#1f6feb')
                    : (isLight ? '#ffffff' : '#161b22'),
                  border: `1px solid ${
                    playbackSpeed === spd
                      ? (isLight ? '#0369a1' : '#388bfd')
                      : (isLight ? '#bfdbfe' : '#30363d')
                  }`,
                  borderRadius: '4px',
                  color: playbackSpeed === spd ? '#ffffff' : (isLight ? '#64748b' : '#8b949e'),
                  fontSize: '9.5px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.1s ease'
                }}
              >
                {spd}x
              </button>
            ))}

            {/* Follow Ship Toggle */}
            <button
              onClick={onToggleFollow}
              title={followShip ? 'Camera Follow ON' : 'Camera Follow OFF'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                padding: '3px 7px',
                background: followShip
                  ? (isLight ? 'rgba(22, 163, 74, 0.15)' : 'rgba(35, 134, 54, 0.2)')
                  : (isLight ? '#ffffff' : '#161b22'),
                border: `1px solid ${
                  followShip
                    ? (isLight ? '#16a34a' : '#3fb950')
                    : (isLight ? '#bfdbfe' : '#30363d')
                }`,
                borderRadius: '4px',
                color: followShip
                  ? (isLight ? '#15803d' : '#3fb950')
                  : (isLight ? '#64748b' : '#8b949e'),
                fontSize: '9.5px',
                fontFamily: 'monospace',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.1s ease'
              }}
            >
              {followShip ? <Eye size={11} /> : <EyeOff size={11} />}
              <span>FOLLOW</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3. Expandable Decision Body */}
      {isExpanded && (
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '10px 12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            fontSize: '11px',
            background: isLight ? '#f8fafc' : 'transparent'
          }}
        >
          {/* Live Vessel Kinematics Strip */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: '4px',
              fontFamily: 'monospace',
              fontSize: '9px'
            }}
          >
            <div style={{ background: isLight ? '#ffffff' : '#161b22', padding: '5px 7px', borderRadius: '4px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
              <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '8px' }}>SPEED OVER GROUND</div>
              <div style={{ fontSize: '11px', fontWeight: 800, color: isLight ? '#0284c7' : '#38bdf8' }}>{step.vesselSOGKt} kt</div>
              <div style={{ fontSize: '7.5px', color: isLight ? '#94a3b8' : '#64748b' }}>STW: {step.vesselSTWKt} kt</div>
            </div>

            <div style={{ background: isLight ? '#ffffff' : '#161b22', padding: '5px 7px', borderRadius: '4px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
              <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '8px' }}>OCEAN CURRENT</div>
              <div style={{ fontSize: '11px', fontWeight: 800, color: step.alongTrackCurrentKt >= 0 ? (isLight ? '#16a34a' : '#22c55e') : '#ef4444' }}>
                {step.alongTrackCurrentKt >= 0 ? '+' : ''}{step.alongTrackCurrentKt} kt
              </div>
              <div style={{ fontSize: '7.5px', color: isLight ? '#94a3b8' : '#64748b' }}>{step.alongTrackCurrentKt >= 0 ? 'Assisting push' : 'Adverse head drag'}</div>
            </div>

            <div style={{ background: isLight ? '#ffffff' : '#161b22', padding: '5px 7px', borderRadius: '4px', border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}` }}>
              <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '8px' }}>FUEL BURN RATE</div>
              <div style={{ fontSize: '11px', fontWeight: 800, color: '#f97316' }}>{step.fuelRateMTPerDay} MT/d</div>
              <div style={{ fontSize: '7.5px', color: isLight ? '#94a3b8' : '#64748b' }}>Leg: {step.fuelBurnMT} MT</div>
            </div>
          </div>

          {/* Environmental State */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              background: isLight ? '#ffffff' : '#161b22',
              padding: '4px 8px',
              borderRadius: '4px',
              border: `1px solid ${isLight ? '#bfdbfe' : '#21262d'}`,
              fontFamily: 'monospace',
              fontSize: '8.5px',
              color: isLight ? '#475569' : '#8b949e'
            }}
          >
            <span>HEADING: <strong style={{ color: isLight ? '#0f172a' : '#f0f6fc' }}>{step.headingDeg}°</strong></span>
            <span>SIC: <strong style={{ color: step.sicPercent > 15 ? '#ef4444' : (isLight ? '#16a34a' : '#22c55e') }}>{step.sicPercent}%</strong></span>
            <span>WAVE: <strong style={{ color: step.waveHeightM > 3.0 ? '#f59e0b' : (isLight ? '#0284c7' : '#38bdf8') }}>{step.waveHeightM}m</strong></span>
            <span>RISK: <strong style={{ color: step.compositeRisk > 0.3 ? '#ef4444' : (isLight ? '#16a34a' : '#22c55e') }}>{Math.round(step.compositeRisk * 100)}%</strong></span>
          </div>

          {/* Section A: WHY THIS GRID WAS CHOSEN */}
          <div
            style={{
              background: isLight ? 'rgba(34, 197, 94, 0.12)' : 'rgba(21, 128, 61, 0.12)',
              border: `1px solid ${isLight ? '#86efac' : '#22c55e'}`,
              borderLeft: `4px solid ${isLight ? '#16a34a' : '#22c55e'}`,
              borderRadius: '5px',
              padding: '7px 9px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '3px' }}>
              <CheckCircle2 size={12} color={isLight ? '#16a34a' : '#22c55e'} />
              <span style={{ fontSize: '10px', fontWeight: 800, color: isLight ? '#15803d' : '#4ade80', fontFamily: 'monospace' }}>
                WHY THIS GRID CELL WAS CHOSEN
              </span>
            </div>
            <div style={{ fontSize: '10px', color: isLight ? '#1e293b' : '#e2e8f0', lineHeight: '1.4' }}>
              {step.chosenGridRationale}
            </div>
          </div>

          {/* Section B: WHY NOT ADJACENT GRIDS */}
          <div
            style={{
              background: isLight ? '#ffffff' : '#161b22',
              border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`,
              borderRadius: '5px',
              overflow: 'hidden'
            }}
          >
            <div
              style={{
                padding: '6px 9px',
                background: isLight ? 'rgba(239, 68, 68, 0.08)' : '#21262d',
                borderBottom: `1px solid ${isLight ? '#fecaca' : '#30363d'}`,
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              <XCircle size={12} color="#ef4444" />
              <span style={{ fontSize: '10px', fontWeight: 800, color: isLight ? '#dc2626' : '#f87171', fontFamily: 'monospace' }}>
                WHY NOT ADJACENT GRIDS (REJECTED CANDIDATES)
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {step.adjacentGrids.map((adj, i) => (
                <div
                  key={adj.directionLabel}
                  style={{
                    padding: '6px 9px',
                    borderBottom: i < step.adjacentGrids.length - 1 ? `1px solid ${isLight ? '#e2e8f0' : '#21262d'}` : 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '9.5px', fontWeight: 700, color: isLight ? '#0f172a' : '#f1f5f9', fontFamily: 'monospace' }}>
                      {adj.directionLabel}
                    </span>
                    <span
                      style={{
                        fontSize: '7.5px',
                        fontWeight: 800,
                        fontFamily: 'monospace',
                        padding: '1px 4px',
                        borderRadius: '2px',
                        background: adj.verdict === 'REJECTED' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: adj.verdict === 'REJECTED' ? (isLight ? '#dc2626' : '#f87171') : (isLight ? '#d97706' : '#fcd34d'),
                        border: `1px solid ${adj.verdict === 'REJECTED' ? '#ef4444' : '#f59e0b'}`
                      }}
                    >
                      {adj.verdict}
                    </span>
                  </div>

                  <div style={{ fontSize: '9px', color: isLight ? '#334155' : '#cbd5e1', lineHeight: '1.3' }}>
                    {adj.reason}
                  </div>

                  <div style={{ fontSize: '8px', color: isLight ? '#dc2626' : '#f87171', fontFamily: 'monospace' }}>
                    Penalty: {adj.simulatedPenalty}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

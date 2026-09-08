import React from 'react';
import { useMission } from '../context/MissionContext';
import { Ship, Calendar } from 'lucide-react';

export const Header: React.FC = () => {
  const { missionConfig, activeView, setActiveView } = useMission();

  return (
    <header style={{
      display: 'flex',
      flexDirection: 'column',
      borderBottom: '1px solid rgba(147, 197, 253, 0.65)',
      background: 'rgba(240, 248, 255, 0.70)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      zIndex: 20
    }}>
      {/* Upper Header: Brand, Expedition Window & Vessel Indicator */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 18px',
        background: 'rgba(255, 255, 255, 0.75)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '0px',
            background: 'rgba(224, 242, 254, 0.85)',
            border: '1px solid #93c5fd',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Ship size={18} color="#2563eb" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontFamily: 'var(--font-sans)', fontSize: '16px', fontWeight: 800, letterSpacing: '0.02em', color: '#172554', margin: 0 }}>
                AMIP // POLAR METEOROLOGICAL WORKSTATION
              </h1>
              <span style={{
                fontSize: '10.5px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '0px',
                background: 'rgba(239, 246, 255, 0.9)',
                color: '#2563eb',
                border: '1px solid #93c5fd'
              }}>
                NCPOR SIH-26059
              </span>
            </div>
            <p style={{ fontSize: '11.5px', color: '#475569', fontFamily: 'var(--font-sans)', marginTop: '2px', margin: 0 }}>
              Antarctic Mission Intelligence Platform • National Centre for Polar and Ocean Research
            </p>
          </div>
        </div>

        {/* Global Controls & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Expedition Planning Window */}
          <div
            onClick={() => setActiveView(activeView === 'mission-setup' ? 'antarctic-map' : 'mission-setup')}
            title="Click to customize expedition parameters, dates & stations"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              borderRadius: '0px',
              background: activeView === 'mission-setup' ? '#eff6ff' : 'rgba(255, 255, 255, 0.85)',
              border: activeView === 'mission-setup' ? '1.5px solid #2563eb' : '1px solid rgba(191, 219, 254, 0.8)',
              fontSize: '11.5px',
              fontFamily: 'var(--font-sans)',
              color: '#0f172a',
              cursor: 'pointer',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
            }}
          >
            <Calendar size={13} color={activeView === 'mission-setup' ? '#2563eb' : '#64748b'} />
            <span style={{ color: activeView === 'mission-setup' ? '#2563eb' : '#64748b', fontWeight: 700 }}>EXP:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{missionConfig.expeditionId} ({missionConfig.startDate} → {missionConfig.endDate})</span>
          </div>

          {/* Vessel Profile */}
          <div
            onClick={() => setActiveView(activeView === 'mission-setup' ? 'antarctic-map' : 'mission-setup')}
            title="Click to customize polar vessel profile & ice class"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              borderRadius: '0px',
              background: activeView === 'mission-setup' ? '#eff6ff' : 'rgba(255, 255, 255, 0.85)',
              border: activeView === 'mission-setup' ? '1.5px solid #2563eb' : '1px solid rgba(191, 219, 254, 0.8)',
              fontSize: '11.5px',
              fontFamily: 'var(--font-sans)',
              color: '#0f172a',
              cursor: 'pointer',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
            }}
          >
            <Ship size={13} color="#2563eb" />
            <span style={{ color: '#64748b', fontWeight: 700 }}>VESSEL:</span>
            <span style={{ fontWeight: 800, color: '#2563eb' }}>{missionConfig.vessel.name}</span>
          </div>

          {/* Return to Map Button (if outside map view) */}
          {activeView !== 'antarctic-map' && (
            <button
              onClick={() => setActiveView('antarctic-map')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: '0px',
                background: '#2563eb',
                border: '1px solid #1d4ed8',
                borderBottom: '2px solid #1e3a8a',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                color: '#ffffff',
                cursor: 'pointer',
                boxShadow: '0 2px 4px rgba(37, 99, 235, 0.3)'
              }}
            >
              <span>← RETURN TO ANTARCTIC MAP</span>
            </button>
          )}

          {/* Model Live Status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '0px',
            background: 'rgba(240, 253, 250, 0.9)',
            border: '1px solid #5eead4',
            fontSize: '11.5px',
            fontFamily: 'var(--font-sans)',
            fontWeight: 800,
            color: '#0d9488'
          }}>
            <span style={{ width: '7px', height: '7px', backgroundColor: '#0d9488', display: 'inline-block' }}></span>
            MODELS ONLINE
          </div>
        </div>
      </div>
    </header>
  );
};

import React from 'react';
import { useMission } from '../context/MissionContext';
import { ViewMode } from '../types/mission';
import {
  Ship,
  Compass,
  TrendingUp,
  MapPin,
  Navigation,
  Crosshair,
  Sliders,
  Calendar
} from 'lucide-react';

export const Header: React.FC = () => {
  const {
    activeView,
    setActiveView,
    missionConfig
  } = useMission();

  const navItems: { id: ViewMode; label: string; icon: React.ReactNode; num: string }[] = [
    { id: 'mission-setup', label: 'Mission Setup', icon: <Sliders size={13} />, num: '1' },
    { id: 'antarctic-map', label: 'Antarctic Map', icon: <Compass size={13} />, num: '2' },
    { id: 'environmental-timeline', label: 'Environmental Timeline', icon: <TrendingUp size={13} />, num: '3' },
    { id: 'location-comparison', label: 'Location Comparison', icon: <MapPin size={13} />, num: '4' },
    { id: 'route-comparison', label: 'Route Comparison', icon: <Navigation size={13} />, num: '5' },
    { id: 'prediction-inspector', label: 'Prediction Inspector', icon: <Crosshair size={13} />, num: '6' }
  ];

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
        borderBottom: '1px solid rgba(191, 219, 254, 0.65)',
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
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '0px',
            background: 'rgba(255, 255, 255, 0.85)',
            border: '1px solid rgba(191, 219, 254, 0.8)',
            fontSize: '11.5px',
            fontFamily: 'var(--font-sans)',
            color: '#0f172a'
          }}>
            <Calendar size={13} color="#64748b" />
            <span style={{ color: '#64748b', fontWeight: 700 }}>EXP:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{missionConfig.expeditionId} ({missionConfig.startDate} → {missionConfig.endDate})</span>
          </div>

          {/* Vessel Profile */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '0px',
            background: 'rgba(255, 255, 255, 0.85)',
            border: '1px solid rgba(191, 219, 254, 0.8)',
            fontSize: '11.5px',
            fontFamily: 'var(--font-sans)',
            color: '#0f172a'
          }}>
            <Ship size={13} color="#2563eb" />
            <span style={{ color: '#64748b', fontWeight: 700 }}>VESSEL:</span>
            <span style={{ fontWeight: 800, color: '#2563eb' }}>{missionConfig.vessel.name}</span>
          </div>

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

      {/* Lower Navigation Bar: Six Core Workstation Views */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '5px 14px',
        gap: '8px',
        overflowX: 'auto',
        background: 'rgba(240, 248, 255, 0.65)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        borderBottom: '1px solid rgba(191, 219, 254, 0.65)'
      }}>
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 16px',
                borderRadius: '0px',
                border: '1px solid',
                borderColor: isActive ? '#1d4ed8' : 'rgba(191, 219, 254, 0.85)',
                borderBottom: isActive ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                background: isActive ? '#2563eb' : 'rgba(255, 255, 255, 0.85)',
                color: isActive ? '#ffffff' : '#334155',
                fontSize: '12px',
                fontFamily: 'var(--font-sans)',
                fontWeight: isActive ? 800 : 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? '0 3px 0 #1e3a8a, 0 4px 8px rgba(30, 58, 138, 0.3)' : '0 2px 0 #93c5fd, 0 2px 5px rgba(37, 99, 235, 0.08)'
              }}
            >
              <span style={{
                fontSize: '10.5px',
                fontWeight: 800,
                width: '18px',
                height: '18px',
                borderRadius: '0px',
                background: isActive ? '#ffffff' : '#e0f2fe',
                color: isActive ? '#2563eb' : '#1e3a8a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid',
                borderColor: isActive ? '#bfdbfe' : '#93c5fd'
              }}>
                {item.num}
              </span>
              {item.icon}
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};

import React from 'react';
import { useMission } from '../context/MissionContext';
import {
  Ship,
  Anchor,
  Sliders,
  CheckCircle,
  ArrowRight,
  Calendar,
  Zap,
  MapPin
} from 'lucide-react';

export const MissionSetupView: React.FC = () => {
  const { missionConfig, setMissionConfig, vessels, setActiveView } = useMission();

  const handleVesselChange = (vesselId: string) => {
    const selected = vessels.find((v) => v.id === vesselId);
    if (selected) {
      setMissionConfig((prev) => ({ ...prev, vessel: selected }));
    }
  };

  const handleWeightChange = (key: keyof typeof missionConfig.priorityWeights, value: number) => {
    setMissionConfig((prev) => ({
      ...prev,
      priorityWeights: {
        ...prev.priorityWeights,
        [key]: value
      }
    }));
  };

  const applyPreset = (preset: 'balanced' | 'safety' | 'fuel' | 'fast') => {
    const presets = {
      balanced: { safety: 70, fuelEconomy: 65, transitSpeed: 50, scienceWindow: 80 },
      safety: { safety: 95, fuelEconomy: 40, transitSpeed: 30, scienceWindow: 70 },
      fuel: { safety: 60, fuelEconomy: 95, transitSpeed: 40, scienceWindow: 60 },
      fast: { safety: 50, fuelEconomy: 40, transitSpeed: 95, scienceWindow: 50 }
    };
    setMissionConfig((prev) => ({
      ...prev,
      priorityWeights: presets[preset]
    }));
  };

  const handleStationToggle = (station: string) => {
    setMissionConfig((prev) => {
      const exists = prev.targetStations.includes(station);
      return {
        ...prev,
        targetStations: exists
          ? prev.targetStations.filter((s) => s !== station)
          : [...prev.targetStations, station]
      };
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%', overflowY: 'auto', padding: '6px' }}>

      {/* Header Banner */}
      <div className="ws-panel" style={{ padding: '14px 18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '10.5px', fontWeight: 800, padding: '2px 7px', background: '#2563eb', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                EXPEDITION SETUP
              </span>
              <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 800, color: '#172554', margin: 0 }}>
                {missionConfig.missionName.toUpperCase()} // {missionConfig.expeditionId}
              </h2>
            </div>
            <p style={{ fontSize: '11.5px', color: '#475569', marginTop: '4px', fontFamily: 'var(--font-mono)', margin: 0 }}>
              Define voyage departure dates, destination stations, vessel selection, and routing priority preferences.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ padding: '6px 14px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid rgba(191, 219, 254, 0.8)', backdropFilter: 'blur(8px)' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>SELECTED VESSEL: </span>
              <span style={{ fontSize: '12px', fontWeight: 800, color: '#2563eb', fontFamily: 'var(--font-mono)' }}>{missionConfig.vessel.name}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Configuration Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '14px' }}>

        {/* Left Column: Voyage Parameters & Vessel Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* 1. Voyage Schedule & Departure */}
          <div className="ws-panel" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Anchor size={15} color="#2563eb" />
              <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                1. VOYAGE PARAMETERS & DEPARTURE
              </h3>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10.5px', color: '#475569', marginBottom: '4px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                  EXPEDITION NAME
                </label>
                <input
                  type="text"
                  value={missionConfig.missionName}
                  onChange={(e) => setMissionConfig((prev) => ({ ...prev, missionName: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: '0px',
                    background: 'rgba(255, 255, 255, 0.9)',
                    border: '1px solid rgba(191, 219, 254, 0.85)',
                    color: '#0f172a',
                    fontSize: '12px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '10.5px', color: '#475569', marginBottom: '4px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                  ORIGIN GATEWAY PORT
                </label>
                <select
                  value={missionConfig.originPort}
                  onChange={(e) => setMissionConfig((prev) => ({ ...prev, originPort: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: '0px',
                    background: 'rgba(255, 255, 255, 0.9)',
                    border: '1px solid rgba(191, 219, 254, 0.85)',
                    color: '#0f172a',
                    fontSize: '12px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700
                  }}
                >
                  <option value="Cape Town (Supply Gateway)">Cape Town, South Africa</option>
                  <option value="Mormugao Port, Goa (NCPOR HQ)">Mormugao Port, Goa (NCPOR)</option>
                  <option value="Port Louis, Mauritius">Port Louis, Mauritius</option>
                  <option value="Hobart, Australia">Hobart, Australia</option>
                </select>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ display: 'block', fontSize: '10.5px', color: '#475569', marginBottom: '4px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                  VOYAGE WINDOW (DEPARTURE → RETURN)
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flex: 1, background: 'rgba(255, 255, 255, 0.9)', padding: '6px 10px', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
                    <Calendar size={14} color="#2563eb" />
                    <input
                      type="date"
                      value={missionConfig.startDate}
                      onChange={(e) => setMissionConfig((prev) => ({ ...prev, startDate: e.target.value }))}
                      style={{
                        width: '100%',
                        border: 'none',
                        background: 'transparent',
                        color: '#0f172a',
                        fontSize: '11.5px',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        outline: 'none'
                      }}
                    />
                  </div>
                  <span style={{ color: '#2563eb', fontWeight: 800 }}>→</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flex: 1, background: 'rgba(255, 255, 255, 0.9)', padding: '6px 10px', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
                    <Calendar size={14} color="#2563eb" />
                    <input
                      type="date"
                      value={missionConfig.endDate}
                      onChange={(e) => setMissionConfig((prev) => ({ ...prev, endDate: e.target.value }))}
                      style={{
                        width: '100%',
                        border: 'none',
                        background: 'transparent',
                        color: '#0f172a',
                        fontSize: '11.5px',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        outline: 'none'
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Target Destinations */}
            <div style={{ marginTop: '14px' }}>
              <label style={{ display: 'block', fontSize: '10.5px', color: '#475569', marginBottom: '6px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                DESTINATION STATIONS
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {[
                  { id: 'Bharati Station', sector: 'Larsemann Hills (Prydz Bay)' },
                  { id: 'Maitri Station', sector: 'Schirmacher Oasis (Lazarev Sea)' },
                  { id: 'Crown Prince Olav Coast', sector: 'Enderby Land Sector' },
                  { id: 'Amery Ice Shelf Lead', sector: 'Prydz Bay Inflow' }
                ].map((st) => {
                  const isChecked = missionConfig.targetStations.includes(st.id);
                  return (
                    <div
                      key={st.id}
                      onClick={() => handleStationToggle(st.id)}
                      style={{
                        padding: '9px 12px',
                        background: isChecked ? 'rgba(255, 255, 255, 0.95)' : 'rgba(248, 250, 252, 0.8)',
                        border: '1.5px solid',
                        borderColor: isChecked ? '#2563eb' : 'rgba(203, 213, 225, 0.8)',
                        borderBottom: isChecked ? '3px solid #1d4ed8' : '3px solid #cbd5e1',
                        boxShadow: isChecked ? '0 3px 0 #1d4ed8, 0 3px 6px rgba(37, 99, 235, 0.15)' : '0 2px 0 #cbd5e1, 0 2px 4px rgba(0, 0, 0, 0.04)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        borderLeft: isChecked ? '4px solid #2563eb' : '1.5px solid rgba(203, 213, 225, 0.8)',
                        backdropFilter: 'blur(8px)',
                        transition: 'transform 0.08s ease, box-shadow 0.08s ease'
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 800, color: isChecked ? '#1e3a8a' : '#0f172a', fontFamily: 'var(--font-mono)' }}>
                          {st.id}
                        </div>
                        <div style={{ fontSize: '10px', color: '#475569', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                          {st.sector}
                        </div>
                      </div>
                      <div style={{
                        width: '16px',
                        height: '16px',
                        border: '1.5px solid',
                        borderColor: isChecked ? '#2563eb' : '#94a3b8',
                        background: isChecked ? '#2563eb' : '#ffffff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        {isChecked && <CheckCircle size={12} color="#ffffff" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 2. Vessel Selection */}
          <div className="ws-panel" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Ship size={15} color="#2563eb" />
                <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                  2. POLAR VESSEL SELECTION
                </h3>
              </div>
              <span style={{ fontSize: '10.5px', color: '#2563eb', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                ICE CLASS: {missionConfig.vessel.iceClass.toUpperCase()}
              </span>
            </div>

            {/* Vessel Selector Tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              {vessels.map((v) => {
                const isSelected = missionConfig.vessel.id === v.id;
                return (
                  <button
                    key={v.id}
                    onClick={() => handleVesselChange(v.id)}
                    style={{
                      flex: 1,
                      padding: '10px 12px',
                      border: '1.5px solid',
                      borderColor: isSelected ? '#1d4ed8' : 'rgba(191, 219, 254, 0.85)',
                      borderBottom: isSelected ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                      background: isSelected ? '#2563eb' : 'rgba(255, 255, 255, 0.9)',
                      color: isSelected ? '#ffffff' : '#0f172a',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontFamily: 'var(--font-mono)',
                      backdropFilter: 'blur(8px)',
                      boxShadow: isSelected ? '0 3px 0 #1e3a8a, 0 4px 8px rgba(30, 58, 138, 0.28)' : '0 2px 0 #93c5fd, 0 2px 5px rgba(37, 99, 235, 0.1)'
                    }}
                  >
                    <div style={{ fontSize: '12px', fontWeight: 800 }}>{v.name}</div>
                    <div style={{ fontSize: '10px', color: isSelected ? '#bfdbfe' : '#475569', marginTop: '2px' }}>
                      {v.iceClass} • {v.speedOpenWater} kts
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Clean Vessel Specs Strip */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '10px',
              padding: '10px 14px',
              background: 'rgba(255, 255, 255, 0.85)',
              border: '1px solid rgba(191, 219, 254, 0.8)',
              fontFamily: 'var(--font-mono)',
              backdropFilter: 'blur(8px)'
            }}>
              <div>
                <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>MAX ICE THICKNESS</span>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                  {missionConfig.vessel.maxIceThickness} m
                </div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>CRUISING FUEL BURN</span>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#0d9488', marginTop: '2px' }}>
                  {missionConfig.vessel.dailyFuelBurnCruising} MT/d
                </div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>ICEBREAKING FUEL BURN</span>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#ea580c', marginTop: '2px' }}>
                  {missionConfig.vessel.dailyFuelBurnIceBreaking} MT/d
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Routing Optimization Strategy */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          <div className="ws-panel" style={{ padding: '16px 18px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Sliders size={15} color="#2563eb" />
                <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                  3. ROUTING OPTIMIZATION STRATEGY
                </h3>
              </div>

              {/* 1-Click Strategy Presets */}
              <div style={{ marginBottom: '18px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <Zap size={13} color="#2563eb" />
                  <span style={{ fontSize: '10px', color: '#475569', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                    STRATEGY PRESETS:
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                  {[
                    { id: 'balanced', label: 'Balanced' },
                    { id: 'safety', label: 'Safest' },
                    { id: 'fuel', label: 'Eco-Fuel' },
                    { id: 'fast', label: 'Fastest' }
                  ].map((p) => (
                    <button
                      key={p.id}
                      onClick={() => applyPreset(p.id as any)}
                      style={{
                        padding: '8px 10px',
                        background: 'rgba(255, 255, 255, 0.9)',
                        border: '1px solid rgba(147, 197, 253, 0.85)',
                        borderBottom: '3px solid #93c5fd',
                        color: '#1e3a8a',
                        fontSize: '11px',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 800,
                        cursor: 'pointer',
                        backdropFilter: 'blur(8px)',
                        boxShadow: '0 2px 0 #93c5fd, 0 2px 5px rgba(37, 99, 235, 0.08)'
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Weight Sliders */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                    <span style={{ color: '#1e293b', fontWeight: 700 }}>Safety & Sea-Ice Avoidance</span>
                    <span style={{ fontWeight: 800, color: '#0d9488', fontSize: '13px' }}>{missionConfig.priorityWeights.safety}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={missionConfig.priorityWeights.safety}
                    onChange={(e) => handleWeightChange('safety', Number(e.target.value))}
                    style={{ width: '100%', accentColor: '#0d9488' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                    <span style={{ color: '#1e293b', fontWeight: 700 }}>Fuel Economy & Emissions</span>
                    <span style={{ fontWeight: 800, color: '#ea580c', fontSize: '13px' }}>{missionConfig.priorityWeights.fuelEconomy}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={missionConfig.priorityWeights.fuelEconomy}
                    onChange={(e) => handleWeightChange('fuelEconomy', Number(e.target.value))}
                    style={{ width: '100%', accentColor: '#ea580c' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                    <span style={{ color: '#1e293b', fontWeight: 700 }}>Transit Speed & Direct Arrival</span>
                    <span style={{ fontWeight: 800, color: '#1e3a8a', fontSize: '13px' }}>{missionConfig.priorityWeights.transitSpeed}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={missionConfig.priorityWeights.transitSpeed}
                    onChange={(e) => handleWeightChange('transitSpeed', Number(e.target.value))}
                    style={{ width: '100%', accentColor: '#1e3a8a' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                    <span style={{ color: '#1e293b', fontWeight: 700 }}>Scientific Operating Window</span>
                    <span style={{ fontWeight: 800, color: '#2563eb', fontSize: '13px' }}>{missionConfig.priorityWeights.scienceWindow}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={missionConfig.priorityWeights.scienceWindow}
                    onChange={(e) => handleWeightChange('scienceWindow', Number(e.target.value))}
                    style={{ width: '100%', accentColor: '#2563eb' }}
                  />
                </div>
              </div>
            </div>

            {/* Quick Strategy Note */}
            <div style={{ marginTop: '16px', padding: '10px 12px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid rgba(191, 219, 254, 0.8)', fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#1e293b', backdropFilter: 'blur(8px)' }}>
              <strong style={{ color: '#2563eb' }}>ROUTING ENGINE:</strong> Prioritizing {missionConfig.priorityWeights.safety >= 70 ? 'conservative ice margins' : 'rapid direct transit'} for {missionConfig.vessel.name}.
            </div>
          </div>

        </div>

      </div>

      {/* Bottom Action Bar */}
      <div className="ws-panel" style={{
        padding: '12px 18px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '2px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MapPin size={16} color="#0d9488" />
          <span style={{ fontSize: '11.5px', fontWeight: 700, color: '#172554', fontFamily: 'var(--font-mono)' }}>
            EXPEDITION CONFIGURED // TARGETS: {missionConfig.targetStations.join(', ')} // {missionConfig.originPort.split(' (')[0]}
          </span>
        </div>

        <button
          onClick={() => setActiveView('antarctic-map')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '9px 22px',
            borderRadius: '0px',
            background: '#2563eb',
            color: '#ffffff',
            border: '1px solid #1d4ed8',
            borderBottom: '3px solid #1e3a8a',
            fontSize: '11.5px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 800,
            cursor: 'pointer',
            letterSpacing: '0.03em',
            boxShadow: '0 3px 0 #1e3a8a, 0 5px 10px rgba(30, 58, 138, 0.3)'
          }}
        >
          <span>LAUNCH ANTARCTIC MAP WORKSPACE</span>
          <ArrowRight size={14} />
        </button>
      </div>

    </div>
  );
};

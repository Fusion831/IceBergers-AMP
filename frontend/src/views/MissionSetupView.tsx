import React, { useState, useMemo } from 'react';
import { useMission } from '../context/MissionContext';
import {
  Ship,
  Anchor,
  Sliders,
  CheckCircle,
  ArrowRight,
  Calendar,
  MapPin,
  Clock,
  Sun,
  Plus
} from 'lucide-react';

interface MissionSetupViewProps {
  onClose?: () => void;
}

interface KnownPort {
  id: string;
  name: string;
  shortName: string;
  coords: [number, number]; // [lon, lat]
  country: string;
  distanceToAntarcticNM: number;
}

const PRESET_GATEWAYS: KnownPort[] = [
  { id: 'cape-town', name: 'Cape Town (Supply Gateway)', shortName: 'Cape Town', coords: [18.4241, -33.9249], country: 'South Africa', distanceToAntarcticNM: 2160 },
  { id: 'mormugao', name: 'Mormugao Port, Goa (NCPOR HQ)', shortName: 'Mormugao, Goa', coords: [73.8016, 15.4140], country: 'India', distanceToAntarcticNM: 5120 },
  { id: 'port-louis', name: 'Port Louis Harbour', shortName: 'Port Louis', coords: [57.5012, -20.1609], country: 'Mauritius', distanceToAntarcticNM: 2980 },
  { id: 'hobart', name: 'Hobart Antarctic Gateway', shortName: 'Hobart, TAS', coords: [147.3272, -42.8821], country: 'Australia', distanceToAntarcticNM: 1450 },
  { id: 'durban', name: 'Port of Durban', shortName: 'Durban', coords: [31.0218, -29.8587], country: 'South Africa', distanceToAntarcticNM: 2420 },
  { id: 'punta-arenas', name: 'Punta Arenas Port', shortName: 'Punta Arenas', coords: [-70.9171, -53.1638], country: 'Chile', distanceToAntarcticNM: 820 },
  { id: 'ushuaia', name: 'Ushuaia Staging Port', shortName: 'Ushuaia', coords: [-68.3030, -54.8019], country: 'Argentina', distanceToAntarcticNM: 680 }
];

const PRESET_STATIONS = [
  { id: 'Bharati Station', sector: 'Larsemann Hills (Prydz Bay)', coords: '69.41°S, 76.19°E', defaultDwell: '48h' },
  { id: 'Maitri Station', sector: 'Schirmacher Oasis (Lazarev Sea)', coords: '69.95°S, 11.73°E', defaultDwell: '72h' },
  { id: 'Dakshin Gangotri Ice Shelf', sector: 'Historical Site / Ice Shelf Shelf Lead', coords: '70.08°S, 12.00°E', defaultDwell: '24h' },
  { id: 'Crown Prince Olav Coast', sector: 'Enderby Land Coastal Transect', coords: '68.50°S, 42.50°E', defaultDwell: '36h' },
  { id: 'Amery Ice Shelf Lead', sector: 'Prydz Bay Inflow Glaciology Station', coords: '69.00°S, 72.00°E', defaultDwell: '24h' }
];

function getSeasonAnalysis(startDateStr: string) {
  if (!startDateStr) return null;
  const date = new Date(startDateStr);
  const month = date.getMonth(); // 0 = Jan, 11 = Dec

  if (month === 11 || month === 0) {
    return {
      season: 'PEAK AUSTRAL SUMMER',
      badgeColor: '#10b981',
      badgeBg: 'rgba(16, 185, 129, 0.15)',
      description: 'Optimal expedition window. Minimum annual circum-Antarctic sea ice extent with 24-hr continuous solar illumination. Favorable marginal ice leads into Prydz Bay and Lazarev Sea.',
      seaIceRisk: 'LOWEST ANNUAL PACK EXTENT',
      transitWindowRating: 'EXCELLENT (OPTIMAL WINDOW)'
    };
  } else if (month === 1) {
    return {
      season: 'LATE AUSTRAL SUMMER',
      badgeColor: '#06b6d4',
      badgeBg: 'rgba(6, 182, 212, 0.15)',
      description: 'Maximum coastal fast-ice thermal decay. Optimal access to sheltered station landing sites, but freeze-up begins toward late February in high-latitude bays.',
      seaIceRisk: 'LOW (NEW ICE EMERGENCE LATE FEB)',
      transitWindowRating: 'FAVORABLE (MONITOR FREEZE)'
    };
  } else if (month === 2 || month === 3) {
    return {
      season: 'AUSTRAL AUTUMN FREEZE-UP',
      badgeColor: '#f59e0b',
      badgeBg: 'rgba(245, 158, 11, 0.15)',
      description: 'Rapid sub-zero temperature drops and sea surface cooling. Nilas and pancake ice consolidate rapidly across Prydz Bay and continental shelf margin.',
      seaIceRisk: 'ELEVATED ICE CONVERGENCE',
      transitWindowRating: 'CAUTION (EXPEDITE DEPARTURE)'
    };
  } else {
    return {
      season: 'AUSTRAL WINTER / SPRING PACK',
      badgeColor: '#ef4444',
      badgeBg: 'rgba(239, 68, 68, 0.15)',
      description: 'Heavy consolidated multi-year pack ice, persistent katabatic gales, and extended polar night. Closed navigation routes for non-icebreaking tonnage.',
      seaIceRisk: 'MAXIMUM ICE THICKNESS (>1.5m)',
      transitWindowRating: 'HIGH HAZARD (CLASS 1A / ESCORT ONLY)'
    };
  }
}

function calculateDuration(startStr: string, endStr: string) {
  if (!startStr || !endStr) return { days: 90, weeks: 12.8, hours: 2160 };
  const d1 = new Date(startStr).getTime();
  const d2 = new Date(endStr).getTime();
  const diffMs = Math.max(0, d2 - d1);
  const days = Math.round(diffMs / (1000 * 60 * 60 * 24));
  const hours = days * 24;
  const weeks = +(days / 7).toFixed(1);
  return { days, weeks, hours };
}

export const MissionSetupView: React.FC<MissionSetupViewProps> = ({ onClose }) => {
  const {
    missionConfig,
    setMissionConfig,
    vessels,
    setActiveView,
    setSelectedRouteId
  } = useMission();

  // Local state for custom port editor
  const [isCustomOrigin, setIsCustomOrigin] = useState<boolean>(() => {
    return !PRESET_GATEWAYS.some((p) => p.name === missionConfig.originPort);
  });
  const [customOriginName, setCustomOriginName] = useState<string>(missionConfig.originPort || 'Custom Port');
  const [customOriginLon, setCustomOriginLon] = useState<number>(missionConfig.originPortCoords?.[0] ?? 18.4241);
  const [customOriginLat, setCustomOriginLat] = useState<number>(missionConfig.originPortCoords?.[1] ?? -33.9249);

  // Return Port customization
  const [separateReturnPort, setSeparateReturnPort] = useState<boolean>(() => {
    return !!(missionConfig.returnPort && missionConfig.returnPort !== missionConfig.originPort);
  });
  const [returnPortName, setReturnPortName] = useState<string>(missionConfig.returnPort || missionConfig.originPort);
  const [returnPortLon, setReturnPortLon] = useState<number>(missionConfig.returnPortCoords?.[0] ?? 18.4241);
  const [returnPortLat, setReturnPortLat] = useState<number>(missionConfig.returnPortCoords?.[1] ?? -33.9249);

  // Custom Antarctic Waypoint state
  const [showAddStation, setShowAddStation] = useState<boolean>(false);
  const [newStationName, setNewStationName] = useState<string>('');
  const [newStationSector, setNewStationSector] = useState<string>('');

  // Calculations
  const duration = useMemo(() => {
    return calculateDuration(missionConfig.startDate, missionConfig.endDate);
  }, [missionConfig.startDate, missionConfig.endDate]);

  const seasonAnalysis = useMemo(() => {
    return getSeasonAnalysis(missionConfig.startDate);
  }, [missionConfig.startDate]);

  // Handlers for Origin Port Selection
  const handleOriginPresetSelect = (portId: string) => {
    if (portId === 'custom') {
      setIsCustomOrigin(true);
      return;
    }
    const found = PRESET_GATEWAYS.find((p) => p.id === portId);
    if (found) {
      setIsCustomOrigin(false);
      setCustomOriginName(found.name);
      setCustomOriginLon(found.coords[0]);
      setCustomOriginLat(found.coords[1]);

      setMissionConfig((prev) => ({
        ...prev,
        originPort: found.name,
        originPortCoords: found.coords,
        returnPort: separateReturnPort ? prev.returnPort : found.name,
        returnPortCoords: separateReturnPort ? prev.returnPortCoords : found.coords
      }));
    }
  };

  const handleCustomOriginCommit = (name: string, lon: number, lat: number) => {
    setMissionConfig((prev) => ({
      ...prev,
      originPort: name,
      originPortCoords: [lon, lat],
      returnPort: separateReturnPort ? prev.returnPort : name,
      returnPortCoords: separateReturnPort ? prev.returnPortCoords : [lon, lat]
    }));
  };

  const handleReturnPortCommit = (name: string, lon: number, lat: number) => {
    setMissionConfig((prev) => ({
      ...prev,
      returnPort: name,
      returnPortCoords: [lon, lat]
    }));
  };

  // Handlers for Schedule Presets
  const applyDatePreset = (preset: 'summer' | 'early' | 'late' | 'extended') => {
    const year = new Date().getFullYear();
    const presets = {
      summer: { start: `${year}-01-01`, end: `${year}-03-31`, time: '06:00' },
      early: { start: `${year}-12-01`, end: `${year + 1}-02-28`, time: '08:00' },
      late: { start: `${year}-02-01`, end: `${year}-04-15`, time: '06:00' },
      extended: { start: `${year}-11-15`, end: `${year + 1}-03-31`, time: '04:00' }
    };
    const sel = presets[preset];
    setMissionConfig((prev) => ({
      ...prev,
      startDate: sel.start,
      endDate: sel.end,
      departureTime: sel.time
    }));
  };

  // Vessel Selection
  const handleVesselChange = (vesselId: string) => {
    const selected = vessels.find((v) => v.id === vesselId);
    if (selected) {
      setMissionConfig((prev) => ({ ...prev, vessel: selected }));
    }
  };

  // Priority Weights
  const handleWeightChange = (key: keyof typeof missionConfig.priorityWeights, value: number) => {
    setMissionConfig((prev) => ({
      ...prev,
      priorityWeights: {
        ...prev.priorityWeights,
        [key]: value
      }
    }));
  };

  const applyPriorityPreset = (preset: 'balanced' | 'safety' | 'fuel' | 'fast') => {
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
    if (preset === 'safety') setSelectedRouteId('safest');
    else if (preset === 'fuel') setSelectedRouteId('fuel_efficient');
    else if (preset === 'fast') setSelectedRouteId('fastest');
    else if (preset === 'balanced') setSelectedRouteId('balanced');
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

  const handleAddCustomStation = () => {
    if (!newStationName.trim()) return;
    const fullName = `${newStationName.trim()} (${newStationSector.trim() || 'Custom Sector'})`;
    setMissionConfig((prev) => ({
      ...prev,
      targetStations: [...prev.targetStations, fullName]
    }));
    setNewStationName('');
    setNewStationSector('');
    setShowAddStation(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%', overflowY: 'auto', padding: '8px' }}>

      {/* Top Banner Header */}
      <div className="ws-panel" style={{ padding: '14px 18px', background: 'rgba(255, 255, 255, 0.96)', border: '1px solid #bfdbfe' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '10.5px', fontWeight: 800, padding: '2px 8px', background: '#2563eb', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                EXPEDITION CONFIGURATION
              </span>
              <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 800, color: '#172554', margin: 0 }}>
                {missionConfig.missionName.toUpperCase()} // {missionConfig.expeditionId}
              </h2>
            </div>
            <p style={{ fontSize: '11.5px', color: '#475569', marginTop: '4px', fontFamily: 'var(--font-mono)', margin: 0 }}>
              Customize voyage departure & return ports, scheduling dates, destination stations, polar vessel profile, and 4D A* routing weights.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ padding: '6px 14px', background: '#eff6ff', border: '1px solid #bfdbfe', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Ship size={14} color="#2563eb" />
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>VESSEL:</span>
              <span style={{ fontSize: '12px', fontWeight: 800, color: '#2563eb', fontFamily: 'var(--font-mono)' }}>{missionConfig.vessel.name}</span>
            </div>

            <div style={{ padding: '6px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={14} color="#16a34a" />
              <span style={{ fontSize: '10px', color: '#15803d', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>DURATION:</span>
              <span style={{ fontSize: '12px', fontWeight: 800, color: '#16a34a', fontFamily: 'var(--font-mono)' }}>{duration.days} DAYS</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Configuration Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.15fr 1fr', gap: '14px' }}>

        {/* LEFT COLUMN: PORTS, DATES & DESTINATIONS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* 1. DEPARTURE & RETURN PORTS */}
          <div className="ws-panel" style={{ padding: '16px 18px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Anchor size={16} color="#2563eb" />
                <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                  1. VOYAGE GATEWAY & RETURN PORTS
                </h3>
              </div>
              <span style={{ fontSize: '10.5px', color: '#2563eb', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                GPS COORDINATES DIRECT LINK
              </span>
            </div>

            {/* Expedition Title */}
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '10.5px', color: '#475569', marginBottom: '4px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                EXPEDITION TITLE / IDENTIFIER
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '8px' }}>
                <input
                  type="text"
                  value={missionConfig.missionName}
                  onChange={(e) => setMissionConfig((prev) => ({ ...prev, missionName: e.target.value }))}
                  style={{
                    padding: '8px 10px',
                    border: '1px solid #bfdbfe',
                    color: '#0f172a',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    outline: 'none',
                    background: '#f8fafc'
                  }}
                  placeholder="Expedition Name"
                />
                <input
                  type="text"
                  value={missionConfig.expeditionId}
                  onChange={(e) => setMissionConfig((prev) => ({ ...prev, expeditionId: e.target.value }))}
                  style={{
                    padding: '8px 10px',
                    border: '1px solid #bfdbfe',
                    color: '#2563eb',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 800,
                    outline: 'none',
                    background: '#eff6ff'
                  }}
                  placeholder="ID (e.g. NCPOR-44)"
                />
              </div>
            </div>

            {/* Departure Origin Port Selector */}
            <div style={{ marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontSize: '10.5px', color: '#475569', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                  ORIGIN STAGING GATEWAY PORT
                </label>
                <button
                  onClick={() => setIsCustomOrigin(!isCustomOrigin)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#2563eb',
                    fontSize: '10.5px',
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  {isCustomOrigin ? '← Select from Known Gateways' : '+ Enter Custom Coordinates'}
                </button>
              </div>

              {!isCustomOrigin ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '8px' }}>
                  {PRESET_GATEWAYS.map((port) => {
                    const isSelected = missionConfig.originPort.includes(port.shortName);
                    return (
                      <div
                        key={port.id}
                        onClick={() => handleOriginPresetSelect(port.id)}
                        style={{
                          padding: '8px 10px',
                          border: isSelected ? '1.5px solid #2563eb' : '1px solid #e2e8f0',
                          borderLeft: isSelected ? '4px solid #2563eb' : '1px solid #e2e8f0',
                          background: isSelected ? '#eff6ff' : '#f8fafc',
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '2px',
                          transition: 'all 0.1s ease'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '11.5px', fontWeight: 800, color: isSelected ? '#1e3a8a' : '#0f172a', fontFamily: 'var(--font-mono)' }}>
                            {port.shortName}
                          </span>
                          {isSelected && <CheckCircle size={13} color="#2563eb" />}
                        </div>
                        <div style={{ fontSize: '9.5px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                          {port.country} • {port.distanceToAntarcticNM} NM to Polar Circle
                        </div>
                        <div style={{ fontSize: '9.5px', color: '#2563eb', fontFamily: 'monospace' }}>
                          {Math.abs(port.coords[1]).toFixed(2)}°S, {Math.abs(port.coords[0]).toFixed(2)}°E
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                /* Custom Origin Port Input Form */
                <div style={{ padding: '12px', background: '#f8fafc', border: '1px dashed #93c5fd', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', marginBottom: '3px' }}>
                      CUSTOM PORT NAME & COUNTRY
                    </label>
                    <input
                      type="text"
                      value={customOriginName}
                      onChange={(e) => {
                        setCustomOriginName(e.target.value);
                        handleCustomOriginCommit(e.target.value, customOriginLon, customOriginLat);
                      }}
                      placeholder="e.g. Fremantle Harbour, Australia"
                      style={{
                        width: '100%',
                        padding: '6px 8px',
                        border: '1px solid #bfdbfe',
                        fontSize: '11.5px',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700
                      }}
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', marginBottom: '3px' }}>
                        LONGITUDE (-180° to 180°)
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        value={customOriginLon}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          setCustomOriginLon(val);
                          handleCustomOriginCommit(customOriginName, val, customOriginLat);
                        }}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          border: '1px solid #bfdbfe',
                          fontSize: '11.5px',
                          fontFamily: 'monospace',
                          fontWeight: 700
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', marginBottom: '3px' }}>
                        LATITUDE (-90° to 90°)
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        value={customOriginLat}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          setCustomOriginLat(val);
                          handleCustomOriginCommit(customOriginName, customOriginLon, val);
                        }}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          border: '1px solid #bfdbfe',
                          fontSize: '11.5px',
                          fontFamily: 'monospace',
                          fontWeight: 700
                        }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Separate Return Port Option */}
            <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '11px', fontWeight: 700, color: '#1e293b', fontFamily: 'var(--font-mono)' }}>
                  <input
                    type="checkbox"
                    checked={separateReturnPort}
                    onChange={(e) => {
                      const checked = e.target.checked;
                      setSeparateReturnPort(checked);
                      if (!checked) {
                        setMissionConfig((prev) => ({
                          ...prev,
                          returnPort: prev.originPort,
                          returnPortCoords: prev.originPortCoords
                        }));
                      }
                    }}
                    style={{ accentColor: '#2563eb' }}
                  />
                  <span>CUSTOMIZE SEPARATE RETURN DESTINATION PORT</span>
                </label>
                <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                  {separateReturnPort ? 'Asymmetric Route' : 'Roundtrip Loop'}
                </span>
              </div>

              {separateReturnPort && (
                <div style={{ padding: '10px', background: '#faf5ff', border: '1px solid #e9d5ff', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '8px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '10px', color: '#6b21a8', fontFamily: 'var(--font-mono)', marginBottom: '3px' }}>
                        RETURN PORT NAME
                      </label>
                      <input
                        type="text"
                        value={returnPortName}
                        onChange={(e) => {
                          setReturnPortName(e.target.value);
                          handleReturnPortCommit(e.target.value, returnPortLon, returnPortLat);
                        }}
                        placeholder="e.g. Mormugao Port, Goa (NCPOR HQ)"
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          border: '1px solid #d8b4fe',
                          fontSize: '11.5px',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 700
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '10px', color: '#6b21a8', fontFamily: 'var(--font-mono)', marginBottom: '3px' }}>
                        LON
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        value={returnPortLon}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          setReturnPortLon(val);
                          handleReturnPortCommit(returnPortName, val, returnPortLat);
                        }}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          border: '1px solid #d8b4fe',
                          fontSize: '11px',
                          fontFamily: 'monospace'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '10px', color: '#6b21a8', fontFamily: 'var(--font-mono)', marginBottom: '3px' }}>
                        LAT
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        value={returnPortLat}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          setReturnPortLat(val);
                          handleReturnPortCommit(returnPortName, returnPortLon, val);
                        }}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          border: '1px solid #d8b4fe',
                          fontSize: '11px',
                          fontFamily: 'monospace'
                        }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 2. VOYAGE DATES & SEASONALITY ADVISOR */}
          <div className="ws-panel" style={{ padding: '16px 18px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={16} color="#2563eb" />
                <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                  2. VOYAGE SCHEDULE & POLAR CLIMATE WINDOW
                </h3>
              </div>
              <span style={{ fontSize: '11px', fontWeight: 800, color: '#16a34a', fontFamily: 'var(--font-mono)' }}>
                {duration.days} DAYS ({duration.weeks} WEEKS)
              </span>
            </div>

            {/* Quick Season Presets */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '10.5px', color: '#475569', marginBottom: '6px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                1-CLICK EXPEDITION SEASON PRESETS
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                {[
                  { id: 'summer', label: 'Peak Summer', dates: 'Jan 01 - Mar 31' },
                  { id: 'early', label: 'Early Inflow', dates: 'Dec 01 - Feb 28' },
                  { id: 'late', label: 'Late Season', dates: 'Feb 01 - Apr 15' },
                  { id: 'extended', label: '135d Deep Survey', dates: 'Nov 15 - Mar 31' }
                ].map((p) => (
                  <button
                    key={p.id}
                    onClick={() => applyDatePreset(p.id as any)}
                    style={{
                      padding: '6px 4px',
                      background: '#f1f5f9',
                      border: '1px solid #cbd5e1',
                      borderBottom: '2px solid #94a3b8',
                      color: '#0f172a',
                      cursor: 'pointer',
                      textAlign: 'center',
                      fontFamily: 'var(--font-mono)'
                    }}
                  >
                    <div style={{ fontSize: '10.5px', fontWeight: 800 }}>{p.label}</div>
                    <div style={{ fontSize: '9px', color: '#64748b', marginTop: '1px' }}>{p.dates}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Precise Date & Time Inputs */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr 1.2fr', gap: '8px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', marginBottom: '3px', fontWeight: 700 }}>
                  DEPARTURE DATE
                </label>
                <input
                  type="date"
                  value={missionConfig.startDate}
                  onChange={(e) => setMissionConfig((prev) => ({ ...prev, startDate: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '7px 10px',
                    border: '1px solid #bfdbfe',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    background: '#f8fafc',
                    color: '#0f172a'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', marginBottom: '3px', fontWeight: 700 }}>
                  TIME (UTC)
                </label>
                <input
                  type="time"
                  value={missionConfig.departureTime || '06:00'}
                  onChange={(e) => setMissionConfig((prev) => ({ ...prev, departureTime: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '7px 8px',
                    border: '1px solid #bfdbfe',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    background: '#f8fafc',
                    color: '#0f172a'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', marginBottom: '3px', fontWeight: 700 }}>
                  MISSION RETURN DATE
                </label>
                <input
                  type="date"
                  value={missionConfig.endDate}
                  onChange={(e) => setMissionConfig((prev) => ({ ...prev, endDate: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '7px 10px',
                    border: '1px solid #bfdbfe',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    background: '#f8fafc',
                    color: '#0f172a'
                  }}
                />
              </div>
            </div>

            {/* Dynamic Polar Seasonality & Climate Advisory Box */}
            {seasonAnalysis && (
              <div
                style={{
                  padding: '12px',
                  background: seasonAnalysis.badgeBg,
                  border: `1px solid ${seasonAnalysis.badgeColor}40`,
                  borderRadius: '2px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '5px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sun size={14} color={seasonAnalysis.badgeColor} />
                    <span style={{ fontSize: '11px', fontWeight: 800, color: seasonAnalysis.badgeColor, fontFamily: 'var(--font-mono)' }}>
                      POLAR SEASON: {seasonAnalysis.season}
                    </span>
                  </div>
                  <span style={{ fontSize: '10px', fontWeight: 800, color: seasonAnalysis.badgeColor, fontFamily: 'var(--font-mono)' }}>
                    {seasonAnalysis.transitWindowRating}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: '#1e293b', lineHeight: '1.45', fontFamily: 'var(--font-mono)' }}>
                  {seasonAnalysis.description}
                </div>
              </div>
            )}
          </div>

          {/* 3. TARGET DESTINATIONS */}
          <div className="ws-panel" style={{ padding: '16px 18px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MapPin size={16} color="#0d9488" />
                <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                  3. TARGET ANTARCTIC STATIONS & COASTAL SITES
                </h3>
              </div>
              <button
                onClick={() => setShowAddStation(!showAddStation)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: '#eff6ff',
                  border: '1px solid #93c5fd',
                  color: '#2563eb',
                  padding: '3px 8px',
                  fontSize: '10px',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer'
                }}
              >
                <Plus size={12} />
                <span>Add Waypoint</span>
              </button>
            </div>

            {/* Station Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
              {PRESET_STATIONS.map((st) => {
                const isChecked = missionConfig.targetStations.some((s) => s.includes(st.id.split(' ')[0]));
                return (
                  <div
                    key={st.id}
                    onClick={() => handleStationToggle(st.id)}
                    style={{
                      padding: '8px 10px',
                      background: isChecked ? '#f0fdfa' : '#f8fafc',
                      border: isChecked ? '1.5px solid #0d9488' : '1px solid #e2e8f0',
                      borderLeft: isChecked ? '4px solid #0d9488' : '1px solid #e2e8f0',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '11.5px', fontWeight: 800, color: isChecked ? '#0f766e' : '#0f172a', fontFamily: 'var(--font-mono)' }}>
                        {st.id}
                      </div>
                      <div style={{ fontSize: '9.5px', color: '#64748b', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                        {st.sector} • {st.coords}
                      </div>
                    </div>
                    <div style={{
                      width: '16px',
                      height: '16px',
                      border: '1.5px solid',
                      borderColor: isChecked ? '#0d9488' : '#94a3b8',
                      background: isChecked ? '#0d9488' : '#ffffff',
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

            {/* Custom Waypoint Input Dropdown */}
            {showAddStation && (
              <div style={{ padding: '10px', background: '#f8fafc', border: '1px dashed #0d9488', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="text"
                  placeholder="Station / Waypoint Name"
                  value={newStationName}
                  onChange={(e) => setNewStationName(e.target.value)}
                  style={{ flex: 1, padding: '6px 8px', border: '1px solid #cbd5e1', fontSize: '11px', fontFamily: 'var(--font-mono)' }}
                />
                <input
                  type="text"
                  placeholder="Sector / Coords (e.g. 71.2°S, 14.5°E)"
                  value={newStationSector}
                  onChange={(e) => setNewStationSector(e.target.value)}
                  style={{ flex: 1, padding: '6px 8px', border: '1px solid #cbd5e1', fontSize: '11px', fontFamily: 'var(--font-mono)' }}
                />
                <button
                  onClick={handleAddCustomStation}
                  style={{
                    padding: '6px 12px',
                    background: '#0d9488',
                    color: '#ffffff',
                    border: 'none',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    fontFamily: 'var(--font-mono)'
                  }}
                >
                  Add
                </button>
              </div>
            )}
          </div>

        </div>

        {/* RIGHT COLUMN: POLAR VESSEL SELECTION & MULTI-OBJECTIVE WEIGHTS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* 4. POLAR VESSEL SELECTION */}
          <div className="ws-panel" style={{ padding: '16px 18px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Ship size={16} color="#2563eb" />
                <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                  4. POLAR VESSEL PROFILE SELECTION
                </h3>
              </div>
              <span style={{ fontSize: '10px', color: '#2563eb', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                {missionConfig.vessel.iceClass.toUpperCase()}
              </span>
            </div>

            {/* Vessel Selector Cards */}
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
                      borderColor: isSelected ? '#1d4ed8' : '#e2e8f0',
                      borderBottom: isSelected ? '3px solid #1e3a8a' : '3px solid #cbd5e1',
                      background: isSelected ? '#2563eb' : '#f8fafc',
                      color: isSelected ? '#ffffff' : '#0f172a',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontFamily: 'var(--font-mono)',
                      boxShadow: isSelected ? '0 3px 0 #1e3a8a, 0 4px 8px rgba(30, 58, 138, 0.28)' : '0 2px 0 #cbd5e1'
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

            {/* Vessel Technical Specs Matrix */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                <div>
                  <span style={{ color: '#64748b', fontSize: '10px' }}>MAX ICE THICKNESS:</span>
                  <div style={{ fontWeight: 800, color: '#1e3a8a' }}>{missionConfig.vessel.maxIceThickness} m</div>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '10px' }}>SERVICE SPEED:</span>
                  <div style={{ fontWeight: 800, color: '#1e3a8a' }}>{missionConfig.vessel.speedOpenWater} kn (Open) / {missionConfig.vessel.speedIce} kn (Ice)</div>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '10px' }}>BUNKER CAPACITY:</span>
                  <div style={{ fontWeight: 800, color: '#1e3a8a' }}>{missionConfig.vessel.fuelCapacity} MT</div>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '10px' }}>DAILY CRUISE BURN:</span>
                  <div style={{ fontWeight: 800, color: '#1e3a8a' }}>{missionConfig.vessel.dailyFuelBurnCruising} MT/day</div>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '10px' }}>ICE BREAKING BURN:</span>
                  <div style={{ fontWeight: 800, color: '#1e3a8a' }}>{missionConfig.vessel.dailyFuelBurnIceBreaking} MT/day</div>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '10px' }}>PROPULSION TYPE:</span>
                  <div style={{ fontWeight: 800, color: '#1e3a8a' }}>Diesel-Electric Twin Azimuth</div>
                </div>
              </div>
            </div>
          </div>

          {/* 5. 4D A* ROUTING WEIGHTS & PRESETS */}
          <div className="ws-panel" style={{ padding: '16px 18px', background: '#ffffff', border: '1px solid #bfdbfe' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={16} color="#2563eb" />
                <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                  5. 4D A* MULTI-OBJECTIVE WEIGHTS
                </h3>
              </div>
              <span style={{ fontSize: '10px', color: '#2563eb', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                DYNAMIC CORRIDOR RE-RANKING
              </span>
            </div>

            {/* Presets */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '10.5px', color: '#475569', marginBottom: '6px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                1-CLICK STRATEGIC PRESETS
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                {[
                  { id: 'balanced', label: 'Balanced', desc: 'Equal Multi-Criterion' },
                  { id: 'safety', label: 'Safety First', desc: 'Max Sea-Ice Clearance' },
                  { id: 'fuel', label: 'Fuel Economy', desc: 'Cubic Resistance Min' },
                  { id: 'fast', label: 'Speed First', desc: 'Peak SOG & Current' }
                ].map((p) => (
                  <button
                    key={p.id}
                    onClick={() => applyPriorityPreset(p.id as any)}
                    style={{
                      padding: '6px 4px',
                      background: '#f8fafc',
                      border: '1px solid #cbd5e1',
                      borderBottom: '2px solid #94a3b8',
                      color: '#0f172a',
                      cursor: 'pointer',
                      textAlign: 'center',
                      fontFamily: 'var(--font-mono)'
                    }}
                  >
                    <div style={{ fontSize: '10.5px', fontWeight: 800 }}>{p.label}</div>
                    <div style={{ fontSize: '9px', color: '#64748b', marginTop: '1px' }}>{p.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Sliders */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px', fontFamily: 'var(--font-mono)' }}>
                  <span style={{ color: '#1e293b', fontWeight: 700 }}>Safety Margin (Ice & Depth)</span>
                  <span style={{ fontWeight: 800, color: '#0d9488' }}>{missionConfig.priorityWeights.safety}%</span>
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
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px', fontFamily: 'var(--font-mono)' }}>
                  <span style={{ color: '#1e293b', fontWeight: 700 }}>Fuel Economy & Emissions</span>
                  <span style={{ fontWeight: 800, color: '#ea580c' }}>{missionConfig.priorityWeights.fuelEconomy}%</span>
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
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px', fontFamily: 'var(--font-mono)' }}>
                  <span style={{ color: '#1e293b', fontWeight: 700 }}>Transit Speed & Direct SOG</span>
                  <span style={{ fontWeight: 800, color: '#1e3a8a' }}>{missionConfig.priorityWeights.transitSpeed}%</span>
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
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px', fontFamily: 'var(--font-mono)' }}>
                  <span style={{ color: '#1e293b', fontWeight: 700 }}>Scientific Operating Window</span>
                  <span style={{ fontWeight: 800, color: '#2563eb' }}>{missionConfig.priorityWeights.scienceWindow}%</span>
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

        </div>

      </div>

      {/* Bottom Floating Action Bar */}
      <div className="ws-panel" style={{
        padding: '12px 18px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#ffffff',
        border: '1.5px solid #2563eb',
        marginTop: '4px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MapPin size={16} color="#0d9488" />
          <span style={{ fontSize: '11.5px', fontWeight: 700, color: '#172554', fontFamily: 'var(--font-mono)' }}>
            EXPEDITION CONFIGURED: {missionConfig.originPort} → {missionConfig.targetStations.join(', ')} ({duration.days} Days)
          </span>
        </div>

        <button
          onClick={() => {
            setActiveView('antarctic-map');
            if (onClose) onClose();
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 24px',
            background: '#2563eb',
            color: '#ffffff',
            border: '1px solid #1d4ed8',
            borderBottom: '3px solid #1e3a8a',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 800,
            cursor: 'pointer',
            letterSpacing: '0.03em',
            boxShadow: '0 3px 0 #1e3a8a, 0 5px 10px rgba(30, 58, 138, 0.3)'
          }}
        >
          <span>APPLY & LAUNCH ANTARCTIC MAP WORKSPACE</span>
          <ArrowRight size={15} />
        </button>
      </div>

    </div>
  );
};

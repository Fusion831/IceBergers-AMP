import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Compass,
  Navigation,
  ArrowLeftRight,
  ShieldAlert,
  Droplets,
  Clock,
  RotateCw,
  AlertTriangle,
  RotateCcw,
  Sparkles
} from 'lucide-react';
import { useMission } from '../context/MissionContext';
import {
  fetchAvailableStations,
  planDynamicVoyage,
  StationInfo,
  PRESET_STATIONS,
  DynamicVoyageResponse,
  DynamicRouteAlternative,
  DynamicWaypoint,
  OBJECTIVE_COLOR_MAP,
  OBJECTIVE_LABELS
} from '../services/routeApi';
import { RouteAlternative } from '../types/mission';

interface DynamicVoyageWindowProps {
  isOpen: boolean;
  onClose: () => void;
  theme?: 'dark' | 'light';
}

export const DynamicVoyageWindow: React.FC<DynamicVoyageWindowProps> = ({
  isOpen,
  onClose,
  theme = 'dark'
}) => {
  const {
    setRoutes,
    setSelectedRouteId,
    setCustomOriginDest,
    resetToCanonicalRoutes,
    selectedRouteId
  } = useMission();

  // Station State
  const [stations, setStations] = useState<StationInfo[]>(PRESET_STATIONS);
  const [originStationId, setOriginStationId] = useState<string>('cape-town');
  const [destStationId, setDestStationId] = useState<string>('bharati');

  // Custom Coordinates
  const [isCustomOrigin, setIsCustomOrigin] = useState<boolean>(false);
  const [customOriginLat, setCustomOriginLat] = useState<number>(-33.9249);
  const [customOriginLon, setCustomOriginLon] = useState<number>(18.4241);

  const [isCustomDest, setIsCustomDest] = useState<boolean>(false);
  const [customDestLat, setCustomDestLat] = useState<number>(-69.4072);
  const [customDestLon, setCustomDestLon] = useState<number>(76.1911);

  // Voyage Config
  const [vesselId, setVesselId] = useState<string>('sagar-kanya');
  const [departureDate, setDepartureDate] = useState<string>('2024-01-01');
  const [activeObjective, setActiveObjective] = useState<string>('FASTEST');

  // Execution States
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<DynamicVoyageResponse | null>(null);
  const [hasCalculated, setHasCalculated] = useState<boolean>(false);

  // Load backend stations
  useEffect(() => {
    fetchAvailableStations().then((data: StationInfo[]) => {
      if (data && data.length > 0) setStations(data);
    });
  }, []);

  const gatewayStations = useMemo(() => {
    return stations.filter((s) => {
      const cat = `${s.category || ''} ${s.type || ''}`.toLowerCase();
      return cat.includes('gateway') || cat.includes('port');
    });
  }, [stations]);

  const antarcticStations = useMemo(() => {
    const list = stations.filter((s) => {
      const cat = `${s.category || ''} ${s.type || ''}`.toLowerCase();
      return cat.includes('antarctic') || cat.includes('station') || cat.includes('base');
    });
    if (list.length === 0) {
      return stations.filter((s) => !gatewayStations.some((g) => g.id === s.id));
    }
    return list;
  }, [stations, gatewayStations]);

  const currentOrigin = useMemo(() => {
    if (isCustomOrigin) {
      return { name: `Custom (${customOriginLat.toFixed(2)}°, ${customOriginLon.toFixed(2)}°)`, coords: [customOriginLon, customOriginLat] as [number, number] };
    }
    const st = stations.find((s) => s.id === originStationId) || stations[0];
    return { name: st.name, coords: [st.longitude, st.latitude] as [number, number] };
  }, [isCustomOrigin, customOriginLat, customOriginLon, originStationId, stations]);

  const currentDest = useMemo(() => {
    if (isCustomDest) {
      return { name: `Custom (${customDestLat.toFixed(2)}°, ${customDestLon.toFixed(2)}°)`, coords: [customDestLon, customDestLat] as [number, number] };
    }
    const st = stations.find((s) => s.id === destStationId) || stations[1];
    return { name: st.name, coords: [st.longitude, st.latitude] as [number, number] };
  }, [isCustomDest, customDestLat, customDestLon, destStationId, stations]);

  // Execute Dynamic Route Calculation via Backend API
  const handleCalculateRoute = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const payload: any = {
        departure_time: new Date(departureDate).toISOString(),
        vessel_id: vesselId,
        objectives: ['FASTEST', 'SAFEST', 'SHORTEST', 'FUEL_EFFICIENT', 'BALANCED']
      };

      if (isCustomOrigin) {
        payload.origin_coords = [customOriginLon, customOriginLat];
        payload.origin_name = `Custom Origin (${customOriginLat.toFixed(2)}, ${customOriginLon.toFixed(2)})`;
      } else {
        payload.origin_station_id = originStationId;
      }

      if (isCustomDest) {
        payload.destination_coords = [customDestLon, customDestLat];
        payload.destination_name = `Custom Dest (${customDestLat.toFixed(2)}, ${customDestLon.toFixed(2)})`;
      } else {
        payload.destination_station_id = destStationId;
      }

      const response = await planDynamicVoyage(payload);
      setLastResponse(response);
      setHasCalculated(true);

      // Convert backend routes to frontend RouteAlternative format
      if (response && response.routes && response.routes.length > 0) {
        const formatted: RouteAlternative[] = response.routes.map((r: DynamicRouteAlternative) => {
          const waypoints: [number, number][] = r.waypoints.map((wp: DynamicWaypoint) => {
            const pt = wp.point || wp.position;
            return pt ? [pt.longitude, pt.latitude] : [0, 0];
          });

          const idKey = r.objective.toLowerCase();
          const color = OBJECTIVE_COLOR_MAP[r.objective] || '#3b82f6';

          return {
            id: idKey,
            name: OBJECTIVE_LABELS[r.objective] || `${r.objective} Voyage`,
            objective: r.objective,
            type: idKey as any,
            tag: `${currentOrigin.name} → ${currentDest.name}`,
            distanceNM: r.metrics.distance_nm,
            transitDays: r.metrics.duration_days,
            durationDays: r.metrics.duration_days,
            durationHours: r.metrics.duration_hours,
            estimatedFuelMT: r.metrics.estimated_fuel_mt,
            meanRisk: r.metrics.mean_risk,
            maxRisk: r.metrics.max_risk,
            medianRisk: r.metrics.mean_risk,
            p95Risk: r.metrics.max_risk,
            seaIceExposurePct: r.metrics.sea_ice_exposure_percent || 0.0,
            icebergRiskIndex: Math.round(r.metrics.iceberg_hazard_exposure * 100),
            weatherSeverityScore: 25,
            confidence: 'HIGH',
            color: color,
            waypoints: waypoints,
            explanation: r.explanation,
            segments: r.segments || [],
            cells: r.cells || []
          };
        });

        // Update MissionContext so AntarcticMap visualizes the dynamic routes immediately with the same colors!
        setRoutes(formatted);
        setCustomOriginDest({
          origin: { name: currentOrigin.name, coords: currentOrigin.coords },
          dest: { name: currentDest.name, coords: currentDest.coords }
        });

        const activeMatch = formatted.find((f) => f.objective === activeObjective) || formatted[0];
        setSelectedRouteId(activeMatch.id);
      }
    } catch (err: any) {
      console.error('Error planning dynamic voyage:', err);
      setError(err?.message || 'Failed to calculate dynamic route. Check backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSwapStations = () => {
    if (isCustomOrigin || isCustomDest) {
      const prevOrigLat = customOriginLat;
      const prevOrigLon = customOriginLon;
      setCustomOriginLat(customDestLat);
      setCustomOriginLon(customDestLon);
      setCustomDestLat(prevOrigLat);
      setCustomDestLon(prevOrigLon);
    } else {
      const prevO = originStationId;
      setOriginStationId(destStationId);
      setDestStationId(prevO);
    }
  };

  const handleResetToCanonical = () => {
    resetToCanonicalRoutes();
    setLastResponse(null);
    setHasCalculated(false);
    setError(null);
  };

  const activeRoute = useMemo(() => {
    if (!lastResponse || !lastResponse.routes) return null;
    return lastResponse.routes.find((r) => r.objective === activeObjective) ||
           lastResponse.routes.find((r) => r.objective.toLowerCase() === selectedRouteId) ||
           lastResponse.routes[0];
  }, [lastResponse, activeObjective, selectedRouteId]);

  if (!isOpen) return null;

  const isLight = theme === 'light';

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        left: '12px',
        bottom: '60px',
        width: '490px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 55,
        background: isLight ? 'rgba(255, 255, 255, 0.96)' : '#0d1117',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        border: isLight ? '1px solid #bfdbfe' : '1px solid #30363d',
        borderRadius: '10px',
        boxShadow: isLight
          ? '0 24px 56px rgba(14, 116, 144, 0.2), 0 4px 16px rgba(0, 0, 0, 0.08)'
          : '0 24px 56px rgba(0, 0, 0, 0.75)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        color: isLight ? '#0f172a' : '#f0f6fc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Window Header */}
      <div
        style={{
          padding: '12px 16px',
          background: isLight ? 'linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%)' : '#161b22',
          borderBottom: isLight ? '1px solid #bfdbfe' : '1px solid #21262d',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: isLight ? 'rgba(22, 163, 74, 0.15)' : 'rgba(35, 134, 54, 0.2)',
              border: `1px solid ${isLight ? '#16a34a' : '#238636'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Navigation size={18} color={isLight ? '#16a34a' : '#3fb950'} />
          </div>
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: isLight ? '#0f172a' : '#f0f6fc', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>Dynamic Voyage Planner</span>
              <span style={{ fontSize: '9px', background: isLight ? '#dcfce7' : '#23863633', color: isLight ? '#15803d' : '#7ee787', padding: '1px 6px', borderRadius: '4px', fontWeight: 800 }}>
                LIVE ENGINE
              </span>
            </div>
            <div style={{ fontSize: '11px', color: isLight ? '#64748b' : '#8b949e' }}>
              POST /api/v1/routes/plan-voyage · Dynamic physics routing
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: isLight ? '#64748b' : '#8b949e',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px'
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Window Scrollable Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Station Selection Box */}
        <div style={{ background: isLight ? '#f8fafc' : '#161b22', border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`, borderRadius: '8px', padding: '12px' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: isLight ? '#0284c7' : '#8b949e', fontWeight: 700, marginBottom: '10px', display: 'flex', justifyContent: 'space-between' }}>
            <span>Voyage Terminus Points</span>
            <button
              onClick={handleSwapStations}
              style={{ background: 'transparent', border: 'none', color: isLight ? '#0284c7' : '#58a6ff', fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}
            >
              <ArrowLeftRight size={12} /> Swap
            </button>
          </div>

          {/* Departure Station */}
          <div style={{ marginBottom: '10px' }}>
            <label style={{ fontSize: '11px', color: isLight ? '#0f172a' : '#c9d1d9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }}></span>
              Starting Station / Departure Port:
            </label>
            {!isCustomOrigin ? (
              <select
                value={originStationId}
                onChange={(e) => {
                  if (e.target.value === 'CUSTOM') setIsCustomOrigin(true);
                  else setOriginStationId(e.target.value);
                }}
                style={{ width: '100%', background: isLight ? '#ffffff' : '#161b22', border: `1px solid ${isLight ? '#cbd5e1' : '#30363d'}`, color: isLight ? '#0f172a' : '#f0f6fc', padding: '8px 10px', borderRadius: '6px', fontSize: '12px', outline: 'none' }}
              >
                {gatewayStations.length > 0 && (
                  <optgroup label="Gateways & Ports" style={{ background: isLight ? '#f0f9ff' : '#161b22', color: isLight ? '#0284c7' : '#58a6ff', fontWeight: 'bold' }}>
                    {gatewayStations.map((s) => (
                      <option key={s.id} value={s.id} style={{ background: isLight ? '#ffffff' : '#0d1117', color: isLight ? '#0f172a' : '#f0f6fc' }}>
                        {s.name} {s.country ? `(${s.country})` : ''}
                      </option>
                    ))}
                  </optgroup>
                )}
                {antarcticStations.length > 0 && (
                  <optgroup label="Antarctic Research Bases" style={{ background: isLight ? '#f0fdf4' : '#161b22', color: isLight ? '#16a34a' : '#7ee787', fontWeight: 'bold' }}>
                    {antarcticStations.map((s) => (
                      <option key={s.id} value={s.id} style={{ background: isLight ? '#ffffff' : '#0d1117', color: isLight ? '#0f172a' : '#f0f6fc' }}>
                        {s.name}
                      </option>
                    ))}
                  </optgroup>
                )}
                {gatewayStations.length === 0 && antarcticStations.length === 0 && stations.map((s) => (
                  <option key={s.id} value={s.id} style={{ background: isLight ? '#ffffff' : '#0d1117', color: isLight ? '#0f172a' : '#f0f6fc' }}>
                    {s.name} {s.country ? `(${s.country})` : ''}
                  </option>
                ))}
                <option value="CUSTOM" style={{ background: isLight ? '#eff6ff' : '#21262d', color: isLight ? '#0284c7' : '#58a6ff', fontWeight: 'bold' }}>
                  📍 Custom Coordinates (Lat, Lon)...
                </option>
              </select>
            ) : (
              <div style={{ display: 'flex', gap: '6px' }}>
                <input
                  type="number"
                  step="0.01"
                  placeholder="Lat (e.g. -33.92)"
                  value={customOriginLat}
                  onChange={(e) => setCustomOriginLat(parseFloat(e.target.value) || 0)}
                  style={{ flex: 1, background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#0284c7' : '#388bfd'}`, color: isLight ? '#0f172a' : '#f0f6fc', padding: '6px 8px', borderRadius: '4px', fontSize: '11.5px' }}
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="Lon (e.g. 18.42)"
                  value={customOriginLon}
                  onChange={(e) => setCustomOriginLon(parseFloat(e.target.value) || 0)}
                  style={{ flex: 1, background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#0284c7' : '#388bfd'}`, color: isLight ? '#0f172a' : '#f0f6fc', padding: '6px 8px', borderRadius: '4px', fontSize: '11.5px' }}
                />
                <button
                  onClick={() => setIsCustomOrigin(false)}
                  style={{ padding: '6px 10px', background: isLight ? '#e2e8f0' : '#21262d', border: `1px solid ${isLight ? '#cbd5e1' : '#30363d'}`, color: isLight ? '#475569' : '#8b949e', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
                >
                  List
                </button>
              </div>
            )}
          </div>

          {/* Destination Station */}
          <div style={{ marginBottom: '12px' }}>
            <label style={{ fontSize: '11px', color: isLight ? '#0f172a' : '#c9d1d9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>
              Ending Destination Station:
            </label>
            {!isCustomDest ? (
              <select
                value={destStationId}
                onChange={(e) => {
                  if (e.target.value === 'CUSTOM') setIsCustomDest(true);
                  else setDestStationId(e.target.value);
                }}
                style={{ width: '100%', background: isLight ? '#ffffff' : '#161b22', border: `1px solid ${isLight ? '#cbd5e1' : '#30363d'}`, color: isLight ? '#0f172a' : '#f0f6fc', padding: '8px 10px', borderRadius: '6px', fontSize: '12px', outline: 'none' }}
              >
                {antarcticStations.length > 0 && (
                  <optgroup label="Antarctic Research Bases" style={{ background: isLight ? '#f0fdf4' : '#161b22', color: isLight ? '#16a34a' : '#7ee787', fontWeight: 'bold' }}>
                    {antarcticStations.map((s) => (
                      <option key={s.id} value={s.id} style={{ background: isLight ? '#ffffff' : '#0d1117', color: isLight ? '#0f172a' : '#f0f6fc' }}>
                        {s.name}
                      </option>
                    ))}
                  </optgroup>
                )}
                {gatewayStations.length > 0 && (
                  <optgroup label="Gateways & Ports" style={{ background: isLight ? '#f0f9ff' : '#161b22', color: isLight ? '#0284c7' : '#58a6ff', fontWeight: 'bold' }}>
                    {gatewayStations.map((s) => (
                      <option key={s.id} value={s.id} style={{ background: isLight ? '#ffffff' : '#0d1117', color: isLight ? '#0f172a' : '#f0f6fc' }}>
                        {s.name} {s.country ? `(${s.country})` : ''}
                      </option>
                    ))}
                  </optgroup>
                )}
                {gatewayStations.length === 0 && antarcticStations.length === 0 && stations.map((s) => (
                  <option key={s.id} value={s.id} style={{ background: isLight ? '#ffffff' : '#0d1117', color: isLight ? '#0f172a' : '#f0f6fc' }}>
                    {s.name} {s.country ? `(${s.country})` : ''}
                  </option>
                ))}
                <option value="CUSTOM" style={{ background: isLight ? '#eff6ff' : '#21262d', color: '#dc2626', fontWeight: 'bold' }}>
                  📍 Custom Coordinates (Lat, Lon)...
                </option>
              </select>
            ) : (
              <div style={{ display: 'flex', gap: '6px' }}>
                <input
                  type="number"
                  step="0.01"
                  placeholder="Lat (e.g. -69.40)"
                  value={customDestLat}
                  onChange={(e) => setCustomDestLat(parseFloat(e.target.value) || 0)}
                  style={{ flex: 1, background: isLight ? '#ffffff' : '#0d1117', border: '1px solid #ef4444', color: isLight ? '#0f172a' : '#f0f6fc', padding: '6px 8px', borderRadius: '4px', fontSize: '11.5px' }}
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="Lon (e.g. 76.19)"
                  value={customDestLon}
                  onChange={(e) => setCustomDestLon(parseFloat(e.target.value) || 0)}
                  style={{ flex: 1, background: isLight ? '#ffffff' : '#0d1117', border: '1px solid #ef4444', color: isLight ? '#0f172a' : '#f0f6fc', padding: '6px 8px', borderRadius: '4px', fontSize: '11.5px' }}
                />
                <button
                  onClick={() => setIsCustomDest(false)}
                  style={{ padding: '6px 10px', background: isLight ? '#e2e8f0' : '#21262d', border: `1px solid ${isLight ? '#cbd5e1' : '#30363d'}`, color: isLight ? '#475569' : '#8b949e', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
                >
                  List
                </button>
              </div>
            )}
          </div>

          {/* Vessel & Date Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
            <div>
              <label style={{ fontSize: '10.5px', color: isLight ? '#475569' : '#8b949e', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
                Vessel Profile
              </label>
              <select
                value={vesselId}
                onChange={(e) => setVesselId(e.target.value)}
                style={{ width: '100%', background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#cbd5e1' : '#30363d'}`, color: isLight ? '#0f172a' : '#f0f6fc', padding: '6px', borderRadius: '5px', fontSize: '11.5px' }}
              >
                <option value="sagar-kanya">ORV Sagar Kanya (9.0 kn)</option>
                <option value="sagar-nidhi">ORV Sagar Nidhi (12.0 kn)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '10.5px', color: isLight ? '#475569' : '#8b949e', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
                Departure Date
              </label>
              <input
                type="date"
                value={departureDate}
                onChange={(e) => setDepartureDate(e.target.value)}
                style={{ width: '100%', background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#cbd5e1' : '#30363d'}`, color: isLight ? '#0f172a' : '#f0f6fc', padding: '5px', borderRadius: '5px', fontSize: '11.5px' }}
              />
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={handleCalculateRoute}
            disabled={isLoading}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '9px',
              background: isLoading ? (isLight ? '#93c5fd' : '#1f6feb88') : '#16a34a',
              border: '1px solid #15803d',
              borderRadius: '6px',
              color: '#ffffff',
              fontSize: '13px',
              fontWeight: 700,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {isLoading ? <RotateCw size={15} className="animate-spin" /> : <Sparkles size={15} />}
            <span>{isLoading ? 'Executing Backend Algorithm...' : 'Calculate Dynamic Route'}</span>
          </button>
        </div>

        {/* Error Notification if any */}
        {error && (
          <div style={{ background: isLight ? '#fee2e2' : 'rgba(248, 81, 73, 0.15)', border: '1px solid #ef4444', borderRadius: '6px', padding: '10px 12px', color: '#b91c1c', fontSize: '11.5px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Dynamically Generated Telemetry Results */}
        {activeRoute && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            
            {/* Multi-Objective Tabs */}
            <div>
              <div style={{ fontSize: '10.5px', textTransform: 'uppercase', letterSpacing: '0.5px', color: isLight ? '#0284c7' : '#8b949e', fontWeight: 700, marginBottom: '6px' }}>
                Multi-Objective Alternatives
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '4px' }}>
                {['FASTEST', 'SAFEST', 'SHORTEST', 'FUEL_EFFICIENT', 'BALANCED'].map((obj) => {
                  const isSelected = activeObjective === obj;
                  const color = OBJECTIVE_COLOR_MAP[obj] || '#3b82f6';
                  return (
                    <button
                      key={obj}
                      onClick={() => {
                        setActiveObjective(obj);
                        setSelectedRouteId(obj.toLowerCase());
                      }}
                      style={{
                        padding: '6px 2px',
                        background: isSelected ? (isLight ? '#eff6ff' : `${color}22`) : (isLight ? '#ffffff' : '#161b22'),
                        border: `1px solid ${isSelected ? color : (isLight ? '#cbd5e1' : '#30363d')}`,
                        borderRadius: '5px',
                        color: isSelected ? color : (isLight ? '#64748b' : '#8b949e'),
                        fontSize: '10px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        textAlign: 'center'
                      }}
                    >
                      {obj.slice(0, 4)}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Dynamic Metric Scoreboard */}
            <div style={{ background: isLight ? '#f8fafc' : '#161b22', border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`, borderRadius: '8px', padding: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: OBJECTIVE_COLOR_MAP[activeRoute.objective] || '#3b82f6' }}>
                  {OBJECTIVE_LABELS[activeRoute.objective] || activeRoute.objective}
                </span>
                <span style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>
                  {currentOrigin.name} → {currentDest.name}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                <div style={{ background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#e2e8f0' : '#21262d'}`, borderRadius: '6px', padding: '8px' }}>
                  <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Compass size={12} color={isLight ? '#0284c7' : '#58a6ff'} /> Distance
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                    {activeRoute.metrics.distance_nm.toLocaleString()} <span style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>NM</span>
                  </div>
                </div>

                <div style={{ background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#e2e8f0' : '#21262d'}`, borderRadius: '6px', padding: '8px' }}>
                  <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} color="#d97706" /> Transit Duration
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                    {activeRoute.metrics.duration_days.toFixed(1)} <span style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>Days</span>
                  </div>
                </div>

                <div style={{ background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#e2e8f0' : '#21262d'}`, borderRadius: '6px', padding: '8px' }}>
                  <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Droplets size={12} color="#9333ea" /> Fuel Consumption
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: isLight ? '#0f172a' : '#f0f6fc' }}>
                    {activeRoute.metrics.estimated_fuel_mt.toFixed(1)} <span style={{ fontSize: '10px', color: isLight ? '#64748b' : '#8b949e' }}>MT</span>
                  </div>
                </div>

                <div style={{ background: isLight ? '#ffffff' : '#0d1117', border: `1px solid ${isLight ? '#e2e8f0' : '#21262d'}`, borderRadius: '6px', padding: '8px' }}>
                  <div style={{ color: isLight ? '#64748b' : '#8b949e', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldAlert size={12} color="#16a34a" /> Mean Risk Score
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: activeRoute.metrics.mean_risk > 0.35 ? '#dc2626' : '#16a34a' }}>
                    {activeRoute.metrics.mean_risk.toFixed(3)}
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '10.5px', color: isLight ? '#475569' : '#8b949e', lineHeight: 1.35, fontStyle: 'italic' }}>
                {activeRoute.explanation}
              </div>
            </div>

            {/* Turn-by-Turn Waypoints Table */}
            <div style={{ background: isLight ? '#f8fafc' : '#161b22', border: `1px solid ${isLight ? '#bfdbfe' : '#30363d'}`, borderRadius: '8px', padding: '10px', maxHeight: '200px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ fontSize: '10.5px', textTransform: 'uppercase', letterSpacing: '0.5px', color: isLight ? '#0284c7' : '#8b949e', fontWeight: 700, marginBottom: '6px' }}>
                Dynamically Generated Waypoints ({activeRoute.waypoints.length})
              </div>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '10.5px', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${isLight ? '#e2e8f0' : '#21262d'}`, color: isLight ? '#475569' : '#8b949e' }}>
                      <th style={{ padding: '4px 6px' }}>#</th>
                      <th style={{ padding: '4px 6px' }}>Coordinates</th>
                      <th style={{ padding: '4px 6px' }}>Speed</th>
                      <th style={{ padding: '4px 6px' }}>SIC %</th>
                      <th style={{ padding: '4px 6px' }}>Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeRoute.waypoints.map((wp: DynamicWaypoint, idx: number) => {
                      const pt = wp.point || wp.position;
                      return (
                        <tr key={idx} style={{ borderBottom: `1px solid ${isLight ? '#e2e8f0' : '#21262d'}` }}>
                          <td style={{ padding: '4px 6px', color: isLight ? '#64748b' : '#8b949e' }}>{wp.sequence}</td>
                          <td style={{ padding: '4px 6px', fontFamily: 'monospace', color: isLight ? '#0f172a' : '#f0f6fc' }}>
                            {pt ? `${pt.latitude.toFixed(2)}°, ${pt.longitude.toFixed(2)}°` : '—'}
                          </td>
                          <td style={{ padding: '4px 6px', color: isLight ? '#334155' : '#c9d1d9' }}>{wp.speed_knots} kn</td>
                          <td style={{ padding: '4px 6px', color: isLight ? '#334155' : '#c9d1d9' }}>{(wp.local_sic * 100).toFixed(1)}%</td>
                          <td style={{ padding: '4px 6px', color: wp.local_risk > 0.25 ? '#dc2626' : '#16a34a', fontWeight: 600 }}>
                            {wp.local_risk.toFixed(3)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Reset to Canonical Button */}
            {hasCalculated && (
              <button
                onClick={handleResetToCanonical}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  background: isLight ? '#e2e8f0' : '#21262d',
                  border: `1px solid ${isLight ? '#cbd5e1' : '#30363d'}`,
                  borderRadius: '6px',
                  color: isLight ? '#475569' : '#8b949e',
                  fontSize: '11px',
                  cursor: 'pointer'
                }}
              >
                <RotateCcw size={12} />
                <span>Reset to Canonical Routes</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DynamicVoyageWindow;

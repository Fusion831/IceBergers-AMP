import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  ViewMode,
  TimeHorizon,
  MissionConfig,
  VesselProfile,
  RouteAlternative,
  LocationData,
  InspectionData
} from '../types/mission';

import canonicalRoutesData from '../data/canonical_routes.json';
import corridorGeojsonData from '../data/corridor_geojson.json';
import environmentByHorizonData from '../data/environment_by_horizon.json';
import riskByHorizonData from '../data/risk_by_horizon.json';
import routeComparisonData from '../data/route_comparison.json';
import icebergsRawData from '../data/icebergs_all_73.json';

import displayAggregateGeojsonData from '../data/display_aggregate_h3.json';

const ROUTE_COLOR_MAP: Record<string, string> = {
  fastest: '#3b82f6',
  shortest: '#f59e0b',
  safest: '#22c55e',
  fuel_efficient: '#a855f7',
  balanced: '#14b8a6'
};

export const AVAILABLE_VESSELS: VesselProfile[] = [
  {
    id: 'sagar-kanya',
    name: 'ORV Sagar Kanya',
    iceClass: 'Open Water / Marginal Ice Zone (< 15% SIC)',
    maxIceThickness: 0.3,
    fuelCapacity: 368.05, // 433 m3 bunker capacity = 368 MT
    dailyFuelBurnCruising: 8.16, // 6.72 MT propulsion + 1.44 MT hotel load at 9.0 knots
    dailyFuelBurnIceBreaking: 14.5,
    speedOpenWater: 9.0, // Published service cruise speed 8-10 kn
    speedIce: 4.0
  },
  {
    id: 'sagar-nidhi',
    name: 'ORV Sagar Nidhi',
    iceClass: 'Ice-Class 1A (Finnish-Swedish)',
    maxIceThickness: 0.8,
    fuelCapacity: 650,
    dailyFuelBurnCruising: 12.5,
    dailyFuelBurnIceBreaking: 18.2,
    speedOpenWater: 14.5,
    speedIce: 6.0
  }
];

export const INITIAL_MISSION: MissionConfig = {
  missionName: 'Canonical NCPOR Indian Antarctic Scientific Expedition',
  expeditionId: 'NCPOR-IASE-44',
  startDate: '2024-01-01',
  endDate: '2024-03-31',
  originPort: 'Cape Town (Supply Gateway)',
  targetStations: ['Bharati Maritime Access (48h dwell)', 'Maitri Maritime Access / India Bay (72h dwell)'],
  vessel: AVAILABLE_VESSELS[0],
  priorityWeights: {
    safety: 85,
    fuelEconomy: 70,
    transitSpeed: 60,
    scienceWindow: 90
  }
};

// Format canonical routes from frozen dataset
const formattedRoutes: RouteAlternative[] = Object.values(canonicalRoutesData).map((r: any) => ({
  id: r.id,
  name: r.name,
  type: r.id as any,
  objective: r.objective || r.id.toUpperCase(),
  tag: r.tag,
  distanceNM: r.distanceNM,
  transitDays: r.transitDays,
  dwellDays: r.dwellDays || 5.0,
  durationDays: r.durationDays,
  durationHours: r.durationHours,
  estimatedFuelMT: r.estimatedFuelMT,
  meanRisk: r.meanRisk,
  maxRisk: r.maxRisk,
  medianRisk: r.meanRisk,
  p95Risk: r.maxRisk,
  seaIceExposurePct: r.meanRisk * 25.0,
  icebergRiskIndex: Math.round(r.meanRisk * 50),
  weatherSeverityScore: 35,
  confidence: 'HIGH',
  color: ROUTE_COLOR_MAP[r.id] || r.color || '#3b82f6',
  waypoints: r.waypoints,
  waypointsDetail: r.waypointsDetail,
  segments: r.segments,
  cells: r.cells,
  explanation: r.explanation,
  searchDiagnostics: r.searchDiagnostics,
  bharatiArrival: r.bharatiArrival,
  maitriArrival: r.maitriArrival,
  capeTownReturn: r.capeTownReturn,
}));

export const INITIAL_LOCATIONS: LocationData[] = [
  {
    id: 'cape-town',
    name: 'Cape Town Staging Port',
    sector: 'South Atlantic Departure Gateway',
    coords: [18.4241, -33.9249],
    operatingWindow: 'Year-Round (Gateway)',
    favorableProbability: 100,
    medianSIC: 0,
    p90SIC: 0,
    icebergExposure: 'Low',
    weatherExposureScore: 15,
    accessibilityConfidence: 'HIGH',
    transitDistanceNM: 0,
    estimatedFuelMT: 0,
    status: 'Recommended'
  },
  {
    id: 'bharati',
    name: 'Bharati Maritime Access',
    sector: 'Larsemann Hills (Prydz Bay Anchorage)',
    coords: [76.19, -69.40],
    operatingWindow: '01 Jan - 28 Feb',
    favorableProbability: 88,
    medianSIC: 8.5,
    p90SIC: 14.2,
    icebergExposure: 'Moderate',
    weatherExposureScore: 26,
    accessibilityConfidence: 'HIGH',
    transitDistanceNM: 2420,
    estimatedFuelMT: 285.0,
    status: 'Recommended'
  },
  {
    id: 'maitri',
    name: 'Maitri Maritime Access (India Bay)',
    sector: 'Princess Astrid Coast / Lazarev Sea Mooring',
    coords: [11.73, -69.95],
    operatingWindow: '10 Jan - 28 Feb',
    favorableProbability: 72,
    medianSIC: 11.4,
    p90SIC: 16.8,
    icebergExposure: 'Moderate',
    weatherExposureScore: 38,
    accessibilityConfidence: 'MEDIUM',
    transitDistanceNM: 1850,
    estimatedFuelMT: 210.0,
    status: 'Recommended'
  }
];

export const INITIAL_INSPECTION: InspectionData = {
  lat: -69.40,
  lon: 76.19,
  sectorName: 'Bharati Maritime Access Node (Prydz Bay)',
  forecastSIC: 8.4,
  iceThicknessMeters: 0.25,
  icebergCount100km2: 2,
  seaSurfaceTempC: -0.8,
  windSpeedKnots: 14.5,
  waveHeightMeters: 1.6,
  oceanCurrentSpeedKnots: 0.35,
  oceanCurrentDirDeg: 275,
  modelConfidence: 94,
  aleatoricUncertainty: 0.04,
  epistemicUncertainty: 0.02,
  featureAttributions: [
    { feature: 'Historical NSIDC G02202 Trend Baseline', contributionPct: 45, impact: 'positive' },
    { feature: 'East Antarctic Coastal Current Drift', contributionPct: 25, impact: 'positive' },
    { feature: 'Summer Insolation Seasonal Retreat', contributionPct: 20, impact: 'positive' },
    { feature: 'Katabatic Offshore Wind Forcing', contributionPct: 10, impact: 'neutral' },
  ]
};

interface MissionContextType {
  activeView: ViewMode;
  setActiveView: (view: ViewMode) => void;
  timeHorizon: TimeHorizon;
  setTimeHorizon: (horizon: TimeHorizon) => void;
  missionConfig: MissionConfig;
  setMissionConfig: React.Dispatch<React.SetStateAction<MissionConfig>>;
  vessels: VesselProfile[];
  routes: RouteAlternative[];
  selectedRouteId: string;
  setSelectedRouteId: (id: string) => void;
  selectedRoute: RouteAlternative;
  locations: LocationData[];
  selectedLocationId: string;
  setSelectedLocationId: (id: string) => void;
  inspectionPoint: InspectionData;
  setInspectionPoint: React.Dispatch<React.SetStateAction<InspectionData>>;
  activeMapLayer: 'sic' | 'icebergs' | 'risk' | 'weather';
  setActiveMapLayer: (layer: 'sic' | 'icebergs' | 'risk' | 'weather') => void;
  
  // Staged Interactive Controls
  showTrajectories: boolean;
  setShowTrajectories: React.Dispatch<React.SetStateAction<boolean>>;
  showH3Grid: boolean;
  setShowH3Grid: React.Dispatch<React.SetStateAction<boolean>>;
  showRoutes: boolean;
  setShowRoutes: React.Dispatch<React.SetStateAction<boolean>>;
  showAlternativeRoutes: boolean;
  setShowAlternativeRoutes: React.Dispatch<React.SetStateAction<boolean>>;
  isPlaying: boolean;
  setIsPlaying: React.Dispatch<React.SetStateAction<boolean>>;
  togglePlay: () => void;
  
  // Specific Inspectors
  selectedH3Cell: any | null;
  setSelectedH3Cell: (cell: any | null) => void;
  selectedSegment: any | null;
  setSelectedSegment: (segment: any | null) => void;
  selectedIceberg: any | null;
  setSelectedIceberg: (iceberg: any | null) => void;
  
  // Data Access Helpers
  corridorGeojson: any;
  displayAggregateGeojson: any;
  getCellEnvironment: (cellId: string, horizon?: string) => any | null;
  getCellRisk: (cellId: string, horizon?: string) => any | null;
  icebergsList: any[];
  routeComparison: any[];
}

const MissionContext = createContext<MissionContextType | undefined>(undefined);

export const MissionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeView, setActiveView] = useState<ViewMode>('antarctic-map');
  const [timeHorizon, setTimeHorizon] = useState<TimeHorizon>('Now');
  const [missionConfig, setMissionConfig] = useState<MissionConfig>(INITIAL_MISSION);
  const [vessels] = useState<VesselProfile[]>(AVAILABLE_VESSELS);
  const [routes] = useState<RouteAlternative[]>(formattedRoutes);
  const [selectedRouteId, setSelectedRouteId] = useState<string>('fastest');
  const [locations] = useState<LocationData[]>(INITIAL_LOCATIONS);
  const [selectedLocationId, setSelectedLocationId] = useState<string>('bharati');
  const [inspectionPoint, setInspectionPoint] = useState<InspectionData>(INITIAL_INSPECTION);
  const [activeMapLayer, setActiveMapLayer] = useState<'sic' | 'icebergs' | 'risk' | 'weather'>('sic');

  // Progressive visibility states
  const [showTrajectories, setShowTrajectories] = useState<boolean>(false);
  const [showH3Grid, setShowH3Grid] = useState<boolean>(true);
  const [showRoutes, setShowRoutes] = useState<boolean>(true);
  const [showAlternativeRoutes, setShowAlternativeRoutes] = useState<boolean>(true);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Inspector states
  const [selectedH3Cell, setSelectedH3Cell] = useState<any | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<any | null>(null);
  const [selectedIceberg, setSelectedIceberg] = useState<any | null>(null);

  const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];

  // Icebergs list from frozen dataset
  const icebergsList = (icebergsRawData as any).features || [];

  // Timeline playback loop
  const horizonsList: TimeHorizon[] = ['Now', '+1d', '+3d', '+7d', '+14d', '+30d', '+60d', '+90d'];
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setTimeHorizon((prev) => {
        const idx = horizonsList.indexOf(prev);
        const nextIdx = (idx + 1) % horizonsList.length;
        return horizonsList[nextIdx];
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const togglePlay = () => setIsPlaying((p) => !p);

  const getCellEnvironment = (cellId: string, horizon?: string) => {
    const hz = horizon || timeHorizon;
    const hzMap = (environmentByHorizonData as any)[hz];
    return hzMap ? hzMap[cellId] || null : null;
  };

  const getCellRisk = (cellId: string, horizon?: string) => {
    const hz = horizon || timeHorizon;
    const hzMap = (riskByHorizonData as any)[hz];
    return hzMap ? hzMap[cellId] || null : null;
  };

  return (
    <MissionContext.Provider
      value={{
        activeView,
        setActiveView,
        timeHorizon,
        setTimeHorizon,
        missionConfig,
        setMissionConfig,
        vessels,
        routes,
        selectedRouteId,
        setSelectedRouteId,
        selectedRoute,
        locations,
        selectedLocationId,
        setSelectedLocationId,
        inspectionPoint,
        setInspectionPoint,
        activeMapLayer,
        setActiveMapLayer,
        showTrajectories,
        setShowTrajectories,
        showH3Grid,
        setShowH3Grid,
        showRoutes,
        setShowRoutes,
        showAlternativeRoutes,
        setShowAlternativeRoutes,
        isPlaying,
        setIsPlaying,
        togglePlay,
        selectedH3Cell,
        setSelectedH3Cell,
        selectedSegment,
        setSelectedSegment,
        selectedIceberg,
        setSelectedIceberg,
        corridorGeojson: corridorGeojsonData,
        displayAggregateGeojson: displayAggregateGeojsonData,
        getCellEnvironment,
        getCellRisk,
        icebergsList,
        routeComparison: routeComparisonData,
      }}
    >
      {children}
    </MissionContext.Provider>
  );
};

export const useMission = () => {
  const context = useContext(MissionContext);
  if (!context) {
    throw new Error('useMission must be used within a MissionProvider');
  }
  return context;
};

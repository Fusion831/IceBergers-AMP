import React, { createContext, useContext, useState } from 'react';
import {
  ViewMode,
  TimeHorizon,
  MissionConfig,
  VesselProfile,
  RouteAlternative,
  LocationData,
  InspectionData
} from '../types/mission';

export const AVAILABLE_VESSELS: VesselProfile[] = [
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
  },
  {
    id: 'sagar-kanya',
    name: 'ORV Sagar Kanya',
    iceClass: 'Open Water / Marginal Ice Zone',
    maxIceThickness: 0.3,
    fuelCapacity: 500,
    dailyFuelBurnCruising: 10.8,
    dailyFuelBurnIceBreaking: 14.5,
    speedOpenWater: 13.0,
    speedIce: 4.2
  },
  {
    id: 'chartered-icebreaker',
    name: 'Chartered Polar Icebreaker (PC-3)',
    iceClass: 'IACS Polar Class 3 (Year-round second-year ice)',
    maxIceThickness: 2.2,
    fuelCapacity: 1400,
    dailyFuelBurnCruising: 19.5,
    dailyFuelBurnIceBreaking: 32.0,
    speedOpenWater: 16.0,
    speedIce: 9.5
  }
];

export const INITIAL_MISSION: MissionConfig = {
  missionName: '44th Indian Scientific Expedition to Antarctica',
  expeditionId: 'ISEA-44',
  startDate: '2026-12-01',
  endDate: '2027-02-28',
  originPort: 'Cape Town (Supply Gateway)',
  targetStations: ['Bharati Station', 'Maitri Station'],
  vessel: AVAILABLE_VESSELS[0],
  priorityWeights: {
    safety: 85,
    fuelEconomy: 70,
    transitSpeed: 60,
    scienceWindow: 90
  }
};

export const INITIAL_ROUTES: RouteAlternative[] = [
  {
    id: 'balanced',
    name: 'Balanced Multi-Objective Route',
    type: 'balanced',
    tag: 'Recommended',
    distanceNM: 4250,
    transitDays: 11.4,
    estimatedFuelMT: 142.5,
    seaIceExposurePct: 18.2,
    icebergRiskIndex: 22,
    weatherSeverityScore: 35,
    medianRisk: 0.24,
    p95Risk: 0.41,
    confidence: 'HIGH',
    color: '#0d9488', // Solid Teal (Balanced)
    waypoints: [
      [18.42, -33.92], // Cape Town Table Bay Port
      [18.15, -34.15], // Atlantic Ocean / Table Bay Exit Channel
      [18.25, -34.55], // West of Cape Point (Clearing Peninsula)
      [18.50, -35.20], // Deep Atlantic South of Cape of Good Hope
      [20.50, -36.60], // Ocean Corridor South of Cape Agulhas
      [25.20, -38.20], // Agulhas Retroflection Deep Water
      [34.50, -43.50], // Roaring Forties Gateway
      [44.00, -48.20], // Prince Edward Trench Deep Water
      [55.00, -53.00], // Crozet-Kerguelen ACC Jet Stream
      [66.00, -58.50], // Antarctic Divergence Transition
      [72.50, -63.00], // 60°S Polar Gateway (Iceberg Avoidance)
      [75.20, -67.00], // Prydz Bay Outer Fracture Channel
      [76.19, -69.41]  // Bharati Station Anchorage (Larsemann Hills)
    ],
    waypointsDetail: [
      { name: 'Cape Town Staging Port', coords: [18.42, -33.92], gridCellId: 'GRID-34-18', distanceFromStartNM: 0, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.5, riskScore: 5 },
      { name: 'Table Bay Oceanic Exit', coords: [18.15, -34.15], gridCellId: 'GRID-34-18', distanceFromStartNM: 22, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.5, riskScore: 8 },
      { name: 'Cape Point Oceanic Clearance', coords: [18.25, -34.55], gridCellId: 'GRID-35-18', distanceFromStartNM: 55, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.5, riskScore: 10 },
      { name: 'South of Cape of Good Hope', coords: [18.50, -35.20], gridCellId: 'GRID-35-18', distanceFromStartNM: 98, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.5, riskScore: 12 },
      { name: 'Cape Agulhas Deep Sea Corridor', coords: [20.50, -36.60], gridCellId: 'GRID-37-20', distanceFromStartNM: 210, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.5, riskScore: 14 },
      { name: 'Agulhas Retroflection Gate', coords: [25.20, -38.20], gridCellId: 'GRID-38-25', distanceFromStartNM: 480, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.8, riskScore: 16 },
      { name: 'Roaring Forties Transit', coords: [34.50, -43.50], gridCellId: 'GRID-43-34', distanceFromStartNM: 1050, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.0, riskScore: 22 },
      { name: 'Prince Edward Islands Passage', coords: [44.00, -48.20], gridCellId: 'GRID-48-44', distanceFromStartNM: 1680, segmentIceCondition: 'Open Water (0%)', speedKnots: 14.2, riskScore: 18 },
      { name: 'Crozet ACC Jet Stream Corridor', coords: [55.00, -53.00], gridCellId: 'GRID-53-55', distanceFromStartNM: 2380, segmentIceCondition: 'Open Water (0%)', speedKnots: 15.5, riskScore: 20 },
      { name: 'Antarctic Divergence Gate', coords: [66.00, -58.50], gridCellId: 'GRID-58-66', distanceFromStartNM: 3080, segmentIceCondition: 'Marginal Ice Zone (12%)', speedKnots: 12.5, riskScore: 28 },
      { name: '60°S Polar Grid Corridor', coords: [72.50, -63.00], gridCellId: 'GRID-63-72', distanceFromStartNM: 3580, segmentIceCondition: 'Marginal Ice Zone (24%)', speedKnots: 11.0, riskScore: 34 },
      { name: 'Prydz Bay Approach Lead', coords: [75.20, -67.00], gridCellId: 'GRID-67-75', distanceFromStartNM: 4050, segmentIceCondition: 'Pack Ice Fracture (36%)', speedKnots: 8.5, riskScore: 40 },
      { name: 'Bharati Station Anchorage', coords: [76.19, -69.41], gridCellId: 'GRID-69-76', distanceFromStartNM: 4250, segmentIceCondition: 'Fast Ice / Mooring Channel', speedKnots: 5.0, riskScore: 25 }
    ]
  },
  {
    id: 'safest',
    name: 'Safest Low-Ice Corridor',
    type: 'safest',
    tag: 'Maximum Safety',
    distanceNM: 4580,
    transitDays: 12.8,
    estimatedFuelMT: 158.0,
    seaIceExposurePct: 8.4,
    icebergRiskIndex: 12,
    weatherSeverityScore: 28,
    medianRisk: 0.14,
    p95Risk: 0.26,
    confidence: 'HIGH',
    color: '#1e3a8a', // Solid Dark Blue (Safest)
    waypoints: [
      [18.42, -33.92], // Cape Town
      [18.15, -34.15], // Ocean Exit
      [18.25, -34.55], // Clear Cape Point
      [18.50, -35.20], // South of Cape of Good Hope
      [20.50, -36.60], // South of Cape Agulhas
      [28.00, -39.50], // Deep Oceanic Arc
      [43.00, -44.50],
      [59.00, -49.50],
      [71.00, -55.50],
      [76.50, -61.50], // North of heavy ice belt
      [76.80, -66.50], // Direct vertical approach into Prydz Bay
      [76.19, -69.41]
    ]
  },
  {
    id: 'fastest',
    name: 'Fastest Direct Route',
    type: 'fastest',
    tag: 'Shortest Transit',
    distanceNM: 3980,
    transitDays: 10.2,
    estimatedFuelMT: 135.0,
    seaIceExposurePct: 38.6,
    icebergRiskIndex: 48,
    weatherSeverityScore: 54,
    medianRisk: 0.46,
    p95Risk: 0.72,
    confidence: 'MEDIUM',
    color: '#ea580c', // Solid Orange (Fastest)
    waypoints: [
      [18.42, -33.92],
      [18.15, -34.15],
      [18.25, -34.55],
      [18.50, -35.20],
      [20.50, -36.60],
      [30.00, -43.50],
      [42.50, -51.50],
      [54.00, -59.00],
      [66.00, -65.00],
      [76.19, -69.41]
    ]
  },
  {
    id: 'fuel',
    name: 'Fuel Optimal Ocean-Current Route',
    type: 'fuel',
    tag: 'Min Fuel',
    distanceNM: 4190,
    transitDays: 11.9,
    estimatedFuelMT: 128.4,
    seaIceExposurePct: 24.5,
    icebergRiskIndex: 30,
    weatherSeverityScore: 40,
    medianRisk: 0.31,
    p95Risk: 0.52,
    confidence: 'HIGH',
    color: '#ea580c', // Solid Orange
    waypoints: [
      [18.42, -33.92],
      [18.15, -34.15],
      [18.25, -34.55],
      [18.50, -35.20],
      [20.50, -36.60],
      [27.50, -40.00],
      [40.00, -46.50],
      [52.50, -52.00],
      [64.50, -57.50],
      [74.00, -64.00],
      [76.19, -69.41]
    ]
  }
];

export const INITIAL_LOCATIONS: LocationData[] = [
  {
    id: 'bharati',
    name: 'Bharati Station',
    sector: 'Larsemann Hills (Prydz Bay Anchorage)',
    coords: [76.19, -69.41],
    operatingWindow: '05 Dec - 20 Jan',
    favorableProbability: 88,
    medianSIC: 32,
    p90SIC: 48,
    icebergExposure: 'Low',
    weatherExposureScore: 26,
    accessibilityConfidence: 'HIGH',
    transitDistanceNM: 4250,
    estimatedFuelMT: 142.5,
    status: 'Recommended'
  },
  {
    id: 'maitri',
    name: 'Maitri Gateway (India Bay)',
    sector: 'Princess Astrid Coast / Lazarev Sea Mooring',
    coords: [11.73, -69.95], // Coast ice shelf mooring
    operatingWindow: '15 Jan - 28 Feb',
    favorableProbability: 64,
    medianSIC: 58,
    p90SIC: 82,
    icebergExposure: 'Moderate',
    weatherExposureScore: 48,
    accessibilityConfidence: 'MEDIUM',
    transitDistanceNM: 4810,
    estimatedFuelMT: 168.0,
    status: 'Caution'
  },
  {
    id: 'prince-olav',
    name: 'Crown Prince Olav Coast (Site C)',
    sector: 'Enderby Land Coastal Approach',
    coords: [44.50, -67.80],
    operatingWindow: '20 Dec - 10 Feb',
    favorableProbability: 76,
    medianSIC: 41,
    p90SIC: 63,
    icebergExposure: 'Low',
    weatherExposureScore: 36,
    accessibilityConfidence: 'HIGH',
    transitDistanceNM: 4420,
    estimatedFuelMT: 151.0,
    status: 'Recommended'
  },
  {
    id: 'amery',
    name: 'Amery Ice Shelf Edge (Site D)',
    sector: 'Prydz Bay Inner Lead',
    coords: [71.50, -68.50],
    operatingWindow: '10 Jan - 15 Feb',
    favorableProbability: 52,
    medianSIC: 69,
    p90SIC: 91,
    icebergExposure: 'High',
    weatherExposureScore: 62,
    accessibilityConfidence: 'LOW',
    transitDistanceNM: 4380,
    estimatedFuelMT: 174.0,
    status: 'Unfavorable'
  }
];

export const INITIAL_INSPECTION: InspectionData = {
  lat: -68.45,
  lon: 74.20,
  sectorName: 'Prydz Bay Approach Channel (68°27\'S, 74°12\'E)',
  forecastSIC: 34.2,
  iceThicknessMeters: 0.65,
  icebergCount100km2: 3,
  seaSurfaceTempC: -1.2,
  windSpeedKnots: 18.5,
  waveHeightMeters: 1.8,
  oceanCurrentSpeedKnots: 0.45,
  oceanCurrentDirDeg: 245,
  modelConfidence: 89,
  aleatoricUncertainty: 0.08,
  epistemicUncertainty: 0.04,
  featureAttributions: [
    { feature: 'Satellite Passive Microwave (AMSR2/SSMIS)', contributionPct: 42, impact: 'positive' },
    { feature: 'Geostrophic Ocean Surface Currents (CMEMS)', contributionPct: 24, impact: 'positive' },
    { feature: '10m Surface Wind Forcing (ERA5/GFS)', contributionPct: 18, impact: 'negative' },
    { feature: 'Sea Surface Temperature Anomalies (OSTIA)', contributionPct: 10, impact: 'positive' },
    { feature: 'Historical Climatological Baseline', contributionPct: 6, impact: 'neutral' }
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
  locations: LocationData[];
  selectedLocationId: string;
  setSelectedLocationId: (id: string) => void;
  inspectionPoint: InspectionData;
  setInspectionPoint: React.Dispatch<React.SetStateAction<InspectionData>>;
  activeMapLayer: 'sic' | 'icebergs' | 'risk' | 'weather';
  setActiveMapLayer: (layer: 'sic' | 'icebergs' | 'risk' | 'weather') => void;
}

const MissionContext = createContext<MissionContextType | undefined>(undefined);

export const MissionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeView, setActiveView] = useState<ViewMode>('antarctic-map');
  const [timeHorizon, setTimeHorizon] = useState<TimeHorizon>('+7d');
  const [missionConfig, setMissionConfig] = useState<MissionConfig>(INITIAL_MISSION);
  const [vessels] = useState<VesselProfile[]>(AVAILABLE_VESSELS);
  const [routes] = useState<RouteAlternative[]>(INITIAL_ROUTES);
  const [selectedRouteId, setSelectedRouteId] = useState<string>('balanced');
  const [locations] = useState<LocationData[]>(INITIAL_LOCATIONS);
  const [selectedLocationId, setSelectedLocationId] = useState<string>('bharati');
  const [inspectionPoint, setInspectionPoint] = useState<InspectionData>(INITIAL_INSPECTION);
  const [activeMapLayer, setActiveMapLayer] = useState<'sic' | 'icebergs' | 'risk' | 'weather'>('sic');

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
        locations,
        selectedLocationId,
        setSelectedLocationId,
        inspectionPoint,
        setInspectionPoint,
        activeMapLayer,
        setActiveMapLayer
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

export type ViewMode =
  | 'mission-setup'
  | 'antarctic-map'
  | 'environmental-timeline'
  | 'location-comparison'
  | 'route-comparison'
  | 'prediction-inspector';

export type TimeHorizon = 'Now' | '+1d' | '+3d' | '+7d' | '+14d' | '+30d' | '+60d' | '+90d';

export interface VesselProfile {
  id: string;
  name: string;
  iceClass: string;
  maxIceThickness: number; // in meters
  fuelCapacity: number; // metric tons
  dailyFuelBurnCruising: number; // metric tons / day
  dailyFuelBurnIceBreaking: number; // metric tons / day
  speedOpenWater: number; // knots
  speedIce: number; // knots
}

export interface MissionConfig {
  missionName: string;
  expeditionId: string;
  startDate: string;
  endDate: string;
  originPort: string;
  targetStations: string[];
  vessel: VesselProfile;
  priorityWeights: {
    safety: number; // 0-100
    fuelEconomy: number; // 0-100
    transitSpeed: number; // 0-100
    scienceWindow: number; // 0-100
  };
}

export interface RouteWaypoint {
  name: string;
  coords: [number, number]; // [lon, lat]
  gridCellId: string;
  distanceFromStartNM: number;
  segmentIceCondition: string;
  speedKnots: number;
  riskScore: number;
}

export interface RouteAlternative {
  id: string;
  name: string;
  type: 'balanced' | 'safest' | 'fastest' | 'fuel';
  tag: string;
  distanceNM: number;
  transitDays: number;
  estimatedFuelMT: number;
  seaIceExposurePct: number;
  icebergRiskIndex: number; // 0-100
  weatherSeverityScore: number; // 0-100
  medianRisk: number; // 0-1
  p95Risk: number; // 0-1
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  color: string;
  waypoints: [number, number][];
  waypointsDetail?: RouteWaypoint[];
}

export interface GridCell {
  id: string;
  bounds: [[number, number], [number, number], [number, number], [number, number]]; // 4 corners
  center: [number, number];
  passable: boolean;
  sicPct: number; // 0 - 100
  iceThicknessM: number;
  icebergCount: number;
  waveHeightM: number;
  traversalCost: number; // 1.0 (ideal open water) to 10.0 (heavy pack/impassable)
  status: 'Open Water' | 'Marginal Ice' | 'Heavy Pack' | 'Land / Ice Shelf';
}

export interface LocationData {
  id: string;
  name: string;
  sector: string;
  coords: [number, number]; // [lon, lat]
  operatingWindow: string;
  favorableProbability: number; // percentage
  medianSIC: number; // percentage
  p90SIC: number; // percentage
  icebergExposure: 'Low' | 'Moderate' | 'High';
  weatherExposureScore: number; // 0-100
  accessibilityConfidence: 'HIGH' | 'MEDIUM' | 'LOW';
  transitDistanceNM: number;
  estimatedFuelMT: number;
  status: 'Recommended' | 'Caution' | 'Unfavorable';
}

export interface InspectionData {
  lat: number;
  lon: number;
  sectorName: string;
  forecastSIC: number;
  iceThicknessMeters: number;
  icebergCount100km2: number;
  seaSurfaceTempC: number;
  windSpeedKnots: number;
  waveHeightMeters: number;
  oceanCurrentSpeedKnots: number;
  oceanCurrentDirDeg: number;
  modelConfidence: number;
  aleatoricUncertainty: number;
  epistemicUncertainty: number;
  featureAttributions: {
    feature: string;
    contributionPct: number;
    impact: 'positive' | 'negative' | 'neutral';
  }[];
}

export interface StationInfo {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  country?: string;
  type?: string;
  category?: string;
  description?: string;
}

export interface DynamicWaypoint {
  sequence: number;
  point?: { latitude: number; longitude: number };
  position?: { latitude: number; longitude: number };
  speed_knots: number;
  local_sic: number;
  local_risk: number;
}

export interface DynamicRouteMetrics {
  distance_nm: number;
  duration_days: number;
  duration_hours: number;
  estimated_fuel_mt: number;
  mean_risk: number;
  max_risk: number;
  sea_ice_exposure_percent?: number;
  iceberg_hazard_exposure: number;
}

export interface DynamicRouteAlternative {
  objective: string;
  waypoints: DynamicWaypoint[];
  metrics: DynamicRouteMetrics;
  segments?: any[];
  cells?: string[];
  explanation?: string;
}

export interface DynamicVoyageResponse {
  origin: { name: string; latitude: number; longitude: number };
  destination: { name: string; latitude: number; longitude: number };
  departure_time: string;
  vessel_id: string;
  routes: DynamicRouteAlternative[];
}

export interface DynamicVoyageRequest {
  origin_station_id?: string;
  destination_station_id?: string;
  origin_coords?: [number, number];
  destination_coords?: [number, number];
  origin_name?: string;
  destination_name?: string;
  vessel_id?: string;
  departure_time?: string;
  objectives?: string[];
}

export const OBJECTIVE_COLOR_MAP: Record<string, string> = {
  FASTEST: '#3b82f6',
  SHORTEST: '#f59e0b',
  SAFEST: '#22c55e',
  FUEL_EFFICIENT: '#a855f7',
  BALANCED: '#14b8a6'
};

export const OBJECTIVE_LABELS: Record<string, string> = {
  FASTEST: 'Fastest Corridor',
  SHORTEST: 'Shortest Geodesic',
  SAFEST: 'Safest Margin',
  FUEL_EFFICIENT: 'Fuel Economical',
  BALANCED: 'Balanced Pareto'
};

export const PRESET_STATIONS: StationInfo[] = [
  { id: 'cape-town', name: 'Cape Town Gateway Port', latitude: -33.9249, longitude: 18.4241, country: 'South Africa', type: 'Gateway Port', category: 'Gateway Port' },
  { id: 'bharati', name: 'Bharati Station (Larsemann Hills)', latitude: -69.4072, longitude: 76.1911, country: 'India', type: 'Antarctic Base', category: 'Antarctic Station' },
  { id: 'maitri', name: 'Maitri Station (India Bay Access)', latitude: -69.9500, longitude: 11.7300, country: 'India', type: 'Antarctic Base', category: 'Antarctic Station' },
  { id: 'hobart', name: 'Hobart Gateway Port', latitude: -42.8821, longitude: 147.3272, country: 'Australia', type: 'Gateway Port', category: 'Gateway Port' },
  { id: 'fremantle', name: 'Fremantle / Perth Gateway', latitude: -32.0569, longitude: 115.7439, country: 'Australia', type: 'Gateway Port', category: 'Gateway Port' },
  { id: 'punta-arenas', name: 'Punta Arenas Gateway', latitude: -53.1638, longitude: -70.9171, country: 'Chile', type: 'Gateway Port', category: 'Gateway Port' },
  { id: 'ushuaia', name: 'Ushuaia Gateway', latitude: -54.8019, longitude: -68.303, country: 'Argentina', type: 'Gateway Port', category: 'Gateway Port' },
  { id: 'christchurch', name: 'Christchurch / Lyttelton Gateway', latitude: -43.6038, longitude: 172.7194, country: 'New Zealand', type: 'Gateway Port', category: 'Gateway Port' },
  { id: 'mcmurdo', name: 'McMurdo Station (Ross Island)', latitude: -77.8419, longitude: 166.6863, country: 'USA', type: 'Antarctic Base', category: 'Antarctic Station' },
  { id: 'casey', name: 'Casey Station (Vincennes Bay)', latitude: -66.2822, longitude: 110.5276, country: 'Australia', type: 'Antarctic Base', category: 'Antarctic Station' },
  { id: 'davis', name: 'Davis Station (Vestfold Hills)', latitude: -68.5764, longitude: 77.9672, country: 'Australia', type: 'Antarctic Base', category: 'Antarctic Station' },
  { id: 'mawson', name: 'Mawson Station (Holme Bay)', latitude: -67.6044, longitude: 62.8739, country: 'Australia', type: 'Antarctic Base', category: 'Antarctic Station' },
  { id: 'troll', name: 'Troll Station (Crown Bay Access)', latitude: -69.8500, longitude: 2.535, country: 'Norway', type: 'Antarctic Base', category: 'Antarctic Station' },
  { id: 'neumayer', name: 'Neumayer Station III (Ekström Ice Shelf)', latitude: -70.6744, longitude: -8.2742, country: 'Germany', type: 'Antarctic Base', category: 'Antarctic Station' }
];

export async function fetchAvailableStations(): Promise<StationInfo[]> {
  try {
    const res = await fetch('/api/v1/routes/stations');
    if (!res.ok) {
      console.warn('Failed to fetch stations from API, using defaults');
      return PRESET_STATIONS;
    }
    const data = await res.json();
    return data.stations || PRESET_STATIONS;
  } catch (err) {
    console.warn('Station fetch error, falling back to presets:', err);
    return PRESET_STATIONS;
  }
}

export async function planDynamicVoyage(request: DynamicVoyageRequest): Promise<DynamicVoyageResponse> {
  const res = await fetch('/api/v1/routes/plan-voyage', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Unknown network error' }));
    throw new Error(errorData.detail || `Routing error: ${res.statusText}`);
  }

  return await res.json();
}

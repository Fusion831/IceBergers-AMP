export interface AntarcticStation {
  id: string;
  name: string;
  shortName: string;
  country: string;
  countryCode: string;
  coords: [number, number]; // [lon, lat]
  type: 'indian_station' | 'antarctic_station' | 'gateway_port' | 'historic_base';
  category: string;
  symbol: string;
  color: string;
  description: string;
}

export const ANTARCTIC_STATIONS: AntarcticStation[] = [
  // 1. Indian Antarctic Expedition Bases
  {
    id: 'bharati',
    name: 'Bharati Research Station',
    shortName: 'Bharati (India)',
    country: 'India',
    countryCode: 'IN',
    coords: [76.1911, -69.4072],
    type: 'indian_station',
    category: 'Indian Antarctic Station',
    symbol: '🇮🇳',
    color: '#10b981',
    description: "India's state-of-the-art research station in Larsemann Hills, East Antarctica (active since 2012)."
  },
  {
    id: 'maitri',
    name: 'Maitri Research Station',
    shortName: 'Maitri / India Bay',
    country: 'India',
    countryCode: 'IN',
    coords: [11.7300, -69.9500],
    type: 'indian_station',
    category: 'Indian Antarctic Station',
    symbol: '🇮🇳',
    color: '#f59e0b',
    description: "India's permanent research base at Schirmacher Oasis / India Bay (active since 1989)."
  },
  {
    id: 'dakshin-gangotri',
    name: 'Dakshin Gangotri',
    shortName: 'Dakshin Gangotri (IN)',
    country: 'India',
    countryCode: 'IN',
    coords: [12.0000, -70.0900],
    type: 'historic_base',
    category: 'Historic Indian Station',
    symbol: '🏛️',
    color: '#ea580c',
    description: "India's historic first permanent Antarctic station, established during the 3rd Indian Expedition (1983)."
  },

  // 2. Gateway Departure & Logistics Ports
  {
    id: 'cape-town',
    name: 'Cape Town Gateway Port',
    shortName: 'Cape Town (Port)',
    country: 'South Africa',
    countryCode: 'ZA',
    coords: [18.4241, -33.9249],
    type: 'gateway_port',
    category: 'Gateway Logistics Port',
    symbol: '⚓',
    color: '#2563eb',
    description: 'Primary departure logistics port for Indian, German, and Scandinavian Antarctic expeditions.'
  },
  {
    id: 'hobart',
    name: 'Hobart Gateway Port',
    shortName: 'Hobart (Port)',
    country: 'Australia',
    countryCode: 'AU',
    coords: [147.3272, -42.8821],
    type: 'gateway_port',
    category: 'Gateway Logistics Port',
    symbol: '⚓',
    color: '#2563eb',
    description: 'Tasmanian deepwater gateway port for French and Australian Antarctic operations.'
  },
  {
    id: 'punta-arenas',
    name: 'Punta Arenas Gateway',
    shortName: 'Punta Arenas (Port)',
    country: 'Chile',
    countryCode: 'CL',
    coords: [-70.9171, -53.1638],
    type: 'gateway_port',
    category: 'Gateway Logistics Port',
    symbol: '⚓',
    color: '#2563eb',
    description: 'Strait of Magellan gateway port for Antarctic Peninsula and South American operations.'
  },
  {
    id: 'ushuaia',
    name: 'Ushuaia Gateway',
    shortName: 'Ushuaia (Port)',
    country: 'Argentina',
    countryCode: 'AR',
    coords: [-68.3030, -54.8019],
    type: 'gateway_port',
    category: 'Gateway Logistics Port',
    symbol: '⚓',
    color: '#2563eb',
    description: 'Southernmost gateway city in Tierra del Fuego, key maritime hub for polar vessels.'
  },
  {
    id: 'christchurch',
    name: 'Christchurch / Lyttelton Port',
    shortName: 'Christchurch (Port)',
    country: 'New Zealand',
    countryCode: 'NZ',
    coords: [172.7194, -43.6038],
    type: 'gateway_port',
    category: 'Gateway Logistics Port',
    symbol: '⚓',
    color: '#2563eb',
    description: 'New Zealand gateway hub to the Ross Sea and McMurdo Sound.'
  },
  {
    id: 'fremantle',
    name: 'Fremantle / Perth Gateway',
    shortName: 'Fremantle (Port)',
    country: 'Australia',
    countryCode: 'AU',
    coords: [115.7439, -32.0569],
    type: 'gateway_port',
    category: 'Gateway Logistics Port',
    symbol: '⚓',
    color: '#2563eb',
    description: 'Western Australian port with direct Indian Ocean access to East Antarctica.'
  },

  // 3. Major International Research Stations across Antarctica
  {
    id: 'mcmurdo',
    name: 'McMurdo Station',
    shortName: 'McMurdo (USA)',
    country: 'United States',
    countryCode: 'US',
    coords: [166.6863, -77.8419],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#0284c7',
    description: 'Largest science and logistics hub in Antarctica, located on Ross Island.'
  },
  {
    id: 'amundsen-scott',
    name: 'Amundsen-Scott South Pole Station',
    shortName: 'South Pole (USA)',
    country: 'United States',
    countryCode: 'US',
    coords: [0.0000, -89.9999],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '❄️',
    color: '#0284c7',
    description: 'US scientific research station located at the geographic South Pole (2,835 m elevation).'
  },
  {
    id: 'davis',
    name: 'Davis Station',
    shortName: 'Davis (Australia)',
    country: 'Australia',
    countryCode: 'AU',
    coords: [77.9672, -68.5764],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#06b6d4',
    description: 'Australian base in the ice-free Vestfold Hills, Princess Elizabeth Land.'
  },
  {
    id: 'mawson',
    name: 'Mawson Station',
    shortName: 'Mawson (Australia)',
    country: 'Australia',
    countryCode: 'AU',
    coords: [62.8739, -67.6044],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#06b6d4',
    description: 'Oldest continuously operating Antarctic station south of the Antarctic Circle.'
  },
  {
    id: 'casey',
    name: 'Casey Station',
    shortName: 'Casey (Australia)',
    country: 'Australia',
    countryCode: 'AU',
    coords: [110.5276, -66.2822],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#06b6d4',
    description: 'Australian station on the Bailey Peninsula facing the Windmill Islands.'
  },
  {
    id: 'troll',
    name: 'Troll Station',
    shortName: 'Troll (Norway)',
    country: 'Norway',
    countryCode: 'NO',
    coords: [2.5350, -69.8500],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#38bdf8',
    description: 'Norwegian year-round research base situated in Jutulsessen, Queen Maud Land.'
  },
  {
    id: 'neumayer',
    name: 'Neumayer Station III',
    shortName: 'Neumayer III (Germany)',
    country: 'Germany',
    countryCode: 'DE',
    coords: [-8.2742, -70.6744],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#eab308',
    description: 'German research station on the Ekström Ice Shelf in Atka Bay.'
  },
  {
    id: 'syowa',
    name: 'Syowa Station',
    shortName: 'Syowa (Japan)',
    country: 'Japan',
    countryCode: 'JP',
    coords: [39.5817, -69.0069],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#ec4899',
    description: 'Japanese Antarctic research base located on East Ongul Island.'
  },
  {
    id: 'rothera',
    name: 'Rothera Research Station',
    shortName: 'Rothera (UK)',
    country: 'United Kingdom',
    countryCode: 'GB',
    coords: [-68.1250, -67.5700],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#8b5cf6',
    description: 'British Antarctic Survey principal operational center on Adelaide Island.'
  },
  {
    id: 'halley',
    name: 'Halley VI Station',
    shortName: 'Halley VI (UK)',
    country: 'United Kingdom',
    countryCode: 'GB',
    coords: [-25.5000, -75.5800],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#8b5cf6',
    description: 'British Antarctic Survey atmospheric research station on the Brunt Ice Shelf.'
  },
  {
    id: 'concordia',
    name: 'Concordia Station',
    shortName: 'Concordia (FR/IT)',
    country: 'France / Italy',
    countryCode: 'EU',
    coords: [123.3333, -75.1000],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#6366f1',
    description: 'Franco-Italian inland research facility on Dome C plateau at 3,233 m altitude.'
  },
  {
    id: 'zhongshan',
    name: 'Zhongshan Station',
    shortName: 'Zhongshan (China)',
    country: 'China',
    countryCode: 'CN',
    coords: [76.3783, -69.3733],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#ef4444',
    description: 'Chinese research station in the Larsemann Hills, Prydz Bay.'
  },
  {
    id: 'progress',
    name: 'Progress Station',
    shortName: 'Progress (Russia)',
    country: 'Russia',
    countryCode: 'RU',
    coords: [76.3861, -69.3778],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#3b82f6',
    description: 'Russian research base in the Larsemann Hills, Prydz Bay.'
  },
  {
    id: 'novolazarevskaya',
    name: 'Novolazarevskaya Station',
    shortName: 'Novolazarevskaya (RU)',
    country: 'Russia',
    countryCode: 'RU',
    coords: [11.8328, -70.7767],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#3b82f6',
    description: 'Russian Antarctic station situated in the Schirmacher Oasis.'
  },
  {
    id: 'esperanza',
    name: 'Esperanza Base',
    shortName: 'Esperanza (Argentina)',
    country: 'Argentina',
    countryCode: 'AR',
    coords: [-56.9967, -63.3967],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#0ea5e9',
    description: 'Permanent Argentine research base in Hope Bay, Trinity Peninsula.'
  },
  {
    id: 'marambio',
    name: 'Marambio Base',
    shortName: 'Marambio (Argentina)',
    country: 'Argentina',
    countryCode: 'AR',
    coords: [-56.6267, -64.2411],
    type: 'antarctic_station',
    category: 'Antarctic Research Base',
    symbol: '◆',
    color: '#0ea5e9',
    description: 'Principal Argentine air hub in Antarctica on Seymour Island.'
  }
];

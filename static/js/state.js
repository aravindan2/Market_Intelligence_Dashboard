/**
 * Application state and shared constants.
 */
export const TIMESPAN_MAP = { '1d': 1, '3d': 3, '7d': 7, '1m': 30 };

export const state = {
  timespan: '7d',
  days: 7,
  layers: {
    globalPrices: true,
    indiaSupply: false,
    refiningHubs: false,
    chokepoints: false,
    oilPorts: false,
    pipelines: false,
    productionRegions: false,
    conflicts: false,
    dayNight: false,
    cii: false,
  },
};

export const CII_COUNTRY_SCORES = {
  AF: 96, SS: 98, SO: 98, SY: 98, YE: 97, IQ: 95, LY: 92, MM: 87, SD: 94, CF: 97, CD: 97, ML: 88, NE: 91, BF: 90, TD: 91, VE: 88, NG: 90, PK: 92, ET: 93, HT: 82, ZW: 85, MW: 72, CM: 88, GN: 90, SL: 78, LR: 80, CI: 82, MR: 78, ER: 89, IR: 85, PS: 84, LB: 86, BI: 89, RW: 75, TZ: 68, KE: 72, UG: 76, CO: 75, MX: 65, GT: 72, HN: 72, SV: 68, NI: 70, PH: 78, ID: 72, TH: 68, EG: 82, DZ: 74, TN: 68, MA: 66, SA: 72, TR: 78, UA: 88, BY: 72, AZ: 75, GE: 78, AM: 76, KZ: 58, UZ: 72, TJ: 78, KG: 70, IN: 68, BD: 82, LK: 78, NP: 80, CN: 62, JP: 42, KR: 48, AU: 32, NZ: 28, US: 45, CA: 35, GB: 38, DE: 32, FR: 38, IT: 40, ES: 38, NL: 32, SE: 28, NO: 26, FI: 28, PL: 42, RU: 82, BR: 58, AR: 62, CL: 48, ZA: 64,
};

export const CII_GEOJSON_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson';

export function scaleGreenRed(t) {
  t = Math.min(1, Math.max(0, t));
  const r = Math.round(54 + (138 - 54) * t);
  const g = Math.round(180 + (31 - 180) * t);
  const b = Math.round(60 + (30 - 60) * t);
  return 'rgb(' + r + ',' + g + ',' + b + ')';
}

export const DASHBOARD_SECTIONS = [
  { id: 'section-kpis', label: 'KPIs & risk' },
  { id: 'section-oil-stocks', label: 'Oil stocks' },
  { id: 'section-signals', label: 'Signals (momentum, RL)' },
  { id: 'section-scenario', label: 'Scenario explorer' },
  { id: 'section-map', label: 'Map & layers' },
  { id: 'section-news', label: 'News' },
  { id: 'section-charts', label: 'Price & correlation charts' },
  { id: 'section-forecast', label: 'WTI forecast & sector' },
  { id: 'section-heatmap', label: 'Daily % heatmap' },
  { id: 'section-opportunities', label: 'Actionable opportunities' },
  { id: 'section-decisions', label: 'Decision framework' },
];

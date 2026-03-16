/**
 * API client for Market Intelligence backend.
 */
export const API = {
  async pricesLatest(useCache) {
    const url = '/api/prices/latest' + (useCache !== false ? '' : '?cache=false');
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async pricesHistory(days) {
    const r = await fetch('/api/prices/history?days=' + (days || 7));
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async news(limit, country) {
    let url = '/api/news?limit=' + (limit || 50);
    if (country) url += '&country=' + encodeURIComponent(country);
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    return d.items || [];
  },
  async newsCategories(limit, country) {
    let url = '/api/news?limit=' + (limit || 80) + '&categories=true';
    if (country) url += '&country=' + encodeURIComponent(country);
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    return d.categories || {};
  },
  async riskSummary() {
    const r = await fetch('/api/risk-summary');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async indiaSupplyChain() {
    const r = await fetch('/api/india-supply-chain');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async decisions() {
    const r = await fetch('/api/decisions');
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    return d.decisions || [];
  },
  async mapPrices() {
    const r = await fetch('/api/map/prices');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async mapLayers() {
    const r = await fetch('/data/map_layers.json');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async marketSignals() {
    const r = await fetch('/api/market-signals');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async priceForecast() {
    const r = await fetch('/api/price-forecast');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async rlSignals() {
    const r = await fetch('/api/rl-signals');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async opportunities() {
    const r = await fetch('/api/opportunities');
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    return d.opportunities || [];
  },
  async scenario(timespan, commodity, riskBand) {
    const params = new URLSearchParams({
      timespan: timespan || '7d',
      commodity: commodity || 'WTI Crude Oil',
      risk_band: riskBand || 'medium',
    });
    const r = await fetch('/api/scenario?' + params.toString());
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async oilStocks() {
    const r = await fetch('/api/oil-stocks');
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
};

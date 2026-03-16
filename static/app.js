(function () {
  'use strict';

  const API = {
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
      var url = '/api/news?limit=' + (limit || 50);
      if (country) url += '&country=' + encodeURIComponent(country);
      const r = await fetch(url);
      if (!r.ok) throw new Error(await r.text());
      const d = await r.json();
      return d.items || [];
    },
    async newsCategories(limit, country) {
      var url = '/api/news?limit=' + (limit || 80) + '&categories=true';
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
      const params = new URLSearchParams({ timespan: timespan || '7d', commodity: commodity || 'WTI Crude Oil', risk_band: riskBand || 'medium' });
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

  const TIMESPAN_MAP = { '1d': 1, '3d': 3, '7d': 7, '1m': 30 };
  const state = {
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
  var CII_COUNTRY_SCORES = {
    AF: 96, SS: 98, SO: 98, SY: 98, YE: 97, IQ: 95, LY: 92, MM: 87, SD: 94, CF: 97, CD: 97, ML: 88, NE: 91, BF: 90, TD: 91, VE: 88, NG: 90, PK: 92, ET: 93, HT: 82, ZW: 85, MW: 72, CM: 88, GN: 90, SL: 78, LR: 80, CI: 82, MR: 78, ER: 89, IR: 85, PS: 84, LB: 86, BI: 89, RW: 75, TZ: 68, KE: 72, UG: 76, CO: 75, MX: 65, GT: 72, HN: 72, SV: 68, NI: 70, PH: 78, ID: 72, TH: 68, EG: 82, DZ: 74, TN: 68, MA: 66, SA: 72, TR: 78, UA: 88, BY: 72, AZ: 75, GE: 78, AM: 76, KZ: 58, UZ: 72, TJ: 78, KG: 70, IN: 68, BD: 82, LK: 78, NP: 80, CN: 62, JP: 42, KR: 48, AU: 32, NZ: 28, US: 45, CA: 35, GB: 38, DE: 32, FR: 38, IT: 40, ES: 38, NL: 32, SE: 28, NO: 26, FI: 28, PL: 42, RU: 82, BR: 58, AR: 62, CL: 48, ZA: 64,
  };
  var CII_GEOJSON_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson';
  function scaleGreenRed(t) {
    t = Math.min(1, Math.max(0, t));
    var r = Math.round(54 + (138 - 54) * t);
    var g = Math.round(180 + (31 - 180) * t);
    var b = Math.round(60 + (30 - 60) * t);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }

  var WORLD_CLOCK_CITIES = [
    { city: 'Mumbai', timezone: 'Asia/Kolkata', exchange: 'NSE', open: [9, 15], close: [15, 30], highlight: true },
    { city: 'New York', timezone: 'America/New_York', exchange: 'NYSE', open: [9, 30], close: [16, 0] },
    { city: 'London', timezone: 'Europe/London', exchange: 'LSE', open: [8, 0], close: [16, 30] },
    { city: 'Dubai', timezone: 'Asia/Dubai', exchange: 'DFM', open: [10, 0], close: [14, 0] },
    { city: 'Singapore', timezone: 'Asia/Singapore', exchange: 'SGX', open: [9, 0], close: [17, 0] },
    { city: 'Bangkok', timezone: 'Asia/Bangkok', exchange: 'SET', open: [9, 45], close: [16, 30] },
    { city: 'Tokyo', timezone: 'Asia/Tokyo', exchange: 'TSE', open: [9, 0], close: [15, 0] },
    { city: 'Sydney', timezone: 'Australia/Sydney', exchange: 'ASX', open: [10, 0], close: [16, 0] },
    { city: 'Riyadh', timezone: 'Asia/Riyadh', exchange: 'Tadawul', open: [10, 0], close: [15, 0] },
    { city: 'Hong Kong', timezone: 'Asia/Hong_Kong', exchange: 'HKEX', open: [9, 30], close: [16, 0] },
    { city: 'Moscow', timezone: 'Europe/Moscow', exchange: 'MOEX', open: [10, 0], close: [18, 40] },
    { city: 'Toronto', timezone: 'America/Toronto', exchange: 'TSX', open: [9, 30], close: [16, 0] },
    { city: 'Houston', timezone: 'America/Chicago', exchange: 'NYMEX', open: [8, 0], close: [14, 30] },
  ];

  function getWorldClockRow(c) {
    var now = new Date();
    var formatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    var timeStr = formatter.format(now).replace(/\./g, ':');
    var dowFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, weekday: 'short' });
    var tzFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, timeZoneName: 'short' });
    var dow = dowFormatter.format(now);
    var tzParts = tzFormatter.formatToParts(now);
    var tzShort = '';
    tzParts.forEach(function (p) { if (p.type === 'timeZoneName') tzShort = p.value; });
    var hourFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, hour: 'numeric', hour12: false });
    var minFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, minute: 'numeric' });
    var localHour = parseInt(hourFormatter.format(now), 10);
    var localMin = parseInt(minFormatter.format(now), 10);
    var localMins = localHour * 60 + localMin;
    var openMins = c.open[0] * 60 + c.open[1];
    var closeMins = c.close[0] * 60 + c.close[1];
    var dayNum = now.toLocaleDateString('en-GB', { timeZone: c.timezone, weekday: 'long' });
    var isWeekend = dayNum === 'Saturday' || dayNum === 'Sunday';
    var isOpen = !isWeekend && localMins >= openMins && localMins < closeMins;
    var statusClass = isOpen ? 'status-open' : 'status-closed';
    var statusLabel = isOpen ? 'OPEN' : 'CLSD';
    var statusDotClass = isOpen ? 'open' : 'closed';
    return '<li class="' + (c.highlight ? 'highlight ' : '') + statusClass + '">' +
      '<div><div class="world-clock-city">' + c.city + '</div><div class="world-clock-exchange">' +
      '<span class="status-dot ' + statusDotClass + '"></span>' + c.exchange + ' ' + statusLabel + '</div></div>' +
      '<div><div class="world-clock-time">' + timeStr + '</div><div class="world-clock-meta">' + dow + ' ' + tzShort + '</div></div></li>';
  }

  var worldClockInterval = null;
  function startWorldClock() {
    var list = document.getElementById('world-clock-list');
    if (!list) return;
    function tick() {
      list.innerHTML = WORLD_CLOCK_CITIES.map(getWorldClockRow).join('');
    }
    tick();
    if (worldClockInterval) clearInterval(worldClockInterval);
    worldClockInterval = setInterval(tick, 1000);
  }
  let commandMap = null;
  let mapLayerGlobal = null;
  let mapLayerIndia = null;
  let mapLayersData = null;
  let lineChartInstance = null;
  let forecastChartInstance = null;
  let corrChartInstance = null;
  let sectorChartInstance = null;
  let priceRefreshIntervalId = null;
  let currentLoadKPIs = null;

  function updateBrandLogo() {
    var img = document.querySelector('.brand-logo');
    if (!img) return;
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    img.src = dark ? '/assets/nix-full-icon-dark.svg' : '/assets/nix-full-icon.svg';
  }

  function themeToggle() {
    const root = document.documentElement;
    const current = root.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    localStorage.setItem('market-int-theme', next);
    const btn = document.getElementById('theme-btn');
    if (btn) btn.innerHTML = next === 'dark' ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon"></i>';
    updateBrandLogo();
  }
  document.getElementById('theme-btn').addEventListener('click', themeToggle);
  if (document.documentElement.getAttribute('data-theme') === 'dark') {
    document.getElementById('theme-btn').innerHTML = '<i class="bi bi-sun"></i>';
  }
  updateBrandLogo();

  var DASHBOARD_SECTIONS = [
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
    { id: 'section-decisions', label: 'Decision framework' }
  ];

  function openSearch() {
    var overlay = document.getElementById('search-overlay');
    var input = document.getElementById('search-input');
    var list = document.getElementById('search-results');
    if (!overlay || !input || !list) return;
    var sections = DASHBOARD_SECTIONS.filter(function (s) { return document.getElementById(s.id); });
    overlay.setAttribute('aria-hidden', 'false');
    overlay.classList.add('search-open');
    input.value = '';
    list.innerHTML = sections.map(function (s) {
      return '<li class="search-result-item" data-section="' + s.id + '">' + s.label + '</li>';
    }).join('');
    list.querySelectorAll('.search-result-item').forEach(function (li) {
      li.addEventListener('click', function () {
        var id = li.getAttribute('data-section');
        var el = document.getElementById(id);
        if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
        closeSearch();
      });
    });
    input.focus();
  }

  function closeSearch() {
    var overlay = document.getElementById('search-overlay');
    var input = document.getElementById('search-input');
    if (!overlay) return;
    overlay.classList.remove('search-open');
    overlay.setAttribute('aria-hidden', 'true');
    if (input) input.blur();
  }

  function filterSearch(query) {
    var list = document.getElementById('search-results');
    if (!list) return;
    var q = (query || '').toLowerCase().trim();
    list.querySelectorAll('.search-result-item').forEach(function (li) {
      var label = (li.textContent || '').toLowerCase();
      li.style.display = !q || label.indexOf(q) >= 0 ? '' : 'none';
    });
  }

  var searchTrigger = document.getElementById('search-trigger');
  if (searchTrigger) searchTrigger.addEventListener('click', openSearch);
  var searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', function () { filterSearch(this.value); });
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { closeSearch(); e.preventDefault(); }
      if (e.key === 'Enter') {
        var items = document.querySelectorAll('#search-results .search-result-item');
        for (var i = 0; i < items.length; i++) { if (items[i].style.display !== 'none') { items[i].click(); break; } }
      }
    });
  }
  var searchOverlay = document.getElementById('search-overlay');
  if (searchOverlay) searchOverlay.addEventListener('click', function (e) {
    if (e.target === this) closeSearch();
  });
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      var ov = document.getElementById('search-overlay');
      if (ov && ov.classList.contains('search-open')) closeSearch();
      else openSearch();
    }
  });

  function renderHeaderTimespan() {
    const el = document.getElementById('header-timespan');
    if (!el) return;
    const pills = ['1d', '3d', '7d', '1m'];
    el.innerHTML = pills.map(function (p) {
      const active = state.timespan === p ? ' active' : '';
      return '<button type="button" class="timespan-pill' + active + '" data-timespan="' + p + '">' + p + '</button>';
    }).join('');
    el.querySelectorAll('.timespan-pill').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const p = btn.getAttribute('data-timespan');
        state.timespan = p;
        state.days = TIMESPAN_MAP[p] || 7;
        renderHeaderTimespan();
        refreshChartsAndClock();
      });
    });
  }

  function updateClock() {
    const el = document.getElementById('header-clock');
    if (el) el.textContent = 'Updated ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function groupNewsByCategory(items) {
    const groups = {};
    (items || []).forEach(function (item) {
      const cat = item.category || 'General';
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(item);
    });
    return groups;
  }

  function refreshChartsAndClock() {
    const body = document.getElementById('content-body');
    if (!body) return;
    const chartWrap = body.querySelector('.charts-row');
    const chartLine = body.querySelector('#chart-line');
    const chartCorr = body.querySelector('#chart-corr');
    if (!chartWrap) return;
    API.pricesHistory(state.days).then(function (history) {
      const names = Object.keys(history).filter(function (k) { return Array.isArray(history[k]) && history[k].length; });
      if (chartLine && names.length) {
        if (lineChartInstance) lineChartInstance.destroy();
        lineChartInstance = drawLineChart(chartLine, history, names);
      }
      if (chartCorr && names.length) {
        if (corrChartInstance) corrChartInstance.destroy();
        corrChartInstance = drawCorrelation(chartCorr, history, names);
      }
      updateClock();
    }).catch(function () {});
  }

  window.__renderCommandDashboard = renderCommandDashboard;
  window.__renderHeaderTimespan = renderHeaderTimespan;
  window.__updateClock = updateClock;
  bindSettingsModal();

  function sparklinePath(series, w, h) {
    if (!series || series.length < 2) return '';
    var min = Math.min.apply(null, series);
    var max = Math.max.apply(null, series);
    var range = max - min || 1;
    var n = series.length;
    var pts = series.map(function (v, i) {
      return (i / (n - 1)) * w + ',' + (h - ((v - min) / range) * h);
    });
    return 'M ' + pts.join(' L ');
  }

  function sparklineSeriesFromHistory(history, key) {
    if (key === 'Brent-WTI Spread') {
      var b = history['Brent Crude Oil'];
      var w = history['WTI Crude Oil'];
      if (!b || !w || !b.length || !w.length) return null;
      var byDate = {};
      b.forEach(function (r) { byDate[r.date] = { b: r.Close, w: null }; });
      w.forEach(function (r) {
        if (byDate[r.date]) byDate[r.date].w = r.Close;
      });
      return Object.keys(byDate).sort().map(function (d) {
        var x = byDate[d];
        return x.b != null && x.w != null ? x.b - x.w : null;
      }).filter(function (v) { return v != null; });
    }
    var arr = history[key];
    if (!arr || !arr.length) return null;
    return arr.map(function (r) { return r.Close; }).filter(function (v) { return v != null; });
  }

  const NEWS_CATEGORIES_ORDER = [
    'Petroleum & EIA', 'OPEC & Markets', 'Geopolitical',
    'Weather & Natural Risk', 'Industry & Markets', 'Macro & Demand'
  ];

  function getShellHTML() {
    var layersHtml = '<div class="map-layers-panel" id="map-layers-panel">' +
      '<div class="layers-header"><button type="button" class="layers-toggle" id="layers-toggle" aria-label="Expand/collapse layers"><span class="layers-toggle-icon">▼</span></button><span class="layers-title">LAYERS</span></div>' +
      '<div class="layers-content">' +
      '<div class="layers-select-all"><button type="button" class="layers-btn" id="layers-select-all">Select all</button><button type="button" class="layers-btn" id="layers-deselect-all">Deselect all</button></div>' +
      '<label><input type="checkbox" id="layer-global" ' + (state.layers.globalPrices ? 'checked' : '') + '> Global prices</label>' +
      '<label><input type="checkbox" id="layer-india" ' + (state.layers.indiaSupply ? 'checked' : '') + '> India supply</label>' +
      '<label><input type="checkbox" id="layer-refining" ' + (state.layers.refiningHubs ? 'checked' : '') + '> Refining hubs</label>' +
      '<label><input type="checkbox" id="layer-chokepoints" ' + (state.layers.chokepoints ? 'checked' : '') + '> Chokepoints</label>' +
      '<label><input type="checkbox" id="layer-ports" ' + (state.layers.oilPorts ? 'checked' : '') + '> Oil ports</label>' +
      '<label><input type="checkbox" id="layer-pipelines" ' + (state.layers.pipelines ? 'checked' : '') + '> Pipelines</label>' +
      '<label><input type="checkbox" id="layer-production" ' + (state.layers.productionRegions ? 'checked' : '') + '> Production regions</label>' +
      '<label><input type="checkbox" id="layer-conflicts" ' + (state.layers.conflicts ? 'checked' : '') + '> Conflicts</label>' +
      '<label><input type="checkbox" id="layer-daynight" ' + (state.layers.dayNight ? 'checked' : '') + '> Day/Night</label>' +
      '<label><input type="checkbox" id="layer-cii" ' + (state.layers.cii ? 'checked' : '') + '> CII Instability</label>' +
      '<div class="cii-scale-widget"><span class="cii-scale-label">CII SCALE</span><div class="cii-scale-bar" aria-hidden="true"></div><span class="cii-scale-value" id="cii-scale-value">1 (stable) — 100 (conflict)</span></div>' +
      '<div class="map-legend" id="map-legend"></div></div></div>';
    return '<div id="section-kpis" class="dashboard-top">' +
      '<div id="kpi-grid" class="kpi-grid"><p class="loading">Loading…</p></div>' +
      '<div id="risk-card-wrap" class="risk-card-wrap"><p class="loading">Loading…</p></div>' +
      '</div>' +
      '<div id="section-oil-stocks" class="oil-stocks-row-wrap">' +
      '<div id="oil-stocks-row" class="oil-stocks-row"><p class="loading">Loading…</p></div></div>' +
      '<div id="section-signals" class="signal-cards-wrap"><p class="loading">Loading…</p></div>' +
      '<div id="section-map" class="panel-card section-map-spaced">' +
      '<div class="map-row-wrap">' +
      '<div class="map-wrap">' +
      '<div id="command-map"></div>' + layersHtml +
      '</div>' +
      '<div class="world-clock-panel">' +
      '<div class="world-clock-title">WORLD CLOCK</div>' +
      '<ul class="world-clock-list" id="world-clock-list"></ul>' +
      '<div class="world-clock-scroll-hint">⋯</div>' +
      '</div>' +
      '</div>' +
      '</div>' +
      '<div id="section-news" class="news-categories"><p class="loading">Loading…</p></div>' +
      '<div id="section-charts" class="charts-row">' +
      '<div class="panel-card"><h3 class="kpi-label">Price (actual)</h3><div class="chart-container"><canvas id="chart-line"></canvas></div></div>' +
      '<div class="panel-card"><h3 class="kpi-label">Correlation</h3><div class="chart-container"><canvas id="chart-corr"></canvas></div></div>' +
      '</div>' +
      '<div id="section-forecast" class="charts-row">' +
      '<div class="panel-card"><h3 class="kpi-label">WTI forecast</h3><div class="chart-container"><canvas id="chart-forecast"></canvas></div></div>' +
      '<div class="panel-card"><h3 class="kpi-label">Signals by sector</h3><div class="chart-container"><canvas id="chart-sector"></canvas></div></div>' +
      '</div>' +
      '<div id="section-heatmap" class="charts-row">' +
      '<div class="panel-card full-width"><h3 class="kpi-label">Daily % change heatmap</h3><div class="chart-container heatmap-container" id="heatmap-container"></div></div>' +
      '</div>' +
      '<div id="section-opportunities" class="panel-card opportunities-panel">' +
      '<h3 class="kpi-label">Actionable opportunities</h3><div id="opportunities-content"><p class="loading">Loading…</p></div></div>' +
      '<div id="section-decisions" class="panel-card decisions-panel">' +
      '<h3 class="kpi-label">Decision framework</h3><div id="decisions-content"><p class="loading">Loading…</p></div></div>' +
      '<div id="section-scenario" class="panel-card scenario-panel">' +
      '<h3 class="kpi-label">Scenario explorer</h3>' +
      '<p class="news-meta">Try different timespan, commodity, and risk band to see resulting insights.</p>' +
      '<div class="scenario-controls">' +
      '<label>Timespan <select id="scenario-timespan"><option value="1d">1d</option><option value="3d">3d</option><option value="7d" selected>7d</option><option value="1m">1m</option></select></label>' +
      '<label>Commodity <select id="scenario-commodity"><option value="WTI Crude Oil" selected>WTI Crude Oil</option><option value="Brent Crude Oil">Brent Crude Oil</option><option value="Natural Gas">Natural Gas</option><option value="Gold">Gold</option></select></label>' +
      '<label>Risk band <select id="scenario-risk"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option></select></label>' +
      '<button type="button" class="scenario-apply-btn" id="scenario-apply">Apply</button>' +
      '</div>' +
      '<div class="scenario-result" id="scenario-result"></div>' +
      '</div>';
  }

  function bindLayersToggle() {
    var btn = document.getElementById('layers-toggle');
    var panel = document.getElementById('map-layers-panel');
    var icon = panel && panel.querySelector('.layers-toggle-icon');
    if (!btn || !panel || !icon) return;
    btn.addEventListener('click', function () {
      panel.classList.toggle('collapsed');
      icon.textContent = panel.classList.contains('collapsed') ? '\u25B6' : '\u25BC';
    });
  }

  function openCountryPanel(code, name, price) {
    var panel = document.getElementById('country-panel');
    var titleEl = document.getElementById('country-panel-title');
    var priceEl = document.getElementById('country-panel-price');
    var newsEl = document.getElementById('country-panel-news');
    if (!panel || !titleEl || !priceEl || !newsEl) return;
    titleEl.textContent = name || code || 'Country';
    priceEl.textContent = price != null ? 'Price index: $' + Number(price).toFixed(2) + '/bbl approx' : '';
    newsEl.innerHTML = '<p class="loading">Loading…</p>';
    panel.setAttribute('aria-hidden', 'false');
    API.news(30, code).then(function (items) {
      if (!items || !items.length) {
        newsEl.innerHTML = '<p class="text-muted">No news for this region.</p>';
        return;
      }
      var html = '<ul class="news-panel-list">';
      items.slice(0, 15).forEach(function (item) {
        var title = (item.title || '–').substring(0, 80) + (item.title && item.title.length > 80 ? '…' : '');
        var tags = item.tags || [];
        var sentiment = item.sentiment || 'neutral';
        var sentimentBadge = '<span class="sentiment-badge sentiment-' + sentiment + '">' + sentiment + '</span>';
        var tagChips = tags.length ? '<div class="news-tags">' + tags.slice(0, 3).map(function (t) { return '<span class="tag-chip">' + t + '</span>'; }).join('') + '</div>' : '';
        html += '<li class="news-item"><div class="news-item-head"><a href="' + (item.link || '#') + '" target="_blank" rel="noopener">' + title + '</a> ' + sentimentBadge + '</div>' + tagChips + '<div class="news-panel-meta">' + (item.source || '') + '</div></li>';
      });
      html += '</ul>';
      newsEl.innerHTML = html;
    }).catch(function () {
      newsEl.innerHTML = '<p class="error-msg">Failed to load news.</p>';
    });
  }

  function closeCountryPanel() {
    var panel = document.getElementById('country-panel');
    if (panel) panel.setAttribute('aria-hidden', 'true');
  }

  function bindCountryPanel() {
    var closeBtn = document.getElementById('country-panel-close');
    if (closeBtn) closeBtn.addEventListener('click', closeCountryPanel);
  }

  var SETTINGS_PANELS_KEY = 'market-int-visible-panels';
  var SETTINGS_REFRESH_KEY = 'market-int-refresh-interval';

  function getVisiblePanelIds() {
    try {
      var raw = localStorage.getItem(SETTINGS_PANELS_KEY);
      if (raw) {
        var arr = JSON.parse(raw);
        if (Array.isArray(arr) && arr.length) return arr;
      }
    } catch (e) {}
    return DASHBOARD_SECTIONS.map(function (s) { return s.id; });
  }

  function applyPanelVisibility() {
    var visible = getVisiblePanelIds();
    DASHBOARD_SECTIONS.forEach(function (s) {
      var el = document.getElementById(s.id);
      if (el) el.style.display = visible.indexOf(s.id) >= 0 ? '' : 'none';
    });
  }

  function savePanelVisibility(visibleIds) {
    try {
      localStorage.setItem(SETTINGS_PANELS_KEY, JSON.stringify(visibleIds));
    } catch (e) {}
    applyPanelVisibility();
  }

  function openSettingsModal() {
    var overlay = document.getElementById('settings-overlay');
    if (!overlay) return;
    var theme = document.documentElement.getAttribute('data-theme') || 'light';
    var themeRadios = document.querySelectorAll('input[name="settings-theme"]');
    themeRadios.forEach(function (r) { r.checked = r.value === theme; });
    var refreshVal = localStorage.getItem(SETTINGS_REFRESH_KEY) || '60';
    var intervalSelect = document.getElementById('settings-refresh-interval');
    if (intervalSelect) intervalSelect.value = refreshVal;
    var panelsContainer = document.getElementById('settings-panels');
    if (panelsContainer) {
      var visible = getVisiblePanelIds();
      panelsContainer.innerHTML = DASHBOARD_SECTIONS.map(function (s) {
        var checked = visible.indexOf(s.id) >= 0 ? ' checked' : '';
        return '<label><input type="checkbox" data-section="' + s.id + '"' + checked + '> ' + s.label + '</label>';
      }).join('');
      panelsContainer.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
        cb.addEventListener('change', function () {
          var vis = [];
          panelsContainer.querySelectorAll('input[type="checkbox"]:checked').forEach(function (c) {
            vis.push(c.getAttribute('data-section'));
          });
          savePanelVisibility(vis.length ? vis : DASHBOARD_SECTIONS.map(function (s) { return s.id; }));
        });
      });
    }
    overlay.setAttribute('aria-hidden', 'false');
  }

  function closeSettingsModal() {
    var overlay = document.getElementById('settings-overlay');
    if (overlay) overlay.setAttribute('aria-hidden', 'true');
  }

  function bindSettingsModal() {
    var addBtn = document.getElementById('add-btn');
    if (addBtn) addBtn.addEventListener('click', openSettingsModal);
    var closeBtn = document.getElementById('settings-close');
    if (closeBtn) closeBtn.addEventListener('click', closeSettingsModal);
    var overlay = document.getElementById('settings-overlay');
    if (overlay) overlay.addEventListener('click', function (e) { if (e.target === overlay) closeSettingsModal(); });
    var themeRadios = document.querySelectorAll('input[name="settings-theme"]');
    themeRadios.forEach(function (r) {
      r.addEventListener('change', function () {
        var val = r.value;
        document.documentElement.setAttribute('data-theme', val);
        localStorage.setItem('market-int-theme', val);
        themeToggle();
      });
    });
    var intervalSelect = document.getElementById('settings-refresh-interval');
    if (intervalSelect) {
      intervalSelect.addEventListener('change', function () {
        var val = Math.max(30, parseInt(intervalSelect.value, 10) || 60);
        localStorage.setItem(SETTINGS_REFRESH_KEY, String(val));
        if (window.__restartPriceRefresh) window.__restartPriceRefresh();
      });
    }
    var exportBtn = document.getElementById('settings-export');
    if (exportBtn) {
      exportBtn.addEventListener('click', function () {
        var theme = document.documentElement.getAttribute('data-theme') || 'light';
        var panels = getVisiblePanelIds();
        var refresh = localStorage.getItem(SETTINGS_REFRESH_KEY) || '60';
        var json = JSON.stringify({ theme: theme, panels: panels, refreshIntervalSeconds: refresh }, null, 2);
        var blob = new Blob([json], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'market-int-settings.json';
        a.click();
        URL.revokeObjectURL(a.href);
      });
    }
    var importBtn = document.getElementById('settings-import');
    var fileInput = document.getElementById('settings-file-input');
    if (importBtn && fileInput) {
      importBtn.addEventListener('click', function () { fileInput.click(); });
      fileInput.addEventListener('change', function () {
        var file = fileInput.files && fileInput.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function () {
          try {
            var data = JSON.parse(reader.result);
            if (data.theme) {
              document.documentElement.setAttribute('data-theme', data.theme);
              localStorage.setItem('market-int-theme', data.theme);
              themeToggle();
            }
            if (Array.isArray(data.panels) && data.panels.length) {
              localStorage.setItem(SETTINGS_PANELS_KEY, JSON.stringify(data.panels));
              applyPanelVisibility();
            }
            if (data.refreshIntervalSeconds) {
              localStorage.setItem(SETTINGS_REFRESH_KEY, String(data.refreshIntervalSeconds));
              if (window.__restartPriceRefresh) window.__restartPriceRefresh();
            }
            closeSettingsModal();
          } catch (e) {}
        };
        reader.readAsText(file);
        fileInput.value = '';
      });
    }
  }

  async function renderCommandDashboard(container) {
    container.innerHTML = getShellHTML();
    applyPanelVisibility();
    bindLayersToggle();
    bindCountryPanel();
    startWorldClock();
    bindScenarioPanel();

    var kpiPriceKeys = ['WTI Crude Oil', 'Brent Crude Oil', 'Natural Gas', 'Gold', 'Brent-WTI Spread'];

    function loadKPIs() {
      Promise.all([API.pricesLatest(), API.pricesHistory(state.days), API.riskSummary().catch(function () { return { score: 0, summary: '', tags: [] }; })])
        .then(function (res) {
          var prices = res[0];
          var history = res[1];
          var riskSummary = res[2];
          var hasAnyPrice = prices && kpiPriceKeys.some(function (k) { var q = prices[k]; return q && q.price != null; });
          if (!hasAnyPrice) {
            return API.pricesLatest(false).then(function (p) { fillKPIs(p || {}, history, riskSummary); });
          }
          fillKPIs(prices, history, riskSummary);
        })
        .catch(function () { var kg = document.getElementById('kpi-grid'); if (kg) kg.innerHTML = '<p class="error-msg">Failed to load</p>'; var rw = document.getElementById('risk-card-wrap'); if (rw) rw.innerHTML = ''; });
    }
    currentLoadKPIs = loadKPIs;

    function fillKPIs(prices, history, riskSummary) {
      var kpiConfig = [
        { key: 'WTI Crude Oil', label: 'WTI' },
        { key: 'Brent Crude Oil', label: 'Brent' },
        { key: 'Natural Gas', label: 'Nat. Gas' },
        { key: 'Gold', label: 'Gold' },
        { key: 'Brent-WTI Spread', label: 'Spread' },
      ];
      var sparkW = 56, sparkH = 20;
      var kpiHtml = '';
      kpiConfig.forEach(function (item) {
        var q = (prices && prices[item.key]) || {};
        var p = (q.price != null) ? ('$' + Number(q.price).toFixed(2)) : '–';
        var chg = q.change_pct != null ? (q.change_pct >= 0 ? '▲' : '▼') + Number(q.change_pct).toFixed(2) + '%' : '';
        var cls = q.change_pct != null && q.change_pct >= 0 ? 'up' : 'down';
        var series = sparklineSeriesFromHistory(history || {}, item.key);
        var pathD = series && series.length >= 2 ? sparklinePath(series, sparkW, sparkH) : '';
        var strokeColor = cls === 'up' ? 'var(--spark-up, #22c55e)' : 'var(--spark-down, #ef4444)';
        var sparkSvg = pathD ? '<div class="kpi-spark"><svg width="' + sparkW + '" height="' + sparkH + '" viewBox="0 0 ' + sparkW + ' ' + sparkH + '" preserveAspectRatio="none"><path fill="none" stroke="' + strokeColor + '" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" d="' + pathD + '"/></svg></div>' : '';
        kpiHtml += '<div class="kpi-card">' + sparkSvg + '<div class="kpi-label">' + item.label + '</div><div class="kpi-value">' + p + '</div><div class="kpi-sub ' + cls + '">' + chg + '</div></div>';
      });
      var riskScore = riskSummary && riskSummary.score != null ? riskSummary.score : 0;
      var riskClass = riskScore >= 7 ? 'critical' : riskScore >= 4 ? 'warning' : 'ok';
      var riskCardHtml = '<div class="risk-card risk-' + riskClass + '">' +
        '<div class="risk-label">Oil supply risk</div>' +
        '<div class="risk-value">' + riskScore + '<span class="risk-max">/10</span></div>' +
        (riskSummary && riskSummary.summary ? '<div class="risk-summary">' + riskSummary.summary + '</div>' : '') +
        '</div>';
      var kg = document.getElementById('kpi-grid');
      var rw = document.getElementById('risk-card-wrap');
      if (kg) { kg.className = 'kpi-grid'; kg.innerHTML = kpiHtml; }
      if (rw) rw.innerHTML = riskCardHtml;
    }

    function loadOilStocks() {
      API.oilStocks().then(function (data) {
        var tickers = ['XOM', 'CVX', 'SHEL', 'BP', 'TTE', 'OXY', 'EOG', 'SLB'];
        var html = '';
        tickers.forEach(function (ticker) {
          var q = data && data[ticker];
          var label = (q && q.label) || ticker;
          var p = (q && q.price != null) ? '$' + Number(q.price).toFixed(2) : '–';
          var chg = (q && q.change_pct != null) ? (q.change_pct >= 0 ? '+' : '') + Number(q.change_pct).toFixed(2) + '%' : '';
          var cls = (q && q.change_pct != null) ? (q.change_pct >= 0 ? 'up' : 'down') : '';
          html += '<div class="oil-stock-card"><div class="oil-stock-ticker">' + ticker + '</div><div class="oil-stock-label">' + label + '</div><div class="oil-stock-price">' + p + '</div><div class="oil-stock-chg ' + cls + '">' + chg + '</div></div>';
        });
        var el = document.getElementById('oil-stocks-row');
        if (el) { el.className = 'oil-stocks-row'; el.innerHTML = html || '<p class="text-muted">No data.</p>'; }
      }).catch(function () { var el = document.getElementById('oil-stocks-row'); if (el) el.innerHTML = '<p class="error-msg">Failed to load.</p>'; });
    }

    function loadNews() {
      API.newsCategories(80).then(function (newsByCat) {
        var html = '';
        NEWS_CATEGORIES_ORDER.forEach(function (cat) {
          var items = (newsByCat && newsByCat[cat]) || [];
          if (cat === 'OPEC & Markets' && items.length === 0) return;
          var listHtml = '';
          items.slice(0, 8).forEach(function (item) {
            var title = (item.title || '–').substring(0, 80) + (item.title && item.title.length > 80 ? '…' : '');
            var tags = item.tags || [];
            var sentiment = item.sentiment || 'neutral';
            var sentimentBadge = '<span class="sentiment-badge sentiment-' + sentiment + '">' + sentiment + '</span>';
            var tagChips = tags.length ? '<div class="news-tags">' + tags.slice(0, 3).map(function (t) { return '<span class="tag-chip">' + t + '</span>'; }).join('') + '</div>' : '';
            listHtml += '<li class="news-item"><div class="news-item-head"><a href="' + (item.link || '#') + '" target="_blank" rel="noopener">' + title + '</a>' + sentimentBadge + '</div>' + tagChips + '<div class="news-panel-meta">' + (item.source || '') + '</div></li>';
          });
          html += '<div class="news-panel">' +
            '<div class="news-panel-header"><span class="news-panel-title">' + cat.toUpperCase() + '</span><span class="news-panel-live">LIVE</span><span class="news-panel-count">' + items.length + '</span></div>' +
            '<ul class="news-panel-list">' + listHtml + '</ul></div>';
        });
        var el = document.getElementById('section-news');
        if (el) el.innerHTML = html || '<p class="text-muted">No news.</p>';
      }).catch(function () { var el = document.getElementById('section-news'); if (el) el.innerHTML = '<p class="error-msg">Failed to load news.</p>'; });
    }

    function loadMap() {
      Promise.all([
        API.mapPrices().catch(function () { return { countries: {} }; }),
        API.indiaSupplyChain().catch(function () { return { regional: [], stages: [], summary: {} }; }),
        API.mapLayers().catch(function () { return {}; }),
      ]).then(function (res) {
        var mapData = res[0], indiaData = res[1], layersData = res[2];
        mapLayersData = layersData;
        var countries = (mapData && mapData.countries) || {};
        renderCommandMap(countries, indiaData, layersData);
        bindLayerCheckboxes(countries, indiaData, layersData);
      });
    }

    function loadCharts() {
      Promise.all([
        API.pricesHistory(state.days),
        API.priceForecast().catch(function () { return {}; }),
        API.marketSignals().catch(function () { return { momentum: 52, confidence: 50, opportunity: 0, sectors: {} }; }),
        API.rlSignals().catch(function () { return { action: 'Balanced', scores: {} }; }),
      ]).then(function (res) {
        var history = res[0], priceForecast = res[1], marketSignals = res[2], rlSignals = res[3];
        var names = Object.keys(history || {}).filter(function (k) { return Array.isArray(history[k]) && history[k].length; });
        var signalsEl = document.getElementById('section-signals');
        if (signalsEl) {
          var ms = marketSignals || {};
          signalsEl.innerHTML = '<div class="signal-cards">' +
            '<div class="signal-card"><div class="signal-label">Momentum</div><div class="signal-value">' + (ms.momentum != null ? ms.momentum : '–') + '</div><div class="signal-sub">' + (ms.momentum_delta != null ? (ms.momentum_delta >= 0 ? '+' : '') + ms.momentum_delta + ' pts' : '') + '</div></div>' +
            '<div class="signal-card"><div class="signal-label">Confidence</div><div class="signal-value">' + (ms.confidence != null ? ms.confidence + '%' : '–') + '</div><div class="signal-sub">Signal strength</div></div>' +
            '<div class="signal-card"><div class="signal-label">Opportunity</div><div class="signal-value">' + (ms.opportunity != null ? ms.opportunity + ' pts' : '–') + '</div><div class="signal-sub">Amplitude this window</div></div>' +
            '<div class="signal-card highlight"><div class="signal-label">RL Signal</div><div class="signal-value">' + (rlSignals.action || 'Balanced') + '</div><div class="signal-sub">' + (priceForecast.forecast != null ? 'Forecast $' + priceForecast.forecast : 'Bandit from returns') + '</div></div></div>';
        }
        if (lineChartInstance) { lineChartInstance.destroy(); lineChartInstance = null; }
        if (forecastChartInstance) { forecastChartInstance.destroy(); forecastChartInstance = null; }
        if (corrChartInstance) { corrChartInstance.destroy(); corrChartInstance = null; }
        if (sectorChartInstance) { sectorChartInstance.destroy(); sectorChartInstance = null; }
        if (names.length) {
          lineChartInstance = drawLineChartActual(document.getElementById('chart-line'), history, names);
          forecastChartInstance = drawLineChartForecast(document.getElementById('chart-forecast'), history, priceForecast, 'WTI Crude Oil');
          corrChartInstance = drawCorrelation(document.getElementById('chart-corr'), history, names);
        }
        sectorChartInstance = drawSectorChart(document.getElementById('chart-sector'), (marketSignals && marketSignals.sectors) || {});
        renderHeatmap(document.getElementById('heatmap-container'), history, names);
        updateClock();
      });
    }

    function loadOpportunities() {
      API.opportunities().then(function (opportunities) {
        var rows = '';
        (opportunities || []).slice(0, 6).forEach(function (o) {
          var prio = (o.priority || '').toLowerCase();
          var prioClass = prio === 'high' ? 'danger' : prio === 'medium' ? 'warning' : 'secondary';
          var statusClass = (o.status || '').toLowerCase() === 'action' ? 'success' : 'info';
          rows += '<tr><td>' + (o.theme || '') + '</td><td><span class="badge badge-' + prioClass + '">' + (o.priority || '') + '</span></td><td>' + (o.impact || '') + '</td><td>' + (o.next_step || '') + '</td><td><span class="badge badge-' + statusClass + '">' + (o.status || '') + '</span></td></tr>';
        });
        var html = rows ? '<table class="opportunities-table"><thead><tr><th>Theme</th><th>Priority</th><th>Impact</th><th>Next Step</th><th>Status</th></tr></thead><tbody>' + rows + '</tbody></table>' : '<p class="text-muted">No opportunities.</p>';
        var el = document.getElementById('opportunities-content');
        if (el) el.innerHTML = html;
      }).catch(function () { var el = document.getElementById('opportunities-content'); if (el) el.innerHTML = '<p class="error-msg">Failed to load.</p>'; });
    }

    function loadDecisions() {
      Promise.all([
        API.decisions().catch(function () { return []; }),
        API.indiaSupplyChain().catch(function () { return { summary: {} }; }),
      ]).then(function (res) {
        var decisions = res[0], indiaData = res[1];
        var summary = (indiaData && indiaData.summary) || {};
        var supplyLine = (summary.monthly_crude_processed_kt != null ? summary.monthly_crude_processed_kt + ' kT processed' : '') +
          (summary.indigenous_production_kt != null ? ' · ' + summary.indigenous_production_kt + ' kT indigenous' : '');
        var list = '<ul class="decision-list">';
        (decisions || []).slice(0, 8).forEach(function (d) {
          list += '<li class="severity-' + (d.severity || 'info') + '"><div class="decision-condition">' + (d.condition || '') + '</div><div class="decision-message">' + (d.message || '') + '</div></li>';
        });
        if (!decisions || decisions.length === 0) list += '<li class="severity-info">No alerts or recommendations.</li>';
        list += '</ul>';
        var el = document.getElementById('decisions-content');
        if (el) el.innerHTML = (supplyLine ? '<p class="news-meta">' + supplyLine + '</p>' : '') + list;
      }).catch(function () { var el = document.getElementById('decisions-content'); if (el) el.innerHTML = '<p class="error-msg">Failed to load.</p>'; });
    }

    loadKPIs();
    loadOilStocks();
    loadNews();
    loadMap();
    loadCharts();
    loadOpportunities();
    loadDecisions();

    if (priceRefreshIntervalId) clearInterval(priceRefreshIntervalId);
    var refreshSec = parseInt(localStorage.getItem('market-int-refresh-interval'), 10) || 60;
    if (refreshSec < 30) refreshSec = 30;
    priceRefreshIntervalId = setInterval(function () {
      if (currentLoadKPIs) currentLoadKPIs();
      updateClock();
    }, refreshSec * 1000);

    function restartPriceRefresh() {
      if (priceRefreshIntervalId) clearInterval(priceRefreshIntervalId);
      var refreshSec = parseInt(localStorage.getItem('market-int-refresh-interval'), 10) || 60;
      if (refreshSec < 30) refreshSec = 30;
      priceRefreshIntervalId = setInterval(function () {
        if (currentLoadKPIs) currentLoadKPIs();
        updateClock();
      }, refreshSec * 1000);
    }
    window.__restartPriceRefresh = restartPriceRefresh;
    return;
  }

  function bindScenarioPanel() {
    const btn = document.getElementById('scenario-apply');
    const resultEl = document.getElementById('scenario-result');
    if (!btn || !resultEl) return;
    function run() {
      const timespan = (document.getElementById('scenario-timespan') || {}).value || '7d';
      const commodity = (document.getElementById('scenario-commodity') || {}).value || 'WTI Crude Oil';
      const riskBand = (document.getElementById('scenario-risk') || {}).value || 'medium';
      resultEl.innerHTML = '<p class="loading">Loading…</p>';
      API.scenario(timespan, commodity, riskBand)
        .then(function (d) {
          let html = '<p class="scenario-summary">' + (d.summary || '') + '</p>';
          if (d.price != null) html += '<p><strong>Price:</strong> $' + Number(d.price).toFixed(2) + '</p>';
          if (d.forecast != null) html += '<p><strong>Forecast:</strong> $' + Number(d.forecast).toFixed(2) + '</p>';
          if ((d.decisions_snippet || []).length) {
            html += '<ul class="scenario-decisions">';
            d.decisions_snippet.forEach(function (x) {
              html += '<li class="severity-' + (x.severity || 'info') + '">' + (x.condition || '') + ': ' + (x.message || '') + '</li>';
            });
            html += '</ul>';
          }
          resultEl.innerHTML = html || '<p class="text-muted">No data.</p>';
        })
        .catch(function (e) {
          resultEl.innerHTML = '<p class="error-msg">' + e.message + '</p>';
        });
    }
    btn.addEventListener('click', run);
    run();
  }

  function bindLayerCheckboxes(countries, indiaData, layersData) {
    function update() {
      state.layers.globalPrices = document.getElementById('layer-global').checked;
      state.layers.indiaSupply = document.getElementById('layer-india').checked;
      state.layers.refiningHubs = document.getElementById('layer-refining').checked;
      state.layers.chokepoints = document.getElementById('layer-chokepoints').checked;
      state.layers.oilPorts = document.getElementById('layer-ports').checked;
      state.layers.pipelines = document.getElementById('layer-pipelines').checked;
      state.layers.productionRegions = document.getElementById('layer-production').checked;
      state.layers.conflicts = document.getElementById('layer-conflicts').checked;
      state.layers.dayNight = document.getElementById('layer-daynight').checked;
      state.layers.cii = document.getElementById('layer-cii').checked;
      if (state.layers.indiaSupply && !state.layers.globalPrices) {
        document.getElementById('layer-global').checked = false;
        state.layers.globalPrices = false;
      }
      renderCommandMap(countries, indiaData, layersData || mapLayersData || {});
    }
    var layerIds = ['layer-global', 'layer-india', 'layer-refining', 'layer-chokepoints', 'layer-ports', 'layer-pipelines', 'layer-production', 'layer-conflicts', 'layer-daynight', 'layer-cii'];
    layerIds.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener('change', update);
    });
    var selectAllBtn = document.getElementById('layers-select-all');
    var deselectAllBtn = document.getElementById('layers-deselect-all');
    if (selectAllBtn) selectAllBtn.addEventListener('click', function () { layerIds.forEach(function (id) { var e = document.getElementById(id); if (e) e.checked = true; }); update(); });
    if (deselectAllBtn) deselectAllBtn.addEventListener('click', function () { layerIds.forEach(function (id) { var e = document.getElementById(id); if (e) e.checked = false; }); update(); });
  }

  function getTileUrl() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    return dark
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
  }

  function renderCommandMap(countries, indiaData, layersData) {
    layersData = layersData || mapLayersData || {};
    const el = document.getElementById('command-map');
    if (!el || !window.L) return;
    if (commandMap) {
      commandMap.remove();
      commandMap = null;
      mapLayerGlobal = null;
      mapLayerIndia = null;
    }
    const showIndia = state.layers.indiaSupply;
    const showGlobal = state.layers.globalPrices;
    const viewIndiaOnly = showIndia && !showGlobal;
    const view = viewIndiaOnly ? [20.5, 78] : [20, 0];
    const zoom = viewIndiaOnly ? 4 : 2;
    commandMap = window.L.map('command-map', {
      maxBounds: [[-85, -180], [85, 180]],
      maxBoundsViscosity: 1,
    }).setView(view, zoom);
    window.L.tileLayer(getTileUrl(), {
      attribution: '&copy; OSM &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
      noWrap: true,
    }).addTo(commandMap);

    if (state.layers.dayNight) {
      var now = new Date();
      var hour = now.getUTCHours() + now.getUTCMinutes() / 60;
      var subsolarLon = 15 * (12 - hour);
      function norm(l) { l = l % 360; if (l > 180) l -= 360; if (l < -180) l += 360; return l; }
      var lon1 = norm(subsolarLon);
      var lon2 = norm(subsolarLon + 180);
      var nightBounds = [[90, lon1], [90, lon2], [-90, lon2], [-90, lon1]];
      var nightLayer = window.L.polygon(nightBounds, {
        fillColor: '#0d0d0d', color: 'transparent', fillOpacity: 0.45, interactive: false,
      });
      nightLayer.addTo(commandMap);
    }

    const legendEl = document.getElementById('map-legend');
    if (showGlobal && Object.keys(countries).length) {
      const countryCoords = {
        USA: [37, -95], CAN: [56, -106], GBR: [54, -2], DEU: [51, 10], FRA: [46, 2], IND: [20, 77], CHN: [35, 105],
        JPN: [36, 138], BRA: [-14, -51], AUS: [-25, 133], RUS: [60, 100], SAU: [24, 45], ARE: [24, 54],
      };
      const vals = Object.values(countries);
      const min = Math.min.apply(null, vals) || 70;
      const max = Math.max.apply(null, vals) || 85;
      const opts = { radius: 6, weight: 1, fillOpacity: 0.85 };
      Object.keys(countries).forEach(function (code) {
        const coord = countryCoords[code];
        if (!coord) return;
        const v = countries[code];
        const norm = (v - min) / (max - min || 1);
        const r = Math.round(200 * (1 - norm));
        const g = Math.round(120 + 135 * norm);
        const marker = window.L.circleMarker(coord, {
          radius: opts.radius,
          fillColor: 'rgb(' + r + ',' + g + ',80)',
          color: 'rgba(0,0,0,.3)',
          weight: opts.weight,
          fillOpacity: opts.fillOpacity,
        });
        marker.bindTooltip(code + ' $' + (v != null ? v.toFixed(1) : ''), { className: 'map-tooltip' });
        marker.bindPopup('<div class="map-popup"><strong>' + code + '</strong><br>Price index: $' + (v != null ? v.toFixed(2) : '') + '/bbl approx<br><span class="map-popup-note">Click for news</span></div>', { className: 'map-popup-wrap' });
        marker.on('click', function () { openCountryPanel(code, code, v); });
        marker.addTo(commandMap);
      });
      if (legendEl) legendEl.textContent = 'Price index by country ($/bbl approx)';
    }

    if (showIndia) {
      fetch('https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson')
        .then(function (r) { return r.json(); })
        .then(function (geojson) {
          const fallback = {
            'Andhra Pradesh': 300, 'Gujarat': 450, 'Maharashtra': 400, 'Tamil Nadu': 250, 'Rajasthan': 180,
            'Karnataka': 180, 'Uttar Pradesh': 200, 'West Bengal': 150, 'Madhya Pradesh': 150, 'Telangana': 130,
            'Kerala': 120, 'Assam': 120, 'Odisha': 100, 'Haryana': 100, 'Punjab': 95, 'Jharkhand': 85, 'Bihar': 80,
          };
          window.L.geoJSON(geojson, {
            style: function (f) {
              const name = f.properties.ST_NM;
              const v = fallback[name] != null ? fallback[name] : 50;
              const t = Math.min(1, (v - 0) / 500);
              const r = Math.round(220 * (1 - t));
              const g = Math.round(180 * t);
              return { fillColor: 'rgb(' + r + ',' + g + ',100)', weight: 1, color: 'rgba(0,0,0,.25)', fillOpacity: 0.75 };
            },
          }).addTo(commandMap);
          if (legendEl) legendEl.textContent = 'Production / supply (kT)';
        })
        .catch(function () { if (legendEl) legendEl.textContent = ''; });
    }

    if (state.layers.refiningHubs) {
      (layersData.refiningHubs || []).forEach(function (p) {
        const m = window.L.circleMarker([p.lat, p.lon], { radius: 7, fillColor: '#f59e0b', color: '#92400e', weight: 1, fillOpacity: 0.9 });
        m.bindTooltip((p.name || '') + ' ' + (p.capacity || ''), { className: 'map-tooltip' });
        m.bindPopup('<div class="map-popup"><strong>' + (p.name || '') + '</strong><br>' + (p.country || '') + '<br>Capacity: ' + (p.capacity || '') + '<br><span class="map-popup-note">Major refining hub</span></div>', { className: 'map-popup-wrap' });
        m.addTo(commandMap);
      });
    }

    if (state.layers.chokepoints) {
      (layersData.chokepoints || []).forEach(function (p) {
        const m = window.L.circleMarker([p.lat, p.lon], { radius: 8, fillColor: '#dc2626', color: '#991b1b', weight: 1, fillOpacity: 0.9 });
        m.bindTooltip((p.name || '') + ' (' + (p.oilShare || '') + ')', { className: 'map-tooltip' });
        m.bindPopup('<div class="map-popup"><strong>' + (p.name || '') + '</strong><br>Oil share: ' + (p.oilShare || '') + '<br><span class="map-popup-note">Strategic chokepoint for oil transit</span></div>', { className: 'map-popup-wrap' });
        m.addTo(commandMap);
      });
    }

    if (state.layers.oilPorts) {
      (layersData.oilPorts || []).forEach(function (p) {
        const m = window.L.circleMarker([p.lat, p.lon], { radius: 6, fillColor: '#0ea5e9', color: '#0369a1', weight: 1, fillOpacity: 0.85 });
        m.bindTooltip((p.name || '') + ' (' + (p.type || '') + ')', { className: 'map-tooltip' });
        m.bindPopup('<div class="map-popup"><strong>' + (p.name || '') + '</strong><br>Type: ' + (p.type || '') + '<br><span class="map-popup-note">Oil/LNG port</span></div>', { className: 'map-popup-wrap' });
        m.addTo(commandMap);
      });
    }

    if (state.layers.pipelines) {
      (layersData.pipelines || []).forEach(function (p) {
        if (!(p.coords && p.coords.length >= 2)) return;
        const latlngs = p.coords.map(function (c) { return [c[0], c[1]]; });
        const pl = window.L.polyline(latlngs, { color: '#8b5cf6', weight: 3, opacity: 0.8 });
        pl.bindTooltip(p.name || '', { className: 'map-tooltip' });
        pl.bindPopup('<div class="map-popup"><strong>' + (p.name || '') + '</strong><br><span class="map-popup-note">Major oil pipeline route</span></div>', { className: 'map-popup-wrap' });
        pl.addTo(commandMap);
      });
    }

    if (state.layers.productionRegions) {
      (layersData.productionRegions || []).forEach(function (p) {
        const m = window.L.circleMarker([p.lat, p.lon], { radius: 6, fillColor: '#059669', color: '#047857', weight: 1, fillOpacity: 0.85 });
        m.bindTooltip((p.name || '') + ' (' + (p.region || '') + ')', { className: 'map-tooltip' });
        m.bindPopup('<div class="map-popup"><strong>' + (p.name || '') + '</strong><br>Region: ' + (p.region || '') + '<br><span class="map-popup-note">Crude production basin</span></div>', { className: 'map-popup-wrap' });
        m.addTo(commandMap);
      });
    }

    if (state.layers.conflicts) {
      (layersData.conflicts || []).forEach(function (p) {
        const m = window.L.circleMarker([p.lat, p.lon], { radius: 8, fillColor: '#ef4444', color: '#b91c1c', weight: 1, fillOpacity: 0.9 });
        m.bindTooltip((p.name || '') + ' – ' + (p.impact || ''), { className: 'map-tooltip' });
        m.bindPopup('<div class="map-popup"><strong>' + (p.name || '') + '</strong><br><span class="map-popup-impact">' + (p.impact || '') + '</span><br>' + (p.description || '') + '</div>', { className: 'map-popup-wrap' });
        m.addTo(commandMap);
      });
    }

    if (state.layers.cii) {
      fetch(CII_GEOJSON_URL)
        .then(function (r) { return r.json(); })
        .then(function (geojson) {
          function scoreToRgb(score) {
            return scaleGreenRed(score / 100);
          }
          window.L.geoJSON(geojson, {
            style: function (f) {
              var iso = (f.properties.ISO_A2 || f.properties.iso_a2 || '').toString().toUpperCase();
              if (iso === '-99' || iso === '') iso = null;
              var score = iso && CII_COUNTRY_SCORES[iso] != null ? CII_COUNTRY_SCORES[iso] : 50;
              return {
                fillColor: scoreToRgb(score),
                color: 'rgba(0,0,0,.25)',
                weight: 0.8,
                fillOpacity: 0.75,
              };
            },
            onEachFeature: function (f, layer) {
              var iso = (f.properties.ISO_A2 || f.properties.iso_a2 || '').toString().toUpperCase();
              var name = f.properties.NAME || f.properties.name || iso || '';
              var score = iso && CII_COUNTRY_SCORES[iso] != null ? CII_COUNTRY_SCORES[iso] : 50;
              layer.bindTooltip((name || iso) + ' ' + score + '/100', { className: 'map-tooltip' });
              layer.bindPopup('<div class="map-popup"><strong>' + (name || iso) + '</strong><br>CII Instability: ' + score + '/100<br><span class="map-popup-note">1 = stable (green), 100 = conflict (red)</span></div>', { className: 'map-popup-wrap' });
            },
          }).addTo(commandMap);
          if (legendEl) legendEl.textContent = 'CII Instability 1 (green) – 100 (red)';
        })
        .catch(function () {
          if (legendEl) legendEl.textContent = 'CII: load failed';
        });
    }

    if (legendEl && !showGlobal && !showIndia) {
      const active = [];
      if (state.layers.refiningHubs) active.push('Refining');
      if (state.layers.chokepoints) active.push('Chokepoints');
      if (state.layers.oilPorts) active.push('Ports');
      if (state.layers.pipelines) active.push('Pipelines');
      if (state.layers.productionRegions) active.push('Production');
      if (state.layers.conflicts) active.push('Conflicts');
      if (state.layers.dayNight) active.push('Day/Night');
      if (state.layers.cii) active.push('CII');
      legendEl.textContent = active.length ? active.join(' · ') : '';
    }
  }

  const MAGNITUDE_THRESHOLD = 100;
  const CHART_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'];

  function drawSectorChart(ctx, sectors) {
    if (!ctx || !window.Chart) return null;
    const labels = Object.keys(sectors);
    const values = labels.map(function (k) { return sectors[k]; });
    if (!labels.length) return null;
    var dataMax = Math.max.apply(null, values);
    var axisMax = Math.max(100, (dataMax * 1.1));
    return new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{ label: 'Share (%)', data: values, backgroundColor: ['#0d6efd', '#198754', '#fd7e14', '#6610f2', '#0dcaf0'] }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        scales: { x: { max: axisMax, title: { display: true, text: 'Share (%)' } } },
      },
    });
  }

  function renderHeatmap(container, history, names) {
    if (!container || !names || !names.length) return;
    names = names.slice(0, 5);
    const changes = {};
    let maxLen = 0;
    names.forEach(function (name) {
      const arr = history[name] || [];
      const pct = [];
      for (let i = 1; i < arr.length; i++) {
        const prev = arr[i - 1].Close;
        const curr = arr[i].Close;
        if (prev != null && curr != null && prev !== 0) pct.push(((curr - prev) / prev) * 100);
      }
      changes[name] = pct;
      if (pct.length > maxLen) maxLen = pct.length;
    });
    if (maxLen === 0) { container.innerHTML = '<p class="text-muted">No data.</p>'; return; }
    var allVals = [];
    names.forEach(function (name) { (changes[name] || []).forEach(function (v) { if (v != null) allVals.push(v); }); });
    var minV = allVals.length ? Math.min.apply(null, allVals) : -5;
    var maxV = allVals.length ? Math.max.apply(null, allVals) : 5;
    var range = maxV - minV || 1;
    const cols = Math.min(maxLen, 14);
    let html = '<table class="heatmap-table"><thead><tr><th>Commodity</th>';
    for (let c = 0; c < cols; c++) html += '<th>' + (cols - c - 1) + 'd</th>';
    html += '</tr></thead><tbody>';
    names.forEach(function (name) {
      const pct = changes[name] || [];
      html += '<tr><td class="heatmap-label">' + name.replace(/ Crude Oil| Oil/g, '') + '</td>';
      for (let c = 0; c < cols; c++) {
        const idx = pct.length - cols + c;
        const v = idx >= 0 ? pct[idx] : null;
        var bg = 'rgba(128,128,128,0.2)';
        if (v != null) {
          var t = (v - minV) / range;
          bg = scaleGreenRed(t);
        }
        html += '<td class="heatmap-cell" style="background:' + bg + '" title="' + (v != null ? v.toFixed(2) + '%' : '') + '">' + (v != null ? v.toFixed(1) + '%' : '') + '</td>';
      }
      html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  }

  function getTypicalPrice(history, name) {
    const arr = history[name] || [];
    if (!arr.length) return 0;
    const closes = arr.map(function (r) { return r.Close; }).filter(function (v) { return v != null; });
    if (!closes.length) return 0;
    return closes.reduce(function (a, b) { return a + b; }, 0) / closes.length;
  }

  function drawLineChartActual(ctx, history, names) {
    if (!ctx || !window.Chart) return null;
    names = names.slice(0, 6);
    const lowMag = [];
    const highMag = [];
    names.forEach(function (name) {
      const typical = getTypicalPrice(history, name);
      if (typical >= MAGNITUDE_THRESHOLD) highMag.push(name);
      else lowMag.push(name);
    });
    const useDualAxis = lowMag.length > 0 && highMag.length > 0;
    const datasets = [];
    names.forEach(function (name, i) {
      const arr = history[name] || [];
      const yAxisID = useDualAxis && highMag.indexOf(name) >= 0 ? 'y1' : 'y';
      datasets.push({
        label: name,
        data: arr.map(function (r) { return { x: r.date, y: r.Close }; }),
        borderColor: CHART_COLORS[i % CHART_COLORS.length],
        backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
        tension: 0.2,
        fill: false,
        yAxisID: yAxisID,
      });
    });
    return _createLineChart(ctx, datasets, useDualAxis, lowMag, highMag);
  }

  function drawLineChartForecast(ctx, history, forecast, forecastName) {
    if (!ctx || !window.Chart) return null;
    const datasets = [];
    const arr = (forecastName && history[forecastName]) ? history[forecastName] : [];
    if (arr.length) {
      datasets.push({
        label: forecastName || 'WTI',
        data: arr.map(function (r) { return { x: r.date, y: r.Close }; }),
        borderColor: CHART_COLORS[0],
        backgroundColor: CHART_COLORS[0],
        tension: 0.2,
        fill: false,
        yAxisID: 'y',
      });
    }
    if (forecast && forecast.trend && forecast.dates && forecast.dates.length) {
      datasets.push({
        label: 'Trend',
        data: forecast.dates.map(function (d, i) { return { x: d, y: forecast.trend[i] }; }),
        borderColor: '#6610f2',
        borderDash: [4, 2],
        tension: 0,
        fill: false,
        yAxisID: 'y',
      });
      if (forecast.forecast != null && forecast.dates.length) {
        const lastDate = forecast.dates[forecast.dates.length - 1];
        const nextDate = lastDate ? (function () { const d = new Date(lastDate); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10); })() : null;
        if (nextDate) {
          datasets.push({
            label: 'Forecast',
            data: [{ x: nextDate, y: forecast.forecast }],
            pointRadius: 8,
            pointBackgroundColor: '#198754',
            borderColor: 'transparent',
            fill: false,
            yAxisID: 'y',
          });
        }
      }
    }
    return _createLineChart(ctx, datasets, false, [], []);
  }

  function _createLineChart(ctx, datasets, useDualAxis, lowMag, highMag) {
    const scales = {
      x: { display: true, grid: { color: 'rgba(0,0,0,0.06)' } },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        beginAtZero: false,
        grid: { color: 'rgba(0,0,0,0.06)' },
        ticks: { callback: function (v) { return typeof v === 'number' ? v.toFixed(2) : v; } },
      },
    };
    if (useDualAxis) {
      scales.y1 = {
        type: 'linear',
        display: true,
        position: 'right',
        beginAtZero: false,
        grid: { drawOnChartArea: false },
        ticks: { callback: function (v) { return typeof v === 'number' ? v.toFixed(0) : v; } },
      };
    }

    return new window.Chart(ctx, {
      type: 'line',
      data: { datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'top' },
          tooltip: { callbacks: { label: function (c) { return c.dataset.label + ': ' + (c.raw.y != null ? c.raw.y.toFixed(2) : ''); } } },
        },
        scales: scales,
      },
    });
  }

  function drawCorrelation(ctx, history, names) {
    if (!ctx || !window.Chart) return null;
    const n = names.length;
    const closes = names.map(function (name) {
      const arr = history[name] || [];
      return arr.map(function (r) { return r.Close; }).filter(function (v) { return v != null; });
    });
    const minLen = Math.min.apply(null, closes.map(function (a) { return a.length; }));
    if (minLen < 2) return null;
    const aligned = closes.map(function (a) { return a.slice(-minLen); });
    const pairLabels = [];
    const data = [];
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const a = aligned[i], b = aligned[j];
        const meanA = a.reduce(function (s, v) { return s + v; }, 0) / a.length;
        const meanB = b.reduce(function (s, v) { return s + v; }, 0) / b.length;
        let num = 0, da = 0, db = 0;
        for (let k = 0; k < a.length; k++) {
          const va = a[k] - meanA, vb = b[k] - meanB;
          num += va * vb;
          da += va * va;
          db += vb * vb;
        }
        pairLabels.push(names[i] + ' vs ' + names[j]);
        data.push(da && db ? num / Math.sqrt(da * db) : 0);
      }
    }
    const bg = data.map(function (v) {
      const t = (v + 1) / 2;
      return 'rgb(' + Math.round(255 * (1 - t)) + ',' + Math.round(255 * t) + ',100)';
    });
    return new window.Chart(ctx, {
      type: 'bar',
      data: { labels: pairLabels, datasets: [{ label: 'Correlation', data: data, backgroundColor: bg }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        scales: { x: { min: -1, max: 1 } },
      },
    });
  }
})();

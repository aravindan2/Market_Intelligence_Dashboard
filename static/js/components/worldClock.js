/**
 * World clock panel (exchange open/close, local times).
 */
export const WORLD_CLOCK_CITIES = [
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

export function getWorldClockRow(c) {
  const now = new Date();
  const formatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  const timeStr = formatter.format(now).replace(/\./g, ':');
  const dowFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, weekday: 'short' });
  const tzFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, timeZoneName: 'short' });
  const dow = dowFormatter.format(now);
  const tzParts = tzFormatter.formatToParts(now);
  let tzShort = '';
  tzParts.forEach(function (p) { if (p.type === 'timeZoneName') tzShort = p.value; });
  const hourFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, hour: 'numeric', hour12: false });
  const minFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: c.timezone, minute: 'numeric' });
  const localHour = parseInt(hourFormatter.format(now), 10);
  const localMin = parseInt(minFormatter.format(now), 10);
  const localMins = localHour * 60 + localMin;
  const openMins = c.open[0] * 60 + c.open[1];
  const closeMins = c.close[0] * 60 + c.close[1];
  const dayNum = now.toLocaleDateString('en-GB', { timeZone: c.timezone, weekday: 'long' });
  const isWeekend = dayNum === 'Saturday' || dayNum === 'Sunday';
  const isOpen = !isWeekend && localMins >= openMins && localMins < closeMins;
  const statusClass = isOpen ? 'status-open' : 'status-closed';
  const statusLabel = isOpen ? 'OPEN' : 'CLSD';
  const statusDotClass = isOpen ? 'open' : 'closed';
  return '<li class="' + (c.highlight ? 'highlight ' : '') + statusClass + '">' +
    '<div><div class="world-clock-city">' + c.city + '</div><div class="world-clock-exchange">' +
    '<span class="status-dot ' + statusDotClass + '"></span>' + c.exchange + ' ' + statusLabel + '</div></div>' +
    '<div><div class="world-clock-time">' + timeStr + '</div><div class="world-clock-meta">' + dow + ' ' + tzShort + '</div></div></li>';
}

let worldClockInterval = null;

export function startWorldClock() {
  const list = document.getElementById('world-clock-list');
  if (!list) return;
  function tick() {
    list.innerHTML = WORLD_CLOCK_CITIES.map(getWorldClockRow).join('');
  }
  tick();
  if (worldClockInterval) clearInterval(worldClockInterval);
  worldClockInterval = setInterval(tick, 1000);
}

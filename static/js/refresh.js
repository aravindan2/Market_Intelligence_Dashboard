/**
 * Background price refresh: runs refreshKPIs and updateClock on an interval.
 */
let priceRefreshIntervalId = null;

export function startBackgroundRefresh(callbacks) {
  if (priceRefreshIntervalId) clearInterval(priceRefreshIntervalId);
  const { refreshKPIs, updateClock } = callbacks || {};
  priceRefreshIntervalId = setInterval(function () {
    if (typeof refreshKPIs === 'function') refreshKPIs();
    if (typeof updateClock === 'function') updateClock();
  }, 60000);
}

export function stopBackgroundRefresh() {
  if (priceRefreshIntervalId) {
    clearInterval(priceRefreshIntervalId);
    priceRefreshIntervalId = null;
  }
}

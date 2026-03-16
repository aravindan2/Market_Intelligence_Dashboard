/**
 * Market Intelligence dashboard – entry point.
 * Loads the legacy app.js which contains the full dashboard logic (with day/night fix and background refresh).
 */
import { initTheme } from './theme.js';
import { bindSearch } from './search.js';

initTheme();
bindSearch();

function init() {
  const body = document.getElementById('content-body');
  if (!body) return;
  // Use the legacy app's dashboard (still loaded via script tag for now)
  if (typeof window.__renderCommandDashboard === 'function') {
    window.__renderCommandDashboard(body);
  }
  if (typeof window.__renderHeaderTimespan === 'function') {
    window.__renderHeaderTimespan();
  }
  if (typeof window.__updateClock === 'function') {
    window.__updateClock();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

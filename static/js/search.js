/**
 * Search overlay: jump to section by label (⌘K).
 */
import { DASHBOARD_SECTIONS } from './state.js';

export function openSearch() {
  const overlay = document.getElementById('search-overlay');
  const input = document.getElementById('search-input');
  const list = document.getElementById('search-results');
  if (!overlay || !input || !list) return;
  const sections = DASHBOARD_SECTIONS.filter(function (s) { return document.getElementById(s.id); });
  overlay.setAttribute('aria-hidden', 'false');
  overlay.classList.add('search-open');
  input.value = '';
  list.innerHTML = sections.map(function (s) {
    return '<li class="search-result-item" data-section="' + s.id + '">' + s.label + '</li>';
  }).join('');
  list.querySelectorAll('.search-result-item').forEach(function (li) {
    li.addEventListener('click', function () {
      const id = li.getAttribute('data-section');
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      closeSearch();
    });
  });
  input.focus();
}

export function closeSearch() {
  const overlay = document.getElementById('search-overlay');
  const input = document.getElementById('search-input');
  if (!overlay) return;
  overlay.classList.remove('search-open');
  overlay.setAttribute('aria-hidden', 'true');
  if (input) input.blur();
}

export function filterSearch(query) {
  const list = document.getElementById('search-results');
  if (!list) return;
  const q = (query || '').toLowerCase().trim();
  list.querySelectorAll('.search-result-item').forEach(function (li) {
    const label = (li.textContent || '').toLowerCase();
    li.style.display = !q || label.indexOf(q) >= 0 ? '' : 'none';
  });
}

export function bindSearch() {
  const searchTrigger = document.getElementById('search-trigger');
  if (searchTrigger) searchTrigger.addEventListener('click', openSearch);
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', function () { filterSearch(this.value); });
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { closeSearch(); e.preventDefault(); }
      if (e.key === 'Enter') {
        const items = document.querySelectorAll('#search-results .search-result-item');
        for (let i = 0; i < items.length; i++) {
          if (items[i].style.display !== 'none') { items[i].click(); break; }
        }
      }
    });
  }
  const searchOverlay = document.getElementById('search-overlay');
  if (searchOverlay) searchOverlay.addEventListener('click', function (e) {
    if (e.target === this) closeSearch();
  });
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      const ov = document.getElementById('search-overlay');
      if (ov && ov.classList.contains('search-open')) closeSearch();
      else openSearch();
    }
  });
}

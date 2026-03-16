/**
 * Theme toggle (light/dark) and brand logo.
 */
export function updateBrandLogo() {
  const img = document.querySelector('.brand-logo');
  if (!img) return;
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  img.src = dark ? '/assets/nix-full-icon-dark.svg' : '/assets/nix-full-icon.svg';
}

export function themeToggle() {
  const root = document.documentElement;
  const current = root.getAttribute('data-theme') || 'light';
  const next = current === 'light' ? 'dark' : 'light';
  root.setAttribute('data-theme', next);
  localStorage.setItem('market-int-theme', next);
  const btn = document.getElementById('theme-btn');
  if (btn) btn.innerHTML = next === 'dark' ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon"></i>';
  updateBrandLogo();
}

export function initTheme() {
  const btn = document.getElementById('theme-btn');
  if (btn) btn.addEventListener('click', themeToggle);
  if (document.documentElement.getAttribute('data-theme') === 'dark') {
    if (btn) btn.innerHTML = '<i class="bi bi-sun"></i>';
  }
  updateBrandLogo();
}

// Apply the saved palette before rendering; same-origin script works with strict CSP.
/* global localStorage, document */
(() => {
  let theme = 'dark';
  try {
    if (localStorage.getItem('inheria-theme') === 'light') theme = 'light';
  } catch { /* Storage is optional; night remains the default. */ }
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]').content = theme === 'light' ? '#f4f7fb' : '#0b1019';
})();

document.addEventListener('DOMContentLoaded', () => {
  const exploreBtn = document.getElementById('explore-btn');
  const brewBtn = document.getElementById('brew-btn');

  if (exploreBtn) {
    exploreBtn.addEventListener('click', () => {
      document.getElementById('menu')?.scrollIntoView({ behavior: 'smooth' });
    });
  }

  if (brewBtn) {
    brewBtn.addEventListener('click', () => {
      alert('Brewing Guide: French Press 1:15 ratio, 94°C water, steep 4 minutes.');
    });
  }

  console.log('Antigravity+ Coffee application loaded successfully.');
});
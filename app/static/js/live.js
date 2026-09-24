// Keeps live tiles current without a page reload: clocks tick every second,
// Home Assistant, status and weather tiles are fetched again every 30 seconds.
// Without JavaScript the page still shows the values from when it was loaded.
(function () {
  const REFRESH_MS = 30000;

  function tickClocks() {
    document.querySelectorAll("[data-clock]").forEach((clock) => {
      const options = { hour: "2-digit", minute: "2-digit" };
      if (clock.dataset.timezone) options.timeZone = clock.dataset.timezone;
      const dateOptions = { weekday: "long", day: "numeric", month: "long", timeZone: options.timeZone };
      const now = new Date();
      clock.querySelector(".clock-time").textContent = now.toLocaleTimeString(clock.dataset.lang, options);
      clock.querySelector(".clock-date").textContent = now.toLocaleDateString(clock.dataset.lang, dateOptions);
    });
  }

  async function refreshTile(section) {
    try {
      const response = await fetch(section.dataset.live, { headers: { Accept: "text/html" } });
      if (response.ok) {
        section.innerHTML = await response.text();
        tickClocks();
      }
    } catch (error) {
      // Offline for a moment: keep showing the last values.
    }
  }

  function refreshAll() {
    if (document.hidden) return;
    document.querySelectorAll("[data-live]").forEach((section) => {
      if (!section.querySelector("[data-clock]")) refreshTile(section);
    });
  }

  tickClocks();
  setInterval(tickClocks, 1000);
  setInterval(refreshAll, REFRESH_MS);
  document.addEventListener("visibilitychange", refreshAll);
})();

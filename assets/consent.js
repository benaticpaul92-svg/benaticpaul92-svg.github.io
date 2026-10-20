(() => {
  "use strict";
  if (!window.JEBN_CONFIG?.googleAds?.enabled) return;
  const panel = document.getElementById("privacy-choices");
  if (!panel) return;
  const key = "jebn_ad_consent_v1";
  const lifetime = 180 * 24 * 60 * 60 * 1000;
  const controls = [...document.querySelectorAll("[data-consent-settings]")];
  const allow = panel.querySelector("[data-consent-allow]");
  const close = panel.querySelector("[data-consent-close]");
  const note = panel.querySelector("[data-consent-note]");
  const status = document.getElementById("consent-status");
  const gpc = navigator.globalPrivacyControl === true;
  let trigger = null;

  function readChoice() {
    try {
      const saved = JSON.parse(localStorage.getItem(key));
      const now = Date.now();
      return saved?.version === 1 && ["allow", "deny"].includes(saved.choice) &&
        Number.isFinite(saved.at) && saved.at <= now && now - saved.at < lifetime ? saved : null;
    } catch { return null; }
  }
  function saveChoice(choice) {
    try {
      localStorage.setItem(key, JSON.stringify({ version: 1, choice, at: Date.now() }));
      return true;
    } catch { return false; }
  }
  function clearAdvertisingCookies() {
    // Remove Google Ads first-party cookies on this site, not unrelated cookies.
    const domains = ["", location.hostname];
    if (location.hostname.endsWith(".jebnengineering.com")) domains.push("jebnengineering.com");
    for (const cookie of document.cookie.split(";")) {
      const name = cookie.split("=")[0].trim();
      if (!/^_g(?:cl|ac)_/.test(name)) continue;
      for (const domain of domains) {
        document.cookie = name + "=; Max-Age=0; Path=/; SameSite=Lax" +
          (domain ? "; Domain=" + domain : "");
      }
    }
  }
  function applyChoice(choice) {
    const granted = !gpc && choice === "allow";
    try {
      window.JEBN_GOOGLE_ADS?.setConsent({
        ad_storage: granted ? "granted" : "denied",
        ad_user_data: granted ? "granted" : "denied",
        ad_personalization: "denied",
        analytics_storage: "denied"
      });
    } catch { /* A blocked tag must not break the visitor's privacy controls. */ }
    if (!granted) clearAdvertisingCookies();
    note.textContent = gpc
      ? "Your browser's Global Privacy Control signal keeps optional advertising measurement off."
      : choice === "allow" ? "Current choice: measurement allowed. Personalized advertising is off."
      : choice === "deny" ? "Current choice: optional advertising measurement is off."
      : "Optional advertising measurement is off until you allow it.";
    return granted;
  }
  function hidePanel() {
    panel.hidden = true;
    (trigger || document.getElementById("main-content"))?.focus({ preventScroll: true });
    trigger = null;
  }
  function choose(choice) {
    if (gpc) choice = "deny";
    const stored = saveChoice(choice);
    const granted = applyChoice(choice);
    close.hidden = false;
    hidePanel();
    status.textContent = (granted ? "Advertising measurement allowed." : "Optional advertising measurement turned off.") +
      (stored ? " Choice saved. You can change it in Cookie settings." : " Your browser could not save the choice; it applies to this page only.");
  }
  for (const button of controls) {
    button.hidden = false;
    button.addEventListener("click", () => {
      trigger = button;
      panel.hidden = false;
      panel.querySelector("h2").focus({ preventScroll: true });
      panel.scrollIntoView({ behavior: "instant", block: "start" });
    });
  }
  allow.disabled = gpc;
  allow.addEventListener("click", () => choose("allow"));
  panel.querySelector("[data-consent-reject]").addEventListener("click", () => choose("deny"));
  close.addEventListener("click", hidePanel);
  panel.addEventListener("keydown", event => {
    if (event.key === "Escape" && !close.hidden) {
      event.preventDefault();
      hidePanel();
    }
  });
  let saved = readChoice();
  if (gpc) {
    saveChoice("deny");
    saved = { choice: "deny" };
  }
  applyChoice(saved?.choice);
  panel.hidden = Boolean(saved);
  close.hidden = !saved;
  // Other tabs apply the newest choice, including removal/withdrawal.
  window.addEventListener("storage", event => {
    if (event.key !== key && event.key !== null) return;
    const current = readChoice();
    applyChoice(current?.choice);
    panel.hidden = Boolean(current) || gpc;
    close.hidden = !current && !gpc;
    status.textContent = "Your advertising privacy choice was updated in another tab.";
  });
})();

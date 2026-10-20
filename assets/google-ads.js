(() => {
  "use strict";
  const settings = window.JEBN_CONFIG?.googleAds;
  const production = ["www.jebnengineering.com", "jebnengineering.com"].includes(location.hostname);
  if (!settings?.enabled || !production || !/^AW-\d+$/.test(settings.tagId)) return;
  // This adapter is not a consent banner/CMP. Until the configured consent
  // solution supplies a permitted state, no Google script is requested.
  if (window.JEBN_GOOGLE_ADS) return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  const denied = {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    analytics_storage: "denied"
  };
  window.gtag("consent", "default", denied);
  let permitted = false;
  let initialized = false;
  const recorded = new Set();

  function setConsent(choice = {}) {
    const state = Object.fromEntries(Object.keys(denied).map(key => [
      key, choice[key] === "granted" ? "granted" : "denied"
    ]));
    permitted = state.ad_storage === "granted" && state.ad_user_data === "granted";
    window.gtag("consent", "update", state);
    if (!permitted || initialized) return;
    initialized = true;
    window.gtag("js", new Date());
    window.gtag("config", settings.tagId, { allow_ad_personalization_signals: false });
    const script = document.createElement("script");
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${settings.tagId}`;
    script.id = "jebn-google-tag";
    document.head.append(script);
  }

  function recordEnquiry(reference) {
    if (!permitted || !initialized || !/^[A-Za-z0-9_-]+$/.test(settings.conversionLabel || "") ||
        typeof reference !== "string" || !reference || recorded.has(reference)) return;
    window.gtag("event", "conversion", {
      send_to: `${settings.tagId}/${settings.conversionLabel}`
    });
    recorded.add(reference);
  }

  // The account's chosen consent solution must call this with the visitor's
  // actual saved/current choice on every page, including withdrawal updates.
  // Events before permission are discarded, not replayed after permission.
  window.JEBN_GOOGLE_ADS = Object.freeze({ setConsent, recordEnquiry });
})();

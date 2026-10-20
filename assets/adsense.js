(() => {
  "use strict";
  const settings = window.JEBN_CONFIG?.adsense;
  const placement = document.querySelector("[data-ad-placement]");
  // No ad-network request until real IDs and account/privacy setup are ready.
  if (!placement || !settings?.enabled || !settings.privacyReady ||
      !/^ca-pub-\d{16}$/.test(settings.client) || !/^\d+$/.test(settings.slot)) return;
  if (location.hostname !== "www.jebnengineering.com" && location.hostname !== "jebnengineering.com") return;
  const params = new URLSearchParams(location.search);
  // Keep paid landing visits focused on the enquiry. Organic studio visits
  // can show the one separated display ad after account setup.
  if (["gclid", "gbraid", "wbraid"].some(key => params.has(key)) ||
      /^(cpc|ppc|paid|paidsearch|paid_search|display)$/i.test(params.get("utm_medium") || "")) return;
  const unit = document.createElement("ins");
  unit.className = "adsbygoogle";
  unit.style.display = "block";
  unit.dataset.adClient = settings.client;
  unit.dataset.adSlot = settings.slot;
  unit.dataset.adFormat = "auto";
  unit.dataset.fullWidthResponsive = "true";
  placement.append(unit);
  placement.hidden = false;
  const script = document.createElement("script");
  script.async = true;
  script.crossOrigin = "anonymous";
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${settings.client}`;
  script.onload = () => {
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); }
    catch { placement.hidden = true; }
  };
  script.onerror = () => { placement.hidden = true; };
  document.head.append(script);
})();

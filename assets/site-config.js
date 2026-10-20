/*
 * Public settings only. Never put recipient lists, private email addresses,
 * API secrets or email passwords in this file.
 * See SETUP.md outside site-for-astra for the private recipient configuration.
 */
window.JEBN_CONFIG = Object.freeze({
  // Example shape: https://formspree.io/f/FORM_ID
  formEndpoint: "",
  formTimeoutMs: 20000,
  googleAds: Object.freeze({
    // Base tag supplied by Martin's Google Ads screenshot, 20 October 2026.
    enabled: false,
    tagId: "AW-18526767007",
    conversionLabel: "" // Pending: the part after "/" in the event's send_to.
    // A consent solution must call JEBN_GOOGLE_ADS.setConsent after setup.
  }),
  adsense: Object.freeze({
    enabled: false,
    client: "", // Your public ca-pub-... ID
    slot: "", // Your responsive display ad-unit ID
    // Enable only after account approval, privacy disclosures and Google's
    // consent/privacy messaging have been configured and tested.
    privacyReady: false
  })
});

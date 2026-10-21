/*
 * Public settings only. Never put recipient lists, private email addresses,
 * API secrets or email passwords in this file.
 * See SETUP.md outside site-for-astra for the private recipient configuration.
 */
window.JEBN_CONFIG = Object.freeze({
  // Paste the Google Apps Script Web app URL ending in /exec after activation.
  // Recipients live only in the private Apps Script project, never in this file.
  formEndpoint: "",
  formTimeoutMs: 45000,
  googleAds: Object.freeze({
    // Base tag supplied by Martin's Google Ads screenshot, 20 October 2026.
    enabled: true,
    tagId: "AW-18526767007",
    conversionLabel: "" // Pending: the part after "/" in the event's send_to.
    // consent.js applies the visitor's saved/current measurement choice.
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

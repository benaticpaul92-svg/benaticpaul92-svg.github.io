/*
 * Public settings only. Never put recipient lists, private email addresses,
 * API secrets or email passwords in this file.
 * Recipients are configured in the private Apps Script project, not here.
 */
window.JEBN_CONFIG = Object.freeze({
  // Active Google Apps Script Web app; only the public endpoint belongs here.
  // Recipients live only in the private Apps Script project, never in this file.
  formEndpoint: "https://script.google.com/macros/s/AKfycbwMn4UD2xAbhB7b9x8Lr6p5sa7M62Wbn5iZyYzMGOkcTh8yXV3g1BmcQcgKmDcfahc/exec",
  formTimeoutMs: 45000,
  googleAds: Object.freeze({
    // Google Ads base tag and conversion label (public values).
    enabled: true,
    tagId: "AW-18526767007",
    conversionLabel: "HTqpCJHD-qMdEJ-PoIJF" // "Submit lead form" conversion action.
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

/* Sends a visit that carries a Google Ads location id (?loc=...) to that visitor's state page.
   Reads only the page address and a static lookup file on this site. No storage, no third party. */
(function () {
  'use strict';
  var S = {AL:'alabama',AK:'alaska',AZ:'arizona',AR:'arkansas',CA:'california',CO:'colorado',CT:'connecticut',DE:'delaware',FL:'florida',GA:'georgia',HI:'hawaii',ID:'idaho',IL:'illinois',IN:'indiana',IA:'iowa',KS:'kansas',KY:'kentucky',LA:'louisiana',ME:'maine',MD:'maryland',MA:'massachusetts',MI:'michigan',MN:'minnesota',MS:'mississippi',MO:'missouri',MT:'montana',NE:'nebraska',NV:'nevada',NH:'new-hampshire',NJ:'new-jersey',NM:'new-mexico',NY:'new-york',NC:'north-carolina',ND:'north-dakota',OH:'ohio',OK:'oklahoma',OR:'oregon',PA:'pennsylvania',RI:'rhode-island',SC:'south-carolina',SD:'south-dakota',TN:'tennessee',TX:'texas',UT:'utah',VT:'vermont',VA:'virginia',WA:'washington',WV:'west-virginia',WI:'wisconsin',WY:'wyoming'};
  try {
    var m = /[?&]loc=(\d{4,9})(?:&|$)/.exec(location.search);
    if (!m || /[?&]nogeo=1/.test(location.search) || !window.fetch) return;
    var id = m[1], root = document.documentElement, live = true;
    var show = function () { live = false; root.style.visibility = ''; };
    root.style.visibility = 'hidden';
    var timer = setTimeout(show, 1500);
    fetch('/assets/geo/' + (Number(id) % 128) + '.json').then(function (r) {
      return r.ok ? r.json() : {};
    }).then(function (map) {
      var slug = S[map[id]];
      if (slug && live) {
        location.replace('/states/' + slug + '/' + location.search + location.hash);
      } else { clearTimeout(timer); show(); }
    }).catch(function () { clearTimeout(timer); show(); });
  } catch (e) { document.documentElement.style.visibility = ''; }
})();

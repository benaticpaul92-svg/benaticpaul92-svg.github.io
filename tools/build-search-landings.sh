#!/bin/sh
# Run from repository root. Run it LAST: tools/build-assets.sh runs an older generator
# (build_studio.py) that overwrites the home page and the Florida page; this script rebuilds both.
set -eu
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.css --minify --outfile=assets/search-landings.min.css
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.js --minify --outfile=assets/search-landings.min.js
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/geo-route.js --minify --outfile=assets/geo-route.min.js
# The shared script bundle (form, consent, picture viewer): the same step as in tools/build-assets.sh,
# without that script's older page generator. Needed when assets/gallery.js or another of these files changes.
ENTRY="${TMPDIR:-/tmp}/jebn-studio-entry.js"
cat assets/site-config.js assets/project-brief.js assets/studio.js assets/google-ads.js assets/consent.js assets/site.js assets/gallery.js > "$ENTRY"
npm exec --yes --package=esbuild@0.27.4 -- esbuild "$ENTRY" --minify --outfile=assets/studio.min.js
rm -f "$ENTRY"
# Builds the home page, eight service pages, all 50 state pages, the states index,
# the privacy notice and the landscape page from tools/data.
# assets/geo/*.json comes from tools/build_geo_lookup.py (only when Google's location list changes).
python3 tools/build_search_landings.py

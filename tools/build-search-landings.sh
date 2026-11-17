#!/bin/sh
# Run from repository root. Run it LAST: tools/build-assets.sh runs an older generator
# (build_studio.py) that overwrites the home page and the Florida page; this script rebuilds both.
set -eu
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.css --minify --outfile=assets/search-landings.min.css
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.js --minify --outfile=assets/search-landings.min.js
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/geo-route.js --minify --outfile=assets/geo-route.min.js
# Builds the home page, eight service pages, all 50 state pages and the states index from tools/data.
# assets/geo/*.json comes from tools/build_geo_lookup.py (only when Google's location list changes).
python3 tools/build_search_landings.py

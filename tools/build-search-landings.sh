#!/bin/sh
# Run from repository root; run AFTER any homepage/studio regeneration.
set -eu
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.css --minify --outfile=assets/search-landings.min.css
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.js --minify --outfile=assets/search-landings.min.js
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/geo-route.js --minify --outfile=assets/geo-route.min.js
# Builds the three national landing pages and all 50 state pages from tools/data.
# assets/geo/*.json comes from tools/build_geo_lookup.py (only when Google's location list changes).
python3 tools/build_search_landings.py

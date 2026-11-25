#!/bin/sh
# Run from the repository root. Builds the style and script bundles, then every page.
set -eu
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.css --minify --outfile=assets/search-landings.min.css
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/studio.css --minify --outfile=assets/studio.min.css
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.js --minify --outfile=assets/search-landings.min.js
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/geo-route.js --minify --outfile=assets/geo-route.min.js
# The shared script bundle (form, consent, picture viewer). Needed when one of these files changes.
ENTRY="${TMPDIR:-/tmp}/jebn-studio-entry.js"
cat assets/site-config.js assets/project-brief.js assets/studio.js assets/google-ads.js assets/consent.js assets/site.js assets/gallery.js > "$ENTRY"
npm exec --yes --package=esbuild@0.27.4 -- esbuild "$ENTRY" --minify --outfile=assets/studio.min.js
rm -f "$ENTRY"
# Builds the home page, the service pages, the state pages, the states index, the company pages,
# the privacy notice and the landscape page from tools/data.
# assets/geo/*.json comes from tools/build_geo_lookup.py (only when Google's location list changes).
python3 tools/build_search_landings.py

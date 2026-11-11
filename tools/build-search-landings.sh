#!/bin/sh
# Run from repository root; run AFTER any homepage/studio regeneration.
set -eu
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.css --minify --outfile=assets/search-landings.min.css
npm exec --yes --package=esbuild@0.27.4 -- esbuild assets/search-landings.js --minify --outfile=assets/search-landings.min.js
python3 tools/build_search_landings.py

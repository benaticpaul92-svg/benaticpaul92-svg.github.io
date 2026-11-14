"""Builds assets/geo/<n>.json: Google Ads location id -> two-letter state code, for geo-route.js.

Input: Google's published geo target list (CSV) from
https://developers.google.com/google-ads/api/data/geotargets
Usage: python3 -I tools/build_geo_lookup.py /path/to/geotargets.csv
Only United States rows whose canonical name ends "<State>,United States" are kept.
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARDS = 128
CODES = {'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'}

shards = [dict() for _ in range(SHARDS)]
kept = 0
with open(sys.argv[1], newline='', encoding='utf-8') as fh:
    for row in csv.DictReader(fh):
        if row['Country Code'] != 'US' or not row['Criteria ID'].isdigit():
            continue
        parts = [p.strip() for p in row['Canonical Name'].split(',')]
        if len(parts) < 2 or parts[-1] != 'United States':
            continue
        code = CODES.get(parts[-2])
        if not code:
            continue
        shards[int(row['Criteria ID']) % SHARDS][row['Criteria ID']] = code
        kept += 1
out = ROOT/'assets/geo'
out.mkdir(exist_ok=True)
for i, s in enumerate(shards):
    (out/f'{i}.json').write_text(json.dumps(s, separators=(',', ':'), sort_keys=True))
print('kept', kept, 'ids in', SHARDS, 'files')

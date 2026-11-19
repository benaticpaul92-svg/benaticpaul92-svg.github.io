"""Makes the sample-sheet pictures in images/samples/ from the sample PDF sets.

Usage (from the repository root; the PDFs are not kept in this repository):
  python3 -I tools/build_sample_sheets.py pool-spa=/path/to/set.pdf water-feature=/path/to/set.pdf

Each PDF page must hold one full-page image, as the VOID-marked sample sets do.
Needs poppler's `pdfimages` and Pillow with WebP support.
A set's optional "skip_pages" lists the PDF pages that are not published; the other pages
are its sheets, in order. Pictures of a set that are no longer made are deleted.

The sets, their sheet names and the close-up crops are listed in tools/data/sample-sets.json,
which tools/build_search_landings.py also reads. For each set this writes:
  <key>-<nn>.webp          every sheet, SHEET_W pixels wide (opened by the viewer)
  <key>-lead-720.webp      close-up shown on the set's card, with a 1200 px version
  <key>-detail-<n>.webp    three smaller close-ups under it
A crop box is [left, top, width] as fractions of the sheet; the height follows from CROP_RATIO.

Check every sheet before it is published: no client name, address, parcel or permit number,
and no engineer's seal without that engineer's permission.
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'images/samples'
SHEET_W = 3200
CROP_RATIO = 1.6          # width / height of every close-up
Image.MAX_IMAGE_PIXELS = None


def webp(im, path, quality):
    im.save(path, 'WEBP', quality=quality, method=6)
    return path.stat().st_size


def crop(page, box, width):
    x0, y0, wf = box
    w, h = page.size
    cw = round(wf*w)
    ch = round(cw/CROP_RATIO)
    x, y = round(x0*w), round(y0*h)
    if x+cw > w or y+ch > h:
        raise SystemExit(f'crop {box} runs off the sheet')
    return page.crop((x, y, x+cw, y+ch)).resize((width, round(width/CROP_RATIO)), Image.LANCZOS)


def main():
    sources = dict(a.split('=', 1) for a in sys.argv[1:])
    sets = json.loads((ROOT/'tools/data/sample-sets.json').read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for s in sets:
        key = s['key']
        if key not in sources:
            raise SystemExit(f'no PDF given for {key}')
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(['pdfimages', '-j', sources[key], str(Path(tmp)/'p')], check=True)
            skip = set(s.get('skip_pages', []))
            files = [f for n, f in enumerate(sorted(Path(tmp).glob('p-*.jpg')), 1) if n not in skip]
            if len(files) != len(s['sheets']):
                raise SystemExit(f'{key}: {len(files)} page images to publish, {len(s["sheets"])} sheets listed')
            for old in OUT.iterdir():
                if re.fullmatch(re.escape(key)+r'-(\d\d|lead-\d+|detail-\d+)\.webp', old.name):
                    old.unlink()
            pages = [Image.open(f).convert('RGB') for f in files]
            for n, page in enumerate(pages, 1):
                h = round(page.height*SHEET_W/page.width)
                if [SHEET_W, h] != s['sheet_px'] and abs(h-s['sheet_px'][1]) > 1:
                    raise SystemExit(f'{key} sheet {n}: {SHEET_W}x{h}, sample-sets.json says {s["sheet_px"]}')
                total += webp(page.resize((SHEET_W, s['sheet_px'][1]), Image.LANCZOS), OUT/f'{key}-{n:02d}.webp', 72)
            lead = pages[s['lead']['sheet']-1]
            total += webp(crop(lead, s['lead']['box'], 1200), OUT/f'{key}-lead-1200.webp', 76)
            total += webp(crop(lead, s['lead']['box'], 720), OUT/f'{key}-lead-720.webp', 78)
            for i, d in enumerate(s['details'], 1):
                total += webp(crop(pages[d['sheet']-1], d['box'], 440), OUT/f'{key}-detail-{i}.webp', 78)
        print(key, len(pages), 'sheets')
    print('wrote', len(list(OUT.glob('*.webp'))), 'files,', round(total/1024/1024, 1), 'MB')


if __name__ == '__main__':
    main()

"""Site pages: home, the service pages, the state pages, the states index, the about,
how-it-works and sample-drawings pages, the privacy notice, the landscape page and the 404 page.

Shared header, consent panel and footer come from tools/site-chrome.html.
Data:
  tools/data/states.json        state-level content for each state page
  tools/data/local/<slug>.json  city and county permit notes with official sources
  tools/data/stamp-answers.json  short sourced answers on the engineer's stamp, for the state pages that have one
  tools/data/privacy-notice.html  the privacy notice wording
Run it with tools/build-search-landings.sh. Does not alter Ads settings or submit forms.

Sitemap dates: a page gets BUILD_DATE when it differs from its last committed version, and
keeps the committed date when it does not, so set BUILD_DATE to the day of the build first.
"""
from pathlib import Path
from html import escape
import hashlib, json, re, subprocess
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://www.jebnengineering.com'
BASE = BeautifulSoup((ROOT/'tools/site-chrome.html').read_text(), 'html.parser')
ALL_STATES = json.loads((ROOT/'tools/data/states.json').read_text())
# State pages held offline. While a slug is listed here no page is built for that state,
# nothing links to it and its address is taken out of the sitemap, so the address answers
# with the 404 page. To restore a page: put its record back in tools/data/states.json and its
# notes back in tools/data/local/ (both are in this repository's history), take the slug out
# of this set, put the state back in assets/geo-route.js and rebuild.
OFFLINE = {'north-carolina'}
STATES = {slug: rec for slug, rec in ALL_STATES.items() if slug not in OFFLINE}
# "Do I need an engineer's stamp for a pool in <State>?" Each answer states only what the official pages listed with it say.
STAMP_ANSWERS = json.loads((ROOT/'tools/data/stamp-answers.json').read_text())
BUILD_DATE = '2026-11-25'   # sitemap date given to pages whose content changed in this build
CHANGED = set()             # addresses of the pages that differ from their last committed version; filled by shell()
_GIT = None
# Time-bound facts in the state data: after the due date the build warns (stderr only) until the sentence is checked against its source.
RECHECK = [('tools/data/local/wyoming.json', 'adopt the 2026 NEC on January 1, 2027', '2027-01-01'), ('tools/data/states.json', 'mandatory April 1, 2027', '2027-04-01'), ('tools/data/states.json', 'on the council\u2019s 2026 agenda', '2027-01-01'), ('tools/data/states.json', 'awaits final approval', '2027-01-01'), ('tools/data/states.json', 'proposed but not yet enacted', '2027-01-01'), ('tools/data/states.json', 'enacted but is not yet issued', '2027-01-01')]


def last_committed(rel):
    """Text of a file as last committed, which is what the live site serves after a publish.
    '' when that commit has no such file, None when git cannot be asked (then the copy on disk is the reference)."""
    global _GIT
    if _GIT is None:
        try:
            top = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
            head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '-q', '--verify', 'HEAD'], capture_output=True)
            # A copy of the site inside some other repository must not be compared with that repository.
            _GIT = top.returncode == 0 and head.returncode == 0 and Path(top.stdout.strip()).resolve() == ROOT
        except OSError:
            _GIT = False
    if not _GIT:
        return None
    r = subprocess.run(['git', '-C', str(ROOT), 'show', f'HEAD:{rel}'], capture_output=True)
    return r.stdout.decode('utf-8') if r.returncode == 0 else ''

# Every service page, in the order used for the home page cards and the footer links.
SERVICE_LINKS = [
    ('/services/pool-permit-drawings/', 'Pool permit drawings', 'Site plan, pool plan, sections and details drawn to your permit office’s checklist.'),
    ('/pool/', 'Pool construction drawings', 'Coordinated plans, sections, construction details and equipment layouts.'),
    ('/services/pool-structural-engineering/', 'Pool structural drawings', 'Shell sections, steel schedules and details drafted from your engineer’s design.'),
    ('/services/pool-hydraulic-design/', 'Plumbing & hydraulic drawings', 'Piping plans, schematics, equipment layouts and pump head (TDH) calculation sheets.'),
    ('/services/pool-shop-drawings/', 'Pool shop drawings', 'Tile, coping, gutter, steel and equipment details for fabrication and installation.'),
    ('/services/outsourced-pool-drafting/', 'Outsourced pool drafting', 'Extra drafting capacity for builders and designers, drawn on your standards.'),
    ('/services/pool-drawings-for-engineer-of-record/', 'Drawings for your engineer of record', 'Drawing sets drafted to the design of the engineer who seals your project.'),
    ('/services/pool-engineering/', 'How the engineer’s seal works', 'Who directs the engineering, who seals the set, and what JEBN drafts.'),
]

# Pages for particular project types. The wording and its sources live in tools/data/topic-pages.json.
TOPICS = json.loads((ROOT/'tools/data/topic-pages.json').read_text())
TOPIC_LINKS = [('/'+t['path']+'/', t['nav_label'], t['card_text']) for t in TOPICS]
RELATED_TOPICS = {}   # address of a main service page -> the project-type pages that belong beside it
for _t in TOPICS:
    for _href in _t['related_services']:
        RELATED_TOPICS.setdefault(_href, []).append(('/'+_t['path']+'/', _t['nav_label']))

# ---------------------------------------------------------------- the company and the seal wording

# The company as registered. The address is a mailing address, not an office, and the pages say so.
COMPANY = 'JEBN Engineering LLC'
COMPANY_KIND = 'a Florida limited liability company'
MAIL_STREET, MAIL_CITY, MAIL_REGION, MAIL_ZIP = '7901 4th St N, Ste 300', 'St. Petersburg', 'FL', '33702'
MAIL_ADDRESS = f'{MAIL_STREET}, {MAIL_CITY}, {MAIL_REGION} {MAIL_ZIP}'
FLORIDA_DOCUMENT = 'L26000581157'   # the company's document number at the Florida Division of Corporations
EMAIL = 'benatic@jebnengineering.com'

# State pages that say only that a licensed engineer must direct and seal, without the line about asking one.
NO_ENGINEER_OFFER = {'georgia', 'louisiana', 'nevada', 'south-carolina', 'texas'}


# JEBN prepares the drawings and does not seal them. The two functions below supply the standard seal
# sentences. The header facts, the phone strip, HERO_SMALL and the seal page text are written out where
# they are used, so change those too when the wording changes.
def seal_short(state=None):
    return ('JEBN does not seal drawings. If your permit office requires an engineer’s seal, a Professional Engineer licensed in '
            f'{state or "your state"} must direct the engineering and seal the set.')


def seal_answer(state=None, offer=True):
    where = state or 'your state'
    text = ('JEBN prepares the drawings and does not seal them. Where your permit office requires an engineer’s seal, a Professional Engineer '
            f'licensed in {where} must direct the engineering and seal the set.')
    if offer:
        text += (f' You can use your own engineer, or we can ask one licensed in {where} to take your project. '
                 'That engineer decides whether to take it and sets the fee for the engineering.')
    return text


TURNAROUND = ('Residential drawing preparation takes 2 business days after we receive all project inputs. Where your permit needs an '
              'engineer’s seal, the engineer’s work takes additional time, and so does the permit office’s own review.')

# Largest or best-known city, used only as the form placeholder example.
CITY = {'alabama':'Birmingham','alaska':'Anchorage','arizona':'Phoenix','arkansas':'Little Rock','california':'San Diego','colorado':'Denver','connecticut':'Stamford','delaware':'Wilmington','florida':'Tampa','georgia':'Atlanta','hawaii':'Honolulu','idaho':'Boise','illinois':'Naperville','indiana':'Carmel','iowa':'Des Moines','kansas':'Overland Park','kentucky':'Lexington','louisiana':'New Orleans','maine':'Portland','maryland':'Annapolis','massachusetts':'Boston','michigan':'Grand Rapids','minnesota':'Minneapolis','mississippi':'Jackson','missouri':'St. Louis','montana':'Billings','nebraska':'Omaha','nevada':'Las Vegas','new-hampshire':'Manchester','new-jersey':'Paramus','new-mexico':'Albuquerque','new-york':'Huntington','north-dakota':'Fargo','ohio':'Columbus','oklahoma':'Oklahoma City','oregon':'Portland','pennsylvania':'Pittsburgh','rhode-island':'Providence','south-carolina':'Charleston','south-dakota':'Sioux Falls','tennessee':'Nashville','texas':'Houston','utah':'Salt Lake City','vermont':'Burlington','virginia':'Virginia Beach','washington':'Seattle','west-virginia':'Charleston','wisconsin':'Madison','wyoming':'Cheyenne'}

def asset(name):
    p = ROOT/'assets'/name
    return '/assets/'+name+'?v='+hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def geo_route_tag():
    # Inlined so a paid visit starts the state lookup without first downloading a separate script.
    return '<script>' + (ROOT/'assets/geo-route.min.js').read_text().strip() + '</script>'


def root_file(name):
    """Address of a file in the site root with a stamp of its content, so a browser fetches a changed icon again."""
    return '/'+name+'?v='+hashlib.sha256((ROOT/name).read_bytes()).hexdigest()[:12]


def icon_links():
    # The .ico is for browsers that do not read SVG icons; the touch icon is what phones put on the home screen.
    return (f'<link rel="icon" href="{root_file("favicon.ico")}" sizes="32x32">'
            f'<link rel="icon" href="{root_file("favicon.svg")}" type="image/svg+xml">'
            f'<link rel="apple-touch-icon" href="{root_file("apple-touch-icon.png")}">'
            '<link rel="manifest" href="/site.webmanifest">')


def name_of(slug):
    return slug.replace('-', ' ').title()


def clean(text):
    return escape(re.sub(r'\s+', ' ', str(text or '')).strip())


def safe_url(url):
    url = str(url or '').strip()
    return url if re.match(r'^https?://[^\s"<>]+$', url) else ''


def ext_link(url, label):
    url = safe_url(url)
    if not url:
        return clean(label)
    return f'<a href="{escape(url)}" target="_blank" rel="noopener">{clean(label)}</a>'


REPLY_TIME = 'We reply by email within 24 hours.'


def next_steps(send):
    """Shown only after the receiver has accepted a request. It repeats the reply time and makes no other promise."""
    return ('<div class="next-steps" data-next-steps="" hidden=""><h3>What happens next</h3><ol>'
            f'<li>Your reference is <strong data-enquiry-ref=""></strong>. {REPLY_TIME}</li>'
            f'<li>{send}</li>'
            '<li><a data-files-draft="" href="mailto:benatic@jebnengineering.com?subject=JEBN%20project%20enquiry">Email your files</a>. '
            'The link opens your email app with your reference filled in.</li>'
            '</ol></div>')


NEXT_STEPS_POOL = next_steps('If you have them, send your survey or site plan, your sketch or existing drawings, and any permit office checklist or review comments.')
NEXT_STEPS_SITE = next_steps('If you have them, send your survey or site plan, photos of the site, and your sketch or existing drawings.')


def form(title, state=None, city=None, notes_placeholder=None, pool=True):
    doc = BeautifulSoup((ROOT/'tools/enquiry-form.html').read_text(), 'html.parser')
    f = doc.form
    f['data-search-enquiry'] = title
    f['aria-label'] = 'Quote request'
    doc.select_one('legend').string = 'Your quote request'
    doc.select_one('.form-intro').string = 'Name and email are enough to start. Your free quote lists the sheets, the revisions included and the delivery date before you commit.'
    # Shown for the instant before the form script runs; the script then sets the live status and enables the button.
    doc.select_one('[data-form-status]').string = 'Fields marked required are needed.'
    doc.select_one('button[type="submit"]').string = 'Get my quote'
    notes = doc.select_one('[name="message"]')
    notes['name'] = 'project_notes'; notes['id'] = 'enquiry-notes'; notes['rows'] = '2'; notes.attrs.pop('required', None)
    notes['placeholder'] = notes_placeholder or 'e.g. 15 x 30 ft pool with spa, builder’s sketch, permit office checklist'
    label = doc.select_one('label[for="enquiry-message"]'); label['for'] = 'enquiry-notes'; label.string = 'What do you need? (optional)'
    hidden = doc.new_tag('input', attrs={'type': 'hidden', 'name': 'message', 'value': title+' quote request.'})
    doc.fieldset.append(hidden)
    doc.select_one('label[for="enquiry-location"]').string = ('Where is the pool?' if pool else 'Where is the site?')+' City and state (optional)'
    loc = doc.select_one('[name="location"]')
    loc['placeholder'] = f'e.g. {city}, {state}' if state else 'e.g. Tampa, FL'
    if state:
        loc['value'] = state
    doc.select_one('.optional-fields summary').string = ('Pool builder? ' if pool else '')+'Add company and timeline (optional)'
    privacy = doc.select_one('.form-privacy')
    privacy.clear(); privacy.append('We use your details to reply to this request and quote the work. ')
    a = doc.new_tag('a', href='/privacy/'); a.string = 'Privacy notice'; privacy.append(a)
    reply = doc.new_tag('p', attrs={'class': 'form-reply'}); reply.string = REPLY_TIME
    privacy.insert_before(reply)
    doc.select_one('[data-email-draft]').string = 'Prefer email? Open an email draft'
    doc.select_one('[data-new-enquiry]').string = 'Send another request'
    # Hidden until a request is accepted. The form script then fills in the reference and the link.
    doc.select_one('[data-form-status]').insert_after(BeautifulSoup(NEXT_STEPS_POOL if pool else NEXT_STEPS_SITE, 'html.parser').div)
    return str(doc)


def package_rows(state=None):
    office = f'your {state} permit office' if state else 'your permit office'
    rows = [
        ('Site & pool layout', 'Pool position, dimensions, depths and sections, coordinated with the site information you supply.'),
        ('Construction details', 'Pool shell and reinforcement details drawn from your engineer’s design or your builder’s standard details, with drawing references for your contractor.'),
        ('Plumbing & equipment', 'Circulation layout, pipe sizes, equipment schedules and a pump head (TDH) calculation sheet where included in your quote.'),
        ('Permit coordination', f'The set is drawn to the checklist {office} publishes, and changes that answer plan review comments are drawn within the revisions in your quote.'),
    ]
    return ''.join(f'<li><span class="sheet-number" aria-hidden="true">{i:02d}</span><div><h3>{label}</h3><p>{text}</p></div></li>' for i, (label, text) in enumerate(rows, 1))


HERO_FACTS = [('Drawing preparation', '2 business days'), ('File delivery', 'DWG + PDF'), ('Engineer’s seal', 'Not included')]
HERO_STRIP = '2 business days · DWG + PDF · Seal not included'
HERO_SMALL = 'For residential pool drawings, the 2 business days start when we have all project inputs. JEBN does not seal drawings. Where your permit needs an engineer’s seal, the engineer’s work takes additional time, and so does permit approval.'


def panel_quote_html():
    """One complete client comment under the form (Aaron Baribeau, a US pool client)."""
    q, who, _ = CLIENT_QUOTES[4]
    return f'<figure class="panel-quote"><blockquote><p>“{escape(q)}”</p></blockquote><figcaption>{escape(who)}</figcaption></figure>'


def hero(kicker, h1, lead, form_html, crumbs='', facts=None, small=None, second=('See sample sheets ↓', '#samples'), form_heading='Get your pool plan quote.', panel_quote=True, picture='', strip=None, jump=None):
    facts_html = ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in (facts or HERO_FACTS))
    quote = panel_quote_html() if panel_quote else ''
    strip = HERO_STRIP if strip is None and not facts else (strip or '')
    strip_html = f'<p class="hero-strip">{strip}</p>' if strip else ''
    # On phones the form sits between the hero text and the first section, so a link jumps past it.
    jump_html = f'<p class="hero-jump"><a href="{jump[1]}">{jump[0]} <span aria-hidden="true">↓</span></a></p>' if jump else ''
    return f'''<section class="search-hero blue{' hero-'+picture if picture else ''}" aria-labelledby="hero-heading"><div class="wrap search-grid"><div class="search-copy">{crumbs}<span class="eyebrow">{kicker}</span><h1 id="hero-heading">{h1}</h1><p class="lead">{lead}</p>{jump_html}{strip_html}<div class="actions"><a class="button primary" href="#contact">Get my quote <span aria-hidden="true">→</span></a><a class="text-link" href="{second[1]}">{second[0]}</a></div></div>
<aside class="quote-panel" id="contact" aria-labelledby="contact-heading"><span class="eyebrow">FREE QUOTE · NO PAYMENT REQUIRED</span><h2 id="contact-heading" tabindex="-1">{form_heading}</h2>{form_html}{quote}</aside>
<div class="search-facts"><dl class="delivery-facts">{facts_html}</dl><p class="small">{small or HERO_SMALL}</p><p class="search-contact">Your contact: <strong>Benatic Paul Martin</strong><br>{COMPANY} · <a href="mailto:{EMAIL}">{EMAIL}</a><br><a href="/about/">About {COMPANY}</a></p></div></div></section>'''


def sheet_rows(rows):
    return ''.join(f'<li><span class="sheet-number" aria-hidden="true">{i:02d}</span><div><h3>{label}</h3><p>{text}</p></div></li>' for i, (label, text) in enumerate(rows, 1))


SET_SHEETS = [
    'Cover sheet with general notes',
    'Site plan with setbacks and the pool barrier (fence, walls, gates)',
    'Pool plan with dimensions and depths',
    'Long section and cross sections',
    'Reinforcement and structural details',
    'Steps, benches and raised features',
    'Hydraulic schematic and pipe sizes',
    'Pump head (TDH) calculation sheet and equipment schedule',
]


def package_section(state=None, links='', rows=None, heading=None, lead=None, sid='package-section', typical=None):
    """The drawing package. Without `rows` it shows the general rows and the list of typical sheets; `typical` forces that list on or off."""
    heading = (heading or 'What a pool permit<br>drawing set includes.').replace('<br>', ' <br>')   # the space keeps words apart where the break is hidden on phones
    lead = lead or 'Your quote lists every sheet, the revisions included and the delivery date before you commit.'
    body = sheet_rows(rows) if rows else package_rows(state)
    if typical is None:
        typical = not rows
    set_list = ''
    if typical:
        set_list = ('<div class="set-list"><p class="set-title">Typical sheets in a residential permit set</p><ul>'
                    + ''.join(f'<li>{t}</li>' for t in SET_SHEETS)
                    + '</ul><p class="set-note">Your quote lists the sheets for your project.</p></div>')
    return f'''<section class="section" id="{sid}" aria-labelledby="package-heading"><div class="wrap package-editorial{' has-set' if set_list else ''}" id="package"><div><span class="eyebrow">YOUR DRAWING PACKAGE</span><h2 id="package-heading">{heading}</h2><p class="lead">{lead}</p><p class="package-note">Request a full package or help with existing plans.</p>{set_list}<a class="text-link" href="#contact">Get a quote for this set →</a>{links}</div><ol class="sheet-list">{body}</ol></div></section>'''


INPUT_ITEMS = [
    ('Project location', 'City, state and permit office, if known.'),
    ('Site information', 'Survey or site plan and known site constraints.'),
    ('Pool layout', 'Sketch, dimensions, depths and proposed features.'),
    ('Existing work', 'Plans, equipment preferences and permit review comments.'),
]


def inputs_section(heading, para, items=None):
    lis = ''.join(f'<li><strong>{k}</strong>{v}</li>' for k, v in (items or INPUT_ITEMS))
    return f'''<section class="section inputs-section" id="inputs" aria-labelledby="inputs-heading"><div class="wrap input-grid"><div><span class="eyebrow">WHAT TO SEND</span><h2 id="inputs-heading">{heading}</h2><p>{para}</p><p>You do not need every document to request a quote. After the first reply, you can share files by email.</p><a class="text-link" href="/resources/pool-project-checklist/">Open the project input checklist ↗</a></div><ul class="input-list">{lis}</ul></div></section>'''


def step_items(steps):
    return ''.join(f'<li><span class="step-n" aria-hidden="true">{i}</span><h3>{k}</h3><p>{v}</p></li>' for i, (k, v) in enumerate(steps, 1))


DELIVERY_STEPS = [
    ('Confirm the scope', 'We review your request and reply by email within 24 hours with questions or a scoped quote. We identify missing inputs and what your permit office asks for.'),
    ('Prepare the drawings', 'Residential drawing preparation takes 2 business days after all project inputs are received. Where your permit needs an engineer’s seal, the engineer’s work takes additional time.'),
    ('Deliver', 'You receive the PDF set for your permit submission and the DWG files. Your quote states the revisions included. Your permit office decides approval and timing.'),
]


def delivery_section(state=None, offer=True, steps=None):
    return f'''<section class="section blue" id="delivery" aria-labelledby="delivery-heading"><div class="wrap"><span class="eyebrow">FROM QUOTE TO DELIVERY</span><h2 id="delivery-heading">Three steps to your drawing set.</h2><ol class="delivery-steps">{step_items(steps or DELIVERY_STEPS)}</ol><div class="review-note"><h3>Who seals the drawings</h3><p>{seal_answer(state, offer)} The permit office decides approval. If it sends comments, send them to us. Your quote states the revisions included.</p><a class="text-link" href="/services/pool-engineering/">How the engineer’s seal works →</a></div><details class="optional-concept"><summary>Optional: 3D pool visualization</summary><p>A 3D view can help you explore the proposed layout and materials. Ask to include it as a separate item alongside the drawing package.</p></details><div class="actions"><a class="button primary" href="#contact">Get my quote <span aria-hidden="true">→</span></a></div></div></section>'''


def state_directory(summary='Choose your state for local permit notes'):
    links = ''.join(f'<a href="/states/{s}/">{name_of(s)}</a>' for s in sorted(STATES))
    return f'<details class="state-directory"><summary>{summary}</summary><nav class="state-grid" aria-label="State pages">{links}</nav></details>'


def coverage_section(extra=''):
    return f'''<section class="coverage-line" id="coverage" aria-label="USA coverage"><div class="wrap"><p><strong>{COMPANY}.</strong> We draft pool drawings for US permit submissions.</p><a href="/states/">View state pages</a></div><div class="wrap coverage-more">{extra}{state_directory()}</div></section>'''


def service_links(current=''):
    """Text links to the other service pages, for the package column."""
    links = ' · '.join(f'<a href="{href}">{label}</a>' for href, label, _ in SERVICE_LINKS if href != current)
    more = ' · '.join(f'<a href="{href}">{escape(label)}</a>' for href, label in RELATED_TOPICS.get(current, []))
    more = f'<p class="package-links"><strong>By project type:</strong> {more}</p>' if more else ''
    return f'<p class="package-links"><strong>Related services:</strong> {links}</p>{more}'


# Client feedback, kept word for word from the earlier landscape page. Do not edit the quotes.
# The labels under the quotes are ours and name the client and the place only.
# One comment and one rated-project chip from the earlier page are not shown at present (held on 20 November 2026).
CLIENT_QUOTES = [
    ("JEBN did a great job on my pool and landscape project. As a main contractor in Dubai, they're now my go-to for all our pool and landscape solutions.", 'Abdellaziz · Main contractor · Dubai, UAE', False),
    ("We build hotels and chose JEBN for our pool and outdoor-space design. The pool area had tough constraints — pump-room placement and a tricky overflow — but their experience brought practical solutions and we finished successfully. They're our go-to for pool and landscape technical work.", 'Judy Lee · Hotel developer · Taiwan', False),
    ("I came to JEBN with an idea for a custom cold-plunge pool and they nailed the technical design from the first concept. With their full solution, I'm now producing custom cold-plunge pools across Europe.", 'Oliver T. · Cold-plunge pools · United Kingdom', False),
    ("Martin was such a pleasure to work with. His work is professional and detailed, and he was able to accommodate any of my requests and features. He even went out of his way to help with parts of the project that were outside the scope we originally agreed on, making my life easier.", 'Nathan · 5.0★ · Design & drawings', True),
    ("We chose JEBN for our swimming-pool technical and construction drawings, and the work was highly professional throughout.", 'Aaron Baribeau · Pool construction drawings · USA', False),
    ("Easy to work with and did a great job!", 'Charles · British Columbia, Canada', False),
]
CLIENT_RATED = ['5.0★ Cold-water pool design', '4.9★ Lawrence Residence', '4.7★ Pool design · 5-day turnaround']

# Pool pages: Aaron Baribeau's comment sits under the quote form; the section shows the other five, two open and three folded.
POOL_QUOTE_ORDER = [3, 5, 1, 2, 0]
STARS = '<span class="stars" role="img" aria-label="5 out of 5 stars">★★★★★</span>'


def quote_cards(items):
    return ''.join(f'<figure class="client-quote"><blockquote><p>{escape(q)}</p></blockquote><figcaption>{STARS if stars else ""}{escape(who)}</figcaption></figure>' for q, who, stars in items)


def clients_section(lead, order=None, visible=None, rated=True):
    items = [CLIENT_QUOTES[i] for i in order] if order else CLIENT_QUOTES
    shown, more = (items[:visible], items[visible:]) if visible else (items, [])
    extra = f'<details class="more-quotes"><summary>Show {len(more)} more client comments</summary><div class="quote-grid">{quote_cards(more)}</div></details>' if more else ''
    chips = ''
    if rated:
        chips = '<p class="rated-label">Recent rated projects</p><ul class="rated-list">'+''.join(f'<li>{escape(r)}</li>' for r in CLIENT_RATED)+'</ul>'
    return f'''<section class="section quotes-section" id="clients" aria-labelledby="clients-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">CLIENT FEEDBACK</span><h2 id="clients-heading">What clients say.</h2></div><div><p>{lead}</p></div></div><div class="quote-grid">{quote_cards(shown)}</div>{extra}{chips}</div></section>'''


def pool_clients():
    return clients_section('Feedback from clients on pool and water feature drawing work.', POOL_QUOTE_ORDER, visible=2, rated=False)


# Sample drawing sets, shown under the hero: every sheet of each set opens in the viewer.
# The sets, their sheet names and the close-up crops are listed in tools/data/sample-sets.json.
# The pictures in images/samples/ are made from the owner's VOID-marked PDF sets by tools/build_sample_sheets.py.
SAMPLE_SETS = json.loads((ROOT/'tools/data/sample-sets.json').read_text())


def pool_section_art():
    """Decorative line drawing of a pool long section (not a design; no values)."""
    dots = []
    x = 172
    while x <= 340:
        dots.append((x, 94+(x-156)*26/190+6.5)); x += 22
    x = 358
    while x <= 480:
        dots.append((x, 126)); x += 22
    dots += [(91, y) for y in range(48, 104, 18)] + [(493, y) for y in range(50, 122, 18)]
    circles = ''.join(f'<circle cx="{cx:.0f}" cy="{cy:.1f}" r="1.7"/>' for cx, cy in dots)
    return ('<svg class="section-art" viewBox="0 0 560 150" aria-hidden="true" focusable="false"><g fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 40H86M498 40h58"/><path d="M96 40v14h20v14h20v14h20v12l190 26h142V40"/><path d="M86 40v70l258 22h154V40"/>'
            '<path d="M97 52h390" stroke-dasharray="10 4 2 4"/><path d="M286 44l6 8 6-8z"/>'
            '<path d="M96 22h392M96 15v14M488 15v14"/><path d="M516 52v68M509 52h14M509 120h14"/><path d="M400 120v6h26v-6"/></g>'
            f'<g fill="currentColor">{circles}</g>'
            '<g fill="currentColor" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="9" letter-spacing=".8">'
            '<text x="292" y="12" text-anchor="middle">LENGTH</text><text x="528" y="89">DEPTH</text><text x="304" y="47">WATER LEVEL</text><text x="170" y="76">STEPS</text><text x="386" y="146">MAIN DRAIN</text></g></svg>')


def viewer_dialog(first, size=(1000, 750), steps=False):
    """Picture preview used by assets/gallery.js (bundled in studio.min.js). With steps, the viewer moves through a drawing set."""
    step_row = '<div class="viewer-steps" data-viewer-steps hidden><button type="button" data-viewer-previous aria-label="Previous sheet">← Previous<span> sheet</span></button><span data-viewer-position aria-live="polite"></span><button type="button" data-viewer-next aria-label="Next sheet">Next<span> sheet</span> →</button></div>' if steps else ''
    return f'''<dialog class="project-viewer{' has-steps' if steps else ''}" id="project-viewer" aria-labelledby="viewer-heading"><div class="viewer-top"><h2 id="viewer-heading">Project preview</h2><button class="viewer-close" type="button" data-close-viewer autofocus>Close</button></div>{step_row}<p data-image-status role="status"></p><img src="/images/{first}" alt="" width="{size[0]}" height="{size[1]}" loading="lazy" decoding="async" hidden><p data-description></p><a href="/images/{first}" data-full-image target="_blank" rel="noopener">Open full image in a new tab</a></dialog>'''


def preview_cards(items, tag='View larger'):
    return ''.join(f'''<div class="portfolio-card"><a class="project-preview-link" href="/images/{img}" data-project-preview aria-label="{tag}: {escape(name)}"><div class="portfolio-image"><img src="/images/{img}" alt="{escape(alt)}" width="1000" height="750" loading="lazy" decoding="async"><span class="view-tag">{tag}</span></div></a><div class="portfolio-content"><h3>{name}</h3><p>{text}</p></div></div>''' for img, alt, name, text in items)


def sample_set_card(s, first=False):
    """One drawing set: a large close-up, three small ones, the description and the list of the sheets shown."""
    key, sheets = s['key'], s['sheets']
    src = lambda n: f'/images/samples/{key}-{n:02d}.webp'
    title = lambda n: f'{sheets[n-1][0]} · {sheets[n-1][1]}'

    def opener(n, inner):
        return (f'<a class="project-preview-link" href="{src(n)}" data-project-preview data-set="{key}" '
                f'aria-label="View larger: sheet {escape(title(n))}">{inner}</a>')

    lazy = '' if first else ' loading="lazy"'
    lead = s['lead']
    lead_img = (f'<img src="/images/samples/{key}-lead-720.webp" srcset="/images/samples/{key}-lead-720.webp 720w, /images/samples/{key}-lead-1200.webp 1200w" '
                f'sizes="(max-width:760px) 92vw, 580px" alt="{escape(lead["alt"])}" width="1200" height="750"{lazy} decoding="async">')
    details = ''.join('<li>' + opener(d['sheet'], f'<img src="/images/samples/{key}-detail-{i}.webp" alt="{escape(d["alt"])}" width="440" height="275" loading="lazy" decoding="async">') + '</li>'
                      for i, d in enumerate(s['details'], 1))
    rows = ''.join(f'<li><a href="{src(n)}" data-project-preview data-set="{key}" data-title="{escape(title(n))}"><b>{escape(no)}</b> {escape(name)}</a></li>'
                   for n, (no, name) in enumerate(sheets, 1))
    count = len(sheets)
    set_text = f'{s["tag"].capitalize()}. {s["note"]}'
    return f'''<article class="sample-set" aria-labelledby="set-{key}"><div class="set-lead">{opener(lead['sheet'], lead_img + '<span class="view-tag">View larger</span>')}</div><ul class="set-details">{details}</ul><div class="set-text"><span class="sheet-tag">{s['tag']} · {count} SHEETS</span><h3 id="set-{key}">{escape(s['title'])}</h3><p>{escape(s['text'])} <strong>{escape(s['note'])}</strong></p><a class="text-link" href="{src(1)}" data-project-preview data-set="{key}">View all {count} sheets →</a><details class="sheet-index"><summary>Sheet list</summary><ol data-sheet-list="{key}" data-set-text="{escape(set_text)}">{rows}</ol></details></div></article>'''


AUDIENCE_ICONS = (
    '<path d="M3 11.5l9-7.5 9 7.5"/><path d="M5.5 10v10h13V10"/><path d="M10 20v-5.5h4V20"/>',
    '<path d="M3 17L17 3l4 4L7 21z"/><path d="M14 6l1.6 1.6M11 9l1.6 1.6M8 12l1.6 1.6"/>',
)


def audience_section(state=None):
    """Two entry points: the homeowner with a permit to get, and the pool builder who needs drafting capacity."""
    office = f'your {state} permit office' if state else 'your permit office'
    where = f' in {state}' if state else ''
    return f'''<section class="section audience-section" id="who" aria-labelledby="who-heading"><div class="wrap"><h2 class="sr-only" id="who-heading">Who we work with</h2><div class="audience-grid"><div class="audience-card">{ICON(AUDIENCE_ICONS[0])}<span class="eyebrow">HOMEOWNERS{where.upper()}</span><h3>Your permit office asked for pool plans.</h3><p>Send your layout or your builder’s sketch and the name of {office}. We prepare the drawings its checklist asks for. {seal_short(state)}</p><a class="text-link" href="#contact">Get my quote →</a></div><div class="audience-card">{ICON(AUDIENCE_ICONS[1])}<span class="eyebrow">POOL BUILDERS AND CONTRACTORS{where.upper()}</span><h3>Send us the jobs your drafting team cannot fit in.</h3><p>Plans, sections and details drawn on your title block and CAD standards, delivered as DWG and PDF files, job by job. Priced per set or per sheet, agreed before work starts.</p><a class="text-link" href="/services/outsourced-pool-drafting/">Drafting for pool builders →</a></div></div></div></section>'''


def samples_section(eyebrow='SAMPLE DRAWINGS', heading='Sample drawing sets.'):
    cards = ''.join(sample_set_card(s, first=(i == 0)) for i, s in enumerate(SAMPLE_SETS))
    first = SAMPLE_SETS[0]
    return f'''<section class="section samples-section" id="samples" aria-labelledby="samples-heading"><div class="wrap"><div class="samples-head"><div><span class="eyebrow">{eyebrow}</span><h2 id="samples-heading">{heading}</h2><p>Sheets from two drawing sets. Client and site names are removed and each sheet is marked VOID. Select a picture to see the sheet larger, then step through the set.</p></div>{pool_section_art()}</div><div class="set-grid">{cards}</div></div></section>{viewer_dialog(f"samples/{first['key']}-01.webp", first['sheet_px'], steps=True)}'''


ICON = lambda d: f'<svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
SERVICE_ICONS = {
    '/services/owner-builder-pool-plans/': '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M9.5 14.5l2 2 3.5-4"/>',
    '/services/pool-site-plan-barrier-plan/': '<path d="M4 20V9l2-2 2 2v11M10 20V9l2-2 2 2v11M16 20V9l2-2 2 2v11"/><path d="M4 13h16M4 17h16"/>',
    '/services/spa-addition-pool-remodel-drawings/': '<rect x="3" y="9" width="13" height="10" rx="1"/><circle cx="17.5" cy="7.5" r="3.5"/><path d="M6 14c1.4 1 2.8-1 4.2 0s2.8-1 4.2 0"/>',
    '/services/vanishing-edge-pool-drawings/': '<path d="M2 8h13v11"/><path d="M2 12c2 1.2 4-1.2 6.5 0s4.5-1.2 6.5 0"/><path d="M18.5 8v11M21.5 11v8"/>',
    '/services/rooftop-elevated-pool-drawings/': '<path d="M5 21V10h14v11"/><path d="M3 10h18"/><path d="M7 6.5c1.6 1 3.3-1 5 0s3.4-1 5 0"/><path d="M9 14h2M13 14h2M9 18h2M13 18h2"/>',
    '/services/commercial-pool-plan-review-drawings/': '<path d="M9 3h6v3H9z"/><path d="M9 5H6v16h12V5h-3"/><path d="M9 14l2 2 4-4.5"/>',
    '/services/pool-engineering/': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5.5"/><path d="M9.8 12.2l1.6 1.6 3-3.4"/>',
    '/services/pool-permit-drawings/': '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/><path d="M9.5 14.5l2 2 3.5-4"/>',
    '/pool/': '<path d="M2 7h4v10h12V7h4"/><path d="M6 10.5c2 1.2 4-1.2 6 0s4-1.2 6 0"/>',
    '/services/pool-structural-engineering/': '<path d="M4 8h16M4 12h16M4 16h16M8 4v16M12 4v16M16 4v16"/>',
    '/services/pool-hydraulic-design/': '<circle cx="10" cy="14" r="5"/><path d="M10 9V4h8M15 14h6M10 14l2.2-2.2"/>',
    '/services/pool-drawings-for-engineer-of-record/': '<path d="M3 6h18M12 6v14"/><path d="M8 20h8"/><path d="M6 6V4M18 6V4"/>',
    '/services/pool-shop-drawings/': '<circle cx="10" cy="10" r="6"/><path d="M14.5 14.5L20 20M7.5 10h5M10 7.5v5"/>',
    '/services/outsourced-pool-drafting/': '<path d="M4 20l1-4L16 5l3 3L8 19z"/><path d="M14 7l3 3"/>',
    '/resources/pool-project-checklist/': '<path d="M10 6h10M10 12h10M10 18h10"/><path d="M3.5 6l1.2 1.2L7 5M3.5 12l1.2 1.2L7 11M3.5 18l1.2 1.2L7 17"/>',
}


def faq_block(eyebrow, heading, items):
    body = ''.join(f'<details><summary>{clean(q)}</summary><p>{clean(a)}</p></details>' for q, a in items)
    return f'<section class="section faq-section" id="faq" aria-labelledby="faq-heading"><div class="wrap faq-layout"><div><span class="eyebrow">{eyebrow}</span><h2 id="faq-heading">{heading}</h2></div><div class="faq-list">{body}</div></div></section>'


def faq_schema(canonical, items):
    return {'@type': 'FAQPage', '@id': canonical+'#faq', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in items]}


def company_block():
    """The company's registered name, what it is, and its mailing address, shown in every footer."""
    return (f'<div class="footer-company"><p class="company-name">{COMPANY}</p>'
            f'<p>{COMPANY_KIND[0].upper()+COMPANY_KIND[1:]}.</p>'
            f'<p>Mailing address: {MAIL_ADDRESS} · <a href="mailto:{EMAIL}">{EMAIL}</a></p></div>')


def shell(path, title, description, body, schema, head_extra='', out=None, noindex=False, brand=' | JEBN'):
    header = ''.join(str(BASE.select_one(s)) for s in ['.skip-link', '.utility-bar', '.site-header', '#privacy-choices'])
    footer_links = ''.join(f'<a href="{href}">{label}</a>' for href, label, _ in SERVICE_LINKS)
    footer_links += ''.join(f'<a href="{h}">{escape(l)}</a>' for h, l, _ in TOPIC_LINKS) + '<a href="/landscape/">Landscape design</a>'
    footer = (str(BASE.select_one('.site-footer')).replace('<!--SERVICE_LINKS-->', footer_links)
              .replace('<!--COMPANY-->', company_block()).replace('<!--COPYRIGHT-->', f'© 2026 {COMPANY}'))
    # A menu or footer link to a section this page does not have points at that section of the home page.
    for anchor in ('services', 'package', 'coverage', 'contact'):
        if f'id="{anchor}"' not in body:
            header, footer = (x.replace(f'href="#{anchor}"', f'href="/#{anchor}"') for x in (header, footer))
    has_form = 'id="contact"' in body
    # Phones: a quote bar that appears once the form is out of view (assets/search-landings.js shows and hides it).
    sticky = '<a class="sticky-cta" href="#contact" data-sticky-cta hidden>Get my quote <span aria-hidden="true">→</span></a>' if has_form else ''
    preload = ''
    if 'search-hero' in body:
        pic = 'landscape-hero' if 'hero-landscape' in body else 'pool-villa-hero'
        preload = (f'<link rel="preload" as="image" href="/images/{pic}.webp" type="image/webp" media="(min-width:761px)">'
                   f'<link rel="preload" as="image" href="/images/{pic}-720.webp" type="image/webp" media="(max-width:760px)">')
    # Search results cut titles at about 60 characters, so titles carry the short brand unless a page asks otherwise.
    full_title = title+brand
    canonical = f'{SITE}/{path}/' if path else f'{SITE}/'
    ld = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")}</script>' if schema else ''
    # A noindex page (the 404 page) is served at any address, so it gets no canonical or og:url.
    index_meta = '<meta name="robots" content="noindex,follow">' if noindex else f'<link rel="canonical" href="{canonical}">'
    og_url = '' if noindex else f'<meta property="og:url" content="{canonical}">'
    og_pic = 'landscape-hero' if 'hero-landscape' in body else 'pool-villa-hero'
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(full_title)}</title><meta name="description" content="{escape(description)}">{index_meta}<meta name="theme-color" content="#072338"><meta name="referrer" content="strict-origin-when-cross-origin">{icon_links()}<meta property="og:title" content="{escape(full_title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:type" content="website"><meta property="og:site_name" content="{COMPANY}">{og_url}<meta property="og:image" content="{SITE}/images/{og_pic}.jpg"><meta property="og:image:width" content="1000"><meta property="og:image:height" content="628"><meta name="twitter:card" content="summary_large_image">{head_extra}{preload}<link rel="stylesheet" href="{asset('studio.min.css')}"><link rel="stylesheet" href="{asset('search-landings.min.css')}"><script src="{asset('search-landings.min.js')}" defer></script><script src="{asset('studio.min.js')}" defer></script>{ld}</head><body class="search-landing">{header}<main id="main-content" tabindex="-1">{body}</main>{sticky}{footer}</body></html>'''
    html = html.replace('↗', '→')
    out = ROOT/out if out else ROOT/path/'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    # The sitemap date moves only when the page itself differs from its last committed version;
    # a new asset stamp (?v=...) alone does not count. Comparing with the commit, not with the copy
    # on disk, gives the same answer when a build is repeated or when another tool rewrote the page.
    unstamped = lambda s: re.sub(r'\?v=[0-9a-f]{12}', '', s)
    before = last_committed(out.relative_to(ROOT).as_posix())
    if before is None:
        before = out.read_text() if out.exists() else ''
    if not noindex and unstamped(before) != unstamped(html):
        CHANGED.add(canonical)
    out.write_text(html)
    return canonical


def organization():
    # The address is the company's mailing address. This is an Organization, not a local business with premises.
    return {'@type': 'Organization', '@id': SITE+'/#organization', 'name': 'JEBN Engineering', 'legalName': COMPANY, 'url': SITE+'/', 'logo': SITE+'/icon-512.png',
            'email': EMAIL, 'address': {'@type': 'PostalAddress', 'streetAddress': MAIL_STREET, 'addressLocality': MAIL_CITY, 'addressRegion': MAIL_REGION, 'postalCode': MAIL_ZIP, 'addressCountry': 'US'},
            'areaServed': {'@type': 'Country', 'name': 'United States'}}


# ---------------------------------------------------------------- service pages

DEFAULT_INPUTS = ('Start with the plans you have.', 'A sketch is enough to begin the conversation. If you already have a survey, drawings or permit comments, tell us what is ready. We identify the missing inputs before drawing work starts.', None)
PLAN_REVIEW_ANSWER = 'Send us the comments. Your quote states the revisions included, and we identify the sheets each comment affects. Comments on the engineering go to the engineer of record.'

SERVICES = [
 dict(path='services/pool-permit-drawings', title='Pool Permit Drawings & Swimming Pool Plans', geo=True, typical=True,
      h1='Pool permit drawings.<br><span>Built around your permit scope.</span>',
      kicker='USA / POOL PERMIT DRAWINGS',
      meta='Pool permit drawings: site plan, pool plan, sections, barrier and equipment layout, drawn to your permit office’s checklist. Send your sketch for a quote.',
      lead='Site plans, pool plans, sections and details for your pool permit package, drawn to the checklist your permit office publishes. We confirm the drawing scope with you before work begins.',
      package_heading='What a pool permit<br>drawing set includes.',
      package_lead='Your quote lists every sheet, the revisions included and the delivery date before you commit.',
      rows=[
        ('Site plan', 'Property lines, the house, the pool position, setbacks, easements and the equipment location.'),
        ('Pool plan & sections', 'Dimensions, depths, steps and benches, with sections through the shell.'),
        ('Barrier & safety items', 'Fence, gates and the other barrier items your permit office lists.'),
        ('Plumbing & equipment', 'Piping schematic, equipment schedule and the TDH worksheet where the office asks for one.'),
        ('Structural sheets', 'Shell and steel details drawn from your engineer’s design or your builder’s standard details.'),
        ('Review comments', 'Changes that answer plan review comments are drawn within the revisions in your quote.')],
      extra=('BEFORE YOU ASK FOR A QUOTE', 'Three things to ask your permit office.', 'Permit offices differ, even inside one state. These three answers decide what goes into your drawing set.', [
        ('Its checklist', 'Ask whether your office publishes a pool submittal checklist. Send it with your request and we draw to it.'),
        ('The code edition', 'Which edition of the residential code and the pool code it enforces, with any local amendments.'),
        ('Whether it wants a seal', 'Some offices ask for plans sealed by a Professional Engineer licensed in the state. JEBN does not seal drawings.')]),
      inputs=('Send the site and the pool.', 'A sketch with dimensions is enough to start. The survey or site plan, the checklist from your permit office and any review comments let us scope the set without follow-up questions.', [
        ('Project location', 'City, state and permit office, if known.'),
        ('Site information', 'Survey or site plan, with easements and known site constraints.'),
        ('Pool layout', 'Sketch, dimensions, depths and proposed features.'),
        ('Permit paperwork', 'The submittal checklist and any review comments you already have.')]),
      faq_heading='Questions about pool permit drawings.',
      faq=[
        ('What does a pool permit drawing set include?', 'Usually a site plan with setbacks and the barrier, a pool plan with dimensions and depths, sections, structural details, a plumbing schematic and an equipment schedule. Your permit office’s checklist decides the exact list, and your quote names every sheet.'),
        ('Do pool permit drawings need an engineer’s stamp?', 'Your state’s law and your permit office’s rules decide. Some offices ask for plans sealed by a Professional Engineer licensed in the state. JEBN prepares the drawings and does not seal them. Where an engineer’s seal is required, a Professional Engineer licensed in your state must direct the engineering and seal the set.'),
        ('Can you work from my builder’s sketch?', 'Yes. Send the sketch with dimensions and depths, the survey or site plan if you have one, and your permit office’s checklist. We tell you what is missing before drawing work starts.'),
        ('What if plan review comes back with comments?', PLAN_REVIEW_ANSWER),
        ('Do you know my city or county’s permit rules?', 'Each state page lists permit notes for named cities and counties, with links to the official sources. Send your permit office’s checklist with your request and we draw to it.'),
        ('How fast can you prepare the permit drawings?', TURNAROUND)]),
 dict(path='pool', title='Swimming Pool Construction Drawings & Details', geo=True,
      h1='Pool construction drawings.<br><span>From layout to detail.</span>',
      kicker='USA / POOL CONSTRUCTION DRAWINGS',
      meta='Swimming pool construction drawings: plans, sections, shell and steel details, plumbing diagram and equipment layout, as DWG and PDF files. Free quote.',
      lead='Coordinated pool plans, sections, construction details and equipment layouts that your builder and trades work from. Send your sketch or existing plans for a drawing-package quote.',
      package_heading='What a pool construction<br>set includes.',
      package_lead='The drawings your builder and trades work from, kept in step with the permit set. Your quote lists the sheets for your project.',
      rows=[
        ('Layout plan', 'Pool outline, dimensions, elevations and reference points for excavation and forming.'),
        ('Sections & depths', 'Long and cross sections with floor slopes, steps, benches, ledges and the waterline.'),
        ('Shell & steel details', 'Wall, floor and beam details, with reinforcement drawn from your engineer’s design or your builder’s standard details.'),
        ('Plumbing & equipment', 'Pipe runs, pipe sizes, valves and fittings, and the equipment pad layout.'),
        ('Finishes & edges', 'Tile, coping, waterline and edge details for the finishing trades.')],
      extra=('PERMIT SET OR CONSTRUCTION SET', 'Permit set or construction set?', 'A permit set shows the permit office what will be built. A construction set gives the crew the dimensions and details to build from. Many projects start with the permit set and add construction sheets once the permit is issued.', [
        ('Permit set', 'Site plan, pool plan, sections and the details the permit office’s checklist asks for.'),
        ('Construction set', 'Layout dimensions, steel, plumbing runs and finish details for the trades.'),
        ('Shop drawings', 'Fabrication details for tile, coping, gutters, steel and equipment.')]),
      inputs=('Start with the plans you have.', 'A sketch is enough to begin. If a permit set already exists, send it so the construction sheets follow it. We identify the missing inputs before drawing work starts.', [
        ('Pool layout', 'Sketch or permit set, with dimensions, depths and features.'),
        ('Site information', 'Survey or site plan, elevations and known site constraints.'),
        ('Structure', 'Your engineer’s design or your builder’s standard steel details.'),
        ('Equipment & finishes', 'Equipment models, tile and coping selections, if chosen.')]),
      faq_heading='Questions about pool construction drawings.',
      faq=[
        ('What is the difference between permit drawings and construction drawings?', 'Permit drawings show the permit office what will be built. Construction drawings add the dimensions, steel, plumbing and finish details the crew builds from. Many projects need both, and the two sets have to agree.'),
        ('Can you draw from my builder’s sketch?', 'Yes. Send the sketch with dimensions and depths, the survey or site plan if you have one, and the equipment you plan to use. We tell you what is missing before drawing work starts.'),
        ('Do construction drawings include the steel?', 'Yes, where it is part of your quote. Reinforcement is drawn from your engineer’s design or your builder’s standard details. JEBN drafts the steel details and does not design them.'),
        ('Will I receive editable files?', 'Yes. You receive DWG and PDF files for the agreed drawing package.'),
        ('Who seals the drawings?', seal_answer()),
        ('How fast can you prepare the construction drawings?', TURNAROUND)]),
 dict(path='services/pool-structural-engineering', title='Pool Structural Drawings & Steel Details',
      h1='Pool structural drawings.<br><span>Shell, steel and details.</span>',
      kicker='USA / POOL STRUCTURAL DRAWINGS',
      meta='Pool structural drawings drafted from your engineer’s design: shell sections, reinforcement schedules, raised walls and edge details. DWG and PDF files.',
      lead='Structural sheets for pools and spas: shell sections, reinforcement schedules and details for raised walls, special edges and attached spas, drafted from your engineer’s design or your builder’s standard details. The structural design belongs to the engineer. JEBN drafts the sheets and does not seal them.',
      package_heading='What the structural<br>sheets show.',
      package_lead='Structural drawings matched to your pool, your site and the checklist from your permit office.',
      rows=[
        ('Shell sections & reinforcement', 'Gunite or shotcrete shell sections with wall and floor reinforcement schedules, steps, benches and sun shelves, drawn from the engineer’s design.'),
        ('Soil & groundwater basis', 'The sheets state the soil basis the engineer gives: your geotechnical report where one exists, or the bearing value the engineer assumes.'),
        ('Raised walls & special edges', 'Raised bond beams, retaining conditions, vanishing edges, perimeter overflow and attached spas.'),
        ('Code references & notes', 'Design loads, concrete and steel notes and code references, as the engineer specifies them for the edition your jurisdiction enforces.'),
        ('Engineer’s mark-ups', 'Changes from your engineer’s mark-ups are drawn within the revisions in your quote. The engineer directs the engineering throughout and seals the sheets.')],
      inputs=('Send the pool and the engineer’s design.', 'A dimensioned layout with depths is enough to start the drafting. The engineer’s sketches, calculations or standard details, a soils report and the survey let us draw the structural sheets without follow-up questions.', [
        ('Pool layout', 'Shape, dimensions, depths, steps, benches and raised features.'),
        ('The design', 'Sketches, calculations, standard details or mark-ups from your engineer, or your builder’s standard steel details.'),
        ('Site & ground', 'Survey or site plan, slopes, nearby walls and footings, and the geotechnical report if there is one.'),
        ('Permit requirements', 'The submittal checklist or review comments from your permit office.')]),
      faq_heading='Questions about pool structural drawings.',
      faq=[
        ('Does my pool need structural engineering?', 'Your state’s law and your permit office’s rules decide. Some permit offices ask for sealed structural plans with every pool permit. Others may ask when the pool is close to a house footing, a retaining wall or a slope, when the ground is difficult, or when the shell has raised walls or a vanishing edge. Send the checklist and we tell you which sheets it asks for.'),
        ('Who designs the shell and the steel?', 'Where your permit office requires an engineer’s seal, a Professional Engineer licensed in your state. JEBN drafts the sheets from that design. Where no seal is required, the sheets follow your builder’s standard details.'),
        ('What if there is no soils report?', 'The engineer decides what bearing value to assume and whether a report is needed. The sheets state that basis, so the plan reviewer can see what the design relies on.'),
        ('Can you detail vanishing-edge and perimeter-overflow pools?', 'Yes. We draft the weir wall, the catch basin and the edge details from the design your engineer or builder provides.'),
        ('Who seals the structural sheets?', seal_answer()),
        ('How fast can you prepare the structural drawings?', TURNAROUND)]),
 dict(path='services/pool-hydraulic-design', title='Pool Plumbing & Hydraulic Drawings',
      h1='Pool plumbing and hydraulic drawings.<br><span>With TDH calculation sheets.</span>',
      kicker='USA / POOL PLUMBING AND HYDRAULIC DRAWINGS',
      meta='Pool plumbing and hydraulic drawings: piping plans, schematics, equipment layouts and TDH calculation sheets drafted from your equipment and pipe runs.',
      lead='Plumbing drawings for pools and spas: piping plans, schematics, equipment pad layouts and schedules, with a total dynamic head (TDH) calculation sheet where your permit office asks for one. Your pool builder or your engineer is responsible for the hydraulic design. We draw it and set out the numbers so the plan reviewer can follow them.',
      package_heading='What the plumbing<br>package shows.',
      package_lead='Drawings and calculation sheets for the circulation system, drafted from your pool layout, pipe routes and equipment.',
      rows=[
        ('Piping plan & schematic', 'Suction and return runs, pipe sizes, valves and unions, shown in plan and as a schematic.'),
        ('TDH calculation sheet', 'Total dynamic head set out line by line from your pipe runs, fittings and equipment, on your permit office’s worksheet where it publishes one.'),
        ('Equipment schedule', 'Pump, filter, heater and sanitizer schedules listing the models your builder or engineer selects.'),
        ('Equipment pad layout', 'The pad drawn to scale with clearances and pipe connections.'),
        ('Suction outlets', 'Drain covers and the suction outlet arrangement, shown with the flow ratings from the maker’s data.')],
      inputs=('Send the layout and the equipment.', 'Pool dimensions and the equipment location are enough to start. Pipe routes, equipment models and any worksheet from your permit office help us finish the sheets without follow-up questions.', [
        ('Pool & spa dimensions', 'Surface area, depths, volume if known, and any water features.'),
        ('Equipment location', 'Distance and height difference between the pool and the equipment pad.'),
        ('Equipment selections', 'Pump, filter, heater and cleaner models your builder or engineer has chosen.'),
        ('Permit forms', 'Any hydraulic or TDH worksheet your permit office requires.')]),
      faq_heading='Questions about pool plumbing drawings.',
      faq=[
        ('Do you complete the TDH worksheet my permit office requires?', 'Yes. Some permit offices publish their own hydraulic or TDH worksheet. Send it with your request and we fill it in from the pipe sizes and equipment your builder or engineer gives us, for your builder to check and sign. Where the office asks for sealed calculations, a Professional Engineer licensed in your state must direct that work and seal it.'),
        ('Who is responsible for the hydraulic design?', 'Your pool builder, or your engineer where the permit office requires sealed calculations. JEBN drafts the drawings and the calculation sheet from the pipe sizes and equipment they choose, and does not seal them.'),
        ('What velocity limits do the sheets show?', 'A common basis is 6 feet per second on suction piping and 8 feet per second on return piping. The sheet states the limit in the code your jurisdiction enforces, any tighter limit from the equipment maker, and the calculated velocity for each pipe size.'),
        ('Can you draw the plumbing for an existing pool?', 'Yes. Send the pipe sizes and runs, the equipment on the pad and what you want to change. We draw the system as it stands and the change your builder plans.'),
        ('Are the hydraulic calculations sealed by an engineer?', 'Only where your permit office asks for sealed calculations, and then by a Professional Engineer licensed in your state who directs that work. JEBN does not seal drawings or calculations.'),
        ('How fast can you prepare the plumbing package?', TURNAROUND)]),
 dict(path='services/pool-shop-drawings', title='Pool Shop Drawings for Fabrication & Installation',
      h1='Pool shop drawings.<br><span>Details your crew can build from.</span>',
      kicker='USA / POOL SHOP DRAWINGS',
      meta='Pool shop drawings for builders and fabricators: tile and coping layout, gutter and overflow details, steel, embeds and equipment layouts. DWG and PDF.',
      lead='Fabrication and installation drawings for pool builders: layout dimensions, edge and gutter details, steel and embeds, and equipment layouts, coordinated with your permit set.',
      facts=[('Sheet list', 'Agreed before work starts'), ('File delivery', 'DWG + PDF')],
      small='Residential pool drawing preparation takes 2 business days after we receive all project inputs. Larger shop drawing packages are scheduled in your quote.',
      package_heading='What the shop<br>drawings cover.',
      package_lead='The details your fabricators and installation crew need, drawn to an agreed sheet list and your drawing standards.',
      rows=[
        ('Tile, coping & waterline', 'Layout dimensions and details for tile, coping and the waterline.'),
        ('Gutters & overflow edges', 'Gutter, grating, vanishing-edge and perimeter-overflow details for fabrication.'),
        ('Steel, embeds & penetrations', 'Reinforcement placing details, embedded items and pipe penetrations through the shell.'),
        ('Equipment & plumbing', 'Equipment pad layout and plumbing schematics for the installation crew.'),
        ('Coordination with the permit set', 'Details checked against your approved plans to reduce conflicts on site.')],
      inputs=('Send the design and the details you need.', 'Send the design or permit drawings and tell us which details your installation team is missing. We agree on the sheet list and your drawing standards before preparing the package.', [
        ('Design drawings', 'The permit or design set the shop drawings must follow.'),
        ('Details needed', 'The edges, finishes, steel or equipment your crew needs drawn.'),
        ('Products & finishes', 'Tile, coping, grating and equipment selections, with maker data if you have it.'),
        ('Your standards', 'Title block, sheet size and CAD standards to follow.')]),
      faq_heading='Questions about pool shop drawings.',
      faq=[
        ('Do you deliver DWG as well as PDF?', 'Yes. You receive DWG and PDF files for the agreed sheets, so fabricators and your crew can work from the native files.'),
        ('Do shop drawings need a PE seal?', 'Shop drawings are fabrication and installation documents. Ask your permit office or your client whether they need a seal. If they do, a Professional Engineer licensed in your state must direct the engineering and seal them. JEBN does not seal drawings.'),
        ('Can you work from another designer’s plans?', 'Yes. Send the design or permit set and we draw the fabrication details that follow it. We tell you if something in the set conflicts with the detail being drawn.'),
        ('How is a shop drawing package priced?', 'By the agreed sheet list. Your quote names the sheets, file formats, revisions included and delivery date before work starts.')]),
 dict(path='services/outsourced-pool-drafting', title='Outsourced Pool Drafting for Builders & Designers', audience=False,
      h1='Outsourced pool drafting.<br><span>Drawn on your standards.</span>',
      kicker='USA / OUTSOURCED POOL DRAFTING',
      meta='Outsourced pool drafting for builders and designers whose drafting is backed up. Plans, sections and details drawn on your title block and CAD standards.',
      lead='Drafting capacity for pool builders and designers when the in-house team is full. Plans, sections and details are drawn on your title block and CAD standards and delivered to you as DWG and PDF files.',
      package_heading='What outsourced<br>drafting covers.',
      package_lead='Your projects, drawn the way your office draws them, with the sheets and the revisions included agreed in advance.',
      rows=[
        ('Your title block & standards', 'We adopt your title block, layer naming, sheet numbering and detail conventions from a sample set.'),
        ('Permit & construction sheets', 'Site layout, pool plans, sections, details and equipment layouts for each project you send.'),
        ('Revisions & review comments', 'Changes from mark-ups and permit review comments, drawn within the revisions in your quote.'),
        ('Sets for your engineer', 'Where a permit office asks for a seal, we draft to your engineer’s design and mark-ups. Your engineer seals the set.'),
        ('Agreed price per set', 'A fixed price per set or per sheet, agreed before work starts.')],
      inputs=('Send a sample set and the next project.', 'A sample set shows us your standards. Then send each project’s sketch, survey and notes, and tell us the delivery date you need.', [
        ('Sample drawing set', 'A recent set that shows your title block and drafting standards.'),
        ('CAD standards', 'Layer list, plot styles and template files, if you use them.'),
        ('Project inputs', 'Sketch or mark-up, survey and equipment selections for each pool.'),
        ('Workload', 'How many sets you expect and when you need them.')]),
      faq_heading='Questions about outsourced drafting.',
      faq=[
        ('Whose name is on the drawings?', 'Yours. Drawings are delivered on your title block and standards, and your client relationship stays with you.'),
        ('Can you match our drawing standards?', 'Yes. Send a sample set and we adopt your layer naming, title block, sheet numbering and detail conventions.'),
        ('How fast do you return a set?', 'Residential drawing preparation takes 2 business days after we receive all project inputs. For regular work we agree on a delivery schedule with you.'),
        ('How is the work priced?', 'Per set or per sheet, agreed before work starts. Your quote lists the sheets, file formats and the revisions included.'),
        ('Can a set be sealed by an engineer?', 'By your engineer, yes. We draft to the engineer’s design and mark-ups, and the engineer directs the engineering and seals the set. JEBN does not seal drawings.')]),
 dict(path='services/pool-drawings-for-engineer-of-record', title='Pool Drawings for Your Engineer of Record', audience=False,
      h1='Pool drawings for your engineer.<br><span>Drafted to the engineer’s design.</span>',
      kicker='USA / DRAFTING FOR THE ENGINEER OF RECORD',
      meta='Pool drawing sets drafted for your engineer of record: plans, sections, steel details and schedules drawn to the engineer’s design. DWG and PDF.',
      lead='For engineers, and for builders and owners who have one. We draft the pool drawing set to your engineer’s design and mark-ups. The engineer directs the work throughout and seals the set. JEBN does not seal drawings.',
      facts=[('JEBN', 'Drafts the set'), ('Your engineer', 'Directs and seals'), ('File delivery', 'DWG + PDF')],
      small='Your quote lists the sheets, the revisions included and the delivery date. The engineer’s work and the permit office’s review take additional time.',
      package_heading='What we draft<br>for the engineer.',
      package_lead='One coordinated set, so the engineer and the plan reviewer work from the same drawings.',
      rows=[
        ('Structural sheets', 'Shell sections, reinforcement schedules and details drawn from the engineer’s design and calculations.'),
        ('Plumbing & equipment', 'Piping schematic, pipe sizes, equipment schedule and layout, as given by the engineer or the builder.'),
        ('Site & layout', 'Pool position, setbacks, easements, elevations and drainage as your permit office requires.'),
        ('Barrier & electrical details', 'Barrier, bonding and clearance details drawn to the code edition your jurisdiction enforces.'),
        ('Mark-ups & revisions', 'Changes from the engineer’s mark-ups and the permit office’s comments are drawn within the revisions in your quote.')],
      extra=('HOW IT WORKS', 'How drafting for an engineer works.', 'The seal is the engineer’s statement of responsibility for the engineering on the sheet. So the engineer leads and we draw.', [
        ('The engineer leads', 'Design decisions, calculations and the code basis come from the engineer of record.'),
        ('We draw', 'Plans, sections, details and schedules are drafted to that design, on the title block and CAD standards you choose.'),
        ('The engineer directs and seals', 'The engineer stays in charge of the engineering while we draw, marks changes as the work goes, and seals the final set. JEBN never places a seal on a sheet.')]),
      inputs=('Send the design and the mark-ups.', 'The engineer’s sketches, calculations or standard details and a dimensioned pool layout are enough to start. Send the permit office’s checklist too, so we can lay out the sheets to match the drawing items it lists.', [
        ('The engineer’s design', 'Sketches, calculations, standard details and notes from the engineer of record.'),
        ('Pool layout', 'Shape, dimensions, depths and features, as a sketch or an earlier drawing.'),
        ('Site information', 'Survey or site plan and the geotechnical report, if there is one.'),
        ('Standards', 'Title block, sheet size and CAD standards to follow.')]),
      faq_heading='Questions from engineers and builders.',
      faq=[
        ('Do you work directly with our engineer?', 'Yes. We take the design, sketches and mark-ups from the engineer, and we revise the sheets as the engineer directs.'),
        ('Whose title block goes on the drawings?', 'The one you choose: the engineer’s, the builder’s or a project title block. The engineer applies the seal and signature. JEBN never places an engineer’s seal on a sheet.'),
        ('Can you prepare the structural calculations?', 'No. Structural calculations are the engineer’s work, and the hydraulic design is the engineer’s or your pool builder’s. We set out their results on the sheets, such as schedules, tables and notes.'),
        ('Who is responsible for the sealed drawings?', 'The engineer of record, who directs the engineering and seals the set under their state license.'),
        ('What if plan review comes back with comments?', PLAN_REVIEW_ANSWER),
        ('We do not have an engineer. Can you still help?', 'We can draft the set, and we can ask an engineer licensed in your state to take your project. That engineer decides whether to take it and sets the fee for the engineering. JEBN does not seal drawings.')]),
]


def crumbs_html(trail):
    parts = []
    for href, label in trail:
        parts.append(f'<a href="{href}">{label}</a>' if href else f'<span aria-current="page">{label}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">'+' <span aria-hidden="true">/</span> '.join(parts)+'</nav>'


def info_section(sid, eyebrow, heading, para, items, link=('Ask about your project ↗', '#contact')):
    """A heading and a paragraph beside a list of short labelled points."""
    lis = ''.join(f'<li><strong>{k}</strong>{v}</li>' for k, v in items)
    return (f'<section class="section inputs-section" id="{sid}" aria-labelledby="{sid}-heading"><div class="wrap input-grid"><div><span class="eyebrow">{eyebrow}</span>'
            f'<h2 id="{sid}-heading">{heading}</h2><p>{para}</p><a class="text-link" href="{link[1]}">{link[0]}</a></div><ul class="input-list">{lis}</ul></div></section>')


def service_schema(canonical, short, title, meta, faq):
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Service', '@id': canonical+'#service', 'name': title, 'serviceType': 'Swimming pool drawings', 'description': meta, 'url': canonical, 'provider': organization(), 'areaServed': {'@type': 'Country', 'name': 'United States'}},
        faq_schema(canonical, faq),
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': short, 'item': canonical}]},
    ]}


def build_service(p):
    path = '/'+p['path']+'/'
    canonical = SITE+path
    short = next(label for href, label, _ in SERVICE_LINKS if href == path)
    extra = info_section('how', *p['extra']) if p.get('extra') else ''
    heading, para, items = p.get('inputs') or DEFAULT_INPUTS
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#package">What it covers</a><a href="#inputs">What to send</a><a href="#faq">Questions</a><a href="#contact">Get my quote ↗</a></div></nav>'
    crumbs = crumbs_html([('/', 'Home'), ('/#services', 'Services'), ('', short)])
    body = (hero(p['kicker'], p['h1'], p['lead'], form(p['title']), crumbs, p.get('facts'), p.get('small')) + nav + samples_section()
            + (audience_section() if p.get('audience', True) else '') + pool_clients()
            + package_section(rows=p['rows'], heading=p['package_heading'], lead=p['package_lead'], links=service_links(path), typical=p.get('typical', False)) + extra
            + inputs_section(heading, para, items)
            + delivery_section()
            + faq_block('BEFORE YOU ASK', p['faq_heading'], p['faq'])
            + coverage_section())
    # Routes a paid visit to the visitor's state page when the ad click carries a location id.
    head_extra = geo_route_tag() if p.get('geo') else ''
    return shell(p['path'], p['title'], p['meta'], body, service_schema(canonical, short, p['title'], p['meta'], p['faq']), head_extra)


# ---------------------------------------------------------------- the page on the engineer's seal

SEAL_ROLES = [
    ('Your permit office', 'Applies your state’s law and its building code. It tells you whether your pool needs sealed plans, and it reviews the set.'),
    ('The engineer of record', 'A Professional Engineer licensed in your state. Directs the engineering while the drawings are prepared, and seals the drawings and calculations.'),
    ('JEBN', 'Drafts the drawing set to the engineer’s design, your builder’s details and the permit office’s checklist. JEBN does not seal drawings.'),
    ('You or your builder', 'Choose the engineer and agree on the fee for the engineering with that engineer.'),
]
SEAL_WHEN = [
    ('The checklist lists sealed plans', 'The pool submittal checklist asks for plans or structural calculations signed and sealed by an engineer licensed in your state.'),
    ('Close to a structure or slope', 'The pool sits near a house footing, a retaining wall, a property-line wall or a slope.'),
    ('Difficult ground', 'High groundwater, expansive clay, fill, or a soils report with design recommendations.'),
    ('Non-standard shells', 'Raised walls, vanishing edges, attached spas or a pool on a structure.'),
]
SEAL_STEPS = [
    ('The engineer takes the project', 'An engineer licensed in your state agrees to be the engineer of record. Until then nobody can promise you a sealed set.'),
    ('The engineer sets the design', 'Shell thickness, steel, the soil basis and the calculations come from the engineer.'),
    ('JEBN drafts the set', 'We draw the plans, sections and details to that design and to your permit office’s checklist.'),
    ('The engineer directs and seals', 'The engineer stays in charge of the engineering while we draw, marks changes as the work goes, and seals and signs the set.'),
]
SEAL_FAQ = [
    ('Does JEBN seal or stamp pool drawings?', 'No. JEBN prepares the drawings. Where your permit office requires an engineer’s seal, a Professional Engineer licensed in your state must direct the engineering and seal the set.'),
    ('Does every pool need an engineer?', 'Not everywhere. Your state’s law and your permit office’s rules decide. Some permit offices ask for sealed plans with every pool permit, and some ask only for certain pools. Ask your permit office for its pool submittal checklist before drawings start.'),
    ('Who is the engineer of record?', 'The term is used for the Professional Engineer who is in charge of a project’s engineering documents and who signs and seals them. Not every state’s rules use the term. Where a seal is required, that engineer generally must hold a license in the state where the pool will be built.'),
    ('Can I send finished drawings to an engineer for a stamp?', 'Not simply for a stamp. Engineering board rules in states such as California, Florida, Texas and Washington let an engineer seal only work the engineer did, or work done under the engineer’s responsible charge, which some states call direct supervision. The engineer has to be in charge of the engineering while the drawings are prepared. Some states let an engineer take over earlier work under set rules, so ask the engineer what applies in your state.'),
    ('How do I find an engineer?', 'You can use an engineer you or your builder already work with. Your state’s engineering board can confirm that an engineer holds a license. You can also ask us: we can ask an engineer licensed in your state to take your project. That engineer decides whether to take it and sets the fee for the engineering.'),
    ('Who pays the engineer?', 'You or your builder, by agreement with the engineer. The engineer sets the fee for the engineering. Ask for it in writing before you commit.'),
]


SEAL_SOURCES = [
    ('NCEES Model Law, August 2025, section 110.10', 'https://ncees.org/wp-content/uploads/2025/09/Model-Law_August-2025_web.pdf'),
    ('NCEES Model Rules, August 2025, sections 240.15 and 240.20', 'https://ncees.org/wp-content/uploads/2025/09/Model_Rules_August-2025_web.pdf'),
    ('California Professional Engineers Act, Business and Professions Code section 6735', 'https://www.bpelsg.ca.gov/laws/pe_act.pdf'),
    ('California Board Rules, 16 CCR 404.1', 'https://www.bpelsg.ca.gov/laws/boardrules.pdf'),
    ('Florida Statutes, section 471.033(1)(j)', 'https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0400-0499/0471/Sections/0471.033.html'),
    ('Florida Administrative Code, rule 61G15-18.011', 'https://www.flrules.org/gateway/ruleNo.asp?id=61G15-18.011'),
    ('Florida Administrative Code, rule 61G15-27.001', 'https://www.flrules.org/gateway/ruleNo.asp?id=61G15-27.001'),
    ('Texas Board of Professional Engineers and Land Surveyors, Acts and Rules, 22 TAC 137.33', 'https://pels.texas.gov/downloads/lawrules.pdf'),
    ('Revised Code of Washington, RCW 18.43.070', 'https://app.leg.wa.gov/RCW/default.aspx?cite=18.43.070'),
    ('Washington Administrative Code, WAC 196-25-070', 'https://app.leg.wa.gov/WAC/default.aspx?cite=196-25-070'),
    ('2024 International Swimming Pool and Spa Code, Section 107.1', 'https://codes.iccsafe.org/content/ISPSC2024P1/chapter-1-scope-and-administration'),
    ('2024 International Residential Code, Section R106.1', 'https://codes.iccsafe.org/content/IRC2024P1/chapter-1-scope-and-administration'),
    ('2024 International Building Code, Section 107.1', 'https://codes.iccsafe.org/content/IBC2024P1/chapter-1-scope-and-administration'),
    ('2024 International Building Code, Section 202, definition of registered design professional', 'https://codes.iccsafe.org/content/IBC2024P1/chapter-2-definitions'),
]


def sources_block(items, note):
    """A short list of the official pages a page's statements were checked against."""
    lis = ''.join(f'<li>{ext_link(url, label)}</li>' for label, url in items)
    return (f'<section class="section sources-section" id="sources" aria-labelledby="sources-heading"><div class="wrap"><div class="sources">'
            f'<h2 id="sources-heading">Sources</h2><p>{note}</p><ul>{lis}</ul></div></div></section>')


def build_seal_page():
    path = '/services/pool-engineering/'
    canonical = SITE+path
    short = next(label for href, label, _ in SERVICE_LINKS if href == path)
    title = 'How an Engineer’s Seal Works on Pool Drawings'
    meta = 'Who seals pool drawings for a permit: what an engineer’s seal means, who directs the engineering and what JEBN drafts. JEBN does not seal drawings.'
    lead = 'Some permit offices ask for pool plans sealed by a Professional Engineer licensed in the state. This page explains who directs the engineering, who seals the set and what JEBN drafts. JEBN prepares the drawings and does not seal them.'
    facts = [('JEBN', 'Drafts the drawings'), ('Engineer of record', 'Directs and seals'), ('Permit office', 'Decides approval')]
    small = 'Rules differ by state. The official texts this page was checked against are listed under Sources.'
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#roles">Who does what</a><a href="#when">When a seal is needed</a><a href="#faq">Questions</a><a href="#contact">Get my quote ↗</a></div></nav>'
    crumbs = crumbs_html([('/', 'Home'), ('/#services', 'Services'), ('', short)])
    roles = info_section('roles', 'WHO DOES WHAT', 'Four parties, four jobs.', 'A sealed pool set has more than one author. Knowing who does what saves time and avoids paying twice.', SEAL_ROLES)
    when = info_section('when', 'WHEN A PERMIT CALLS FOR AN ENGINEER', 'When a pool permit calls for an engineer.', 'Your state’s law and your permit office’s rules decide whether a pool needs sealed plans. Some permit offices list sealed plans among the documents for a pool permit. Where the ICC building or residential code is adopted, the building official may also ask for documents from a registered design professional when special conditions exist. These are situations to raise with your permit office before drawings start.', SEAL_WHEN)
    steps = f'''<section class="section blue" id="delivery" aria-labelledby="delivery-heading"><div class="wrap"><span class="eyebrow">WITH AN ENGINEER OF RECORD</span><h2 id="delivery-heading">How the work runs when a seal is needed.</h2><ol class="delivery-steps four">{step_items(SEAL_STEPS)}</ol><div class="review-note"><h3>Already have plans?</h3><p>A seal certifies the work shown on the documents it is placed on. Plans sealed by an engineer licensed only in another state are generally not enough where your state requires a seal. If a different engineer adapts a sealed design to a new site, the NCEES model rules and California’s rules treat that as engineering the new engineer must take responsible charge of. Florida’s rules set similar steps for reusing another engineer’s sealed plans. Ask your permit office how it handles standard or repeat designs.</p></div><div class="actions"><a class="button primary" href="#contact">Get my quote <span aria-hidden="true">→</span></a></div></div></section>'''
    body = (hero('USA / THE ENGINEER’S SEAL', 'Who seals pool drawings.<br><span>And what JEBN drafts.</span>', lead, form('Pool Drawings and the Engineer’s Seal'), crumbs, facts, small,
                 second=('See who does what ↓', '#roles'), panel_quote=False) + nav
            + roles + when + steps
            + faq_block('BEFORE YOU ASK', 'Questions about seals and stamps.', SEAL_FAQ)
            + sources_block(SEAL_SOURCES, 'The statements on this page were checked against these official texts in November 2026. Rules differ by state and change over time, so confirm them with your permit office and your state’s engineering board. This page is general information, not legal advice.')
            + coverage_section())
    # Routes a paid visit to the visitor's state page when the ad click carries a location id.
    head_extra = geo_route_tag()
    schema = page_schema(canonical, title, meta, short)
    schema['@graph'].insert(1, faq_schema(canonical, SEAL_FAQ))
    return shell('services/pool-engineering', title, meta, body, schema, head_extra)


# ---------------------------------------------------------------- pages for particular project types

TOPIC_STEPS = [
    DELIVERY_STEPS[0],
    ('Draft the set', 'We draw the sheets listed in your quote from the design, details and measurements you send. Your quote states the delivery date.'),
    DELIVERY_STEPS[2],
]
TOPIC_FACTS = [('JEBN', 'Drafts the set'), ('File delivery', 'DWG + PDF'), ('Engineer’s seal', 'Not included')]
TOPIC_SMALL = 'Delivery time depends on the scope. Your quote states the delivery date.'
TOPIC_SOURCES_NOTE = ('The statements on this page were checked against these official pages in November 2026. Codes, editions and local rules differ '
                      'and change, so confirm what applies with your permit office. This page is general information, not legal advice.')
# On these two the project already has its own engineer or architect, so the page does not offer to ask one.
TOPIC_NO_OFFER = {'rooftop-elevated', 'commercial-plan-review'}
# On this page the reviewer is often a health department, so the shared steps say "reviewing agency".
TOPIC_AGENCY = {'commercial-plan-review'}
AGENCY_WORDS = [('what your permit office asks for', 'what the reviewing agency asks for'),
                ('Your permit office decides approval and timing', 'The reviewing agency decides approval and timing'),
                ('The permit office decides approval', 'The reviewing agency decides approval'),
                # The state rules this page cites accept an engineer or an architect.
                ('Where your permit office requires an engineer’s seal, a Professional Engineer licensed in your state must direct the engineering and seal the set.',
                 'Where your permit office or the reviewing agency requires a seal, a Professional Engineer licensed in your state, or an architect where the rule allows one, '
                 'must direct the engineering and seal the set.')]


def topic_delivery(t):
    markup = delivery_section(offer=t['key'] not in TOPIC_NO_OFFER, steps=TOPIC_STEPS)
    if t['key'] in TOPIC_AGENCY:
        for old, new in AGENCY_WORDS:
            if markup.count(old) != 1:  # not an assert: python -O would skip it and leave the old words in place
                raise SystemExit(f'topic_delivery: expected one {old!r} in the delivery section, found {markup.count(old)}')
            markup = markup.replace(old, new)
    return markup


def build_topic(t):
    path = '/'+t['path']+'/'
    canonical = SITE+path
    by_key = {x['key']: x for x in TOPICS}
    labels = {href: label for href, label, _ in SERVICE_LINKS}
    related = [(href, labels[href]) for href in t['related_services']] + [('/'+by_key[k]['path']+'/', escape(by_key[k]['nav_label'])) for k in t['related']]
    links = '<p class="package-links"><strong>Related:</strong> ' + ' · '.join(f'<a href="{h}">{l}</a>' for h, l in related) + '</p>'
    pairs = lambda items: [(clean(x['label']), clean(x['text'])) for x in items]
    faq = [(x['q'], x['a']) for x in t['faq']]
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#package">What the set shows</a><a href="#roles">Who does what</a><a href="#inputs">What to send</a><a href="#faq">Questions</a><a href="#contact">Get my quote ↗</a></div></nav>'
    crumbs = crumbs_html([('/', 'Home'), ('/#more-services', 'Drawing sets'), ('', clean(t['nav_label']))])
    h1 = f'{clean(t["h1_main"])}<br><span>{clean(t["h1_sub"])}</span>'
    body = (hero('USA / '+escape(t['nav_label'].upper()), h1, clean(t['lead']), form(t['title']), crumbs, TOPIC_FACTS, TOPIC_SMALL, strip='DWG + PDF · Seal not included') + nav
            + samples_section()
            + package_section(rows=pairs(t['shows']), heading=clean(t['shows_heading']), lead=clean(t['shows_intro']), links=links, typical=False)
            + info_section('roles', 'WHO DOES WHAT', clean(t['roles_heading']), clean(t['roles_intro']), pairs(t['roles']))
            + inputs_section(clean(t['send_heading']), clean(t['send_intro']), pairs(t['send']))
            + topic_delivery(t)
            + faq_block('BEFORE YOU ASK', clean(t['faq_heading']), faq)
            + sources_block([(x['title'], x['url']) for x in t['sources']], TOPIC_SOURCES_NOTE)
            + coverage_section())
    return shell(t['path'], t['title'], t['meta'], body, service_schema(canonical, t['nav_label'], t['title'], t['meta'], faq))


def build_moved(old_path, new_path, label):
    """A page left at an old address that sends visitors, with their query string, on to the new address."""
    target = f'/{new_path}/'
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>This page has moved | JEBN</title>'
            f'<link rel="canonical" href="{SITE}{target}"><script>location.replace({json.dumps(target)}+location.search+location.hash)</script>'
            f'<meta http-equiv="refresh" content="0; url={target}"></head><body><h1>This page has moved</h1><p><a href="{target}">{escape(label)}</a></p></body></html>')
    out = ROOT/old_path/'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


# ---------------------------------------------------------------- home page

HOME_FAQ = [
    ('When do the 2 business days start?', 'Once we have received all project inputs. It covers preparation of residential pool drawings. Where your permit needs an engineer’s seal, the engineer’s work takes additional time, and so does the permit office’s review.'),
    ('What should I send to get started?', 'Your project city and state, a site plan or sketch, pool dimensions if known, and the drawings you need. Include existing plans and any permit review comments if you have them.'),
    ('Will I receive editable files?', 'Yes. You receive PDF files and the DWG (CAD) files for the agreed drawing package.'),
    ('Do you work with pool contractors and builders?', 'Yes. We work with homeowners, pool contractors and builders on permit drawings, construction drawings and drawing updates within an agreed scope.'),
    ('Who seals the drawings?', seal_answer()+' The permit office decides approval.'),
    ('What if plan review comes back with comments?', PLAN_REVIEW_ANSWER),
    ('Do you know my city or county’s permit rules?', 'Each state page lists permit notes for named cities and counties, with links to the official sources. Send your permit office’s checklist with your request and we draw to it.'),
    ('How is drafting for pool builders priced?', 'Per set or per sheet, agreed before work starts. Your quote lists the sheets, file formats and the revisions included.'),
    ('Can you match our drawing standards?', 'Yes. Send a sample set and we adopt your layer naming, title block, sheet numbering and detail conventions.'),
]


def build_home():
    title = 'Pool Plans & Permit Drawings'
    description = 'Pool plans and permit drawings for US homeowners and pool builders. Residential sets in 2 business days after all inputs. JEBN does not seal. Free quote.'
    lead = f'Permit drawings, construction drawings and plumbing and equipment layouts for homeowners and pool builders, drawn to your permit office’s checklist. {seal_short()}'
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#services">Services</a><a href="#coverage">Find your state</a><a href="#package">Drawing package</a><a href="#contact">Get my quote ↗</a></div></nav>'
    cards = ''.join(f'<a class="state-card service-card" href="{href}">{ICON(SERVICE_ICONS[href])}<strong>{label}</strong><span>{text}</span><span class="card-go" aria-hidden="true">Open →</span></a>' for href, label, text in SERVICE_LINKS)
    services = f'''<section class="section local-section" id="services" aria-labelledby="services-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">POOL DRAWING SERVICES</span><h2 id="services-heading">Pool drawing and drafting services.</h2></div><div><p>Permit drawings, construction drawings and shop drawings for homeowners, pool contractors and builders. Choose a complete drawing package or the drafting support your team needs.</p><a class="text-link" href="#contact">Get my quote ↗</a></div></div><nav class="state-cards four" aria-label="Services">{cards}</nav></div></section>'''
    topic_cards = ''.join(f'<a class="state-card service-card" href="{href}">{ICON(SERVICE_ICONS[href])}<strong>{escape(label)}</strong><span>{escape(text)}</span><span class="card-go" aria-hidden="true">Open →</span></a>' for href, label, text in TOPIC_LINKS)
    more = f'''<section class="section local-section more-services" id="more-services" aria-labelledby="more-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">DRAWING SETS BY PROJECT TYPE</span><h2 id="more-heading">Drawing sets for particular projects.</h2></div><div><p>Owner-builder permits, remodels, vanishing edges and pools on structures each need their own sheets.</p><p>Hotel, rooftop and public pools: shop drawings and permit drafting for the project’s engineer of record, quoted per project.</p></div></div><nav class="state-cards" aria-label="Drawing sets by project type">{topic_cards}</nav></div></section>'''
    state_links = ''.join(f'<a href="/states/{s}/">{name_of(s)}</a>' for s in sorted(STATES))
    state_options = ''.join(f'<option value="/states/{s}/">{name_of(s)}</option>' for s in sorted(STATES))
    states = f'''<section class="section local-section" id="coverage" aria-labelledby="coverage-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">USA · STATE PAGES</span><h2 id="coverage-heading">Pool permit drawings by state.</h2></div><div><p>Every state page has the state-level pool rules, permit notes for named cities and counties with links to the official sources, and the quote form.</p><p>Your city or county is not listed? Name the permit office in your request. We draw to the checklist it publishes.</p><a class="text-link" href="/states/">Browse all state pages ↗</a></div></div><div class="state-jump"><label for="state-jump">Go to your state</label><select id="state-jump" data-state-jump><option value="">Choose a state…</option>{state_options}</select></div><noscript><style>.state-jump{{display:none}}</style></noscript><details class="state-fold" data-open-wide><summary>Show all state pages</summary><nav class="state-grid wide" aria-label="State pages">{state_links}</nav></details></div></section>'''
    line = f'''<section class="coverage-line" aria-label="USA coverage"><div class="wrap"><p><strong>{COMPANY}.</strong> We draft pool drawings for US permit submissions.</p><a href="/states/">View state pages</a></div></section>'''
    body = (hero('USA / POOL PERMIT AND CONSTRUCTION DRAWINGS', 'Pool permit drawings<br><span>and construction drawings.</span>', lead, form('Pool Plans and Permit Drawings')) + nav
            + samples_section() + audience_section() + pool_clients() + services + more
            + package_section(sid='package-section') + states
            + inputs_section(*DEFAULT_INPUTS[:2])
            + delivery_section()
            + faq_block('QUESTIONS', 'Common questions about pool drawings.', HOME_FAQ)
            + line)
    canonical = SITE+'/'
    org = dict(organization(), **{'@id': canonical+'#organization', 'description': 'Pool permit drawings, construction drawings, plumbing and equipment layouts and shop drawings for US projects. JEBN prepares the drawings and does not seal them.'})
    schema = {'@context': 'https://schema.org', '@graph': [
        org,
        {'@type': 'WebSite', '@id': canonical+'#website', 'name': 'JEBN Engineering', 'alternateName': [COMPANY, 'JEBN'], 'url': canonical, 'publisher': {'@id': canonical+'#organization'}},
        faq_schema(canonical, HOME_FAQ),
        {'@type': 'ItemList', 'name': 'Pool drawing services', 'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': label, 'url': SITE+href} for i, (href, label, _) in enumerate(SERVICE_LINKS, 1)]},
    ]}
    # Routes a paid visit to the visitor's state page when the ad click carries a location id.
    head_extra = geo_route_tag()
    return shell('', title, description, body, schema, head_extra, brand=f' | {COMPANY}')


# ---------------------------------------------------------------- privacy notice

CHECKLIST = [
    ('1. The project', ['Project city, state and permit office, if known.',
                        'Residential or commercial use; new pool or renovation.',
                        'Your role: owner, pool contractor, builder or designer.']),
    ('2. The starting information', ['Site plan or survey showing the property and proposed pool location.',
                                     'Sketch, dimensions, depths and preferred features.',
                                     'Existing drawings and permit review comments, if available.',
                                     'Equipment preferences and known site constraints.']),
    ('3. The package you need', ['Permit drawings, construction drawings, structural sheets, plumbing and hydraulic drawings or shop drawings.',
                                 'Whether your permit office asks for an engineer’s seal, and whether you already have an engineer.',
                                 'Your target date and project contact.']),
]


def build_checklist():
    """The project input checklist, in the shared layout. The download file resources/pool-project-checklist/checklist.txt carries the same list."""
    title = 'Pool Project Input Checklist'
    description = 'Prepare your pool project brief with this free checklist of site information, drawings and scope. No email signup required.'
    crumbs = crumbs_html([('/', 'Home'), ('', 'Project checklist')])
    blocks = ''.join(f'<h2>{h}</h2><ul>{"".join(f"<li>{i}</li>" for i in items)}</ul>' for h, items in CHECKLIST)
    body = f'''<section class="section prose-page" aria-labelledby="page-heading"><div class="wrap"><div class="prose">{crumbs}<span class="eyebrow">PROJECT RESOURCE · NO SIGNUP NEEDED</span><h1 id="page-heading">Before we draw: your pool project checklist.</h1><p class="lead">Use this list to put your project brief together. You do not need every answer to start a conversation. We identify any missing inputs before drawing work begins.</p><div class="actions"><a class="text-link" href="/resources/pool-project-checklist/checklist.txt" download>Download checklist (.txt) ↓</a></div>{blocks}<h2>Ready to send it?</h2><p>Send the list, or as much of it as you have, with your quote request. {REPLY_TIME} {TURNAROUND}</p><div class="actions"><a class="button primary" href="/#contact">Get my quote <span aria-hidden="true">→</span></a></div></div></div></section>'''
    canonical = f'{SITE}/resources/pool-project-checklist/'
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': canonical+'#page', 'name': title, 'description': description, 'url': canonical, 'isPartOf': {'@type': 'WebSite', 'name': 'JEBN Engineering', 'url': SITE+'/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Project checklist', 'item': canonical}]},
    ]}
    return shell('resources/pool-project-checklist', title, description, body, schema)


def build_privacy():
    """Wraps the notice text in tools/data/privacy-notice.html in the shared layout. The wording is not changed here."""
    doc = BeautifulSoup((ROOT/'tools/data/privacy-notice.html').read_text(), 'html.parser')
    for c in doc.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    doc.h1['id'] = 'page-heading'
    doc.h1.find_next_sibling('p')['class'] = 'small'
    title = 'Privacy Notice'
    description = f'How {COMPANY} handles quote requests, website information and Google Ads measurement choices.'
    crumbs = crumbs_html([('/', 'Home'), ('', 'Privacy notice')])
    body = f'<section class="section prose-page" aria-labelledby="page-heading"><div class="wrap"><div class="prose">{crumbs}{str(doc).strip()}</div></div></section>'
    canonical = f'{SITE}/privacy/'
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': canonical+'#page', 'name': title, 'description': description, 'url': canonical, 'isPartOf': {'@type': 'WebSite', 'name': 'JEBN Engineering', 'url': SITE+'/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Privacy notice', 'item': canonical}]},
    ]}
    return shell('privacy', title, description, body, schema, brand=f' | {COMPANY}')


# ---------------------------------------------------------------- sample drawings, how it works, about

def page_schema(canonical, title, description, crumb, kind='WebPage'):
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': kind, '@id': canonical+'#page', 'name': title, 'description': description, 'url': canonical, 'isPartOf': {'@type': 'WebSite', 'name': 'JEBN Engineering', 'url': SITE+'/'}, 'about': organization()},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': crumb, 'item': canonical}]},
    ]}


QUOTE_BUTTON = '<div class="actions"><a class="button primary" href="/#contact">Get my quote <span aria-hidden="true">→</span></a></div>'


def build_samples():
    title = 'Sample Pool Plans & Drawing Sheets'
    description = 'Sample pool drawing sheets from two sets: a pool and spa set and a water feature set. Each sheet is marked VOID. Open any sheet to see it larger.'
    crumbs = crumbs_html([('/', 'Home'), ('', 'Sample drawings')])
    counts = ' and '.join(f'{len(s["sheets"])} sheets of a {s["tag"].lower()}' for s in SAMPLE_SETS)
    head = f'''<section class="section prose-page" aria-labelledby="page-heading"><div class="wrap"><div class="prose">{crumbs}<span class="eyebrow">SAMPLE DRAWINGS</span><h1 id="page-heading">Sample pool drawing sets.</h1><p class="lead">See the kind of sheets you receive before you ask for a quote: {counts}.</p><p>Your own set is drawn for your site, to the checklist your permit office publishes.</p>{QUOTE_BUTTON}</div></div></section>'''
    tail = f'''<section class="section prose-page" aria-labelledby="receive-heading"><div class="wrap"><div class="prose"><h2 id="receive-heading">What you receive</h2><p>A PDF set for your permit submission and the DWG files. Your quote lists the sheets, the revisions included and the delivery date before you commit.</p><p>{seal_short()} <a href="/services/pool-engineering/">How the engineer’s seal works</a></p><p><a href="/how-it-works/">How the service works</a> · <a href="/services/pool-permit-drawings/">Pool permit drawings</a> · <a href="/pool/">Pool construction drawings</a></p>{QUOTE_BUTTON}</div></div></section>'''
    canonical = f'{SITE}/samples/'
    total = sum(len(s['sheets']) for s in SAMPLE_SETS)
    sets = samples_section('THE SHEETS', f'{len(SAMPLE_SETS)} sets, {total} sheets.')
    return shell('samples', title, description, head + sets + tail, page_schema(canonical, title, description, 'Sample drawings'))


HOW_STEPS = [
    ('You send what you have', 'Your city and state, a sketch or existing plans, the survey or site plan, and your permit office’s checklist or review comments. A sketch is enough to start.'),
    ('We reply with a quote', 'We reply by email within 24 hours with questions or a quote. The quote lists every sheet, the revisions included and the delivery date. Asking is free.'),
    ('We draft the set', 'Plans, sections, details and schedules are drawn to the checklist. Residential drawing preparation takes 2 business days after all project inputs are received.'),
    ('You receive the files', 'A PDF set for your permit submission and the DWG files. You or your builder submit the set, and your permit office decides approval. If it sends comments, send them to us.'),
]
HOW_ROLES = [
    ('You or your pool builder', 'Send the project information, choose the equipment and finishes, and submit the set to the permit office.'),
    ('JEBN', 'Drafts the drawing set and draws the changes within the revisions in your quote. JEBN does not seal drawings.'),
    ('The engineer of record', 'Needed where your state’s law or your permit office requires an engineer’s seal. Directs the engineering while the drawings are prepared, and seals the set.'),
    ('Your permit office', 'Publishes the checklist, reviews the set and decides approval.'),
]
HOW_RECEIVE = [
    ('A sheet list first', 'Every sheet is named in your quote before you commit.'),
    ('The PDF set', 'The drawing set as PDF files, for your permit submission.'),
    ('The DWG files', 'The CAD files of the same sheets, for your builder and trades.'),
    ('Revisions', 'Changes within the revisions stated in your quote, including changes that answer plan review comments.'),
]


def build_how():
    title = 'How the Pool Drawing Service Works'
    description = 'How the pool drawing service works: what you send, what JEBN drafts, who seals where a seal is needed, and the files you receive. The quote is free.'
    crumbs = crumbs_html([('/', 'Home'), ('', 'How it works')])
    quote = ('Get my quote →', '/#contact')
    head = f'''<section class="section prose-page" aria-labelledby="page-heading"><div class="wrap"><div class="prose">{crumbs}<span class="eyebrow">HOW IT WORKS</span><h1 id="page-heading">How the service works.</h1><p class="lead">Who does what, what you send and what you get.</p>{QUOTE_BUTTON}</div></div></section>'''
    steps = f'''<section class="section blue" id="delivery" aria-labelledby="delivery-heading"><div class="wrap"><span class="eyebrow">FROM FIRST EMAIL TO DRAWING SET</span><h2 id="delivery-heading">Four steps to your drawing set.</h2><ol class="delivery-steps four">{step_items(HOW_STEPS)}</ol><div class="review-note"><h3>Who seals the drawings</h3><p>{seal_answer()}</p><a class="text-link" href="/services/pool-engineering/">How the engineer’s seal works →</a></div><div class="actions"><a class="button primary" href="/#contact">Get my quote <span aria-hidden="true">→</span></a></div></div></section>'''
    body = (head + steps
            + info_section('roles', 'WHO DOES WHAT', 'Four parties, four jobs.', 'A pool permit set passes through several hands. This is who does what on a JEBN project.', HOW_ROLES, quote)
            + inputs_section('What to send.', 'A sketch is enough to begin the conversation. If you already have a survey, drawings or permit comments, tell us what is ready. We identify the missing inputs before drawing work starts.')
            + info_section('receive', 'WHAT YOU RECEIVE', 'What you receive.', 'Files you can submit and files your builder can work from.', HOW_RECEIVE, ('See sample drawings →', '/samples/')))
    canonical = f'{SITE}/how-it-works/'
    return shell('how-it-works', title, description, body, page_schema(canonical, title, description, 'How it works'))


def build_about():
    title = f'About {COMPANY}'
    description = f'{COMPANY} is {COMPANY_KIND} that prepares pool drawing packages. It does not seal drawings.'
    crumbs = crumbs_html([('/', 'Home'), ('', 'About')])
    services = ''.join(f'<li><a href="{href}">{label}</a>. {text}</li>' for href, label, text in SERVICE_LINKS[:7])
    services += '<li><a href="/landscape/">Landscape design drawings</a>. Master plans, hardscape layouts and planting drawings.</li>'
    by_type = ' · '.join(f'<a href="{href}">{escape(label)}</a>' for href, label, _ in TOPIC_LINKS)
    body = f'''<section class="section prose-page" aria-labelledby="page-heading"><div class="wrap"><div class="prose">{crumbs}<span class="eyebrow">ABOUT</span><h1 id="page-heading">About {COMPANY}.</h1><p class="lead">JEBN prepares swimming pool drawing packages for US permits and construction: permit drawings, construction drawings, shop drawings and drafting support for pool builders, designers and engineers.</p><h2>The company</h2><p>{COMPANY} is {COMPANY_KIND}. It is on file with the Florida Division of Corporations under document number {FLORIDA_DOCUMENT}. Benatic Paul Martin, the founder, is your contact for every project.</p><h2>What JEBN does</h2><ul>{services}</ul><p>Drawing sets by project type: {by_type}</p><p>Drawings are delivered as DWG and PDF files. Your quote lists the sheets, the revisions included and the delivery date before you commit. <a href="/how-it-works/">How the service works</a> · <a href="/samples/">Sample drawings</a></p><h2>What JEBN does not do</h2><p>{seal_short()} <a href="/services/pool-engineering/">How the engineer’s seal works</a></p><h2>Contact</h2><p>Benatic Paul Martin · <a href="mailto:{EMAIL}">{EMAIL}</a></p><p>Mailing address: {COMPANY}, {MAIL_ADDRESS}. This is a mailing address, not an office. Please send drawings and project files by email.</p>{QUOTE_BUTTON}</div></div></section>'''
    canonical = f'{SITE}/about/'
    return shell('about', title, description, body, page_schema(canonical, title, description, 'About', 'AboutPage'), brand='')


# ---------------------------------------------------------------- 404 page

def build_404():
    links = [('/', 'Home'), ('/services/pool-permit-drawings/', 'Pool permit drawings'), ('/pool/', 'Pool construction drawings'),
             ('/samples/', 'Sample drawings'), ('/how-it-works/', 'How it works'), ('/states/', 'All state pages'), ('/landscape/', 'Landscape design'),
             ('/resources/pool-project-checklist/', 'Project input checklist'), ('/about/', 'About JEBN')]
    lis = ''.join(f'<li><a href="{h}">{t}</a></li>' for h, t in links)
    body = f'''<section class="section prose-page" aria-labelledby="page-heading"><div class="wrap"><div class="prose"><span class="eyebrow">PAGE NOT FOUND</span><h1 id="page-heading">This page could not be found.</h1><p>The address may have changed or the page may have moved. Use one of these links, or send us your project details.</p><ul class="not-found-links">{lis}</ul><div class="actions"><a class="button primary" href="/#contact">Get my quote <span aria-hidden="true">→</span></a></div>{state_directory('Or choose your state')}</div></div></section>'''
    shell('', 'Page Not Found', 'Find JEBN pool drawing services, state pages and the quote request form.', body, None, out='404.html', noindex=True)


# ---------------------------------------------------------------- landscape page

LANDSCAPE_ROWS = [
    ('Landscape master plans', 'One buildable master plan that brings softscape, hardscape, grades and drainage together. Grading and drainage follow your engineer’s or contractor’s information.'),
    ('Hardscape layouts', 'Paving, walls, pergolas, water features and outdoor living areas, laid out and detailed for your contractor. Retaining walls and other structures follow your engineer’s or builder’s structural details.'),
    ('Softscape & planting design', 'Climate-adaptive, water-wise planting plans and schedules. Native and adapted species matched to your site, from US hardiness zones to hot, arid regions.'),
    ('Technical & construction drawings', 'Layout plans, sections, details and specifications for your contractor, and for permit submission where your office asks for landscape drawings.'),
    ('Irrigation & water-wise design', 'Irrigation layouts for hot, dry climates that keep planting healthy and limit water use.'),
    ('3D visuals', 'Renders and concept visuals that show the design before it is built. Ask to include them alongside the drawing set.'),
]

LANDSCAPE_POINTS = [
    ('Planting matched to the site', 'US hardiness zones, HOA-friendly layouts, or heat-, drought- and salt-tolerant species where the site calls for them.'),
    ('Soft and hard landscape together', 'Planting, paving and hardscape are laid out together, so the drawings agree with each other.'),
    ('Visuals and construction drawings', 'The 3D visuals and the build set are prepared by the same designer, from concept to handoff.'),
    ('Villas to commercial sites', 'Private villas, residential developments and commercial properties, including a planting plan for a 40-acre site.'),
    ('Remote delivery', 'Drawings and visuals are prepared remotely and delivered as DWG and PDF files.'),
]

LANDSCAPE_WORK = [
    ('landscape-frontyard-villa.jpg', 'Front yard landscape design for a private villa', 'Front yard landscape, private villa', 'Full front-yard design integrating planting, hardscape and the entry approach into one buildable plan.'),
    ('landscape-villa-backyard.jpg', 'Private villa backyard landscape design', 'Private villa backyard', 'Complete backyard design with pergola, planting and outdoor living for a private villa.'),
    ('landscape-backyard-kids-pool.jpg', 'Backyard landscape with kids play area and pool', 'Backyard, kids’ play area and pool', 'Family backyard integrating a kids’ play area, lawn, planting and a swimming pool.'),
    ('landscape-hardscape-pool-villa.jpg', 'Hardscape and swimming pool design for a private villa', 'Hardscape and pool, private villa', 'Integrated hardscape and swimming-pool design with water features for a private villa.'),
    ('landscape-planting-commercial.jpg', 'Planting plan for a 40-acre commercial property', 'Planting plan, 40-acre commercial site', 'Large-scale planting plan and plant palette for a 40-acre commercial property.'),
    ('landscape-soft-hardscape-plan.jpg', '2D softscape planting plan and hardscape layout', 'Softscape and hardscape plan', 'Coordinated 2D softscape planting plan and hardscape layout.'),
]

LANDSCAPE_SEAL = 'JEBN does not seal drawings. If your permit office asks for sealed landscape or site drawings, a landscape architect or engineer licensed in your state has to take responsibility for them and seal them. Send the office’s checklist with your request, so we can tell you which sheets it covers.'

LANDSCAPE_FAQ = [
    ('What do I receive?', 'DWG and PDF drawing sets, planting plans and schedules, irrigation layouts, bills of quantities and 3D renders, depending on the scope you choose.'),
    ('Can you design for my climate?', 'Yes. Planting is matched to your site, whether that means US hardiness zones and HOA-friendly layouts or hot, arid conditions. We choose species that perform where you build.'),
    ('Do you work with clients in other time zones?', 'Yes. We deliver for clients across the USA, UK, Canada and the Gulf, and work around your time zone with digital delivery.'),
    ('How fast can you deliver?', 'It depends on the scope. Smaller residential plans can be delivered within days. We confirm the timeline with you before work starts.'),
    ('Can the drawings be sealed for a permit?', LANDSCAPE_SEAL),
    ('How do we start?', 'Send your scope through the form on this page. We reply within 24 hours with questions or a quote. No payment is needed to ask.'),
]

def build_landscape():
    title = 'Landscape Design Drawings & Master Plans'
    description = 'Landscape master plans, hardscape layouts and planting drawings for homeowners, pool contractors and builders. DWG and PDF with 3D visuals. Free quote.'
    lead = 'Landscape master plans, hardscape layouts and planting drawings for homeowners, pool contractors and builders. Build-ready construction drawings and 3D visuals, with planting matched to your climate.'
    crumbs = crumbs_html([('/', 'Home'), ('', 'Landscape design')])
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#package">What we draw</a><a href="#work">Sample work</a><a href="#faq">Questions</a><a href="#contact">Get my quote ↗</a></div></nav>'
    links = '<p class="package-links"><strong>Pool work:</strong> <a href="/services/pool-permit-drawings/">Pool permit drawings</a> · <a href="/pool/">Construction drawings</a> · <a href="/services/pool-shop-drawings/">Shop drawings</a></p>'
    points = ''.join(f'<li><strong>{k}</strong>{v}</li>' for k, v in LANDSCAPE_POINTS)
    about = f'''<section class="section inputs-section" id="about" aria-labelledby="about-heading"><div class="wrap input-grid"><div><span class="eyebrow">ABOUT THE LANDSCAPE WORK</span><h2 id="about-heading">Landscape drawings for your site and climate.</h2><p>{COMPANY} prepares landscape design drawings alongside its pool drawing work: hardscape, softscape and planting design, with 3D visuals and build-ready technical drawings.</p><p>Benatic Paul Martin, founder and landscape designer, has worked on private villas, residential developments and commercial projects for clients in the USA, the UK and the Gulf.</p><a class="text-link" href="#contact">Ask about your project ↗</a></div><ul class="input-list">{points}</ul></div></section>'''
    cards = preview_cards(LANDSCAPE_WORK, 'View preview')
    work = f'''<section class="section local-section" id="work" aria-labelledby="work-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">SAMPLE WORK</span><h2 id="work-heading">Landscape, hardscape and planting projects.</h2></div><div><p>A selection of landscape, hardscape and planting projects, from private villas to commercial sites.</p><p class="work-note">Produced in AutoCAD, SketchUp, Lumion, Revit and Photoshop. Deliverables include DWG and PDF drawings, planting schedules, irrigation layouts, bills of quantities and 3D renders.</p></div></div><div class="work-grid">{cards}</div></div></section>''' + viewer_dialog(LANDSCAPE_WORK[0][0])
    steps = [
        ('1. Share your project', 'Send your site plan or photos, style preferences and scope through the form. We reply within 24 hours with questions or a quote.'),
        ('2. Design and visuals', 'Planting design, hardscape detailing and 3D visuals, prepared in AutoCAD, SketchUp and Lumion.'),
        ('3. Review and refine', 'You review the design and we revise it to fit your site, climate and budget. Your quote states the revisions included.'),
        ('4. Build-ready handoff', 'DWG and PDF drawings, planting schedules, irrigation layouts and bills of quantities for your contractor.'),
    ]
    step_html = step_items([(k.split('. ', 1)[1], v) for k, v in steps])
    process = f'''<section class="section blue" id="delivery" aria-labelledby="delivery-heading"><div class="wrap"><span class="eyebrow">FROM BRIEF TO BUILD-READY</span><h2 id="delivery-heading">Four steps from brief to drawings.</h2><ol class="delivery-steps four">{step_html}</ol><div class="review-note"><h3>Permits and sealed drawings</h3><p>{LANDSCAPE_SEAL} The permit office decides permit approval.</p></div><div class="actions"><a class="button primary" href="#contact">Get my quote <span aria-hidden="true">→</span></a></div></div></section>'''
    feedback = clients_section('Feedback from clients on pool, water feature and outdoor-space drawing work.')
    line = f'''<section class="coverage-line" id="coverage" aria-label="Coverage"><div class="wrap"><p><strong>{COMPANY} · Landscape design drawings, delivered remotely.</strong> Need pool plans as well? Pool plans and permit drawings are available for US projects.</p><a href="/services/pool-permit-drawings/">Pool permit drawings</a></div></section>'''
    facts = [('Timeline', 'Agreed in your quote'), ('File delivery', 'DWG + PDF')]
    small = 'Delivery time depends on the scope and is confirmed before work starts. JEBN does not seal drawings.'
    body = (hero('LANDSCAPE DESIGN DRAWINGS', 'Landscape design drawings.<br><span>Planting, hardscape and master plans.</span>', lead,
                 form(title, notes_placeholder='e.g. backyard with pool, planting plan and paving layout, about 60 x 40 ft', pool=False), crumbs, facts, small,
                 second=('See sample work ↓', '#work'), form_heading='Get your landscape drawing quote.', panel_quote=False, picture='landscape', strip='') + nav
            + package_section(rows=LANDSCAPE_ROWS, heading='What we draw<br>for your site.', lead='Planting, paving and hardscape laid out together, then drawn as one coordinated set a contractor can build from.', links=links)
            + about + work + process + feedback
            + faq_block('BEFORE YOU ASK', 'Questions about landscape drawings.', LANDSCAPE_FAQ)
            + line)
    canonical = f'{SITE}/landscape/'
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Service', '@id': canonical+'#service', 'name': title, 'serviceType': 'Landscape design drawings', 'description': description, 'url': canonical, 'provider': organization()},
        faq_schema(canonical, LANDSCAPE_FAQ),
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Landscape design', 'item': canonical}]},
    ]}
    return shell('landscape', title, description, body, schema)


# ---------------------------------------------------------------- state pages

def short_place(name):
    n = re.split(r'\s*[(/]', name)[0].strip()
    n = re.sub(r'^(City|Town|Village|Township) of ', '', n)
    return re.sub(r' area$', '', n)


def load_local(slug):
    p = ROOT/'tools/data/local'/f'{slug}.json'
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    d['jurisdictions'] = [j for j in d.get('jurisdictions', []) if j.get('name') and j.get('notes')]
    return d


def date_words(iso):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    y, m, d = (int(x) for x in iso.split('-'))
    return f'{months[m-1]} {d}, {y}'


def local_section(state, local):
    names = []
    for j in (local or {}).get('jurisdictions', []):
        n = short_place(j['name'])
        if n and n not in names:
            names.append(n)
    if len(names) > 3:
        h2 = f'Pool permit notes for {", ".join(names[:3])} and more in {state}.'
    elif names:
        h2 = f'Pool permit notes for {names[0] if len(names) == 1 else ", ".join(names[:-1])+" and "+names[-1]}, {state}.'
    else:
        h2 = f'Local pool permit notes for {state}.'
    head = f'<span class="eyebrow">{state.upper()} · CITY AND COUNTY PERMIT NOTES</span><h2 id="local-heading">{h2}</h2>'
    other = f'<p>Your city or county is not listed? Name the permit office in the quote form. We draw to the checklist it publishes.</p>'
    if not local or not local['jurisdictions']:
        return f'''<section class="section local-section" id="local" aria-labelledby="local-heading"><div class="wrap local-head"><div>{head}</div><div><p>Each city and county in {state} runs its own pool permit review. Send the name of your permit office and its submittal checklist with your request. We identify the drawings and calculations it asks for before work starts.</p><a class="text-link" href="#contact">Send your permit office ↗</a></div></div></section>'''
    cards, used, jumps = [], set(), []
    state_date = local.get('researched') or BUILD_DATE
    saved_copy = False
    for j in local['jurisdictions']:
        jid = re.sub(r'[^a-z0-9]+', '-', short_place(j['name']).lower()).strip('-') or 'place'
        while jid in used:
            jid += '-2'
        used.add(jid)
        office = clean(j.get('office'))
        portal = ''
        if j.get('portal_name') and safe_url(j.get('portal_url')):
            portal = f'<span class="local-portal">Online portal: {ext_link(j["portal_url"], j["portal_name"])}</span>'
        elif j.get('portal_name'):
            portal = f'<span class="local-portal">Online portal: {clean(j["portal_name"])}</span>'
        rest = j['notes'][2:]
        more = ''
        if rest:
            more = f'<details class="more-notes"><summary>{len(rest)} more permit note{"s" if len(rest) != 1 else ""}</summary><ul>{"".join(f"<li>{clean(n)}</li>" for n in rest)}</ul></details>'
        notes = '<ul>'+''.join(f'<li>{clean(n)}</li>' for n in j['notes'][:2])+'</ul>'+more
        srcs = []
        for s in j.get('sources', []):
            if not safe_url(s.get('url')):
                continue
            link = ext_link(s.get('url'), s.get('title') or 'Official page')
            if s.get('as_of'):
                # Read from a dated copy of the official page, not the live page.
                link += f' (copy saved {date_words(s["as_of"])})'
                saved_copy = True
            srcs.append(link)
        checked_on = f' · Checked {date_words(j["checked"])}' if j.get('checked') and j['checked'] != state_date else ''
        src = f'<p class="local-src">Source: {" · ".join(srcs)}{checked_on}</p>' if srcs else ''
        place, _, county = j['name'].partition(' / ')
        h3 = f'{clean(place)} pool permit notes ({clean(county)})' if county else f'{clean(j["name"])} pool permit notes'
        portal_line = f'<p class="local-office">{portal}</p>' if portal else ''
        jumps.append(f'<a href="#{jid}">{clean(short_place(j["name"]))}</a>')
        cards.append(f'<details class="local-card" id="{jid}" data-open-wide><summary><h3>{h3}</h3><span class="local-office">{office}</span></summary>{portal_line}{notes}{src}</details>')
    state_level = ''
    if local.get('state_level'):
        items = ''.join(f'<li>{clean(s.get("note"))} <span class="local-src">Source: {ext_link((s.get("source") or {}).get("url"), (s.get("source") or {}).get("title") or "Official page")}</span></li>' for s in local['state_level'] if s.get('note'))
        if items:
            state_level = f'<div class="state-level"><h3>Statewide</h3><ul>{items}</ul></div>'
    checked = date_words(state_date)
    copy_note = ' Where a source says “copy saved”, the note was read from a dated copy of that official page.' if saved_copy else ''
    later = ' unless a card gives a later date' if any(j.get('checked') and j['checked'] != state_date for j in local['jurisdictions']) else ''
    return f'''<section class="section local-section" id="local" aria-labelledby="local-heading"><div class="wrap"><div class="local-head"><div>{head}</div><div><p>Each city and county runs its own pool permit review. These notes come from the pages each office publishes, checked on {checked}{later}. Rules change, so open the linked source or send us the current checklist with your request.{copy_note}</p>{other}</div></div><p class="local-jump"><span>Jump to:</span> {' '.join(jumps)}</p><div class="local-grid">{''.join(cards)}</div>{state_level}</div></section>'''


STAMP_REMINDER = 'Rules change, so check the current requirements before you submit.'


def stamp_question(state):
    return f'Do I need an engineer’s stamp for a pool in {state}?'


def stamp_entry(slug):
    """The state's short answer, or None. Stops the build if an entry is incomplete, so a half-written answer cannot go out."""
    entry = STAMP_ANSWERS['states'].get(slug)
    if entry is None:
        return None
    sources = entry.get('sources') or []
    parts = entry.get('answer') or []
    parts = [re.sub(r'\s+', ' ', str(p)).strip() for p in ([parts] if isinstance(parts, str) else parts)]
    if not parts or not all(parts) or not sources or not all(safe_url(s.get('url')) and s.get('title') for s in sources):
        raise SystemExit(f'tools/data/stamp-answers.json: the entry for {slug} needs an answer and at least one source with a title and an address')
    # The reminder is part of the answer itself, so it travels with the copy that search engines read.
    parts[-1] = f'{parts[-1]} {STAMP_REMINDER}'
    return {'answer': parts, 'sources': sources}


def stamp_text(entry):
    """The whole answer as one string, for the question-and-answer data that search engines read."""
    return ' '.join(entry['answer'])


def stamp_section(state, entry):
    """A short answer under the hero of a state page, with the official pages it was read from.
    The first part is the answer in one sentence; the rest says where it comes from."""
    srcs = ' · '.join(ext_link(s['url'], s['title'] + (' (PDF)' if '.pdf' in s['url'].lower() else '')) for s in entry['sources'])
    text = ''.join(f'<p class="stamp-text{" stamp-lead" if i == 0 else ""}">{clean(p)}</p>' for i, p in enumerate(entry['answer']))
    return (f'<section class="section stamp-section" id="stamp" aria-labelledby="stamp-heading"><div class="wrap"><div class="stamp-answer">'
            f'<span class="eyebrow">{state.upper()} · SHORT ANSWER</span><h2 id="stamp-heading">{clean(stamp_question(state))}</h2>'
            f'{text}'
            f'<p class="stamp-role">{seal_short(state)} <a href="/services/pool-engineering/">How the engineer’s seal works</a></p>'
            f'<p class="local-src">Sources: {srcs} · Checked {date_words(STAMP_ANSWERS["checked"])}. General information, not legal advice.</p></div></div></section>')


def fact_sources(fact):
    """An optional third element of a state fact: the official pages it was read from."""
    srcs = [ext_link(x.get('url'), x.get('title') or 'Official page') for x in (fact[2] if len(fact) > 2 else []) if safe_url(x.get('url'))]
    return f' <span class="local-src">Source: {" · ".join(srcs)}</span>' if srcs else ''


def join_places(names):
    names = list(names)
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


def requirements_section(state, rec):
    article = 'an' if state[0] in 'AEIOU' else 'a'
    steps = []
    for raw in rec['seal_steps']:
        s = BeautifulSoup(raw, 'html.parser')
        num = s.b.get_text(strip=True) if s.b else ''
        text = s.span.get_text(' ', strip=True) if s.span else s.get_text(' ', strip=True)
        steps.append(f'<li><b aria-hidden="true">{clean(num)}</b><span>{clean(text)}</span></li>')
    intro = (f'<p>Each city and county reviews pool plans against its own checklist. These are requirements and site conditions that can apply in {state}. '
             'Structural design, including any wind, flood, seismic or uplift loads at your site, comes from your engineer or your builder’s standard details. We draw it.</p>')
    seal = f'<p class="small">{seal_short(state)}</p>'
    left = f'<div><span class="eyebrow">{state.upper()} REQUIREMENTS</span><h2 id="req-heading">What {state} permit offices check.</h2>{intro}<ol class="req-list">{"".join(steps)}</ol>{seal}</div>'
    right = ''
    if rec['facts']:
        split = lambda v: re.sub(r'\.?;\s+(\S)', lambda m: '. ' + m.group(1).upper(), str(v))
        facts = ''.join(f'<dt>{clean(f[0])}</dt><dd>{clean(split(f[1]))}{fact_sources(f)}</dd>' for f in rec['facts'])
        fi = clean(rec['facts_intro'][0]) if rec['facts_intro'] else 'The state-level rules your drawings are checked against. Cities and counties can add local amendments, so name your permit office in your request.'
        right = f'<div><h3 class="facts-title">{state} state-level rules</h3><p class="small">{fi}</p><dl class="state-facts">{facts}</dl></div>'
    cls = 'req-grid' if right else 'req-grid single'
    return f'<section class="section req-section" id="requirements" aria-labelledby="req-heading"><div class="wrap {cls}">{left}{right}</div></section>'


def faq_items(state, rec, offer=True):
    items = [(q, a) for q, a in rec['faq']]
    if not any('sealed by an engineer' in q for q, _ in items):
        # Every state page answers the seal question. Most records carry their own answer; these do not.
        items.append((f'Who seals pool drawings in {state}?', seal_answer(state, offer)))
    items.append(('What if plan review comes back with comments?', PLAN_REVIEW_ANSWER))
    items.append((f'How fast can you prepare {state} pool drawings?', TURNAROUND))
    items.append((f'Do you work to my city or county’s checklist in {state}?', 'Yes. Send the submittal checklist or the review comments from your permit office. Your quote lists the drawings that respond to it.'))
    return items


def faq_section(state, items):
    body = ''.join(f'<details><summary>{clean(q)}</summary><p>{clean(a)}</p></details>' for q, a in items)
    return f'<section class="section faq-section" id="faq" aria-labelledby="faq-heading"><div class="wrap faq-layout"><div><span class="eyebrow">{state.upper()} QUESTIONS</span><h2 id="faq-heading">Questions about {state} pool plans.</h2></div><div class="faq-list">{body}</div></div></section>'


def build_state(slug, rec):
    state = name_of(slug)
    local = load_local(slug)
    places = []
    if local:
        for j in local['jurisdictions']:
            n = short_place(j['name'])
            if n and n not in places:
                places.append(n)
    offer = slug not in NO_ENGINEER_OFFER
    title = f'{state} Pool Plans & Permit Drawings'
    base = f'{state} pool plans and permit drawings.'
    tail = ' Free quote, reply within 24 hours.'
    description = base+tail
    for k in (4, 3, 2, 1):
        if len(places) >= k:
            listed = ', '.join(places[:k])
            more = ' and more' if len(places) > k else ''
            cand = f'{base} Permit notes for {listed}{more}.{tail}'
            if len(cand) <= 155:
                description = cand
                break
    where = f'pools in {", ".join(places[:3])} and across {state}' if len(places) >= 3 else f'pools across {state}'
    lead = f'Permit and construction drawings for {where}, drawn to your permit office’s checklist. {seal_short(state)}'
    crumbs = f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">/</span> <a href="/states/">States</a> <span aria-hidden="true">/</span> <span aria-current="page">{state}</span></nav>'
    h1 = f'{state} pool permit drawings<br><span>and construction drawings.</span>'
    stamp = stamp_entry(slug)
    stamp_link = '<a href="#stamp">Engineer’s stamp</a>' if stamp else ''
    nav = f'<nav class="landing-nav" aria-label="Page sections"><div class="wrap">{stamp_link}<a href="#local">Local permit notes</a><a href="#requirements">State requirements</a><a href="#package">Drawing package</a><a href="#contact">Get my quote ↗</a></div></nav>'
    links = '<p class="package-links"><a href="/services/pool-permit-drawings/">Pool permit drawings</a> · <a href="/pool/">Construction drawings</a> · <a href="/services/pool-engineering/">How the engineer’s seal works</a></p>'
    links += '<p class="package-links"><strong>By project type:</strong> ' + ' · '.join(f'<a href="{href}">{escape(label)}</a>' for href, label, _ in TOPIC_LINKS) + '</p>'
    faqs = faq_items(state, rec, offer)
    nearby = ''
    near = [(h, t) for h, t in rec.get('nearby', []) if h.strip('/').split('/')[-1] not in OFFLINE]   # no link to a page that is offline
    if near:
        nearby = '<p class="nearby-line"><strong>Nearby states:</strong> '+' · '.join(f'<a href="{escape(h)}">{clean(t)}</a>' for h, t in near)+'</p>'
    if stamp:
        jump = (clean(stamp_question(state)), '#stamp')
    elif places:
        jump = (clean(f'Permit notes for {join_places(places[:3])}'), '#local')
    else:
        jump = None
    body = (hero(f'{state.upper()} / POOL PERMIT DRAWINGS', h1, lead, form(title, state, CITY[slug]), crumbs, strip=HERO_STRIP, jump=jump) + nav
            + (stamp_section(state, stamp) if stamp else '') + samples_section()
            + local_section(state, local) + audience_section(state) + pool_clients()
            + package_section(state, links=links)
            + requirements_section(state, rec)
            + inputs_section(f'Planning a pool in {state}?', 'Start with your project address and the city or county reviewing the permit. Send its submittal checklist or review comments if you have them, so we can identify the drawings needed.')
            + delivery_section(state, offer)
            + faq_section(state, faqs)
            + coverage_section(nearby))
    canonical = f'{SITE}/states/{slug}/'
    # The short answer is shown under the hero, not in the questions list, so it is added to the page's question data here.
    asked = ([(stamp_question(state), stamp_text(stamp))] if stamp else []) + faqs
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Service', '@id': canonical+'#service', 'name': title, 'serviceType': 'Swimming pool permit and construction drawings', 'description': description, 'url': canonical, 'provider': organization(), 'areaServed': {'@type': 'State', 'name': state, 'containedInPlace': {'@type': 'Country', 'name': 'United States'}}},
        {'@type': 'FAQPage', '@id': canonical+'#faq', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in asked]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'States', 'item': SITE+'/states/'},
            {'@type': 'ListItem', 'position': 3, 'name': state, 'item': canonical}]},
    ]}
    return shell(f'states/{slug}', title, description, body, schema)


def build_states_index():
    title = 'Pool Permit Drawings by State'
    description = 'Pool permit drawings and construction drawings by state. Choose your state for city and county permit notes, state pool rules and a drawing quote.'
    cards = []
    for slug, rec in sorted(STATES.items()):
        state = name_of(slug)
        local = load_local(slug)
        places = []
        if local:
            for j in local['jurisdictions']:
                n = short_place(j['name'])
                if n and n not in places:
                    places.append(n)
        line = clean(rec.get('index_blurb') or f'Pool permit drawing sets for {state}.')
        notes = f'<span class="state-places">Local permit notes: {clean(", ".join(places[:4]))}</span>' if places else ''
        cards.append(f'<a class="state-card" href="/states/{slug}/"><strong>{state}</strong><span>{line}</span>{notes}</a>')
    crumbs = '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">/</span> <span aria-current="page">States</span></nav>'
    lead = 'Pool permit drawings, construction drawings and details for homeowners, pool contractors and builders. Each state page lists city and county permit notes with links to the official sources.'
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#all-states">All state pages</a><a href="#package">Drawing package</a><a href="#delivery">Delivery and seals</a><a href="#contact">Get my quote ↗</a></div></nav>'
    grid = f'''<section class="section local-section" id="all-states" aria-labelledby="states-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">USA · STATE PAGES</span><h2 id="states-heading">Choose your state.</h2></div><div><p>Every state page has the state-level pool rules, permit notes for named cities and counties, and the quote form. Your city or county is not listed? Name the permit office in your request.</p></div></div><nav class="state-cards" aria-label="State pages">{"".join(cards)}</nav></div></section>'''
    body = (hero('USA / POOL PERMIT DRAWINGS BY STATE', 'Pool permit drawings.<br><span>State by state.</span>', lead, form('Pool Permit Drawings by State'), crumbs, second=('See all state pages ↓', '#all-states')) + nav
            + grid + package_section() + delivery_section()
            + f'''<section class="coverage-line" id="coverage" aria-label="USA coverage"><div class="wrap"><p><strong>{COMPANY}.</strong> We draft pool drawings for US permit submissions.</p><a href="/services/pool-permit-drawings/">Pool permit drawings</a></div></section>''')
    canonical = f'{SITE}/states/'
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', '@id': canonical+'#page', 'name': title, 'description': description, 'url': canonical, 'isPartOf': {'@type': 'WebSite', 'name': 'JEBN Engineering', 'url': SITE+'/'}},
        {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': name_of(s), 'url': f'{SITE}/states/{s}/'} for i, s in enumerate(sorted(STATES), 1)]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'States', 'item': canonical}]},
    ]}
    return shell('states', title, description, body, schema)


def update_sitemap(urls):
    """Writes sitemap.xml with exactly the pages built. A page that differs from its last committed version gets
    BUILD_DATE; every other page keeps the date it has in the committed sitemap."""
    p = ROOT/'sitemap.xml'
    dates = lambda xml: dict(re.findall(r'<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>', xml or ''))
    committed = dates(last_committed('sitemap.xml'))
    on_disk = dates(p.read_text() if p.exists() else '')
    rows = []
    for u in urls:
        day = BUILD_DATE if u in CHANGED else (committed.get(u) or on_disk.get(u) or BUILD_DATE)
        rows.append(f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{day}</lastmod>\n  </url>\n')
    p.write_text("<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"+''.join(rows)+'</urlset>\n')


def remove_offline_pages():
    """Deletes the built page of each state in OFFLINE."""
    gone = []
    for slug in sorted(OFFLINE):
        folder = ROOT/'states'/slug
        (folder/'index.html').unlink(missing_ok=True)
        if folder.is_dir():
            (folder/'.DS_Store').unlink(missing_ok=True)   # Finder leaves this file in a folder it has opened
            if any(folder.iterdir()):
                print('Not removed, it holds other files:', folder)
            else:
                folder.rmdir()
        gone.append(f'{SITE}/states/{slug}/')
    return gone


if __name__ == '__main__':
    import datetime, sys
    for f, phrase, due in RECHECK:
        if datetime.date.today().isoformat() >= due and (ROOT/f).is_file() and phrase in (ROOT/f).read_text(encoding='utf-8'):
            print(f'RECHECK {f}: "{phrase}" was due for a source check on {due}', file=sys.stderr)
    built = [build_home()]
    built += [build_service(p) for p in SERVICES]
    built.append(build_seal_page())
    built += [build_topic(t) for t in TOPICS]
    built += [build_state(slug, rec) for slug, rec in sorted(STATES.items())]
    built.append(build_states_index())
    built += [build_samples(), build_how(), build_about()]
    built += [build_privacy(), build_landscape(), build_checklist()]
    build_404()   # served for any missing address; not listed in the sitemap
    # The page about sealed plans became the page on drafting for an engineer of record; its old address sends visitors on.
    build_moved('services/pe-stamped-pool-plans', 'services/pool-drawings-for-engineer-of-record', 'Pool drawings for your engineer of record')
    remove_offline_pages()
    update_sitemap(built)
    print('Built', len(built), 'pages;', len(CHANGED), 'changed')

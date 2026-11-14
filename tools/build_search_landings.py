"""Focused Search destinations: three national pages and the 50 state pages.

Reuses the deployed header, consent panel, footer and enquiry form contract.
Data:
  tools/data/states.json        state-level content for each state page
  tools/data/local/<slug>.json  city and county permit notes with official sources
Run after build-assets.sh. Does not alter Ads settings or submit forms.
"""
from pathlib import Path
from html import escape
import hashlib, json, re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://www.jebnengineering.com'
BASE = BeautifulSoup((ROOT/'index.html').read_text(), 'html.parser')
STATES = json.loads((ROOT/'tools/data/states.json').read_text())
BUILD_DATE = '2026-11-15'

# Largest or best-known city, used only as the form placeholder example.
CITY = {'alabama':'Birmingham','alaska':'Anchorage','arizona':'Phoenix','arkansas':'Little Rock','california':'San Diego','colorado':'Denver','connecticut':'Stamford','delaware':'Wilmington','florida':'Tampa','georgia':'Atlanta','hawaii':'Honolulu','idaho':'Boise','illinois':'Naperville','indiana':'Carmel','iowa':'Des Moines','kansas':'Overland Park','kentucky':'Lexington','louisiana':'New Orleans','maine':'Portland','maryland':'Annapolis','massachusetts':'Boston','michigan':'Grand Rapids','minnesota':'Minneapolis','mississippi':'Jackson','missouri':'St. Louis','montana':'Billings','nebraska':'Omaha','nevada':'Las Vegas','new-hampshire':'Manchester','new-jersey':'Paramus','new-mexico':'Albuquerque','new-york':'Huntington','north-carolina':'Charlotte','north-dakota':'Fargo','ohio':'Columbus','oklahoma':'Oklahoma City','oregon':'Portland','pennsylvania':'Pittsburgh','rhode-island':'Providence','south-carolina':'Charleston','south-dakota':'Sioux Falls','tennessee':'Nashville','texas':'Houston','utah':'Salt Lake City','vermont':'Burlington','virginia':'Virginia Beach','washington':'Seattle','west-virginia':'Charleston','wisconsin':'Madison','wyoming':'Cheyenne'}

NATIONAL = [
 dict(path='pool', title='Pool Construction Drawings & Engineering Plans',
      h1='Pool construction drawings.<br><span>From layout to detail.</span>',
      kicker='USA / RESIDENTIAL POOL DRAWING PACKAGES',
      description='Coordinated pool plans, sections, construction details and equipment layouts for residential projects. Send your sketch or existing plans for a drawing-package quote.'),
 dict(path='services/pool-permit-drawings', title='Swimming Pool Plans & Permit Drawings',
      h1='Swimming pool plans.<br><span>Built around your permit scope.</span>',
      kicker='USA / RESIDENTIAL POOL PERMIT DRAWINGS',
      description='Site layouts, pool plans, sections and supporting calculations for your residential pool permit package. We confirm the project requirements and drawing scope before work begins.'),
 dict(path='services/pool-engineering', title='Pool Engineering Plans & Structural Design',
      h1='Pool engineering plans.<br><span>Structural design for your permit.</span>',
      kicker='USA / RESIDENTIAL POOL ENGINEERING',
      description='Residential pool engineering for homeowners, pool contractors and builders: structural plans, reinforcement details, hydraulic calculations and PE review for your permit. Send your layout for a scope and quote.',
      meta='Pool engineering for your permit: structural plans, reinforcement details, hydraulic calculations and PE review. Send your layout for a scope and quote.',
      engineering=True),
]


def asset(name):
    p = ROOT/'assets'/name
    return '/assets/'+name+'?v='+hashlib.sha256(p.read_bytes()).hexdigest()[:12]


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


def form(title, state=None, city=None):
    doc = BeautifulSoup((ROOT/'tools/enquiry-form.html').read_text(), 'html.parser')
    f = doc.form
    f['data-search-enquiry'] = title
    doc.select_one('.form-intro').string = 'Name and email are enough to start. Add project details if you have them.'
    notes = doc.select_one('[name="message"]')
    notes['name'] = 'project_notes'; notes['id'] = 'enquiry-notes'; notes['rows'] = '2'; notes.attrs.pop('required', None)
    notes['placeholder'] = 'Pool dimensions, existing plans or permit comments…'
    label = doc.select_one('label[for="enquiry-message"]'); label['for'] = 'enquiry-notes'; label.string = 'Project details (optional)'
    hidden = doc.new_tag('input', attrs={'type': 'hidden', 'name': 'message', 'value': title+' quote request.'})
    doc.fieldset.append(hidden)
    loc = doc.select_one('[name="location"]')
    loc['placeholder'] = f'For example: {city}, {state}' if state else 'Project city and state'
    if state:
        loc['value'] = state
    privacy = doc.select_one('.form-privacy')
    privacy.clear(); privacy.append('We use your details to reply to this enquiry. ')
    a = doc.new_tag('a', href='/privacy/'); a.string = 'Privacy policy'; privacy.append(a)
    return str(doc)


def package_rows(pe, engineering=False):
    rows = [
        ('Site & pool layout', 'Pool position, dimensions, depths and sections, coordinated with the site information you supply.'),
        ('Construction details', 'Pool shell and reinforcement details within the agreed engineering scope; drawing references for your contractor.'),
        ('Hydraulics & equipment', 'Circulation layout, pipe sizing, TDH calculations and equipment schedules where included in your quote.'),
        ('Permit & PE coordination', pe),
    ]
    if engineering:
        rows = [
            ('Structural plans & details', 'Pool shell, wall and floor reinforcement, steps, benches and raised features, drawn to the engineering scope agreed for your project.'),
            ('Site & pool layout', 'Pool position, dimensions, depths and sections, coordinated with the site information you supply.'),
            ('Hydraulics & equipment', 'Circulation layout, pipe sizing, TDH calculations and equipment schedules where included in your quote.'),
            ('PE review & permit coordination', pe),
        ]
    return ''.join(f'<li><span class="sheet-number" aria-hidden="true">{i:02d}</span><div><h3>{label}</h3><p>{text}</p></div></li>' for i, (label, text) in enumerate(rows, 1))


def hero(kicker, h1, lead, form_html, crumbs=''):
    return f'''<section class="search-hero blue" aria-labelledby="hero-heading"><div class="wrap search-grid"><div class="search-copy">{crumbs}<span class="eyebrow">{kicker}</span><h1 id="hero-heading">{h1}</h1><p class="lead">{lead}</p><div class="actions"><a class="button primary" href="#contact">Get a drawing quote <span aria-hidden="true">↗</span></a><a class="text-link" href="#package">See the drawing package ↓</a></div><dl class="delivery-facts"><div><dt>Drawing preparation</dt><dd>2 business days</dd></div><div><dt>File delivery</dt><dd>DWG + PDF</dd></div></dl><p class="small">Two business days starts after we receive all project inputs for residential pool drawings. PE review, sealing and permit approval have separate timelines.</p><p class="search-contact">Your contact: <strong>Benatic Paul Martin</strong><br>JEBN Engineering · <a href="mailto:benatic@jebnengineering.com">benatic@jebnengineering.com</a></p></div>
<aside class="quote-panel" id="contact" aria-labelledby="contact-heading"><span class="eyebrow">PROJECT ENQUIRY · NO PAYMENT REQUIRED</span><h2 id="contact-heading" tabindex="-1">Get your drawing quote.</h2>{form_html}</aside></div></section>'''


def package_section(pe, engineering=False, links=''):
    return f'''<section class="section" id="services" aria-labelledby="package-heading"><div class="wrap package-editorial" id="package"><div><span class="eyebrow">YOUR DRAWING PACKAGE</span><h2 id="package-heading">Know what you’re<br>asking us to deliver.</h2><p class="lead">One project-specific scope, with the drawings, calculations and review responsibilities identified before you commit.</p><p class="package-note">Request a full package or help with existing plans. Your quote identifies the included sheets, PE review where applicable, revision scope and delivery date.</p><a class="text-link" href="#contact">Discuss your drawing set ↗</a>{links}</div><ol class="sheet-list">{package_rows(pe, engineering)}</ol></div></section>'''


def inputs_section(heading, para):
    return f'''<section class="section inputs-section" id="inputs" aria-labelledby="inputs-heading"><div class="wrap input-grid"><div><span class="eyebrow">WHAT TO SEND</span><h2 id="inputs-heading">{heading}</h2><p>{para}</p><p>You do not need every document to request a quote. After the first reply, you can share files by email.</p><a class="text-link" href="/resources/pool-project-checklist/">Open the project input checklist ↗</a></div><ul class="input-list"><li><strong>Project location</strong>City, state and permitting authority, if known.</li><li><strong>Site information</strong>Survey or site plan and known site constraints.</li><li><strong>Pool layout</strong>Sketch, dimensions, depths and proposed features.</li><li><strong>Existing work</strong>Plans, equipment preferences and permit review comments.</li></ul></div></section>'''


def delivery_section(pe):
    return f'''<section class="section blue" id="delivery" aria-labelledby="delivery-heading"><div class="wrap"><span class="eyebrow">FROM ENQUIRY TO DELIVERY</span><h2 id="delivery-heading">A clear scope.<br>A clear next step.</h2><ol class="delivery-steps"><li><h3>1. Confirm the scope</h3><p>We review your enquiry and reply with questions or a scoped quote. We identify missing inputs and the project’s review requirements.</p></li><li><h3>2. Prepare the drawings</h3><p>Residential drawing preparation takes 2 business days after all project inputs are received. PE review and sealing have a separate timeline.</p></li><li><h3>3. Review & deliver</h3><p>Receive the agreed DWG and PDF package. We confirm revision support in your quote. The local authority decides permit approval and timing.</p></li></ol><div class="review-note"><h3>Engineering & PE review</h3><p>{pe} A quote request does not guarantee permit approval.</p></div><details class="optional-concept"><summary>Optional: 3D pool visualization</summary><p>A 3D view can help you explore the proposed layout and materials. Ask to include it as a separate item alongside the drawing package.</p></details><div class="actions"><a class="button primary" href="#contact">Request your drawing quote ↗</a></div></div></section>'''


def state_directory(summary='Choose your state for local permit notes'):
    links = ''.join(f'<a href="/states/{s}/">{name_of(s)}</a>' for s in sorted(STATES))
    return f'<details class="state-directory"><summary>{summary}</summary><nav class="state-grid" aria-label="State pages">{links}</nav></details>'


def coverage_section(extra=''):
    return f'''<section class="coverage-line" id="coverage" aria-label="USA coverage"><div class="wrap"><p><strong>JEBN Engineering · USA enquiries, all 50 states.</strong> Project-specific engineering and PE arrangements are confirmed before acceptance.</p><a href="/states/">View state coverage</a></div><div class="wrap coverage-more">{extra}{state_directory()}</div></section>'''


def shell(path, title, description, body, schema, head_extra=''):
    header = ''.join(str(BASE.select_one(s)) for s in ['.skip-link', '.utility-bar', '.site-header', '#privacy-choices'])
    header = header.replace('Engineering services', 'Drawing services')
    footer = str(BASE.select_one('.site-footer'))
    full_title = title+' | JEBN Engineering'
    canonical = f'{SITE}/{path}/'
    ld = json.dumps(schema, ensure_ascii=False).replace('</', '<\\/')
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(full_title)}</title><meta name="description" content="{escape(description)}"><link rel="canonical" href="{canonical}"><meta name="theme-color" content="#0c5488"><meta name="referrer" content="strict-origin-when-cross-origin"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><meta property="og:title" content="{escape(full_title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{SITE}/images/pool-beachfront-villa.jpg"><meta name="twitter:card" content="summary_large_image">{head_extra}<link rel="stylesheet" href="{asset('studio.min.css')}"><link rel="stylesheet" href="{asset('search-landings.min.css')}"><script src="{asset('search-landings.min.js')}" defer></script><script src="{asset('studio.min.js')}" defer></script><script type="application/ld+json">{ld}</script></head><body class="search-landing">{header}<main id="main-content" tabindex="-1">{body}</main>{footer}</body></html>'''
    out = ROOT/path/'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return canonical


def organization():
    return {'@type': 'Organization', 'name': 'JEBN Engineering', 'url': SITE+'/'}


# ---------------------------------------------------------------- national pages

def build_national(p):
    pe = 'Engineering and PE review arrangements are confirmed for your project state and scope before work is accepted. Ask which services are available for your location.'
    engineering = p.get('engineering', False)
    extra = ''
    if engineering:
        extra = '''<section class="section inputs-section" id="when" aria-labelledby="when-heading"><div class="wrap input-grid"><div><span class="eyebrow">WHEN YOU NEED A POOL ENGINEER</span><h2 id="when-heading">When a pool permit calls for engineering.</h2><p>Many permit offices ask for engineered structural plans before they issue a pool permit. These are the common reasons. The checklist from your permit office decides what applies to your project.</p><a class="text-link" href="#contact">Ask about your project ↗</a></div><ul class="input-list"><li><strong>Sealed plans requested</strong>The checklist asks for structural plans or calculations sealed by a Professional Engineer licensed in your state.</li><li><strong>Close to a structure or slope</strong>The pool sits near a house footing, a retaining wall, a property-line wall or a slope.</li><li><strong>Difficult ground</strong>High groundwater, expansive clay, fill, or a soils report with design recommendations.</li><li><strong>Non-standard shells</strong>Raised walls, vanishing edges, attached spas, deep ends or a pool on a structure.</li></ul></div></section>'''
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#package">Drawing package</a><a href="#inputs">What to send</a><a href="#delivery">Delivery & PE review</a><a href="#contact">Request a quote ↗</a></div></nav>'
    body = (hero(p['kicker'], p['h1'], p['description'], form(p['title'])) + nav
            + package_section(pe, engineering) + extra
            + inputs_section('Start with the plans you have.', 'A sketch is enough to begin the conversation. If you already have a survey, drawings or permit comments, tell us what is ready. We identify the missing inputs before drawing work starts.')
            + delivery_section(pe) + coverage_section())
    canonical = f"{SITE}/{p['path']}/"
    meta = p.get('meta', p['description'])
    schema = {'@context': 'https://schema.org', '@type': 'Service', 'name': p['title'], 'description': meta, 'url': canonical, 'provider': organization(), 'areaServed': {'@type': 'Country', 'name': 'United States'}}
    # Routes a paid visit to the visitor's state page when the ad click carries a location id.
    head_extra = f'<script src="{asset("geo-route.min.js")}"></script>'
    return shell(p['path'], p['title'], meta, body, schema, head_extra)


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
    return f'{d} {months[m-1]} {y}'


def local_section(state, local):
    head = f'<span class="eyebrow">{state.upper()} · CITY AND COUNTY PERMIT NOTES</span><h2 id="local-heading">Local permit notes for {state}.</h2>'
    other = f'<p>Your city or county is not listed? Name the permit office in the enquiry form. We draw to the checklist it publishes.</p>'
    if not local or not local['jurisdictions']:
        return f'''<section class="section local-section" id="local" aria-labelledby="local-heading"><div class="wrap local-head"><div>{head}</div><div><p>Each city and county in {state} runs its own pool permit review. Send the name of your permit office and its submittal checklist with your enquiry. We identify the drawings and calculations it asks for before work starts.</p><a class="text-link" href="#contact">Send your permit office ↗</a></div></div></section>'''
    cards, used = [], set()
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
        notes = ''.join(f'<li>{clean(n)}</li>' for n in j['notes'])
        srcs = [ext_link(s.get('url'), s.get('title') or 'Official page') for s in j.get('sources', []) if safe_url(s.get('url'))]
        src = f'<p class="local-src">Source: {" · ".join(srcs)}</p>' if srcs else ''
        cards.append(f'<article class="local-card" id="{jid}"><h3>{clean(j["name"])}</h3><p class="local-office">{office}{portal}</p><ul>{notes}</ul>{src}</article>')
    state_level = ''
    if local.get('state_level'):
        items = ''.join(f'<li>{clean(s.get("note"))} <span class="local-src">Source: {ext_link((s.get("source") or {}).get("url"), (s.get("source") or {}).get("title") or "Official page")}</span></li>' for s in local['state_level'] if s.get('note'))
        if items:
            state_level = f'<div class="state-level"><h3>Statewide</h3><ul>{items}</ul></div>'
    checked = date_words(local.get('researched') or BUILD_DATE)
    return f'''<section class="section local-section" id="local" aria-labelledby="local-heading"><div class="wrap"><div class="local-head"><div>{head}</div><div><p>Each city and county runs its own pool permit review. These notes come from the pages each office publishes, checked on {checked}. Rules change, so open the linked source or send us the current checklist with your enquiry.</p>{other}</div></div><div class="local-grid">{''.join(cards)}</div>{state_level}</div></section>'''


def requirements_section(state, rec):
    article = 'an' if state[0] in 'AEIOU' else 'a'
    steps = []
    for raw in rec['seal_steps']:
        s = BeautifulSoup(raw, 'html.parser')
        num = s.b.get_text(strip=True) if s.b else ''
        text = s.span.get_text(' ', strip=True) if s.span else s.get_text(' ', strip=True)
        steps.append(f'<li><b aria-hidden="true">{clean(num)}</b><span>{clean(text)}</span></li>')
    paras = rec['seal_paras']
    intro = f'<p>{clean(paras[0])}</p>' if paras else ''
    seal = f'<p class="small">{clean(paras[-1])}</p>' if len(paras) > 1 else ''
    left = f'<div><span class="eyebrow">{state.upper()} REQUIREMENTS</span><h2 id="req-heading">What {article} {state} set has to satisfy.</h2>{intro}<ol class="req-list">{"".join(steps)}</ol>{seal}</div>'
    right = ''
    if rec['facts']:
        facts = ''.join(f'<dt>{clean(k)}</dt><dd>{clean(v)}</dd>' for k, v in rec['facts'])
        fi = clean(rec['facts_intro'][0]) if rec['facts_intro'] else 'The state-level rules your drawings are checked against. Cities and counties can add local amendments, so send the jurisdiction with your enquiry.'
        right = f'<div><h3 class="facts-title">{state} state-level rules</h3><p class="small">{fi}</p><dl class="state-facts">{facts}</dl></div>'
    cls = 'req-grid' if right else 'req-grid single'
    return f'<section class="section req-section" id="requirements" aria-labelledby="req-heading"><div class="wrap {cls}">{left}{right}</div></section>'


def faq_items(state, rec):
    items = [(q, a) for q, a in rec['faq']]
    items.append((f'How fast can you prepare {state} pool drawings?', 'Residential drawing preparation takes 2 business days after we receive all project inputs. PE review and sealing, and the permit office’s own review, have separate timelines.'))
    items.append((f'Do you work to my city or county’s checklist in {state}?', 'Yes. Send the submittal checklist or the review comments from your permit office. Your quote lists the drawings and calculations that respond to it.'))
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
    title = f'{state} Pool Plans & Permit Drawings'
    base = f'{state} pool engineering plans and permit drawings for homeowners, contractors and builders.'
    tail = ' Request a scope and quote.'
    description = base+tail
    for k in (3, 2, 1):
        if len(places) >= k:
            listed = places[0] if k == 1 else ', '.join(places[:k-1])+' and '+places[k-1]
            cand = f'{base} Local permit notes for {listed}.{tail}'
            if len(cand) <= 165:
                description = cand
                break
    if places:
        listed = places[0] if len(places) == 1 else (', '.join(places[:min(len(places), 3)-1])+' and '+places[min(len(places), 3)-1])
        lead = f'Pool engineering plans, permit drawings and construction details for {state} homeowners, pool contractors and builders. This page has local permit notes for {escape(listed)}. Get a scope and quote for your project.'
    else:
        lead = f'Pool engineering plans, permit drawings and construction details for {state} homeowners, pool contractors and builders. Get a scope and quote for your project.'
    pe = f'{state} PE review and sealing can be included in your agreed package. We confirm the responsible engineer and review requirements before work begins.'
    crumbs = f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">/</span> <a href="/states/">States</a> <span aria-hidden="true">/</span> <span aria-current="page">{state}</span></nav>'
    h1 = f'{state} pool plans.<br><span>Permit drawings for your project.</span>'
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#local">Local permit notes</a><a href="#requirements">State requirements</a><a href="#package">Drawing package</a><a href="#contact">Request a quote ↗</a></div></nav>'
    links = '<p class="package-links"><a href="/services/pool-engineering/">Pool engineering plans</a> · <a href="/services/pool-permit-drawings/">Permit drawings</a> · <a href="/pool/">Construction drawings</a></p>'
    faqs = faq_items(state, rec)
    nearby = ''
    if rec.get('nearby'):
        nearby = '<p class="nearby-line"><strong>Nearby states:</strong> '+' · '.join(f'<a href="{escape(h)}">{clean(t)}</a>' for h, t in rec['nearby'])+'</p>'
    body = (hero(f'{state.upper()} / RESIDENTIAL POOL ENGINEERING', h1, lead, form(title, state, CITY[slug]), crumbs) + nav
            + local_section(state, local)
            + requirements_section(state, rec)
            + package_section(pe, links=links)
            + inputs_section(f'Planning a pool in {state}?', 'Start with your project address and the city or county reviewing the permit. Send its submittal checklist or review comments if you have them, so we can identify the drawings and calculations needed.')
            + delivery_section(pe)
            + faq_section(state, faqs)
            + coverage_section(nearby))
    canonical = f'{SITE}/states/{slug}/'
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Service', '@id': canonical+'#service', 'name': title, 'serviceType': 'Swimming pool permit drawings and engineering plans', 'description': description, 'url': canonical, 'provider': organization(), 'areaServed': {'@type': 'State', 'name': state, 'containedInPlace': {'@type': 'Country', 'name': 'United States'}}},
        {'@type': 'FAQPage', '@id': canonical+'#faq', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'States', 'item': SITE+'/states/'},
            {'@type': 'ListItem', 'position': 3, 'name': state, 'item': canonical}]},
    ]}
    return shell(f'states/{slug}', title, description, body, schema)


def update_sitemap(urls):
    p = ROOT/'sitemap.xml'
    xml = p.read_text()
    for u in urls:
        block = f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{BUILD_DATE}</lastmod>\n  </url>\n'
        pat = re.compile(r'  <url>\s*<loc>'+re.escape(u)+r'</loc>.*?</url>\n', re.S)
        if pat.search(xml):
            xml = pat.sub(block, xml)
        else:
            xml = xml.replace('</urlset>', block+'</urlset>')
    p.write_text(xml)


if __name__ == '__main__':
    built = [build_national(p) for p in NATIONAL]
    built += [build_state(slug, rec) for slug, rec in sorted(STATES.items())]
    update_sitemap(built)
    print('Built', len(built), 'pages')

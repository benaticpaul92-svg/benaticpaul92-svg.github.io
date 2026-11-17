"""Site pages: home, eight service pages, the 50 state pages and the states index.

Shared header, consent panel and footer come from tools/site-chrome.html.
Data:
  tools/data/states.json        state-level content for each state page
  tools/data/local/<slug>.json  city and county permit notes with official sources
Run after build-assets.sh (that script's older generator overwrites the home page
and the Florida page; this one puts them back). Does not alter Ads settings or submit forms.
"""
from pathlib import Path
from html import escape
import hashlib, json, re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://www.jebnengineering.com'
BASE = BeautifulSoup((ROOT/'tools/site-chrome.html').read_text(), 'html.parser')
STATES = json.loads((ROOT/'tools/data/states.json').read_text())
BUILD_DATE = '2026-11-18'

# Every service page, in the order used for the home page cards and the footer links.
SERVICE_LINKS = [
    ('/services/pool-engineering/', 'Pool engineering plans', 'Structural plans, reinforcement details and hydraulic calculations for your permit.'),
    ('/services/pool-permit-drawings/', 'Pool permit drawings', 'Site layout, pool plans, sections and supporting calculations for the permit package.'),
    ('/pool/', 'Pool construction drawings', 'Coordinated plans, sections, construction details and equipment layouts.'),
    ('/services/pool-structural-engineering/', 'Pool structural engineering', 'Shell design, reinforcement schedules and details for raised walls and special edges.'),
    ('/services/pool-hydraulic-design/', 'Hydraulic design & TDH', 'Pipe sizing, total dynamic head calculations and equipment schematics.'),
    ('/services/pe-stamped-pool-plans/', 'PE-stamped pool plans', 'Plans sealed by a Professional Engineer licensed in the project state.'),
    ('/services/pool-shop-drawings/', 'Pool shop drawings', 'Tile, coping, gutter, steel and equipment details for fabrication and installation.'),
    ('/services/outsourced-pool-drafting/', 'Outsourced pool drafting', 'Overflow drafting for builders and designers, drawn on your standards.'),
]

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
      description='Site layouts, pool plans, sections and supporting calculations for your residential pool permit package. We confirm the project requirements and drawing scope before work begins.',
      meta='Site layouts, pool plans, sections and supporting calculations for your residential pool permit package. Send your sketch for a drawing scope and quote.'),
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


HERO_FACTS = [('Drawing preparation', '2 business days'), ('File delivery', 'DWG + PDF')]
HERO_SMALL = 'Two business days starts after we receive all project inputs for residential pool drawings. PE review, sealing and permit approval have separate timelines.'


def hero(kicker, h1, lead, form_html, crumbs='', facts=None, small=None):
    facts_html = ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in (facts or HERO_FACTS))
    return f'''<section class="search-hero blue" aria-labelledby="hero-heading"><div class="wrap search-grid"><div class="search-copy">{crumbs}<span class="eyebrow">{kicker}</span><h1 id="hero-heading">{h1}</h1><p class="lead">{lead}</p><div class="actions"><a class="button primary" href="#contact">Get a drawing quote <span aria-hidden="true">↗</span></a><a class="text-link" href="#package">See the drawing package ↓</a></div><dl class="delivery-facts">{facts_html}</dl><p class="small">{small or HERO_SMALL}</p><p class="search-contact">Your contact: <strong>Benatic Paul Martin</strong><br>JEBN Engineering · <a href="mailto:benatic@jebnengineering.com">benatic@jebnengineering.com</a></p></div>
<aside class="quote-panel" id="contact" aria-labelledby="contact-heading"><span class="eyebrow">PROJECT ENQUIRY · NO PAYMENT REQUIRED</span><h2 id="contact-heading" tabindex="-1">Get your drawing quote.</h2>{form_html}</aside></div></section>'''


def sheet_rows(rows):
    return ''.join(f'<li><span class="sheet-number" aria-hidden="true">{i:02d}</span><div><h3>{label}</h3><p>{text}</p></div></li>' for i, (label, text) in enumerate(rows, 1))


def package_section(pe, engineering=False, links='', rows=None, heading=None, lead=None, sid='services'):
    heading = heading or 'Know what you’re<br>asking us to deliver.'
    lead = lead or 'One project-specific scope, with the drawings, calculations and review responsibilities identified before you commit.'
    body = sheet_rows(rows) if rows else package_rows(pe, engineering)
    return f'''<section class="section" id="{sid}" aria-labelledby="package-heading"><div class="wrap package-editorial" id="package"><div><span class="eyebrow">YOUR DRAWING PACKAGE</span><h2 id="package-heading">{heading}</h2><p class="lead">{lead}</p><p class="package-note">Request a full package or help with existing plans. Your quote identifies the included sheets, PE review where applicable, revision scope and delivery date.</p><a class="text-link" href="#contact">Discuss your drawing set ↗</a>{links}</div><ol class="sheet-list">{body}</ol></div></section>'''


INPUT_ITEMS = [
    ('Project location', 'City, state and permitting authority, if known.'),
    ('Site information', 'Survey or site plan and known site constraints.'),
    ('Pool layout', 'Sketch, dimensions, depths and proposed features.'),
    ('Existing work', 'Plans, equipment preferences and permit review comments.'),
]


def inputs_section(heading, para, items=None):
    lis = ''.join(f'<li><strong>{k}</strong>{v}</li>' for k, v in (items or INPUT_ITEMS))
    return f'''<section class="section inputs-section" id="inputs" aria-labelledby="inputs-heading"><div class="wrap input-grid"><div><span class="eyebrow">WHAT TO SEND</span><h2 id="inputs-heading">{heading}</h2><p>{para}</p><p>You do not need every document to request a quote. After the first reply, you can share files by email.</p><a class="text-link" href="/resources/pool-project-checklist/">Open the project input checklist ↗</a></div><ul class="input-list">{lis}</ul></div></section>'''


def delivery_section(pe):
    return f'''<section class="section blue" id="delivery" aria-labelledby="delivery-heading"><div class="wrap"><span class="eyebrow">FROM ENQUIRY TO DELIVERY</span><h2 id="delivery-heading">A clear scope.<br>A clear next step.</h2><ol class="delivery-steps"><li><h3>1. Confirm the scope</h3><p>We review your enquiry and reply with questions or a scoped quote. We identify missing inputs and the project’s review requirements.</p></li><li><h3>2. Prepare the drawings</h3><p>Residential drawing preparation takes 2 business days after all project inputs are received. PE review and sealing have a separate timeline.</p></li><li><h3>3. Review & deliver</h3><p>Receive the agreed DWG and PDF package. We confirm revision support in your quote. The local authority decides permit approval and timing.</p></li></ol><div class="review-note"><h3>Engineering & PE review</h3><p>{pe} A quote request does not guarantee permit approval.</p></div><details class="optional-concept"><summary>Optional: 3D pool visualization</summary><p>A 3D view can help you explore the proposed layout and materials. Ask to include it as a separate item alongside the drawing package.</p></details><div class="actions"><a class="button primary" href="#contact">Request your drawing quote ↗</a></div></div></section>'''


def state_directory(summary='Choose your state for local permit notes'):
    links = ''.join(f'<a href="/states/{s}/">{name_of(s)}</a>' for s in sorted(STATES))
    return f'<details class="state-directory"><summary>{summary}</summary><nav class="state-grid" aria-label="State pages">{links}</nav></details>'


def coverage_section(extra=''):
    return f'''<section class="coverage-line" id="coverage" aria-label="USA coverage"><div class="wrap"><p><strong>JEBN Engineering · USA enquiries, all 50 states.</strong> Project-specific engineering and PE arrangements are confirmed before acceptance.</p><a href="/states/">View state coverage</a></div><div class="wrap coverage-more">{extra}{state_directory()}</div></section>'''


def service_links(current=''):
    """Text links to the other service pages, for the package column."""
    links = ' · '.join(f'<a href="{href}">{label}</a>' for href, label, _ in SERVICE_LINKS if href != current)
    return f'<p class="package-links"><strong>Related services:</strong> {links}</p>'


def faq_block(eyebrow, heading, items):
    body = ''.join(f'<details><summary>{clean(q)}</summary><p>{clean(a)}</p></details>' for q, a in items)
    return f'<section class="section faq-section" id="faq" aria-labelledby="faq-heading"><div class="wrap faq-layout"><div><span class="eyebrow">{eyebrow}</span><h2 id="faq-heading">{heading}</h2></div><div class="faq-list">{body}</div></div></section>'


def faq_schema(canonical, items):
    return {'@type': 'FAQPage', '@id': canonical+'#faq', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in items]}


def shell(path, title, description, body, schema, head_extra='', home=False):
    header = ''.join(str(BASE.select_one(s)) for s in ['.skip-link', '.utility-bar', '.site-header', '#privacy-choices'])
    if not home:
        header = header.replace('Engineering services', 'Drawing services')
    footer_links = ''.join(f'<a href="{href}">{label}</a>' for href, label, _ in SERVICE_LINKS)
    footer = str(BASE.select_one('.site-footer')).replace('<!--SERVICE_LINKS-->', footer_links)
    full_title = title+' | JEBN Engineering'
    canonical = f'{SITE}/{path}/' if path else f'{SITE}/'
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
            + package_section(pe, engineering, links=service_links('/'+p['path']+'/')) + extra
            + inputs_section('Start with the plans you have.', 'A sketch is enough to begin the conversation. If you already have a survey, drawings or permit comments, tell us what is ready. We identify the missing inputs before drawing work starts.')
            + delivery_section(pe) + coverage_section())
    canonical = f"{SITE}/{p['path']}/"
    meta = p.get('meta', p['description'])
    schema = {'@context': 'https://schema.org', '@type': 'Service', 'name': p['title'], 'description': meta, 'url': canonical, 'provider': organization(), 'areaServed': {'@type': 'Country', 'name': 'United States'}}
    # Routes a paid visit to the visitor's state page when the ad click carries a location id.
    head_extra = f'<script src="{asset("geo-route.min.js")}"></script>'
    return shell(p['path'], p['title'], meta, body, schema, head_extra)


# ---------------------------------------------------------------- service pages

PE_NATIONAL = 'Engineering and PE review arrangements are confirmed for your project state and scope before work is accepted. Ask which services are available for your location.'
TURNAROUND = 'Residential drawing preparation takes 2 business days after we receive all project inputs. PE review and sealing, and the permit office’s own review, have separate timelines.'

SERVICES = [
 dict(path='services/pool-structural-engineering', title='Pool Structural Engineering Plans & Details',
      h1='Pool structural engineering.<br><span>Shell, steel and details.</span>',
      kicker='USA / POOL STRUCTURAL ENGINEERING',
      meta='Pool structural plans for your permit: shell design, reinforcement schedules, raised walls, vanishing edges and soil basis. Send your layout for a scope and quote.',
      lead='Structural plans for residential pools: shell sections, reinforcement schedules and details for raised walls, special edges and attached spas. For homeowners, pool contractors and builders, with PE review and sealing where your permit office asks for it.',
      package_heading='What the structural<br>set covers.',
      package_lead='Structural drawings and calculations matched to your pool, your site and the checklist from your permit office.',
      rows=[
        ('Shell design & reinforcement', 'Gunite or shotcrete shell sections with wall and floor reinforcement schedules, steps, benches and sun shelves.'),
        ('Soil & groundwater basis', 'The design follows your geotechnical report where one exists. Where none exists, the assumed bearing capacity is stated on the drawings so the reviewer can see what the design relies on.'),
        ('Raised walls & special edges', 'Raised bond beams, retaining conditions, vanishing edges, perimeter overflow and attached spas.'),
        ('Code references & notes', 'Design loads, concrete and steel notes, and references to the code edition your jurisdiction enforces.'),
        ('PE review & permit coordination', PE_NATIONAL)],
      inputs=('Send the pool and the ground it sits in.', 'A dimensioned layout with depths is enough to start. A soils report, the survey and photos of nearby walls or slopes help us scope the structural work before drawing starts.', [
        ('Pool layout', 'Shape, dimensions, depths, steps, benches and raised features.'),
        ('Site conditions', 'Survey or site plan, slopes, retaining walls and nearby footings.'),
        ('Ground information', 'Geotechnical report, or the soil and groundwater conditions you know of.'),
        ('Permit requirements', 'The submittal checklist or review comments from your permit office.')]),
      faq_heading='Questions about pool structural plans.',
      faq=[
        ('Does my pool need structural engineering?', 'Your permit office decides. Many ask for engineered structural plans when the pool is close to a house footing, a retaining wall or a slope, when the ground is difficult, or when the shell has raised walls or a vanishing edge. Send the checklist and we identify what applies.'),
        ('Do you design for expansive or poor soils?', 'Where a geotechnical report is available, the design follows its recommendations. Where one is not, the drawings state the assumed bearing capacity so the reviewing engineer and the plan reviewer can see what the design relies on.'),
        ('Can you detail vanishing-edge and perimeter-overflow pools?', 'Yes. The structural scope covers the weir wall and catch basin, and the hydraulic design for the edge can be included in the same package.'),
        ('Who seals the structural plans?', 'Where sealing is part of your agreed package, a Professional Engineer licensed in the project state takes responsible charge and seals the plans. We confirm the responsible engineer before work begins.'),
        ('How fast can you prepare the structural drawings?', TURNAROUND)]),
 dict(path='services/pe-stamped-pool-plans', title='PE-Stamped Pool Plans for Your Permit',
      h1='PE-stamped pool plans.<br><span>Sealed for your project state.</span>',
      kicker='USA / PE-STAMPED POOL PLANS',
      meta='PE-stamped pool plans for your permit. Structural, hydraulic and site drawings in one package, sealed by a Professional Engineer licensed in your project state.',
      lead='Many permit offices ask for pool plans sealed by a Professional Engineer licensed in the project state. We prepare the drawing package, and the engineer licensed in your state takes responsible charge of the engineering and seals the plans as part of your agreed scope.',
      package_heading='What goes into<br>the sealed set.',
      package_lead='One coordinated package, so the engineer and the plan reviewer work from the same drawings and calculations.',
      rows=[
        ('Structural plans', 'Shell design, reinforcement schedules and details, with the soil basis stated.'),
        ('Hydraulics & equipment', 'Pipe sizing, TDH calculations, equipment schedules and the equipment layout.'),
        ('Site & layout', 'Pool position, setbacks, easements, elevations and drainage as your permit office requires.'),
        ('Barrier & electrical details', 'Barrier, bonding and clearance details drawn to the code edition your jurisdiction enforces.'),
        ('Seal & signature', 'Sealed and signed by the responsible Professional Engineer licensed in the project state. Digital seals are supplied where your permit office accepts them.')],
      extra=('HOW SEALING WORKS', 'How PE sealing works.', 'The seal is the engineer’s statement of responsibility for the engineering on the sheet. Each state sets its own rules for it, so we confirm the arrangement for your project state before work is accepted.', [
        ('Scope confirmed first', 'We confirm the project state, the permit office’s requirements and the responsible engineer before work begins.'),
        ('One coordinated package', 'Structural, hydraulic and site drawings are prepared as one set, so the engineer works from a complete package.'),
        ('Responsible charge', 'The Professional Engineer licensed in the project state takes responsible charge of the engineering and applies the seal and signature.'),
        ('Sealed set delivered', 'You receive the sealed PDF set for submission, plus DWG files of the drawings.')]),
      faq_heading='Questions about PE-stamped plans.',
      faq=[
        ('Do I need to find my own engineer?', 'No. Where sealing is part of your agreed package, the responsible Professional Engineer is confirmed with your quote. If you already work with an engineer, we can prepare the drawings for that engineer instead.'),
        ('Which states do you cover?', 'We take enquiries from all 50 states. The engineer must be licensed in the project state, and we confirm that arrangement for your project before work is accepted.'),
        ('Who is responsible for the sealed drawings?', 'The sealing engineer, who takes responsible charge of the engineering under their state licence. Your quote names the scope the seal covers.'),
        ('How long does sealing take?', 'Residential drawing preparation takes 2 business days after we receive all project inputs. The engineer’s review and sealing have a separate timeline, which we confirm in your quote.'),
        ('What if plan review comes back with comments?', 'Send us the comments. Your quote states the revision support included, and we identify the sheets and calculations each comment affects.'),
        ('Do you provide digital seals?', 'Digital seals are supplied where your permit office accepts them. Tell us if your office asks for wet-sealed prints so we can confirm that before work begins.')]),
 dict(path='services/pool-hydraulic-design', title='Pool Hydraulic Design & TDH Calculations',
      h1='Pool hydraulic design.<br><span>TDH calculations and pipe sizing.</span>',
      kicker='USA / POOL HYDRAULIC DESIGN',
      meta='Pool hydraulic design for your permit: TDH calculations, pipe sizing to velocity limits, pump and filter selection and equipment schematics. Request a quote.',
      lead='Hydraulic calculations and drawings for residential pools and spas: total dynamic head, pipe sizing, pump and filter selection and the equipment layout. Each number is shown, so the plan reviewer can follow the calculation.',
      package_heading='What the hydraulic<br>package covers.',
      package_lead='Calculations and drawings for the circulation system, prepared from your pool layout, pipe routes and equipment.',
      rows=[
        ('TDH calculation', 'Total dynamic head worked out from your pipe runs, fittings and equipment, with the friction losses shown.'),
        ('Pipe sizing', 'Suction and return pipe sizes checked against the velocity limits in the code your jurisdiction enforces.'),
        ('Pump & filter selection', 'Pump, filter and heater schedules matched to the calculated flow and head.'),
        ('Equipment layout & schematic', 'Equipment pad layout and a piping schematic with valves and unions.'),
        ('Suction outlets', 'Drain cover flow ratings and the suction outlet arrangement checked against the calculated flow.')],
      inputs=('Send the layout and the equipment.', 'Pool dimensions and the equipment location are enough to start. Pipe routes, equipment models and any worksheet from your permit office help us finish the calculation without follow-up questions.', [
        ('Pool & spa dimensions', 'Surface area, depths, volume if known, and any water features.'),
        ('Equipment location', 'Distance and height difference between the pool and the equipment pad.'),
        ('Equipment preferences', 'Pump, filter, heater and cleaner models you plan to use.'),
        ('Permit forms', 'Any hydraulic or TDH worksheet your permit office requires.')]),
      faq_heading='Questions about pool hydraulics.',
      faq=[
        ('Do you complete the TDH worksheet my permit office requires?', 'Yes. Some permit offices publish their own hydraulic or TDH worksheet. Send it with your enquiry and we complete it as part of the hydraulic package.'),
        ('What velocity limits do you design to?', 'A common basis is 6 feet per second on suction piping and 8 feet per second on return piping. We use the limits in the code your jurisdiction enforces and any tighter limit from the equipment maker.'),
        ('Can you size the pump for an existing pool?', 'Yes. Send the pipe sizes and runs, the equipment on the pad and what you want to change. We calculate the system head and identify a pump that suits it.'),
        ('Is the hydraulic design sealed by an engineer?', 'Where your permit office asks for sealed hydraulic calculations, PE review and sealing can be included in your agreed package. We confirm the responsible engineer before work begins.'),
        ('How fast can you prepare the hydraulic package?', TURNAROUND)]),
 dict(path='services/pool-shop-drawings', title='Pool Shop Drawings for Fabrication & Installation',
      h1='Pool shop drawings.<br><span>Details your crew can build from.</span>',
      kicker='USA / POOL SHOP DRAWINGS',
      meta='Pool shop drawings for builders and fabricators: tile and coping setting-out, gutter and overflow details, steel, embeds and equipment layouts. DWG and PDF files.',
      lead='Fabrication and installation drawings for pool builders: setting-out dimensions, edge and gutter details, steel and embeds, and equipment layouts, coordinated with your permit set.',
      facts=[('Sheet list', 'Agreed before work starts'), ('File delivery', 'DWG + PDF')],
      small='Residential pool drawing preparation takes 2 business days after we receive all project inputs. Larger shop drawing packages are scheduled in your quote.',
      package_heading='What the shop<br>drawings cover.',
      package_lead='The details your fabricators and installation crew need, drawn to an agreed sheet list and your drawing standards.',
      rows=[
        ('Tile, coping & waterline', 'Setting-out dimensions and details for tile, coping and the waterline.'),
        ('Gutters & overflow edges', 'Gutter, grating, vanishing-edge and perimeter-overflow details for fabrication.'),
        ('Steel, embeds & penetrations', 'Reinforcement placing details, embedded items and pipe penetrations through the shell.'),
        ('Equipment & plumbing', 'Equipment pad layout and plumbing schematics for the installation crew.'),
        ('Coordination with the permit set', 'Details checked against your approved plans to reduce conflicts on site.')],
      inputs=('Send the design and the details you need.', 'Send the design or permit drawings and tell us which details your installation team is missing. We agree the sheet list and your drawing standards before preparing the package.', [
        ('Design drawings', 'The permit or design set the shop drawings must follow.'),
        ('Details needed', 'The edges, finishes, steel or equipment your crew needs drawn.'),
        ('Products & finishes', 'Tile, coping, grating and equipment selections, with maker data if you have it.'),
        ('Your standards', 'Title block, sheet size and CAD standards to follow.')]),
      faq_heading='Questions about pool shop drawings.',
      faq=[
        ('Do you deliver DWG as well as PDF?', 'Yes. You receive DWG and PDF files for the agreed sheets, so fabricators and your crew can work from the native files.'),
        ('Do shop drawings need a PE seal?', 'Usually not. They are fabrication and installation documents, not permit documents. If your jurisdiction or client asks for a seal, tell us and we confirm the arrangement in your quote.'),
        ('Can you work from another designer’s plans?', 'Yes. Send the design or permit set and we draw the fabrication details that follow it. We tell you if something in the set conflicts with the detail being drawn.'),
        ('How is a shop drawing package priced?', 'By the agreed sheet list. Your quote names the sheets, file formats, revision allowance and delivery date before work starts.')]),
 dict(path='services/outsourced-pool-drafting', title='Outsourced Pool Drafting for Builders & Designers',
      h1='Outsourced pool drafting.<br><span>Drawn on your standards.</span>',
      kicker='USA / OUTSOURCED POOL DRAFTING',
      meta='Outsourced pool drafting for builders and designers whose drafting is backed up. Plans, sections and details drawn on your title block and CAD standards.',
      lead='Drafting capacity for pool builders and designers when the in-house team is full. Plans, sections and details are drawn on your title block and CAD standards and delivered to you as DWG and PDF files.',
      package_heading='What outsourced<br>drafting covers.',
      package_lead='Your projects, drawn the way your office draws them, with the sheets and revision allowance agreed in advance.',
      rows=[
        ('Your title block & standards', 'We adopt your title block, layer naming, sheet numbering and detail conventions from a sample set.'),
        ('Permit & construction sheets', 'Site layout, pool plans, sections, details and equipment layouts for each project you send.'),
        ('Revisions & review comments', 'Mark-ups and permit review comments drawn up within the revision allowance in your quote.'),
        ('PE-sealed sets when needed', 'PE review and sealing can be included for the projects whose permit office asks for it.'),
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
        ('How fast do you return a set?', 'Residential drawing preparation takes 2 business days after we receive all project inputs. For regular work we agree a delivery schedule with you.'),
        ('How is the work priced?', 'Per set or per sheet, agreed before work starts. Your quote lists the sheets, file formats and revision allowance.'),
        ('Can a set be sealed by an engineer?', 'Yes, where the project needs it. PE review and sealing can be added for that project, and we confirm the responsible engineer before work begins.')]),
]


def crumbs_html(trail):
    parts = []
    for href, label in trail:
        parts.append(f'<a href="{href}">{label}</a>' if href else f'<span aria-current="page">{label}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">'+' <span aria-hidden="true">/</span> '.join(parts)+'</nav>'


def build_service(p):
    path = '/'+p['path']+'/'
    canonical = SITE+path
    short = next(label for href, label, _ in SERVICE_LINKS if href == path)
    extra = ''
    if p.get('extra'):
        eyebrow, heading, para, items = p['extra']
        lis = ''.join(f'<li><strong>{k}</strong>{v}</li>' for k, v in items)
        extra = f'<section class="section inputs-section" id="how" aria-labelledby="how-heading"><div class="wrap input-grid"><div><span class="eyebrow">{eyebrow}</span><h2 id="how-heading">{heading}</h2><p>{para}</p><a class="text-link" href="#contact">Ask about your project ↗</a></div><ul class="input-list">{lis}</ul></div></section>'
    heading, para, items = p.get('inputs') or ('Start with the plans you have.', 'A sketch is enough to begin the conversation. If you already have a survey, drawings or permit comments, tell us what is ready. We identify the missing inputs before drawing work starts.', None)
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#package">What it covers</a><a href="#inputs">What to send</a><a href="#faq">Questions</a><a href="#contact">Request a quote ↗</a></div></nav>'
    crumbs = crumbs_html([('/', 'Home'), ('/#services', 'Services'), ('', short)])
    body = (hero(p['kicker'], p['h1'], p['lead'], form(p['title']), crumbs, p.get('facts'), p.get('small')) + nav
            + package_section(PE_NATIONAL, rows=p['rows'], heading=p['package_heading'], lead=p['package_lead'], links=service_links(path)) + extra
            + inputs_section(heading, para, items)
            + delivery_section(PE_NATIONAL)
            + faq_block('BEFORE YOU ASK', p['faq_heading'], p['faq'])
            + coverage_section())
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Service', '@id': canonical+'#service', 'name': p['title'], 'description': p['meta'], 'url': canonical, 'provider': organization(), 'areaServed': {'@type': 'Country', 'name': 'United States'}},
        faq_schema(canonical, p['faq']),
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE+'/'},
            {'@type': 'ListItem', 'position': 2, 'name': short, 'item': canonical}]},
    ]}
    return shell(p['path'], p['title'], p['meta'], body, schema)


# ---------------------------------------------------------------- home page

HOME_FAQ = [
    ('When does the two-business-day turnaround start?', 'Once we have received all project inputs. It covers preparation of residential pool drawings. PE review and sealing, where required, and the permit office’s review have separate timelines.'),
    ('What should I send to get started?', 'Your project city and state, a site plan or sketch, pool dimensions if known, and the services you need. Include existing plans and any permit review comments if you have them.'),
    ('Will I receive editable files?', 'Yes. You receive both DWG and PDF files for the agreed drawing package.'),
    ('Do you work with pool contractors and builders?', 'Yes. We work with homeowners, pool contractors and builders on engineering plans, permit drawings, calculations and drawing updates within an agreed scope.'),
    ('How are PE review and permit approval handled?', 'PE review and sealing can be included in your agreed package, by a Professional Engineer licensed in the project state. We confirm the responsible engineer before work begins. The permit office decides approval.'),
    ('Do you know my city or county’s permit rules?', 'Each state page lists permit notes for named cities and counties, with links to the official sources. Send your permit office’s checklist with your enquiry and we draw to it.'),
]


def build_home():
    title = 'USA Pool Engineering Plans & PE-Sealed Drawings'
    description = 'Residential pool engineering plans, permit drawings, structural details, hydraulics, TDH calculations and PE review. USA project enquiries from all 50 states.'
    lead = 'Engineering plans, permit drawings and calculations for homeowners, pool contractors and builders. Send what you have and get a scope and quote for your project.'
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#services">Services</a><a href="#coverage">Find your state</a><a href="#package">Drawing package</a><a href="#contact">Request a quote ↗</a></div></nav>'
    cards = ''.join(f'<a class="state-card" href="{href}"><strong>{label}</strong><span>{text}</span></a>' for href, label, text in SERVICE_LINKS)
    cards += '<a class="state-card" href="/resources/pool-project-checklist/"><strong>Project input checklist</strong><span>What to send before drawing work starts. No signup needed.</span></a>'
    services = f'''<section class="section local-section" id="services" aria-labelledby="services-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">RESIDENTIAL POOL ENGINEERING SERVICES</span><h2 id="services-heading">One coordinated scope.<br>Every technical detail.</h2></div><div><p>Engineering plans, calculations and permit drawings for homeowners, pool contractors and builders. Choose a complete package or the technical support your team needs.</p><a class="text-link" href="#contact">Request an engineering quote ↗</a></div></div><nav class="state-cards" aria-label="Services">{cards}</nav></div></section>'''
    state_links = ''.join(f'<a href="/states/{s}/">{name_of(s)}</a>' for s in sorted(STATES))
    states = f'''<section class="section local-section" id="coverage" aria-labelledby="coverage-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">USA · ALL 50 STATES</span><h2 id="coverage-heading">Find your state.</h2></div><div><p>Every state page has the state-level pool rules, permit notes for named cities and counties with links to the official sources, and the quote form.</p><p>Your city or county is not listed? Name the permit office in your enquiry. We draw to the checklist it publishes.</p><a class="text-link" href="/states/">Browse all state pages ↗</a></div></div><nav class="state-grid wide" aria-label="State pages">{state_links}</nav></div></section>'''
    line = '''<section class="coverage-line" aria-label="USA coverage"><div class="wrap"><p><strong>JEBN Engineering · USA enquiries, all 50 states.</strong> Project-specific engineering and PE arrangements are confirmed before acceptance.</p><a href="/states/">View state coverage</a></div></section>'''
    body = (hero('USA / ALL 50 STATES / RESIDENTIAL POOLS', 'Residential pool engineering.<br><span>For your next build.</span>', lead, form('Residential Pool Engineering')) + nav
            + services + states
            + package_section(PE_NATIONAL, engineering=True, sid='package-section')
            + inputs_section('Start with the plans you have.', 'A sketch is enough to begin the conversation. If you already have a survey, drawings or permit comments, tell us what is ready. We identify the missing inputs before drawing work starts.')
            + delivery_section(PE_NATIONAL)
            + faq_block('BEFORE WE BEGIN', 'Clear scope.<br>Clear expectations.', HOME_FAQ)
            + line)
    canonical = SITE+'/'
    org = dict(organization(), **{'@id': canonical+'#organization', 'description': 'Residential pool engineering plans, permit drawings, hydraulics, TDH calculations and PE review coordination for US projects.'})
    schema = {'@context': 'https://schema.org', '@graph': [
        org,
        {'@type': 'WebSite', '@id': canonical+'#website', 'name': 'JEBN Engineering', 'url': canonical, 'publisher': {'@id': canonical+'#organization'}},
        faq_schema(canonical, HOME_FAQ),
        {'@type': 'ItemList', 'name': 'Pool engineering and drawing services', 'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': label, 'url': SITE+href} for i, (href, label, _) in enumerate(SERVICE_LINKS, 1)]},
    ]}
    # Routes a paid visit to the visitor's state page when the ad click carries a location id.
    head_extra = f'<script src="{asset("geo-route.min.js")}"></script>'
    return shell('', title, description, body, schema, head_extra, home=True)


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
        notes = ''.join(f'<li>{clean(n)}</li>' for n in j['notes'])
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
        cards.append(f'<article class="local-card" id="{jid}"><h3>{clean(j["name"])}</h3><p class="local-office">{office}{portal}</p><ul>{notes}</ul>{src}</article>')
    state_level = ''
    if local.get('state_level'):
        items = ''.join(f'<li>{clean(s.get("note"))} <span class="local-src">Source: {ext_link((s.get("source") or {}).get("url"), (s.get("source") or {}).get("title") or "Official page")}</span></li>' for s in local['state_level'] if s.get('note'))
        if items:
            state_level = f'<div class="state-level"><h3>Statewide</h3><ul>{items}</ul></div>'
    checked = date_words(state_date)
    copy_note = ' Where a source says “copy saved”, the note was read from a dated copy of that official page.' if saved_copy else ''
    later = ' unless a card gives a later date' if any(j.get('checked') and j['checked'] != state_date for j in local['jurisdictions']) else ''
    return f'''<section class="section local-section" id="local" aria-labelledby="local-heading"><div class="wrap"><div class="local-head"><div>{head}</div><div><p>Each city and county runs its own pool permit review. These notes come from the pages each office publishes, checked on {checked}{later}. Rules change, so open the linked source or send us the current checklist with your enquiry.{copy_note}</p>{other}</div></div><div class="local-grid">{''.join(cards)}</div>{state_level}</div></section>'''


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


def build_states_index():
    title = 'Pool Permit Drawings by State | All 50 States'
    description = 'Pool engineering plans and permit drawings in all 50 states. Choose your state for city and county permit notes, state pool rules and a drawing quote.'
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
    lead = 'Pool engineering plans, permit drawings and construction details for homeowners, pool contractors and builders in all 50 states. Each state page lists city and county permit notes with links to the official sources.'
    pe = 'Engineering and PE review arrangements are confirmed for your project state and scope before work is accepted. Ask which services are available for your location.'
    nav = '<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#all-states">All 50 states</a><a href="#package">Drawing package</a><a href="#delivery">Delivery & PE review</a><a href="#contact">Request a quote ↗</a></div></nav>'
    grid = f'''<section class="section local-section" id="all-states" aria-labelledby="states-heading"><div class="wrap"><div class="local-head"><div><span class="eyebrow">USA · ALL 50 STATES</span><h2 id="states-heading">Choose your state.</h2></div><div><p>Every state page has the state-level pool rules, permit notes for named cities and counties, and the quote form. Your city or county is not listed? Name the permit office in your enquiry.</p></div></div><nav class="state-cards" aria-label="State pages">{"".join(cards)}</nav></div></section>'''
    body = (hero('USA / POOL PERMIT DRAWINGS BY STATE', 'Pool permit drawings.<br><span>State by state.</span>', lead, form('Pool Permit Drawings by State'), crumbs) + nav
            + grid + package_section(pe) + delivery_section(pe)
            + '''<section class="coverage-line" id="coverage" aria-label="USA coverage"><div class="wrap"><p><strong>JEBN Engineering · USA enquiries, all 50 states.</strong> Project-specific engineering and PE arrangements are confirmed before acceptance.</p><a href="/services/pool-engineering/">Pool engineering plans</a></div></section>''')
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
    built = [build_home()]
    built += [build_national(p) for p in NATIONAL]
    built += [build_service(p) for p in SERVICES]
    built += [build_state(slug, rec) for slug, rec in sorted(STATES.items())]
    built.append(build_states_index())
    update_sitemap(built)
    print('Built', len(built), 'pages')

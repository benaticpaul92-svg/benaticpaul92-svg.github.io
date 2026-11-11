"""Focused Search destinations. Reuses the deployed identity and enquiry contract.
Run after build-assets.sh; does not alter Ads settings or submit forms.
"""
from pathlib import Path
from html import escape
import hashlib, json
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[1]
BASE = BeautifulSoup((ROOT/'index.html').read_text(), 'html.parser')
PAGES = [
 ('states/florida', 'Florida Pool Plans & Permit Drawings', 'Florida pool plans.<br><span>Drawn for your project.</span>', 'FLORIDA / RESIDENTIAL POOL ENGINEERING', 'Pool engineering plans, permit drawings and construction details for Florida homeowners, pool contractors and builders. Get a scope and quote for your project.', True),
 ('pool', 'Pool Construction Drawings & Engineering Plans', 'Pool construction drawings.<br><span>From layout to detail.</span>', 'USA / RESIDENTIAL POOL DRAWING PACKAGES', 'Coordinated pool plans, sections, construction details and equipment layouts for residential projects. Send your sketch or existing plans for a drawing-package quote.', False),
 ('services/pool-permit-drawings', 'Swimming Pool Plans & Permit Drawings', 'Swimming pool plans.<br><span>Built around your permit scope.</span>', 'USA / RESIDENTIAL POOL PERMIT DRAWINGS', 'Site layouts, pool plans, sections and supporting calculations for your residential pool permit package. We confirm the project requirements and drawing scope before work begins.', False),
]

def asset(name):
 p=ROOT/'assets'/name
 return '/assets/'+name+'?v='+hashlib.sha256(p.read_bytes()).hexdigest()[:12]

def form(title,fl):
 doc=BeautifulSoup((ROOT/'tools/enquiry-form.html').read_text(),'html.parser')
 form=doc.form
 form['data-search-enquiry']=title
 doc.select_one('.form-intro').string='Name and email are enough to start. Add project details if you have them.'
 notes=doc.select_one('[name="message"]')
 notes['name']='project_notes'; notes['id']='enquiry-notes'; notes['rows']='2'; notes.attrs.pop('required',None)
 notes['placeholder']='Pool dimensions, existing plans or permit comments…'
 label=doc.select_one('label[for="enquiry-message"]'); label['for']='enquiry-notes'; label.string='Project details (optional)'
 hidden=doc.new_tag('input',attrs={'type':'hidden','name':'message','value':title+' quote request.'})
 doc.fieldset.append(hidden)
 loc=doc.select_one('[name="location"]')
 loc['placeholder']='For example: Tampa, Florida' if fl else 'Project city and state'
 if fl: loc['value']='Florida'
 privacy=doc.select_one('.form-privacy')
 privacy.clear(); privacy.append('We use your details to reply to this enquiry. ')
 a=doc.new_tag('a',href='/privacy/'); a.string='Privacy policy'; privacy.append(a)
 return str(doc)

for path,title,h1,kicker,description,fl in PAGES:
 pe='Florida PE review and sealing can be included in your agreed package. We confirm the responsible engineer and review requirements before work begins.' if fl else 'Engineering and PE review arrangements are confirmed for your project state and scope before work is accepted. Ask which services are available for your location.'
 local='''<h2 id="inputs-heading">Planning a pool in Florida?</h2><p>Start with your project address and the city or county reviewing the permit. Send its submittal checklist or review comments if you have them, so we can identify the drawings and calculations needed.</p>''' if fl else '''<h2 id="inputs-heading">Start with the plans you have.</h2><p>A sketch is enough to begin the conversation. If you already have a survey, drawings or permit comments, tell us what is ready. We identify the missing inputs before drawing work starts.</p>'''
 rows=[('01','Site & pool layout','Pool position, dimensions, depths and sections, coordinated with the site information you supply.'),('02','Construction details','Pool shell and reinforcement details within the agreed engineering scope; drawing references for your contractor.'),('03','Hydraulics & equipment','Circulation layout, pipe sizing, TDH calculations and equipment schedules where included in your quote.'),('04','Permit & PE coordination',pe)]
 package=''.join(f'<li><span class="sheet-number" aria-hidden="true">{n}</span><div><h3>{label}</h3><p>{text}</p></div></li>' for n,label,text in rows)
 body=f'''<main id="main-content" tabindex="-1">
<section class="search-hero blue" aria-labelledby="hero-heading"><div class="wrap search-grid"><div class="search-copy"><span class="eyebrow">{kicker}</span><h1 id="hero-heading">{h1}</h1><p class="lead">{description}</p><div class="actions"><a class="button primary" href="#contact">Get a drawing quote <span aria-hidden="true">↗</span></a><a class="text-link" href="#package">See the drawing package ↓</a></div><dl class="delivery-facts"><div><dt>Drawing preparation</dt><dd>2 business days</dd></div><div><dt>File delivery</dt><dd>DWG + PDF</dd></div></dl><p class="small">Two business days starts after we receive all project inputs for residential pool drawings. PE review, sealing and permit approval have separate timelines.</p><p class="search-contact">Your contact: <strong>Benatic Paul Martin</strong><br>JEBN Engineering · <a href="mailto:benatic@jebnengineering.com">benatic@jebnengineering.com</a></p></div>
<aside class="quote-panel" id="contact" aria-labelledby="contact-heading"><span class="eyebrow">PROJECT ENQUIRY · NO PAYMENT REQUIRED</span><h2 id="contact-heading" tabindex="-1">Get your drawing quote.</h2>{form(title,fl)}</aside></div></section>
<nav class="landing-nav" aria-label="Page sections"><div class="wrap"><a href="#package">Drawing package</a><a href="#inputs">What to send</a><a href="#delivery">Delivery & PE review</a><a href="#contact">Request a quote ↗</a></div></nav>
<section class="section" id="services" aria-labelledby="package-heading"><div class="wrap package-editorial" id="package"><div><span class="eyebrow">YOUR DRAWING PACKAGE</span><h2 id="package-heading">Know what you’re<br>asking us to deliver.</h2><p class="lead">One project-specific scope, with the drawings, calculations and review responsibilities identified before you commit.</p><p class="package-note">Request a full package or help with existing plans. Your quote identifies the included sheets, PE review where applicable, revision scope and delivery date.</p><a class="text-link" href="#contact">Discuss your drawing set ↗</a></div><ol class="sheet-list">{package}</ol></div></section>
<section class="section inputs-section" id="inputs" aria-labelledby="inputs-heading"><div class="wrap input-grid"><div><span class="eyebrow">WHAT TO SEND</span>{local}<p>You do not need every document to request a quote. After the first reply, you can share files by email.</p><a class="text-link" href="/resources/pool-project-checklist/">Open the project input checklist ↗</a></div><ul class="input-list"><li><strong>Project location</strong>City, state and permitting authority, if known.</li><li><strong>Site information</strong>Survey or site plan and known site constraints.</li><li><strong>Pool layout</strong>Sketch, dimensions, depths and proposed features.</li><li><strong>Existing work</strong>Plans, equipment preferences and permit review comments.</li></ul></div></section>
<section class="section blue" id="delivery" aria-labelledby="delivery-heading"><div class="wrap"><span class="eyebrow">FROM ENQUIRY TO DELIVERY</span><h2 id="delivery-heading">A clear scope.<br>A clear next step.</h2><ol class="delivery-steps"><li><h3>1. Confirm the scope</h3><p>We review your enquiry and reply with questions or a scoped quote. We identify missing inputs and the project’s review requirements.</p></li><li><h3>2. Prepare the drawings</h3><p>Residential drawing preparation takes 2 business days after all project inputs are received. PE review and sealing have a separate timeline.</p></li><li><h3>3. Review & deliver</h3><p>Receive the agreed DWG and PDF package. We confirm revision support in your quote. The local authority decides permit approval and timing.</p></li></ol><div class="review-note"><h3>Engineering & PE review</h3><p>{pe} A quote request does not guarantee permit approval.</p></div><details class="optional-concept"><summary>Optional: 3D pool visualization</summary><p>A 3D view can help you explore the proposed layout and materials. Ask to include it as a separate item alongside the drawing package.</p></details><div class="actions"><a class="button primary" href="#contact">Request your drawing quote ↗</a></div></div></section>
<section class="coverage-line" id="coverage" aria-label="USA coverage"><div class="wrap"><p><strong>JEBN Engineering · USA enquiries, all 50 states.</strong> Project-specific engineering and PE arrangements are confirmed before acceptance.</p><a href="/states/">View state coverage</a></div></section></main>'''
 # Reuse the deployed header/consent/footer; keep form IDs and receipt tracking contract intact.
 header=''.join(str(BASE.select_one(s)) for s in ['.skip-link','.utility-bar','.site-header','#privacy-choices'])
 header=header.replace('Engineering services','Drawing services').replace('USA coverage','USA coverage')
 footer=str(BASE.select_one('.site-footer'))
 full_title=title+' | JEBN Engineering'
 canonical='https://www.jebnengineering.com/'+path+'/'
 schema={'@context':'https://schema.org','@type':'Service','name':title,'description':description,'url':canonical,'provider':{'@type':'Organization','name':'JEBN Engineering','url':'https://www.jebnengineering.com/'},'areaServed':{'@type':'AdministrativeArea' if fl else 'Country','name':'Florida' if fl else 'United States'}}
 html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(full_title)}</title><meta name="description" content="{escape(description)}"><link rel="canonical" href="{canonical}"><meta name="theme-color" content="#0c5488"><meta name="referrer" content="strict-origin-when-cross-origin"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><meta property="og:title" content="{escape(full_title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta property="og:image" content="https://www.jebnengineering.com/images/pool-beachfront-villa.jpg"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="{asset('studio.min.css')}"><link rel="stylesheet" href="{asset('search-landings.min.css')}"><script src="{asset('search-landings.min.js')}" defer></script><script src="{asset('studio.min.js')}" defer></script><script type="application/ld+json">{json.dumps(schema)}</script></head><body class="search-landing">{header}{body}{footer}</body></html>'''
 (ROOT/path/'index.html').write_text(BeautifulSoup(html,'html.parser').prettify())
 print('Built',path)

"""Browser checks against a running local site. No contact is sent externally."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

BASE=os.environ.get('TEST_BASE_URL','http://127.0.0.1:3000')
OUT=Path(os.environ.get('TEST_ARTIFACTS','/tmp/amh-browser'));OUT.mkdir(parents=True,exist_ok=True)
report={'viewports':[],'checks':[],'errors':[]}
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page()
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    page.add_init_script("""window.__metrics={lcp:0,cls:0};new PerformanceObserver(l=>{for(const e of l.getEntries())window.__metrics.lcp=e.startTime}).observe({type:'largest-contentful-paint',buffered:true});new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__metrics.cls+=e.value}).observe({type:'layout-shift',buffered:true});""")
    for width,height in [(1440,1000),(768,1024),(390,844),(360,800)]:
        page.set_viewport_size({'width':width,'height':height})
        response=page.goto(BASE,wait_until='networkidle');assert response.status==200
        assert page.locator('h1').count()==1
        dimensions=page.evaluate('({viewport:innerWidth,content:document.documentElement.scrollWidth})')
        assert dimensions['content']<=width,dimensions
        hero=page.locator('.premium-hero').bounding_box()
        image=page.locator('.hero-photo').bounding_box()
        copy=page.locator('.hero-copy').bounding_box()
        assert round(hero['width'])==width
        if width>700:
            assert image['width']>=width*.65
        else:
            assert image['y']<copy['y']
        assert page.locator('.header').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(6, 29, 50)'
        assert page.locator('.hero-actions .button').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(249, 246, 241)'
        if width>950:
            logo=page.locator('.header-brand').bounding_box()
            assert abs(logo['x']+logo['width']/2-width/2)<2
        assert page.evaluate("(font) => document.fonts.check(font)", '400 16px "Cormorant Garamond"')
        for y in range(0,page.evaluate('document.documentElement.scrollHeight'),650):
            page.evaluate('(y)=>scrollTo(0,y)',y);page.wait_for_timeout(80)
        page.wait_for_timeout(250)
        assert page.locator('img').evaluate_all('(es)=>es.filter(e=>e.getAttribute("src")).every(e=>e.complete&&e.naturalWidth>0)')
        page.evaluate('scrollTo(0,0)')
        report['viewports'].append({'width':width,'height':height,'overflow':False})
        if width in [1440,390]:
            page.screenshot(path=str(OUT/f'home-{width}.png'),full_page=True)
            page.screenshot(path=str(OUT/f'first-screen-{width}.png'))
    report['checks'].append('V6 art direction: centered logo on desktop, marine header, photographic hero, local fonts and brand colors; all images loaded; no overflow at 360, 390, 768, 1440px')
    page.goto(BASE,wait_until='networkidle')
    button=page.get_by_role('button',name='Menu',exact=False)
    button.click();assert button.get_attribute('aria-expanded')=='true'
    assert page.locator('body').evaluate('(e)=>getComputedStyle(e).overflow')=='hidden'
    page.locator('.nav-mobile-contact a').last.focus();page.keyboard.press('Tab')
    assert page.locator(':focus').get_attribute('class')=='brand header-brand'
    page.screenshot(path=str(OUT/'navigation-mobile.png'))
    page.keyboard.press('Escape');assert button.get_attribute('aria-expanded')=='false'
    assert page.locator(':focus').get_attribute('class')=='menu-toggle'
    page.locator('.faq-list summary').first.click()
    assert page.locator('.faq-list details').first.get_attribute('open') is not None
    report['checks'].append('Mobile menu, Escape/focus restoration, FAQ')
    page.goto(BASE+'/realisations/',wait_until='networkidle')
    page.get_by_role('navigation',name='Filtrer les réalisations').get_by_role('link',name='Menuiserie',exact=True).click()
    assert page.locator('.project-card').count()==3
    page.locator('.project-card h3 a').first.click()
    page.locator('[data-lightbox]').first.click()
    assert page.locator('#lightbox').evaluate('(e)=>e.open')
    page.keyboard.press('Escape');assert not page.locator('#lightbox').evaluate('(e)=>e.open')
    report['checks'].append('Server filters, project details, lightbox and Escape')
    for path in ['/contact/','/menuiserie-sur-mesure-paris/','/renovation-appartement-paris/','/renovation-bureaux-commerces-paris/','/syndic-et-copropriete/','/la-societe/','/deroulement-projet/','/blog/','/blog/preparer-projet-sur-mesure/','/mentions-legales/','/confidentialite/']:
        response=page.goto(BASE+path,wait_until='networkidle');assert response.status==200,path
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),path
        assert page.locator('h1').count()==1,path
        for a in page.locator('a[href^="/"]').evaluate_all('(es)=>es.map(e=>e.getAttribute("href"))'):
            r=page.request.get(BASE+a);assert r.status<400,(path,a,r.status)
    report['checks'].append('Internal links, page headings and mobile layout on all principal pages')
    page.goto(BASE+'/contact/',wait_until='networkidle')
    page.screenshot(path=str(OUT/'contact-mobile.png'),full_page=True)
    page.get_by_label('Votre nom',exact=False).fill('Test local')
    page.get_by_label('Votre email',exact=False).fill('test@example.com')
    page.get_by_label('Type de projet',exact=False).select_option('menuiserie')
    page.get_by_label('Votre projet en quelques mots',exact=False).fill('Test local du comportement sans configuration SMTP.')
    page.wait_for_timeout(2200)
    with page.expect_response(lambda r:r.url.endswith('/contact/') and r.request.method=='POST') as pending:
        page.get_by_role('button',name='Envoyer mon projet').click()
    assert pending.value.status==503
    assert page.get_by_label('Votre nom',exact=False).input_value()=='Test local'
    assert page.get_by_role('alert').is_visible()
    assert 'n’a pas été envoyée' in page.get_by_role('alert').inner_text()
    report['checks'].append('Unconfigured SMTP returns 503, honest error, entered content retained')
    page.emulate_media(reduced_motion='reduce')
    page.goto(BASE,wait_until='networkidle')
    assert page.evaluate('document.getAnimations().length')==0
    page.locator('.hero-actions .button').hover()
    assert page.locator('.hero-actions .button').evaluate('(e)=>getComputedStyle(e).transform')=='none'
    report['checks'].append('Reduced motion: no entrance/reveal animations and no hover translation')
    page.emulate_media(reduced_motion='no-preference')
    assert not report['errors'],report['errors']
    page.set_viewport_size({'width':1440,'height':1000})
    page.goto(BASE,wait_until='networkidle')
    page.locator('.nav-expertises summary').click()
    assert page.locator('.nav-dropdown a').count()==4
    assert page.locator('.nav-dropdown').is_visible()
    page.screenshot(path=str(OUT/'navigation-desktop.png'))
    page.keyboard.press('Escape')
    assert page.locator('.nav-expertises').get_attribute('open') is None
    assert page.locator(':focus').evaluate('(e)=>e.tagName')=='SUMMARY'
    report['checks'].append('V6 navigation: mobile focus trap and scroll lock; desktop expertise menu, Escape and focus restoration')
    page.locator('[data-craft-index="2"]').hover()
    assert page.locator('[data-craft-scene="2"]').get_attribute('aria-hidden')=='false'
    page.locator('[data-craft-index="1"]').focus()
    assert page.locator('[data-craft-scene="1"]').get_attribute('aria-hidden')=='false'
    assert page.locator('[data-craft-scene="2"]').get_attribute('aria-hidden')=='true'
    report['checks'].append('Expertise image preview follows pointer and keyboard focus; inactive scenes are hidden from assistive technology')
    page.goto(BASE,wait_until='networkidle');page.wait_for_timeout(500)
    report['local_lab_metrics']=page.evaluate('window.__metrics')
    report['local_lab_metrics']['conditions']='Local Chromium, desktop 1440x1000, no network/CPU throttling; not field Core Web Vitals. INP unmeasured. Browser cache already populated by preceding checks.'
    browser.close()
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))

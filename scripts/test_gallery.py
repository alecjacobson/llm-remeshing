from playwright.sync_api import sync_playwright
from pathlib import Path
R=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((R/'gallery/index.html').as_uri());page.wait_for_timeout(1200)
 assert page.locator('.card').count()>0
 page.screenshot(path=str(R/'gallery/preview.png'))
 page.locator('.picture').first.click();assert page.locator('#modal').evaluate('(d)=>d.open')
 page.locator('#sourceView').click();assert '_source.png' in page.locator('#detailImage').get_attribute('src')
 page.locator('#finalView').click();assert '_source.png' not in page.locator('#detailImage').get_attribute('src')
 page.locator('#next').click();page.keyboard.press('Escape')
 page.locator('#search').fill('428607');assert page.locator('.card').count()==1
 page.locator('#search').fill('no-match-xyz');assert page.locator('.card').count()==0
 page.locator('#search').fill('');page.locator('#filter').select_option('exact');assert page.locator('.card').count()>0
 page.locator('#filter').select_option('all');page.locator('#sort').select_option('faces')
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(R/'gallery/preview-mobile.png'))
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 assert not errors,errors
 print('GALLERY_TESTS_PASSED');browser.close()

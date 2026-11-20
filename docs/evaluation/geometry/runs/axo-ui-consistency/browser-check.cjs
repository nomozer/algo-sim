const { chromium } = require(process.cwd() + '/node_modules/playwright');
(async () => {
 const browser = await chromium.launch({headless:true});
 const sizes = [[1920,1080],[1440,900],[1366,768],[1280,800],[1024,768],[768,1024],[390,844],[360,800]];
 const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/aN8AAAAASUVORK5CYII=', 'base64');
 for (const [width,height] of sizes) {
  const p = await browser.newPage({viewport:{width,height}}); const errors=[]; p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://127.0.0.1:4317/app',{waitUntil:'domcontentloaded'}); await p.locator('#home-problem-input').waitFor();
  await p.locator('#home-problem-input').fill('Bản nháp kiểm thử');
  await p.locator('#home-file-input').setInputFiles([{name:'de-anh.png',mimeType:'image/png',buffer:png},{name:'de-bai.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4\n%%EOF')}]);
  await p.locator('.file-preview-card').first().waitFor();
  const data = await p.evaluate(()=>({cards:document.querySelectorAll('.file-preview-card').length, overflow:document.documentElement.scrollWidth>window.innerWidth, composer:document.querySelector('.composer-card').getBoundingClientRect().width, heading:getComputedStyle(document.querySelector('.home-hero-title')).fontSize}));
  await p.screenshot({path:`../docs/evaluation/geometry/runs/axo-ui-consistency/images/after-${width}.png`});
  await p.locator('.file-preview-card').first().click(); const preview = await p.locator('#composer-single-file-modal').count();
  await p.locator('#btn-close-file-modal').click(); await p.locator('.file-card-remove').first().click({force:true});
  const remaining=await p.locator('.file-preview-card').count(); const text=await p.locator('#home-problem-input').inputValue();
  console.log(JSON.stringify({width,height,...data,preview,remaining,text,errors})); await p.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

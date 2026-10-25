// Transport adapter for the UNCHANGED official product-build suite/orbit assertions.
// No oracle, fixture expectation, geometry, threshold or evidence classification is modified.
import {dirname,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {existsSync} from 'node:fs';
let root=dirname(fileURLToPath(import.meta.url));
while(!existsSync(join(root,'frontend/package.json'))){const parent=dirname(root);if(parent===root)throw Error('Repository root missing');root=parent;}
const {chromium}=await import(pathToFileURL(join(root,'frontend/node_modules/playwright/index.mjs')).href);
const {BrowserSession}=await import(pathToFileURL(join(root,'frontend/scripts/browser-runner.mjs')).href);
BrowserSession.prototype.open=async function(){
  if(this.napModuleDev)throw Error('This adapter is limited to product-build checks');
  const start=Date.now();
  const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--hide-scrollbars']});
  this._pwBrowser=browser;
  const context=await browser.newContext({viewport:{width:this.viewport,height:this.height},deviceScaleFactor:1});
  await context.route('**/*',route=>{const host=new URL(route.request().url()).hostname;return host==='127.0.0.1'||host==='localhost'?route.continue():route.abort();});
  const page=await context.newPage();
  const cdp=await context.newCDPSession(page);
  this._send=async(method,params={})=>({result:await cdp.send(method,params)});
  cdp.on('Fetch.requestPaused',p=>{for(const fn of this._subs.get('Fetch.requestPaused')??[])fn(p);});
  cdp.on('Runtime.exceptionThrown',p=>this.consoleEvents.push({loai:'exception',text:String(p.exceptionDetails?.exception?.description??p.exceptionDetails?.text??'?').split('\n')[0]}));
  cdp.on('Runtime.consoleAPICalled',p=>{if(['error','warning','assert'].includes(p.type))this.consoleEvents.push({loai:p.type,text:(p.args??[]).map(a=>String(a.value??a.description??'')).join(' ').slice(0,300)});});
  await cdp.send('Page.enable');await cdp.send('Runtime.enable');await page.goto(this.url);
  await page.locator('.app-main,.nav-bar').first().waitFor({state:'attached',timeout:40000});
  this.serverStarts++;this.timings.startup=Date.now()-start;return this;
};
BrowserSession.prototype._donDep=async function(){await this._pwBrowser?.close();this._pwBrowser=null;};

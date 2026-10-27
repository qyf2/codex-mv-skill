import { requireNode, parseArgs, findChrome, browserArgs, run, loadProject } from './lib/runtime.mjs';
import { existsSync } from 'node:fs';
const args = parseArgs(process.argv.slice(2), ['chrome','ffmpeg','soft-gl','no-sandbox','gpu-angle']);
let failed=false;
async function check(label, fn) { try { await fn(); console.log(`OK ${label}`); } catch(e) { failed=true; console.error(`FAIL ${label}: ${e.message}`); } }
await check('Node.js',()=>requireNode());
await check('project config',()=>loadProject());
await check('FFmpeg',()=>run(args.ffmpeg || process.env.FFMPEG_PATH || 'ffmpeg',['-version']));
await check('p5 + p5.brush',()=>{ for(const p of ['node_modules/p5/lib/p5.min.js','node_modules/p5.brush/dist/p5.brush.js']) if(!existsSync(p)) throw Error('Run npm ci first'); });
await check('browser and WebGL2',async()=>{
  const {default:puppeteer}=await import('puppeteer-core'); let browser;
  try {
    const path=findChrome(args.chrome); console.log(`Browser: ${path}`);
    browser=await puppeteer.launch({executablePath:path,headless:true,args:browserArgs(args)});
    const page=await browser.newPage();
    const info=await page.evaluate(()=>{const g=document.createElement('canvas').getContext('webgl2'); if(!g) throw Error('WebGL2 unavailable; try --soft-gl'); const e=g.getExtension('WEBGL_debug_renderer_info'); return e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);});
    console.log(info);
  } finally { await browser?.close(); }
});
process.exitCode=failed?1:0;

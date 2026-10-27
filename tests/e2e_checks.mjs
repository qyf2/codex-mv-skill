import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, readdirSync, statSync, renameSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const root=resolve(process.argv[2]); process.chdir(root);
const {default:puppeteer}=await import(pathToFileURL(join(root,'node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js')));
const rt=await import(pathToFileURL(join(root,'lib/runtime.mjs')));
const browser=await puppeteer.launch({executablePath:rt.findChrome(),headless:true,args:rt.browserArgs()});
try {
  const page=await browser.newPage();
  await page.goto(pathToFileURL(join(root,'studio.html')).href+'?render');
  await page.waitForFunction('window.ready===true',{timeout:120000});
  const render=t=>page.evaluate(t=>window.renderAt(t),t);
  const a=await render(1.25); await render(.75); const b=await render(1.25);
  assert.equal(createHash('sha256').update(a).digest('hex'),createHash('sha256').update(b).digest('hex'),'same t must render identically after another frame');
  console.log('PASS repeated out-of-order frame equality');
} finally { await browser.close(); }

function cli(args,success=true) {
  const r=spawnSync(process.execPath,['render.mjs',...args],{cwd:root,env:process.env,encoding:'utf8',timeout:240000});
  console.log(r.stdout); if(r.stderr) console.error(r.stderr);
  if(r.error) throw r.error;
  assert.equal(r.status===0,success,`unexpected status ${r.status}: ${args.join(' ')}`);
  return r;
}
const options=['--fps=12','--width=960','--height=540'];
cli(['--sheet=.5,1.5,2.5,3.5','--cols=4','--w=480','--out=out/check/lyrics.jpg']);
cli(['--strip=1:1.25','--w=320','--out=out/check/motion.jpg']);
cli(['--frames','--workers=2',...options]);
const dirs=readdirSync('out/frames'); assert.equal(dirs.length,1);
const cache=join('out/frames',dirs[0]), first=join(cache,'f0000000.jpg'), last=join(cache,'f0000047.jpg');
const before=statSync(first).mtimeMs;
cli(['--frames','--workers=2',...options]);
assert.equal(statSync(first).mtimeMs,before,'resumption should reuse complete frames');
renameSync(last,last+'.saved');
assert.match(cli(['--encode',...options],false).stderr,/missing frames/);
cli(['--frames','--workers=2',...options]);
assert.equal(statSync(first).mtimeMs,before,'repair must preserve other frames');
assert.match(cli(['--encode',...options,'--ffmpeg=codex-nonexistent-ffmpeg'],false).stderr,/Cannot launch/);
// An invalid browser path cannot affect pure encoding.
cli(['--encode',...options,'--chrome=missing-browser.exe','--out=out/smoke.mp4']);
assert.equal(JSON.parse(readFileSync('out/smoke.mp4.json','utf8')).frames,48);
cli(['--clip',...options,'--range=1:2','--out=out/one-second.mp4']);
assert.equal(JSON.parse(readFileSync('out/one-second.mp4.json','utf8')).frames,12);
cli(['--encode',...options,'--no-audio','--range=1:2','--out=out/silent.mp4']);
assert.equal(JSON.parse(readFileSync('out/silent.mp4.json','utf8')).audio,null);
const old=readFileSync('local-fonts.css','utf8');
try {
  writeFileSync('local-fonts.css',old+'\n/* content change */\n');
  assert.match(cli(['--encode',...options],false).stderr,/No matching cache/);
} finally { writeFileSync('local-fonts.css',old); }
console.log('PASS cache/resume/missing-frame/encoder-failure checks');

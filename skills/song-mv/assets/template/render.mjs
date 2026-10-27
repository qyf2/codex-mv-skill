// Codex MV renderer. Run from the project directory. See --help.
import { mkdirSync, writeFileSync, readFileSync, existsSync, statSync, renameSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { requireNode, parseArgs, number, integer, loadProject, findChrome, browserArgs, run, fingerprint } from './lib/runtime.mjs';

const HELP = `Usage: node render.mjs MODE [--key=value]
Modes (exactly one):
 --sheet=0.1,1,2     contact sheet; --cols=3 --w=480 --crop=x,y,w,h
 --strip=1:1.3      every frame in a short interval (max 240 preview frames)
 --stills=0.5,1     PNG stills in --out=out/stills
 --frames          resumable JPEGs, --workers=1..16 --range=start:end
 --encode          validate cache and encode; browser is NOT required
 --clip            render frames + encode, optionally --range=start:end
Options: --out=path --fps=24 --width=1920 --height=1080 --audio=path
 --no-audio --chrome=path --ffmpeg=path --soft-gl --gpu-angle=vulkan|gl-egl
 --no-sandbox (explicit opt-in for containers only) --loop=name
 --frames-dir=out/frames --timeout=120000 --crf=18 --preset=medium
Cache is keyed by source/assets/settings; changed code never reuses stale frames.
--range uses absolute frame numbers; --encode with the same range encodes that span.
--clip/--frames default to full duration. Render small previews first.`;
const FLAGS = ['help','sheet','strip','stills','frames','encode','clip','cols','w','crop','out','fps','width','height','audio','no-audio','chrome','ffmpeg','soft-gl','gpu-angle','no-sandbox','loop','frames-dir','timeout','crf','preset','workers','range'];

async function main() {
  const args = parseArgs(process.argv.slice(2), FLAGS);
  if (args.help) { console.log(HELP); return; }
  requireNode();
  const modes = ['sheet','strip','stills','frames','encode','clip'].filter(k => k in args);
  if (modes.length !== 1) throw Error('Choose exactly one render mode. Run --help.');
  const mode = modes[0], project = loadProject();
  const fps = integer(args.fps ?? project.fps ?? 24, 'fps', 1, 120);
  const width = integer(args.width ?? 1920, 'width', 16, 7680), height = integer(args.height ?? 1080, 'height', 16, 4320);
  if (width % 2 || height % 2) throw Error('Video width and height must be even for yuv420p');
  const workers = integer(args.workers ?? 2, 'workers', 1, 16);
  const timeout = integer(args.timeout ?? 120000, 'timeout', 1000, 3600000);
  const list = value => {
    if (typeof value !== 'string' || !value) throw Error('Expected comma-separated times');
    return value.split(',').map(v => number(v, 'time'));
  };
  let duration = project.duration, browser;
  try {
    if (args.loop && mode === 'encode') {
      const meta = JSON.parse(readFileSync(`out/loop-${String(args.loop).replace(/[^a-zA-Z0-9_-]/g, '_')}.json`, 'utf8'));
      duration = number(meta.duration, 'loop duration', 0.001);
    }
    if (mode !== 'encode') {
      const puppeteer = (await import('puppeteer-core')).default;
      browser = await puppeteer.launch({ executablePath: findChrome(args.chrome), headless: true, protocolTimeout: timeout, args: browserArgs(args) });
    }
    async function pageFor() {
      const page = await browser.newPage(), failures = [];
      page.on('pageerror', e => failures.push(e.message));
      page.on('console', m => { if (m.type() === 'error') console.error('[browser]', m.text()); });
      await page.goto(pathToFileURL(resolve('studio.html')).href + '?render', { waitUntil: 'load', timeout });
      try { await page.waitForFunction('window.ready === true', { timeout }); }
      catch (e) { throw Error(`Studio not ready: ${failures.join('; ') || e.message}. Try --soft-gl; check p5 and local fonts.`); }
      if (failures.length) throw Error(failures.join('; '));
      if (args.loop) await page.evaluate(name => {
        if (!LOOPS[name]) throw Error(`Unknown loop: ${name}`);
        window.LOOP = LOOPS[name];
      }, args.loop);
      return page;
    }
    if (browser) {
      const probe = await pageFor();
      duration = await probe.evaluate(() => window.LOOP ? window.LOOP.len : DUR);
      console.log('GPU:', await probe.evaluate(() => window.gpuInfo()));
      await probe.close();
      if (args.loop) { mkdirSync('out', { recursive: true }); writeFileSync(`out/loop-${String(args.loop).replace(/[^a-zA-Z0-9_-]/g, '_')}.json`, JSON.stringify({ duration })); }
    }
    const validTime = t => { if (t < 0 || t >= duration) throw Error(`Time ${t} outside [0, ${duration})`); return t; };
    let a = 0, b = duration;
    if (args.range) {
      const parts = String(args.range).split(':');
      if (parts.length !== 2) throw Error('--range requires start:end');
      [a,b] = parts.map(v => number(v, 'range'));
      if (!(a < b && b <= duration + 1e-8)) throw Error(`Range must satisfy 0 <= start < end <= ${duration}`);
      for (const v of [a,b]) if (Math.abs(v * fps - Math.round(v * fps)) > 1e-6) throw Error('Range endpoints must lie on frame boundaries. Use multiples of 1/fps.');
    }
    const first = Math.round(a * fps), last = args.range ? Math.round(b * fps) : Math.ceil(duration * fps);
    const count = last - first, seconds = count / fps;
    if (count < 1) throw Error('Range contains no frames');
    if (['sheet','strip','stills'].includes(mode)) {
      let ts;
      if (mode === 'strip') {
        const parts = String(args.strip).split(':');
        if (parts.length !== 2) throw Error('--strip requires start:end');
        const [start,end] = parts.map(v => number(v, 'strip time'));
        if (start > end || end >= duration) throw Error('Invalid strip interval');
        ts = Array.from({ length: Math.floor((end-start)*fps+1e-8)+1 }, (_,i) => start+i/fps);
      } else ts = list(args[mode]);
      if (!ts.length || ts.length > 240) throw Error('Preview must contain 1..240 frames');
      ts.forEach(validTime);
      const page = await pageFor();
      if (mode === 'stills') {
        const out = args.out || 'out/stills'; mkdirSync(out, { recursive: true });
        for (const t of ts) {
          const url = await page.evaluate(t => window.renderAt(t), t);
          writeFileSync(join(out, `t${t.toFixed(4).replace('.', '_')}.png`), Buffer.from(url.split(',')[1], 'base64'));
        }
        console.log(`Wrote ${ts.length} stills to ${out}`);
      } else {
        const cols = integer(args.cols ?? (mode === 'strip' ? 6 : 3), 'cols', 1, 24), w = integer(args.w ?? 480, 'w', 16, 1920);
        const crop = args.crop ? list(args.crop) : null;
        if (crop && (crop.length !== 4 || crop[2] <= 0 || crop[3] <= 0 || crop[0]+crop[2] > 1920 || crop[1]+crop[3] > 1080)) throw Error('crop must be x,y,width,height within 1920x1080');
        const result = await page.evaluate((ts,c,w,crop) => window.renderSheet(ts,c,w,crop), ts,cols,w,crop);
        const out = args.out || 'out/check/sheet.jpg'; mkdirSync(dirname(out), { recursive: true });
        writeFileSync(out, Buffer.from(result.url.split(',')[1], 'base64'));
        console.log(`${out}: ${ts.length} frames; ms/frame ${result.ms.join(' ')}`);
      }
      return;
    }
    const settings = { fps, width, height, duration, loop: args.loop || null, softwareGL: !!args['soft-gl'], angle: args['gpu-angle'] || process.platform };
    const id = fingerprint(settings), dir = join(args['frames-dir'] || 'out/frames', id), metaFile = join(dir, 'manifest.json');
    console.log(`Cache: ${dir}; span ${first}..${last-1} (${count} frames, ${seconds.toFixed(3)}s)`);
    const filename = i => join(dir, `f${String(i).padStart(7,'0')}.jpg`);
    const valid = i => existsSync(filename(i)) && statSync(filename(i)).size > 100;
    if (mode !== 'encode') {
      mkdirSync(dir, { recursive: true }); writeFileSync(metaFile, JSON.stringify({ id, ...settings }, null, 2));
      const todo = []; for (let i=first;i<last;i++) if (!valid(i)) todo.push(i);
      console.log(`${todo.length} missing, ${count-todo.length} reused; ${workers} workers`);
      let next=0, done=0; const start=Date.now();
      if (todo.length) await Promise.all(Array.from({ length: Math.min(workers,todo.length) }, async () => {
        const page = await pageFor();
        try {
          while (next < todo.length) {
            const i=todo[next++];
            const url=await page.evaluate(async (t,w,h) => {
              await window.renderAt(t);
              const canvas=document.createElement('canvas'); canvas.width=w; canvas.height=h;
              canvas.getContext('2d').drawImage(document.getElementById('out'),0,0,w,h);
              return canvas.toDataURL('image/jpeg',.95);
            }, i/fps,width,height);
            writeFileSync(filename(i)+'.tmp',Buffer.from(url.split(',')[1],'base64')); renameSync(filename(i)+'.tmp',filename(i));
            done++;
            if (done%24===0 || done===todo.length) console.log(`${done}/${todo.length}, ${Math.round((Date.now()-start)/done)} ms/frame effective`);
          }
        } finally { await page.close(); }
      }));
      if (mode === 'frames') return;
    }
    if (!existsSync(metaFile)) throw Error('No matching cache. Run --frames with identical fps/size/GPU/loop options first.');
    const missing=[]; for(let i=first;i<last;i++) if(!valid(i)) missing.push(i);
    if(missing.length) throw Error(`Cannot encode: ${missing.length} missing frames (first ${missing.slice(0,8).join(',')}). Run --frames with the same options.`);
    const audio=args['no-audio'] ? '' : (args.audio ?? project.audio ?? '');
    if (audio && !existsSync(audio)) throw Error(`Audio not found: ${audio}`);
    const out=args.out || 'out/video.mp4'; mkdirSync(dirname(out),{recursive:true});
    const crf=integer(args.crf ?? 18,'crf',0,51), preset=args.preset || 'medium';
    if (!['ultrafast','superfast','veryfast','faster','fast','medium','slow','slower','veryslow'].includes(preset)) throw Error('Invalid x264 preset');
    const ffmpeg=args.ffmpeg || process.env.FFMPEG_PATH || 'ffmpeg';
    await run(ffmpeg,['-y','-loglevel','error','-framerate',String(fps),'-start_number',String(first),'-i',join(dir,'f%07d.jpg'),
      ...(audio ? ['-ss',String(first/fps),'-i',audio,'-map','0:v:0','-map','1:a:0','-af','apad','-c:a','aac','-b:a','192k'] : ['-map','0:v:0']),
      '-t',String(seconds),'-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
      '-c:v','libx264','-preset',preset,'-crf',String(crf),'-pix_fmt','yuv420p','-color_range','tv',
      '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',out]);
    if (!existsSync(out) || statSync(out).size < 100) throw Error('FFmpeg produced no usable output');
    writeFileSync(out+'.json',JSON.stringify({path:resolve(out),frames:count,fps,duration:seconds,width,height,audio:audio||null,cache:dir},null,2));
    console.log(`Wrote ${out} (${seconds.toFixed(3)}s, ${count} frames${audio?', audio included':''})`);
  } finally { if (browser) await browser.close(); }
}
main().catch(e => { console.error(`ERROR: ${e.message}`); process.exitCode=1; });

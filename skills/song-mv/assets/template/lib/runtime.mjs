import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { homedir } from 'node:os';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import vm from 'node:vm';

export function requireNode() {
  const [major, minor] = process.versions.node.split('.').map(Number);
  if (major < 22 || (major === 22 && minor < 12)) throw Error('Node.js >=22.12 required. Install a current LTS release; then reopen your terminal.');
}
export function parseArgs(argv, allowed) {
  const args = {};
  for (const a of argv) {
    if (!a.startsWith('--')) throw Error(`Use --key=value arguments, received: ${a}`);
    const i = a.indexOf('='), k = a.slice(2, i < 0 ? undefined : i);
    if (!allowed.includes(k)) throw Error(`Unknown flag --${k}. Run --help.`);
    if (k in args) throw Error(`Duplicate flag --${k}`);
    args[k] = i < 0 ? true : a.slice(i + 1);
  }
  return args;
}
export function number(v, label, min = 0, max = Infinity) {
  const n = Number(v);
  if (v === true || !Number.isFinite(n) || n < min || n > max) throw Error(`${label} must be a number in [${min}, ${max}]`);
  return n;
}
export function integer(v, label, min, max) {
  const n = number(v, label, min, max);
  if (!Number.isInteger(n)) throw Error(`${label} must be an integer`);
  return n;
}
export function loadProject() {
  // config.js is trusted project code; no shell or browser needed for encoding.
  const p = vm.runInNewContext(readFileSync('src/config.js', 'utf8') + '\nJSON.parse(JSON.stringify(PROJECT))', {}, { timeout: 1000 });
  number(p.duration, 'PROJECT.duration', 0.001); number(p.bpm, 'PROJECT.bpm', 1);
  if (!Number.isFinite(Number(p.offset ?? 0))) throw Error('PROJECT.offset must be finite');
  return p;
}
export function findChrome(explicit) {
  const local = process.env.LOCALAPPDATA || '';
  const candidates = [explicit, process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    join(local, 'Google/Chrome/Application/chrome.exe'), 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
  for (const root of [process.env.PLAYWRIGHT_BROWSERS_PATH, join(homedir(), '.cache/ms-playwright'), join(local, 'ms-playwright')].filter(Boolean)) {
    if (!existsSync(root)) continue;
    for (const n of readdirSync(root).filter(n => /^chromium-\d+$/.test(n)).sort().reverse()) {
      for (const suffix of ['chrome-win/chrome.exe', 'chrome-win64/chrome.exe', 'chrome-linux/chrome', 'chrome-linux64/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium', 'chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium']) candidates.push(join(root, n, suffix));
    }
  }
  if (explicit && !existsSync(explicit)) throw Error(`Browser not found: ${explicit}`);
  const found = candidates.find(p => p && existsSync(p));
  if (!found) throw Error('Chrome/Chromium/Edge not found. Set CHROME_PATH or pass --chrome=absolute-path.');
  return resolve(found);
}
export function browserArgs(args = {}) {
  if (args['gpu-angle'] && !['vulkan', 'gl-egl'].includes(args['gpu-angle'])) throw Error('--gpu-angle must be vulkan or gl-egl');
  const gpu = args['soft-gl'] ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    : args['gpu-angle'] === 'vulkan' ? ['--use-angle=vulkan', '--enable-features=Vulkan'] : args['gpu-angle'] ? ['--use-angle=gl-egl']
    : process.platform === 'win32' ? ['--use-angle=d3d11'] : process.platform === 'darwin' ? ['--use-angle=metal'] : ['--use-gl=angle'];
  return [...gpu, ...(args['no-sandbox'] ? ['--no-sandbox'] : []), '--allow-file-access-from-files', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--disable-renderer-backgrounding', '--disable-background-timer-throttling'];
}
export function run(cmd, args, options = {}) {
  return new Promise((ok, bad) => {
    const p = spawn(cmd, args, { stdio: 'inherit', ...options });
    p.once('error', e => bad(Error(`Cannot launch ${cmd}: ${e.message}`)));
    p.once('close', code => code === 0 ? ok() : bad(Error(`${cmd} exited ${code}`)));
  });
}
export function fingerprint(settings) {
  const h = createHash('sha256').update(JSON.stringify(settings));
  function walk(p) {
    if (!existsSync(p)) return;
    for (const e of readdirSync(p, { withFileTypes: true }).sort((a,b) => a.name.localeCompare(b.name))) {
      const f = join(p, e.name);
      if (e.isDirectory()) walk(f); else h.update(f.replaceAll('\\', '/')).update(readFileSync(f));
    }
  }
  for (const f of ['studio.html', 'local-fonts.css', 'package-lock.json', 'render.mjs', 'lib/runtime.mjs']) h.update(f).update(readFileSync(f));
  walk('src'); walk('assets');
  return h.digest('hex').slice(0, 20);
}

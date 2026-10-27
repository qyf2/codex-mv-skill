import test from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs, number, integer, browserArgs, run } from '../skills/song-mv/assets/template/lib/runtime.mjs';
test('paths containing equals survive parsing',()=>assert.equal(parseArgs(['--out=a=b.mp4'],['out']).out,'a=b.mp4'));
test('unknown, duplicate and positional args fail',()=>{
  for(const args of [['--bogus'],['--fps=2','--fps=3'],['x']]) assert.throws(()=>parseArgs(args,['fps']));
});
test('invalid numeric settings fail',()=>{
  for(const v of ['NaN','Infinity',true,'-1']) assert.throws(()=>number(v,'value'));
  assert.throws(()=>integer(1.5,'fps',1,120)); assert.throws(()=>integer(0,'workers',1,16));
});
test('sandbox stays on unless explicitly disabled',()=>{
  assert.equal(browserArgs({}).includes('--no-sandbox'),false);
  assert.equal(browserArgs({'no-sandbox':true}).includes('--no-sandbox'),true);
});
test('GPU arguments are validated',()=>{
  assert.throws(()=>browserArgs({'gpu-angle':'anything'}));
  assert.ok(browserArgs({'soft-gl':true}).includes('--use-angle=swiftshader'));
});
test('failed executables and missing commands reject',async()=>{
  await assert.rejects(run(process.execPath,['-e','process.exit(7)'],{stdio:'ignore'}));
  await assert.rejects(run('codex-mv-nonexistent-executable-7234',[],{stdio:'ignore'}));
});

#!/usr/bin/env node
// Surface-authored fixed fixtures over exact upstream TypeScript sources.
// This is a headless reference, never a renderer or an arbitrary-input broker.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, lstatSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

if (Number(process.versions.node.split('.')[0]) < 24) {
  throw new Error('This fixed TypeScript fixture requires Node 24 or later.');
}
const root = path.dirname(fileURLToPath(import.meta.url));
const manifestBytes = readFileSync(path.join(root, 'IMPORT_MANIFEST.json'));
const hash = data => createHash('sha256').update(data).digest('hex');
assert.equal(hash(manifestBytes), '6eebb37ec30fceae018fcd158e39fecb2f3c47cacae6a732891f3fdb99ebaf01', 'import custody manifest');
const manifest = JSON.parse(manifestBytes);
for (const row of manifest.files.filter(row => row.upstream === 'substrate-university')) {
  const target = path.join(root, row.path);
  assert.ok(lstatSync(target).isFile(), 'regular imported source');
  const bytes = readFileSync(target);
  assert.equal(bytes.length, row.bytes, 'import custody size');
  assert.equal(hash(bytes), row.sha256, 'import custody hash');
}
// Node's native TypeScript stripping needs explicit extensions; the preserved
// Vite sources use extensionless relative imports. Resolve only inside this
// pinned source tree, without rewriting the captured bytes.
const sourceURL = new URL('./substrate-university/src/', import.meta.url).href;
registerHooks({
  resolve(specifier, context, nextResolve) {
    try { return nextResolve(specifier, context); }
    catch (error) {
      if (error.code === 'ERR_MODULE_NOT_FOUND' && /^\.\.?\//.test(specifier)
          && context.parentURL?.startsWith(sourceURL)) {
        return nextResolve(specifier + '.ts', context);
      }
      throw error;
    }
  },
});

const { compile } = await import('./substrate-university/src/math/addressCompiler.ts');
const { mat, vec, preimage } = await import('./substrate-university/src/math/matrix.ts');
const { weave, topologicalOrder } = await import('./substrate-university/src/math/world.ts');
const { TOPICS, DIVISIONS } = await import('./substrate-university/src/content/registry.ts');

const address = 'loom://plate/START/ROTATE:90/SCALE:2/SHIFT:1,0/COMMIT';
const compiled = compile(address);
assert.ok(compiled.ok);
const matrix = compiled.matrix.map(row => row.map(String));
assert.deepEqual(matrix, [['0', '-2', '1'], ['2', '0', '0'], ['0', '0', '1']]);
const rows = weave(90, 9, 4).map(row => row.join(''));
assert.deepEqual(rows, ['000010000', '000101000', '001000100', '010101010']);
const A = mat([[1, 2], [2, 4]]);
const preimages = [preimage(A, vec([1, 1])).kind, preimage(A, vec([3, 6])).kind];
const nonQuarterTurn = !compile('loom://plate/START/ROTATE:45/COMMIT').ok;
const uncommitted = !compile('loom://plate/START/SCALE:2').ok;
const cycle = topologicalOrder({ nodes: ['a', 'b'], edges: [['a', 'b'], ['b', 'a']] }) === null;
assert.ok(nonQuarterTurn && uncommitted && cycle);
assert.deepEqual(preimages, ['empty', 'affine']);
assert.equal(TOPICS.length, 62);
assert.equal(new Set(TOPICS.map(topic => topic.id)).size, 62);
const labels = {};
const byDivision = {};
for (const topic of TOPICS) {
  labels[topic.status] = (labels[topic.status] ?? 0) + 1;
  byDivision[topic.division] = (byDivision[topic.division] ?? 0) + 1;
}
assert.deepEqual(labels, { established: 42, house: 18, application: 2 });
assert.deepEqual(byDivision, { foundations: 10, relational: 10, languages: 10, geometry: 12, acoustic: 10, worlds: 10 });
const result = {
  schema: 'surface.university-demo/1', status: 'PASS', node: process.version,
  source_commit: '6a0f5eaa8dd39b58bdd99889721ecea5f54e62bb',
  address, matrix, states: compiled.states, rule90_rows: rows,
  non_quarter_turn_refused: nonQuarterTurn, uncommitted_refused: uncommitted,
  cycle_refused: cycle, preimage_kinds: preimages,
  registry: { topic_count: TOPICS.length, division_count: DIVISIONS.length,
              labels, topics_by_division: byDivision,
              topics: TOPICS.map(({ id, division, status }) => ({ id, division, status })) },
  browser_required: false, llm_inference: false, full_university_acceptance: false,
  scope: 'Fixed, bounded headless fixtures. Original TypeScript is loaded with native stripping; no static typecheck or browser suite is claimed.',
  limitations: [
    'The upstream loom parser accepts some surplus arguments; this example exposes no arbitrary-input API.',
    'World dimensions and matrix shapes are fixed validated fixtures; upstream helpers do not fully validate hostile inputs.',
    'Fold is excluded because original Greek glyphs can collide with generated rule names.',
    'Six divisions and all 62 topic identities are retained. PolyIA IX and VII/VIII belong to a separate registry.',
  ],
};
process.stdout.write(JSON.stringify(result, null, 2) + '\n');

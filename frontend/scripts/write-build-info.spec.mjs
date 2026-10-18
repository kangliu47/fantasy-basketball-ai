import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { sourceFingerprint, writeBuildInfo } from './write-build-info.mjs';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'synthetic-ui-build-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'src'), { recursive: true });
  mkdirSync(join(root, 'public'));
  writeFileSync(join(root, 'package.json'), JSON.stringify({ version: '0.2.0' }));
  writeFileSync(join(root, 'src/main.ts'), '// Synthetic app source');
  return root;
}
test('compiled identity and served manifest are identical; generated output cannot change the source hash', (t) => {
  const root = fixture(t),
    before = sourceFingerprint(root);
  const info = writeBuildInfo(root, { now: new Date('2026-10-18T14:00:00Z') });
  assert.equal(info.buildId, '20261018T140000Z-' + before);
  assert.deepEqual(JSON.parse(readFileSync(join(root, 'public/build-info.json'), 'utf8')), info);
  assert.ok(
    readFileSync(join(root, 'generated/build-info.ts'), 'utf8').includes(
      JSON.stringify(info, null, 2),
    ),
  );
  assert.equal(sourceFingerprint(root), before);
});
test('actual public source changes alter the ID; private storage is excluded', (t) => {
  const root = fixture(t),
    before = sourceFingerprint(root);
  writeFileSync(join(root, '.env'), 'SYNTHETIC_DO_NOT_READ=not-a-real-secret');
  mkdirSync(join(root, '.local'));
  writeFileSync(join(root, '.local/example.json'), 'Synthetic private content');
  assert.equal(sourceFingerprint(root), before);
  writeFileSync(join(root, 'src/main.ts'), '// Changed synthetic app');
  assert.notEqual(sourceFingerprint(root), before);
});
test('if-missing preserves an existing identity and development does not pretend to be a stamped production build', (t) => {
  const root = fixture(t);
  writeBuildInfo(root, { development: true });
  assert.equal(
    JSON.parse(readFileSync(join(root, 'public/build-info.json'), 'utf8')).buildId,
    'development',
  );
  assert.equal(writeBuildInfo(root, { ifMissing: true }), undefined);
  const prod = writeBuildInfo(root, { now: new Date('2026-10-18T14:00:00Z') });
  assert.notEqual(prod.buildId, 'development');
});

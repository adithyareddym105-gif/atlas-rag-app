const test = require('node:test');
const assert = require('node:assert/strict');
const { chunkText, retrieveChunks, tokenize } = require('../src-rag');

test('chunkText returns overlapping chunks for long text', () => {
  const text = Array.from({ length: 420 }, (_, i) => `word${i}`).join(' ');
  const chunks = chunkText(text, 100, 20);
  assert.ok(chunks.length > 1);
  assert.equal(chunks[0].split(/\s+/).length, 100);
  assert.ok(chunks[1].includes('word80'));
});

test('retrieval ranks relevant chunks above unrelated chunks', () => {
  const chunks = [
    { source: 'billing.md', index: 0, text: 'Invoices can be downloaded from the billing settings page.' },
    { source: 'security.md', index: 0, text: 'Use multi-factor authentication to protect your account.' },
    { source: 'shipping.md', index: 0, text: 'Track a delayed parcel using the tracking number.' }
  ];
  const result = retrieveChunks('Where can I download invoices from billing settings?', chunks, 2);
  assert.equal(result[0].source, 'billing.md');
  assert.ok(result[0].score > 0);
});

test('empty and stopword-only input is handled safely', () => {
  assert.deepEqual(chunkText('  '), []);
  assert.deepEqual(retrieveChunks('the and for', [{ text: 'unrelated content', source: 'x', index: 0 }]), []);
  assert.ok(tokenize('reset my password').includes('password'));
});

test('tokenizer normalizes case and punctuation', () => { assert.deepEqual(tokenize('BILLING, Billing!'), ['billing','billing']); });

// Lightweight BM25-style lexical retrieval: no vector database or embedding API required for V1.
const STOP = new Set(['the','a','an','and','or','but','if','to','of','in','on','for','with','is','are','was','were','be','been','being','it','this','that','these','those','i','you','we','they','he','she','as','at','by','from','can','could','would','should','do','does','did','how','what','when','where','why','who','which','my','your','our','their','about']);
function tokenize(text) {
  return String(text || '').toLowerCase().normalize('NFKD').replace(/[^\p{L}\p{N}\s_-]/gu, ' ').split(/\s+/).filter(t => t.length > 1 && !STOP.has(t));
}
function chunkText(text, maxWords = 180, overlap = 35) {
  const words = String(text || '').split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  const chunks = [];
  const step = Math.max(1, maxWords - overlap);
  for (let start = 0; start < words.length; start += step) {
    const part = words.slice(start, start + maxWords).join(' ').trim();
    if (part) chunks.push(part);
    if (start + maxWords >= words.length) break;
  }
  return chunks;
}
function retrieveChunks(question, chunks, topK = 4) {
  if (!chunks.length) return [];
  const qTerms = tokenize(question);
  if (!qTerms.length) return [];
  const docs = chunks.map(c => ({ ...c, terms: tokenize(c.text) }));
  const N = docs.length;
  const avgdl = docs.reduce((s, d) => s + d.terms.length, 0) / N || 1;
  const df = new Map();
  for (const d of docs) for (const t of new Set(d.terms)) df.set(t, (df.get(t) || 0) + 1);
  const scored = docs.map(d => {
    const counts = new Map(); for (const t of d.terms) counts.set(t, (counts.get(t) || 0) + 1);
    let score = 0;
    for (const term of qTerms) {
      const tf = counts.get(term) || 0; if (!tf) continue;
      const idf = Math.log(1 + (N - (df.get(term) || 0) + 0.5) / ((df.get(term) || 0) + 0.5));
      score += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * d.terms.length / avgdl));
    }
    return { ...d, score };
  });
  return scored.filter(d => d.score > 0).sort((a, b) => b.score - a.score).slice(0, topK).map(({ terms, ...rest }) => rest);
}
module.exports = { chunkText, retrieveChunks, tokenize };

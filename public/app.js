const $ = id => document.getElementById(id);
async function api(url, options = {}) {
  const res = await fetch(url, options); const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`); return data;
}
function message(id, text, kind = '') { const el = $(id); el.textContent = text; el.className = `message ${kind}`.trim(); }
function esc(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function formatSize(chars) { return `${Number(chars).toLocaleString()} chars`; }
async function refreshStatus() {
  try { const s = await api('/api/health'); $('status').textContent = s.llmConfigured ? `LLM ready · ${s.model}` : 'LLM not configured'; $('status').className = `status ${s.llmConfigured ? 'ready' : 'warning'}`; document.querySelector('.live-dot').style.background = s.llmConfigured ? '#35c6a2' : '#e5a55d'; }
  catch { $('status').textContent = 'Server unavailable'; $('status').className = 'status warning'; document.querySelector('.live-dot').style.background = '#df6375'; }
}
async function refreshDocs() {
  const corpus = $('corpus-select')?.value || 'custom'; const docs = await api(`/api/documents?corpus=${encodeURIComponent(corpus)}`); $('doc-count').textContent = docs.length; $('source-label').textContent = `${docs.length} ${docs.length === 1 ? 'file' : 'files'}`;
  if (!docs.length) {
    $('documents').innerHTML = '<div class="empty-state"><span>▤</span><p>Your library is waiting.</p><small>Add a document to get started.</small></div>';
    $('document-selection').innerHTML = '<span class="muted">Upload documents to choose your sources.</span>'; return;
  }
  const oldSelected = new Set([...document.querySelectorAll('input[name="selected-document"]:checked')].map(el => el.value));
  $('document-selection').innerHTML = docs.map(d => `<label class="document-choice"><input type="checkbox" name="selected-document" value="${esc(d.id)}" ${(!oldSelected.size || oldSelected.has(d.id)) ? 'checked' : ''}> <span>${esc(d.name)}</span></label>`).join('');
  $('documents').innerHTML = docs.map(d => `<article class="doc-item"><div class="file-icon">${esc(d.type.toUpperCase())}</div><div class="doc-meta"><strong>${esc(d.name)}</strong><span>${formatSize(d.chars)}${d.builtin ? ' · provided corpus' : ''}</span></div>${d.builtin ? '<span class="builtin-tag">KB</span>' : `<button class="delete-button" title="Remove ${esc(d.name)}" data-delete="${esc(d.id)}" aria-label="Delete document">×</button>`}</article>`).join('');
  $('documents').querySelectorAll('[data-delete]').forEach(btn => btn.addEventListener('click', async () => { if (!confirm('Remove this document from the knowledge base?')) return; try { await api(`/api/documents/${encodeURIComponent(btn.dataset.delete)}`, { method: 'DELETE' }); await refreshDocs(); message('upload-message', 'Document removed from your knowledge base.', 'success'); } catch(e) { message('upload-message', e.message, 'error'); } }));
}
async function uploadFile(file) {
  if (!file) return;
  if (!/\.(txt|md)$/i.test(file.name)) return message('upload-message', 'Please choose a .txt or .md file.', 'error');
  const fd = new FormData(); fd.append('file', file); const button = document.querySelector('#upload-form button'); button.disabled = true; button.innerHTML = '<span>↻</span> Adding document…'; message('upload-message', 'Adding your file to the knowledge base…');
  try { const r = await api('/api/documents', { method: 'POST', body: fd }); await refreshDocs(); $('file-input').value = ''; message('upload-message', `Added ${r.document.name} · ${r.chunksCreated} chunks indexed.`, 'success'); }
  catch(err) { message('upload-message', err.message, 'error'); }
  finally { button.disabled = false; button.innerHTML = '<span>＋</span> Add to knowledge base'; }
}
$('upload-form').addEventListener('submit', async e => { e.preventDefault(); const file = $('file-input').files[0]; if (!file) return message('upload-message', 'Choose a file first.', 'error'); await uploadFile(file); });
const dropzone = $('dropzone');
['dragenter','dragover'].forEach(name => dropzone.addEventListener(name, e => { e.preventDefault(); dropzone.classList.add('dragover'); }));
['dragleave','drop'].forEach(name => dropzone.addEventListener(name, e => { e.preventDefault(); dropzone.classList.remove('dragover'); }));
dropzone.addEventListener('drop', async e => { const file = e.dataTransfer?.files?.[0]; if (file) await uploadFile(file); });
$('file-input').addEventListener('change', () => { const f = $('file-input').files[0]; if (f) { dropzone.querySelector('strong').textContent = f.name; dropzone.querySelector('small').textContent = 'Ready to add to your knowledge base'; } });
$('question').addEventListener('input', () => $('question-count').textContent = `${$('question').value.length} / 1000`);
document.querySelectorAll('[data-prompt]').forEach(btn => btn.addEventListener('click', () => { $('question').value = btn.dataset.prompt; $('question').focus(); $('question-count').textContent = `${$('question').value.length} / 1000`; }));
$('select-all').addEventListener('click', () => document.querySelectorAll('input[name="selected-document"]').forEach(el => el.checked = true));
$('select-none').addEventListener('click', () => document.querySelectorAll('input[name="selected-document"]').forEach(el => el.checked = false));
$('overlap').addEventListener('change', () => { const size = Number($('chunk-size').value) || 180; if (Number($('overlap').value) >= size) $('overlap').value = Math.max(0, size - 1); });
$('chunk-size').addEventListener('change', () => { const size = Math.min(500, Math.max(40, Number($('chunk-size').value) || 180)); $('chunk-size').value = size; if (Number($('overlap').value) >= size) $('overlap').value = size - 1; });
function openSourceModal(name, chunk, text) { $('modal-title').textContent = 'Source passage'; $('modal-meta').textContent = `${name} · Chunk ${chunk}`; $('modal-text').textContent = text; $('chunk-modal').hidden = false; $('close-modal').focus(); }
function closeSourceModal() { $('chunk-modal').hidden = true; }
$('close-modal').addEventListener('click', closeSourceModal); $('modal-done').addEventListener('click', closeSourceModal);
$('chunk-modal').addEventListener('click', e => { if (e.target === $('chunk-modal')) closeSourceModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSourceModal(); });

$('ask-form').addEventListener('submit', async e => {
  e.preventDefault();

  const query = $('question').value.trim();
  if (!query) return;

  const button = $('ask-button');
  button.disabled = true;
  button.textContent = 'Generating answer...';
  message('ask-message', 'Searching documents and generating an answer...');
  $('welcome').hidden = true;
  $('answer-section').hidden = true;

  try {
    const r = await api('/api/answer', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        query,
        corpus: $('corpus-select').value,
        top_k: Number($('top-k').value)
      })
    });

    $('answer').textContent = r.answer;
    $('model-label').textContent = r.not_found ? 'Insufficient evidence' : 'Gemini ? Grounded answer';
    $('source-count').textContent = r.results.length;

    $('sources').innerHTML = r.results.map((item, i) => `
      <article class="source-card">
        <button type="button" class="source-open" data-source-index="${i}">
          <div class="source-top">
            <span class="source-tag">Retrieved evidence</span>
            <strong>${esc(item.source)}</strong>
            <span class="chunk-label">${esc(item.chunk_id)}</span>
          </div>
          <p>${esc(item.text.slice(0, 700))}${item.text.length > 700 ? '...' : ''}</p>
          <div class="score">Hybrid score: ${Number(item.hybrid_score).toFixed(4)} ? Click to inspect</div>
        </button>
      </article>
    `).join('');

    $('sources').querySelectorAll('[data-source-index]').forEach(btn => {
      btn.addEventListener('click', () => {
        const item = r.results[Number(btn.dataset.sourceIndex)];
        openSourceModal(item.source, item.chunk_number ?? item.chunk_id, item.text);
      });
    });

    $('usage').textContent = `Citations: ${r.citations.join(', ') || 'None'}`;
    $('answer-section').hidden = false;
    message('ask-message', 'Answer ready. Check the retrieved evidence below.', 'success');
    $('answer-section').scrollIntoView({behavior: 'smooth', block: 'start'});

  } catch (err) {
    $('welcome').hidden = false;
    message('ask-message', err.message, 'error');
  } finally {
    button.disabled = false;
    button.innerHTML = '<span>Ask Atlas</span><span class="button-arrow">?</span>';
  }
});

refreshStatus(); refreshDocs().catch(e => message('upload-message', e.message, 'error'));


// V2 workspace views
function showView(id) {
  document.querySelectorAll('.workspace-tab').forEach(b =>
    b.classList.toggle('active', b.dataset.view === id)
  );
  ['ask-view', 'words-view', 'evaluation-view'].forEach(v => {
    const el = $(v);
    if (el) el.hidden = v !== id;
  });
  if (id === 'words-view') loadWords();
}

document.querySelectorAll('.workspace-tab').forEach(b =>
  b.addEventListener('click', () => showView(b.dataset.view))
);

$('corpus-select').addEventListener('change', async () => {
  await refreshDocs();
  if (!$('words-view').hidden) loadWords();
});

async function loadWords() {
  try {
    const data = await api(`/api/words?corpus=${encodeURIComponent($('corpus-select').value)}`);

    $('words-stats').innerHTML = `
      <div class="stats-strip">
        <span><b>${data.totalWords}</b><small>total words</small></span>
        <span><b>${data.uniqueWords}</b><small>unique words</small></span>
        <span><b>${Object.keys(data.wordChunks).length}</b><small>indexed words</small></span>
      </div>`;

    $('word-results').innerHTML = `
      <div class="vocab-list">
        ${data.topWords.map(w => `
          <div class="vocab-row">
            <span>${esc(w.word)}</span>
            <small>${w.count} occurrences ? ${(data.wordChunks[w.word] || []).length} chunks</small>
          </div>
        `).join('')}
      </div>`;
  } catch (e) {
    $('words-stats').textContent = e.message;
  }
}

$('word-search').addEventListener('input', async () => {
  const term = $('word-search').value.trim().toLowerCase();
  if (!term) return loadWords();

  try {
    const data = await api(`/api/words?corpus=${encodeURIComponent($('corpus-select').value)}`);
    const chunks = data.wordChunks[term] || [];
    $('word-results').innerHTML = chunks.length
      ? `<h4>${esc(term)} ? ${chunks.length} matching chunks</h4>
         ${chunks.map(id => `<div class="word-location">${esc(id)}</div>`).join('')}`
      : `<p>No matching word found.</p>`;
  } catch (e) {
    $('word-results').textContent = e.message;
  }
});

$('analyze-question').addEventListener('click', async () => {
  const query = $('word-question').value.trim();
  if (!query) return;

  try {
    const r = await api('/api/words/question', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        query,
        corpus: $('corpus-select').value,
        top_k: 5
      })
    });

    $('question-word-results').innerHTML = `
      <div class="question-word-summary">
        ${r.present.length} words found ? ${r.absent.length} words absent
      </div>
      <h4>Present in corpus</h4>
      ${r.present.map(w => `
        <div class="question-word found">
          <b>${esc(w.word)}</b>
          <small>${w.chunks.map(esc).join(', ')}</small>
        </div>`).join('')}
      <h4>Absent from corpus</h4>
      ${r.absent.map(w => `
        <div class="question-word missing"><b>${esc(w)}</b><span>Not found</span></div>
      `).join('')}`;
  } catch (e) {
    $('question-word-results').textContent = e.message;
  }
});

$('run-evaluation').addEventListener('click', () => {
  $('evaluation-message').textContent =
    'Evaluation completed. Results are saved in the results folder. Run python scripts\\evaluate.py in PowerShell to generate a fresh evaluation.';
});

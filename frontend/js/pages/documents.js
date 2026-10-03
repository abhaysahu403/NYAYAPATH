import { Documents } from '../api/endpoints.js';
import { friendlyMessage } from '../api/client.js';
import { initShell, loadingState, emptyState, errorState, sourceCard } from '../components/shell.js';
import { esc, formatDate, fileSize, showToast, qs } from '../utils/helpers.js';

let lang = initShell('documents', (l) => { lang = l; renderList(); renderMain(); });
const $ = (id) => document.getElementById(id);
const t = (en, hi) => (lang === 'hi' ? hi : en);
let docs = [], current = null, text = '', analysis = null, qa = [];
const ALLOWED = ['pdf', 'docx', 'jpg', 'jpeg', 'png', 'txt'];

async function loadList() {
  $('docList').innerHTML = loadingState('Loading your documents...', 'आपके दस्तावेज़ लोड हो रहे हैं...');
  try { docs = await Documents.list(); renderList(); if (!current) renderMain(); if (qs('id')) openDoc(qs('id')); }
  catch (e) { $('docList').innerHTML = errorState(friendlyMessage(e), loadList); }
}

function renderList() {
  if (!docs.length) { $('docList').innerHTML = `<p class="np-muted">${t('No documents yet. Upload a court order, notice or supporting document.', 'अभी कोई दस्तावेज़ नहीं। कोर्ट आदेश, नोटिस या सहायक दस्तावेज़ अपलोड करें।')}</p>`; return; }
  $('docList').innerHTML = docs.map(d => `<button class="doc-card" style="width:100%;text-align:left;${current?.id === d.id ? 'border-color:var(--gold-main)' : ''}" data-open="${d.id}">
    <div class="doc-info"><div class="doc-name">${esc(d.original_filename)}</div>
    <div class="doc-meta">${fileSize(d.file_size)} · ${esc(d.status)} · ${formatDate(d.uploaded_at, lang)}</div></div></button>`).join('');
  document.querySelectorAll('[data-open]').forEach(b => b.onclick = () => openDoc(b.dataset.open));
}

function steps(state) { // state: 0 uploading, 1 extracting, 2 analyzing, 3 done
  const items = [t('Document uploaded', 'दस्तावेज़ अपलोड हुआ'), t('Text extracted', 'पाठ निकाला गया'), t('Analyzing', 'विश्लेषण हो रहा है')];
  return `<div class="processing-steps" role="status">${items.map((l, i) => `<div class="processing-step ${state > i ? 'done' : state === i ? 'active' : ''}"><span class="processing-step-icon">${state > i ? '✓' : '…'}</span>${l}</div>`).join('')}</div>`;
}

async function upload(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!ALLOWED.includes(ext)) { showToast(t('Supported: PDF, DOCX, JPG, PNG, Text', 'समर्थित: PDF, DOCX, JPG, PNG, Text'), 'error'); return; }
  $('progress').innerHTML = steps(0) + `<p class="np-loading-text">${t('Reading your document...', 'आपका दस्तावेज़ पढ़ा जा रहा है...')}</p>`;
  try {
    const d = await Documents.upload(file);
    $('progress').innerHTML = steps(d.status === 'FAILED' || d.status === 'OCR_REQUIRED' ? 1 : 2);
    docs.unshift(d); renderList(); await openDoc(d.id, true);
    $('progress').innerHTML = '';
  } catch (e) { $('progress').innerHTML = ''; showToast(friendlyMessage(e), 'error'); }
}

async function openDoc(id, auto = false) {
  current = docs.find(d => d.id === id) || { id }; analysis = null; qa = []; text = '';
  $('docMain').innerHTML = loadingState('Reading your document...', 'आपका दस्तावेज़ पढ़ा जा रहा है...');
  try {
    const d = await Documents.get(id, true);
    current = d; text = d.extracted_text || ''; analysis = d.analysis_result && Object.keys(d.analysis_result).length ? d.analysis_result : null;
    docs = docs.map(x => x.id === id ? d : x); renderList(); renderMain();
    if (auto && !analysis && ['TEXT_EXTRACTED', 'INDEXED'].includes(d.status)) analyze();
  } catch (e) { $('docMain').innerHTML = errorState(friendlyMessage(e), () => openDoc(id)); }
}

async function analyze() {
  $('aiPane').innerHTML = steps(2) + loadingState('Analyzing your document...', 'आपके दस्तावेज़ का विश्लेषण हो रहा है...');
  try { const r = await Documents.analyze(current.id, lang); analysis = r.analysis; current.status = r.status; renderMain(); }
  catch (e) { $('aiPane').innerHTML = errorState(friendlyMessage(e), analyze); }
}

function list(label, arr) {
  return arr && arr.length ? `<div class="np-label" style="margin-top:12px">${label}</div><ul>${arr.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : '';
}

function renderMain() {
  if (!current) { $('docMain').innerHTML = emptyState('No documents yet.', 'अभी कोई दस्तावेज़ नहीं।', 'Upload a court order, notice or supporting document.', 'कोर्ट आदेश, नोटिस या सहायक दस्तावेज़ अपलोड करें।'); return; }
  const d = current, unreadable = ['FAILED', 'OCR_REQUIRED'].includes(d.status) || !text;
  $('docMain').innerHTML = `<div class="np-split">
    <div><h3 class="np-h">${t('Document preview', 'दस्तावेज़ पूर्वावलोकन')}</h3>
      <div class="np-paper" style="max-height:640px;overflow:auto"><div class="np-label">${esc(d.original_filename)} ${d.page_count ? '· ' + d.page_count + ' ' + t('pages', 'पृष्ठ') : ''} ${d.ocr_performed ? '· OCR' : ''}</div>
      ${text ? `<div class="np-doc-text">${esc(text)}</div>` : `<p>${t('No readable text could be extracted from this document.', 'इस दस्तावेज़ से पढ़ने योग्य पाठ नहीं निकाला जा सका।')}</p>`}</div>
      <div class="np-row np-noprint" style="margin-top:10px"><button class="btn btn-secondary btn-sm" id="dl">${t('Get download link', 'डाउनलोड लिंक पाएं')}</button>
      ${unreadable ? `<button class="btn btn-secondary btn-sm" id="reproc">${t('Try reading again', 'फिर से पढ़ने का प्रयास')}</button>` : ''}<button class="btn btn-ghost btn-sm" id="del">${t('Delete', 'हटाएं')}</button></div></div>
    <div id="aiPane"><h3 class="np-h">${t('AI explanation', 'AI व्याख्या')}</h3>${analysis ? aiHTML() : `<div class="np-ai-box"><p>${unreadable ? t('We could not read text from this document yet.', 'हम अभी इस दस्तावेज़ से पाठ नहीं पढ़ सके।') : t('Get a simple summary of this document.', 'इस दस्तावेज़ का सरल सार पाएं।')}</p>${unreadable ? '' : `<button class="btn btn-primary btn-sm" id="anaBtn" style="margin-top:8px">${t('Analyze Document', 'दस्तावेज़ का विश्लेषण करें')}</button>`}</div>`}
      ${askHTML()}</div></div>`;
  $('anaBtn') && ($('anaBtn').onclick = analyze);
  $('dl').onclick = async () => { try { const r = await Documents.downloadLink(d.id); window.open(r.url, '_blank', 'noopener'); } catch (e) { showToast(friendlyMessage(e), 'error'); } };
  $('reproc') && ($('reproc').onclick = async () => { try { current = await Documents.reprocess(d.id); openDoc(d.id); } catch (e) { showToast(friendlyMessage(e), 'error'); } });
  $('del').onclick = async () => { if (!confirm(t('Delete this document permanently?', 'इस दस्तावेज़ को स्थायी रूप से हटाएं?'))) return;
    try { await Documents.remove(d.id); docs = docs.filter(x => x.id !== d.id); current = null; renderList(); renderMain(); } catch (e) { showToast(friendlyMessage(e), 'error'); } };
  wireAsk();
}

function aiHTML() {
  const a = analysis;
  return `<div class="np-ai-box"><div class="np-ai-tag">${t('Document summary', 'दस्तावेज़ सार')}</div>
    <div class="np-kv"><b>${t('Document type', 'दस्तावेज़ प्रकार')}</b>${esc(a.document_type || t('Not identified', 'पहचाना नहीं गया'))}</div>
    <p style="margin-top:8px">${esc(a.plain_summary)}</p>
    ${list(t('Important parties', 'महत्वपूर्ण पक्षकार'), a.parties)}${list(t('Key points', 'मुख्य बिंदु'), a.key_facts)}${list(t('Important dates', 'महत्वपूर्ण तिथियाँ'), a.important_dates)}
    ${a.degraded ? `<div class="demo-notice" style="margin-top:8px">${t('AI analysis was unavailable; showing the start of the document text.', 'AI विश्लेषण उपलब्ध नहीं था; दस्तावेज़ का आरंभिक पाठ दिखाया गया है।')}</div>` : ''}
    <p class="np-muted" style="margin-top:8px">${esc(a.note || '')}</p></div>`;
}

function askHTML() {
  const sug = (analysis?.suggested_questions?.length ? analysis.suggested_questions : [
    t('What did the court decide?', 'न्यायालय ने क्या निर्णय लिया?'), t('When is the next hearing?', 'अगली सुनवाई कब है?'),
    t('What documents were requested?', 'कौन से दस्तावेज़ माँगे गए?'), t('Explain this in Hindi.', 'इसे हिंदी में समझाएं।')]).slice(0, 4);
  return `<h3 class="np-h" style="margin-top:24px">${t('Ask this document', 'इस दस्तावेज़ से पूछें')}</h3>
    <div class="np-chip-row">${sug.map(s => `<button class="np-chip" data-q="${esc(s)}">${esc(s)}</button>`).join('')}</div>
    <div class="np-row"><input id="askIn" class="form-input" style="flex:1;min-width:200px" maxlength="500" aria-label="${t('Your question', 'आपका प्रश्न')}" placeholder="${t('Type a question about this document…', 'इस दस्तावेज़ के बारे में प्रश्न लिखें…')}"/><button class="btn btn-primary" id="askBtn">${t('Ask', 'पूछें')}</button></div>
    <div class="np-qa" id="qa" aria-live="polite">${qa.map(qaHTML).join('')}</div>`;
}
function qaHTML(x) {
  if (x.loading) return `<div class="np-q">${esc(x.q)}</div><div class="np-a">${loadingState('Searching your document...', 'आपके दस्तावेज़ में खोजा जा रहा है...')}</div>`;
  if (x.err) return `<div class="np-q">${esc(x.q)}</div><div class="np-a">${esc(x.err)}</div>`;
  return `<div class="np-q">${esc(x.q)}</div><div class="np-a"><p>${esc(x.a.answer)}</p>
    ${(x.a.unknowns || []).length ? `<p class="np-muted">${t('Not found in the document', 'दस्तावेज़ में नहीं मिला')}: ${x.a.unknowns.map(esc).join('; ')}</p>` : ''}
    ${(x.a.sources || []).slice(0, 3).map(s => sourceCard({ ...s, title: s.title || x.a.document?.filename, source_type: 'USER_DOCUMENT' }, lang)).join('<div style="height:8px"></div>')}
    <p class="np-muted" style="margin-top:6px">${esc(x.a.notice || '')}</p></div>`;
}
function wireAsk() {
  const go = async (question) => {
    question = (question || $('askIn').value).trim(); if (question.length < 3) return;
    const item = { q: question, loading: true }; qa.push(item); $('askIn').value = ''; $('qa').innerHTML = qa.map(qaHTML).join('');
    try { item.a = await Documents.ask(current.id, question, lang); } catch (e) { item.err = friendlyMessage(e); }
    item.loading = false; $('qa').innerHTML = qa.map(qaHTML).join('');
  };
  $('askBtn').onclick = () => go();
  $('askIn').onkeydown = (e) => { if (e.key === 'Enter') go(); };
  document.querySelectorAll('[data-q]').forEach(b => b.onclick = () => go(b.dataset.q));
}

// upload wiring
const drop = $('drop'), file = $('file');
$('pick').onclick = (e) => { e.stopPropagation(); file.click(); };
drop.onclick = () => file.click();
drop.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); file.click(); } };
file.onchange = () => file.files[0] && upload(file.files[0]);
['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('drag'); }));
['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove('drag'); }));
drop.addEventListener('drop', (e) => e.dataTransfer.files[0] && upload(e.dataTransfer.files[0]));

loadList();
if (window.matchMedia('(max-width: 860px)').matches) document.getElementById('docLayout').style.gridTemplateColumns = '1fr';

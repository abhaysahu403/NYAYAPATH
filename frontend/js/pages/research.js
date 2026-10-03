import { Judgments, AI, Core } from '../api/endpoints.js';
import { friendlyMessage } from '../api/client.js';
import { initShell, loadingState, emptyState, errorState, sourceCard, verifyBadge, whyBox, pager } from '../components/shell.js';
import { esc, formatDate, topicLabel, qs, showToast } from '../utils/helpers.js';

let lang = initShell('research', (l) => { lang = l; rerender(); });
let last = { results: [], meta: null }, body = null;
const $ = (id) => document.getElementById(id);
const t = (en, hi) => (lang === 'hi' ? hi : en);

// topics from backend
Core.legalTopics().then((topics) => {
  $('fTopic').insertAdjacentHTML('beforeend', topics.map(x => `<option value="${esc(x.code)}">${esc(topicLabel(x.code, lang) !== x.code ? topicLabel(x.code, lang) : x.label)}</option>`).join(''));
  if (qs('topic')) $('fTopic').value = qs('topic');
}).catch(() => {});

if (qs('q')) $('q').value = qs('q');

function filters() {
  const v = (id) => $(id).value.trim();
  const b = { query: v('q') };
  if (v('fTopic')) b.topic = v('fTopic');
  if (v('fState')) b.state = v('fState');
  if (v('fCourt')) b.court = v('fCourt');
  if (v('fDistrict')) b.district = v('fDistrict');
  if (v('fFrom')) b.date_from = v('fFrom');
  if (v('fTo')) b.date_to = v('fTo');
  if (v('fSource')) b.source_type = v('fSource');
  return b;
}

async function run(page = 1) {
  const b = filters();
  if (b.query.length < 2) { showToast(t('Please type at least two characters.', 'कृपया कम से कम दो अक्षर लिखें।'), 'error'); return; }
  body = b;
  $('results').innerHTML = loadingState('Finding relevant legal sources...', 'प्रासंगिक कानूनी स्रोत खोजे जा रहे हैं...');
  try {
    const res = await Judgments.search(b, { page, pageSize: 10 });
    last = { results: res, meta: res.meta };
    rerender();
  } catch (e) {
    $('results').innerHTML = errorState(friendlyMessage(e), () => run(page));
  }
}

function card(r) {
  const open = r.judgment_id
    ? `<a class="btn btn-primary btn-sm" href="judgment.html?id=${encodeURIComponent(r.judgment_id)}" data-en="Read Case" data-hi="केस पढ़ें">${t('Read Case', 'केस पढ़ें')}</a>
       <button class="btn btn-secondary btn-sm" data-explain="${esc(r.judgment_id)}">${t('Explain This Case', 'इस केस को समझाएं')}</button>` : '';
  return `<article class="np-case-card">
    <div class="np-between"><div class="np-case-title">${esc(r.title)}</div>${verifyBadge(r.verification_status, r.is_demo_data, lang)}</div>
    <div class="np-meta-line">${[r.court, r.date ? formatDate(r.date, lang) : null, r.citation, r.source_type].filter(Boolean).map(x => `<span>${esc(x)}</span>`).join('')}</div>
    ${r.snippet ? `<p class="np-snippet">${esc(r.snippet)}…</p>` : ''}
    <div class="np-row" style="margin-top:8px">${r.relevance_label ? `<span class="badge badge-gold" title="${t('Search relevance, not legal similarity', 'खोज प्रासंगिकता, कानूनी समानता नहीं')}">${t('Search relevance', 'खोज प्रासंगिकता')}: ${esc(r.relevance_label)}</span>` : ''}</div>
    ${whyBox(r.relevance_reason, lang)}
    <div class="np-row" style="margin-top:12px">${open}</div>
    <div style="margin-top:12px">${sourceCard({ ...r, source_url: r.source_url }, lang)}</div></article>`;
}

function rerender() {
  if (!body) return;
  const { results, meta } = last;
  if (!results.length) {
    $('results').innerHTML = emptyState('No matching case was found in the available records.', 'उपलब्ध रिकॉर्ड में कोई मेल खाता केस नहीं मिला।', 'Try different words or remove some filters.', 'अलग शब्द आज़माएँ या कुछ फ़िल्टर हटाएँ।');
    return;
  }
  const total = meta?.pagination?.count ?? results.length;
  $('results').innerHTML = `<p class="np-muted">${total} ${t('results', 'परिणाम')} · ${esc(meta?.data_freshness || '')}</p>
    <div class="np-grid">${results.map(card).join('')}</div>${pager(meta, run)}`;
  document.querySelectorAll('[data-explain]').forEach(b => b.addEventListener('click', () => explain(b.dataset.explain)));
}

async function explain(id) {
  $('explainModal').classList.add('open');
  $('exBody').innerHTML = loadingState('Reading the judgment...', 'निर्णय पढ़ा जा रहा है...');
  try {
    const r = await AI.explainJudgment(id, { language: lang, question: body?.query || '' });
    const e = r.explanation;
    $('exBody').innerHTML = `<div class="np-paper" style="margin-top:12px">
      <div class="np-label">${esc(r.judgment.title)}</div>
      <p>${esc(e.plain_summary)}</p>
      ${e.legal_issue ? `<div class="np-label" style="margin-top:12px">${t('Key issue', 'मुख्य मुद्दा')}</div><p>${esc(e.legal_issue)}</p>` : ''}
      ${e.outcome ? `<div class="np-label" style="margin-top:12px">${t('Outcome', 'परिणाम')}</div><p>${esc(e.outcome)}</p>` : ''}
    </div><div class="np-disclaimer">${esc(r.note)}</div>
    ${(r.warnings || []).map(w => `<div class="demo-notice">${esc(w.detail)}</div>`).join('')}
    <a class="btn btn-primary btn-sm" href="judgment.html?id=${encodeURIComponent(id)}">${t('Read Full Case', 'पूरा केस पढ़ें')}</a>`;
  } catch (e) { $('exBody').innerHTML = errorState(friendlyMessage(e), () => explain(id)); }
}
window.closeExplain = () => $('explainModal').classList.remove('open');

$('searchForm').addEventListener('submit', (e) => { e.preventDefault(); run(1); });

// Recent judgments (browse endpoint)
(async function recent() {
  try {
    const list = await Judgments.list({ page_size: 6 });
    $('recent').innerHTML = list.length ? list.map(j => `<article class="np-case-card">
      <div class="np-case-title">${esc(j.title)}</div>
      <div class="np-meta-line">${[j.court_name, j.judgment_date ? formatDate(j.judgment_date, lang) : null, j.citation].filter(Boolean).map(x => `<span>${esc(x)}</span>`).join('')}</div>
      <div class="np-row">${verifyBadge(j.verification_status, j.is_demo_data, lang)}<a href="judgment.html?id=${encodeURIComponent(j.id)}" class="source-card">${t('Read Case', 'केस पढ़ें')} →</a></div></article>`).join('')
      : emptyState('No judgments stored yet.', 'अभी कोई निर्णय संग्रहीत नहीं है।', 'Ask your administrator to load judgments.', 'प्रशासक से निर्णय लोड करने को कहें।');
  } catch (e) { $('recent').innerHTML = errorState(friendlyMessage(e), recent); }
})();

if (qs('q') || qs('topic')) { if (!$('q').value) $('q').value = qs('topic') ? topicLabel(qs('topic'), lang) : ''; if ($('q').value) run(1); }

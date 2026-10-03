import { Judgments, AI } from '../api/endpoints.js';
import { friendlyMessage } from '../api/client.js';
import { initShell, loadingState, errorState, sourceCard, verifyBadge } from '../components/shell.js';
import { esc, formatDate, topicLabel, qs, isSafeUrl } from '../utils/helpers.js';

let lang = initShell('research', (l) => { lang = l; if (J) render(); });
const root = document.getElementById('jRoot');
const t = (en, hi) => (lang === 'hi' ? hi : en);
let J = null, EXP = {};
const id = qs('id');

async function load() {
  if (!id) { root.innerHTML = errorState(t('No judgment was selected.', 'कोई निर्णय चुना नहीं गया।')); return; }
  root.innerHTML = loadingState('Opening the judgment...', 'निर्णय खोला जा रहा है...');
  try { J = await Judgments.get(id); render(); if (qs('explain')) explain(); }
  catch (e) { root.innerHTML = errorState(friendlyMessage(e), load); }
}

function render() {
  const j = J;
  const court = j.court_detail?.name;
  root.innerHTML = `
  <div class="np-paper" style="margin-bottom:20px">
    <div class="np-between"><div><div class="np-label">${t('JUDGMENT', 'निर्णय')}</div><h1 style="font-size:clamp(1.5rem,3vw,2.2rem);color:#211D19">${esc(j.title)}</h1></div>
      <div>${verifyBadge(j.verification_status, j.is_demo_data, lang)}</div></div>
    <div class="np-meta-line" style="color:#655B50;margin-top:10px">${[court, j.judgment_date ? formatDate(j.judgment_date, lang) : null, j.citation, j.case_number, j.state].filter(Boolean).map(x => `<span>${esc(x)}</span>`).join('')}</div>
    ${j.bench ? `<p><b>${t('Bench', 'पीठ')}:</b> ${esc(j.bench)}</p>` : ''}
    ${(j.petitioner || j.respondent) ? `<p><b>${t('Parties', 'पक्षकार')}:</b> ${esc(j.petitioner || '—')} <i>v.</i> ${esc(j.respondent || '—')}</p>` : ''}
    ${(j.legal_topics || []).length ? `<div class="np-row" style="margin-top:8px">${j.legal_topics.map(x => `<span class="badge badge-gold">${esc(topicLabel(x, lang))}</span>`).join('')}</div>` : ''}
    ${j.is_demo_data ? `<div class="demo-notice" style="margin-top:12px">${t('Demo / Sample Data — not a real judgment.', 'डेमो / नमूना डेटा — वास्तविक निर्णय नहीं।')}</div>` : ''}
  </div>

  <div class="np-grid cols-2" style="align-items:start">
    <section>
      <h2 class="np-h">${t('Original Judgment Record', 'मूल निर्णय रिकॉर्ड')}</h2>
      <div class="np-paper">
        <div class="np-label">${t('Summary on record', 'रिकॉर्ड में सार')}</div>
        <p class="np-doc-text">${esc(j.summary || t('No summary is stored for this judgment.', 'इस निर्णय के लिए कोई सार संग्रहीत नहीं है।'))}</p>
      </div>
      <div style="margin-top:16px">${sourceCard({ title: j.title, court, citation: j.citation, date: j.judgment_date, source_type: 'JUDGMENT', verification_status: j.verification_status, is_demo_data: j.is_demo_data, source_url: isSafeUrl(j.source_url) ? j.source_url : null }, lang)}</div>
      ${isSafeUrl(j.source_url) ? `<a class="btn btn-primary" style="margin-top:12px" target="_blank" rel="noopener noreferrer" href="${esc(j.source_url)}">${t('Open Original Source', 'मूल स्रोत खोलें')}</a>` : ''}
    </section>
    <section>
      <h2 class="np-h">${t('Explain in simple language', 'सरल भाषा में समझें')}</h2>
      <div class="np-ai-box">
        <div class="np-ai-tag">${t('AI explanation — separate from the original text', 'AI व्याख्या — मूल पाठ से अलग')}</div>
        <p class="np-muted">${t('Built only from the stored judgment text. Read the original before relying on it.', 'केवल संग्रहीत निर्णय पाठ से बनी है। भरोसा करने से पहले मूल पढ़ें।')}</p>
        <div class="np-row" style="margin-top:10px"><button class="btn btn-primary btn-sm" id="exEn">${t('In Simple English', 'सरल English में')}</button><button class="btn btn-secondary btn-sm" id="exHi">सरल हिंदी में</button></div>
      </div>
      <div id="exOut" style="margin-top:16px"></div>
    </section>
  </div>`;
  document.getElementById('exEn').onclick = () => explain('en');
  document.getElementById('exHi').onclick = () => explain('hi');
  showExp();
}

function showExp() {
  const out = document.getElementById('exOut');
  if (!out) return;
  const parts = Object.entries(EXP).map(([lg, r]) => {
    const e = r.explanation, hi = lg === 'hi';
    const sec = (lbl, txt) => txt ? `<div class="np-label" style="margin-top:12px">${lbl}</div><p>${esc(txt)}</p>` : '';
    return `<div class="np-paper" style="margin-bottom:16px"><div class="np-label">${hi ? 'सरल हिंदी में' : 'In Simple English'}</div>
      <p>${esc(e.plain_summary)}</p>${sec(hi ? 'मुख्य मुद्दा' : 'Key issue', e.legal_issue)}${sec(hi ? 'न्यायालय ने क्या विचार किया' : 'What the court considered', e.court_reasoning)}${sec(hi ? 'निर्णय / परिणाम' : 'Decision / outcome', e.outcome)}
      ${(e.key_facts || []).length ? `<div class="np-label" style="margin-top:12px">${hi ? 'महत्वपूर्ण बिंदु' : 'Important points'}</div><ul>${e.key_facts.map(f => `<li>${esc(f)}</li>`).join('')}</ul>` : ''}
      <div class="np-label" style="margin-top:12px">${hi ? 'स्रोत' : 'Source'}</div><p class="np-muted" style="color:#655B50">${(r.grounding || []).map(g => esc(g.locator || g.label)).join(', ') || '—'}</p>
      ${r.is_degraded ? `<div class="demo-notice">${t('The AI explanation was unavailable; the stored summary is shown instead.', 'AI व्याख्या उपलब्ध नहीं थी; संग्रहीत सार दिखाया गया है।')}</div>` : ''}
    </div>${(r.warnings || []).map(w => `<div class="np-disclaimer">${esc(w.detail)}</div>`).join('')}<div class="np-disclaimer">${esc(r.note || '')}</div>`;
  });
  out.innerHTML = parts.join('');
}

async function explain(lg = lang) {
  const out = document.getElementById('exOut');
  out.innerHTML = loadingState('Reading the judgment...', 'निर्णय पढ़ा जा रहा है...');
  try { EXP[lg] = await AI.explainJudgment(id, { language: lg }); showExp(); }
  catch (e) { out.innerHTML = errorState(friendlyMessage(e), () => explain(lg)); }
}

load();

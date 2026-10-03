/**
 * The NyayaPath Result screen — the centerpiece. Built only from what the backend returned for the
 * citizen's own message (ai/chat + ai/similar-cases). Nothing here is invented: missing facts show as "not stated".
 */
import { initShell, emptyState, sourceCard, whyBox, disclaimerBanner, verifyBadge } from '../components/shell.js';
import { esc, topicLabel, formatDate, ssGet } from '../utils/helpers.js';

let lang = initShell('ask', () => { lang = initLang(); render(); });
function initLang() { try { return localStorage.getItem('nyayapath_lang') || 'en'; } catch (_) { return 'en'; } }
const root = document.getElementById('resultRoot');
const t = (en, hi) => (lang === 'hi' ? hi : en);
const store = ssGet('nyayapath_chat');

// Plain-language explanations of common status words (UI help text, not legal data)
const EXPLAIN = {
  pending: ['“Pending” means the case has not been marked as disposed in the available record. It does not by itself explain why the case has been delayed.',
            '“लंबित” का अर्थ है कि उपलब्ध रिकॉर्ड में केस को निपटाया हुआ चिह्नित नहीं किया गया है। यह अपने आप में देरी का कारण नहीं बताता।'],
  age: ['This is the time since the case was filed, as stated by you or found in the record. Long duration alone does not tell you what stage the case is at.',
        'यह केस दाखिल होने के बाद का समय है, जैसा आपने बताया या रिकॉर्ड में मिला। केवल लंबी अवधि से यह पता नहीं चलता कि केस किस चरण में है।'],
  stage: ['The stage describes where the case is in court procedure (for example evidence or hearing). It was not stated, so we do not guess.',
          'चरण बताता है कि केस न्यायालय प्रक्रिया में कहाँ है (जैसे साक्ष्य या सुनवाई)। यह नहीं बताया गया, इसलिए हम अनुमान नहीं लगाते।'],
};

function explainBtn(key) {
  return `<button class="np-link-btn" data-explain="${key}">${t('Explain this', 'इसे समझाएं')}</button><div class="np-explain-pop" id="ex-${key}" hidden>${esc(EXPLAIN[key][lang === 'hi' ? 1 : 0])}</div>`;
}

function render() {
  if (!store?.chat) {
    root.innerHTML = emptyState('Your case workspace is empty.', 'आपका केस वर्कस्पेस खाली है।', 'Start by describing your legal problem.', 'अपनी कानूनी समस्या बताकर शुरू करें।', 'ask.html', 'Tell NyayaPath what happened', 'NyayaPath को बताएं क्या हुआ');
    return;
  }
  const c = store.chat, ent = c.entities || {}, sim = store.similar;
  const topic = topicLabel(c.detected_intent, lang);
  const place = [ent.district, ent.state].filter(Boolean).join(', ');
  const ref = (c.case_references || [])[0];
  const years = ent.case_age_years;
  const status = ref?.status ? ref.status : (ent.existing_case ? 'PENDING_STATED' : null);
  const longPending = (years && years >= 3) || (ent.issue_flags || []).some(f => /DELAY|PENDING/i.test(f));

  const judgments = (c.judgment_references || []).length ? c.judgment_references : (sim?.results || []);
  const provisions = (c.sources || []).filter(s => ['GOVERNMENT', 'LEGAL_INFORMATION'].includes(s.source_type));
  const docs = ent.documents || [];
  const steps = c.next_steps || [];
  const allSources = [...(c.sources || [])];
  const hasDemo = allSources.some(s => s.is_demo_data) || (c.warnings || []).some(w => w.code === 'DEMO_DATA');

  root.innerHTML = `
  <section class="np-result-hero">
    <div class="np-eyebrow">${t('YOUR LEGAL PATH', 'आपका कानूनी मार्ग')}</div>
    <h1 style="margin:10px 0 4px">${esc(topic)}</h1>
    <p style="color:var(--text-secondary)">${esc(place || t('Location not stated', 'स्थान नहीं बताया गया'))}</p>
    <p class="np-muted" style="margin-top:10px">“${esc(store.message || '')}”</p>
    <div class="np-stats">
      <div class="np-stat"><small>${t('Case status', 'केस की स्थिति')}</small><strong>${status === 'PENDING' || status === 'PENDING_STATED' ? t('Pending', 'लंबित') : status ? esc(status) : '—'}</strong>
        <span class="np-muted">${status === 'PENDING_STATED' ? t('as stated by you', 'आपके अनुसार') : ref ? t('from case record', 'केस रिकॉर्ड से') : t('not stated', 'नहीं बताया')}</span><br>${status ? explainBtn('pending') : ''}</div>
      <div class="np-stat"><small>${t('Case age', 'केस की आयु')}</small><strong>${years ? years + ' ' + t('yrs', 'वर्ष') : '—'}</strong><span class="np-muted">${years ? t('as stated by you', 'आपके अनुसार') : t('not stated', 'नहीं बताया')}</span><br>${years ? explainBtn('age') : ''}</div>
      <div class="np-stat"><small>${t('Current stage', 'वर्तमान चरण')}</small><strong style="font-size:1.2rem">${esc(ref?.title ? t('See case record', 'केस रिकॉर्ड देखें') : t('Not stated', 'नहीं बताया'))}</strong><span class="np-muted">${t('we do not guess', 'हम अनुमान नहीं लगाते')}</span><br>${explainBtn('stage')}</div>
    </div>
    ${hasDemo ? `<div class="demo-notice">${t('Demo / Sample Data: some sources shown are for development and are not real legal authority.', 'डेमो / नमूना डेटा: दिखाए गए कुछ स्रोत विकास हेतु हैं और वास्तविक कानूनी प्राधिकार नहीं हैं।')}</div>` : ''}
  </section>

  <h2 class="np-h">${t('What we found', 'हमें क्या मिला')}</h2>
  <div class="np-found">
    <div><b>${judgments.length}</b>${t('Relevant judgments', 'प्रासंगिक निर्णय')}</div>
    <div><b>${provisions.length}</b>${t('Legal provisions / information sources', 'कानूनी प्रावधान / जानकारी स्रोत')}</div>
    <div><b>${docs.length}</b>${t('Documents mentioned', 'उल्लिखित दस्तावेज़')}</div>
    <div><b>${longPending ? t('Yes', 'हाँ') : '—'}</b>${t('Long-pending case', 'लंबे समय से लंबित केस')}</div>
  </div>
  ${c.answer ? `<div class="np-paper" style="margin-top:20px"><div class="np-label">${t('Explanation', 'व्याख्या')} · <span style="color:#655B50">${t('AI-written, based on the sources below', 'AI द्वारा लिखित, नीचे दिए स्रोतों पर आधारित')}</span></div><p>${esc(c.answer)}</p>
    ${(c.unknowns || []).length ? `<div class="np-label" style="margin-top:10px">${t('Could not be determined', 'निर्धारित नहीं हो सका')}</div><ul>${c.unknowns.map(u => `<li>${esc(u)}</li>`).join('')}</ul>` : ''}</div>` : ''}
  ${(c.follow_up_questions || []).length ? `<div class="np-ai-box" style="margin-top:16px"><div class="np-ai-tag">${t('To help further, it would be useful to know', 'आगे मदद के लिए यह जानना उपयोगी होगा')}</div><ul>${c.follow_up_questions.map(q => `<li>${esc(typeof q === 'string' ? q : (q.question || q.text || ''))}</li>`).join('')}</ul><a class="btn btn-secondary btn-sm" href="ask.html">${t('Add details', 'विवरण जोड़ें')}</a></div>` : ''}

  <hr class="np-divider"/>
  <h2 class="np-h">${t('Cases relevant to your problem', 'आपकी समस्या से संबंधित केस')}</h2>
  ${judgments.length ? `<div class="np-grid cols-2">${judgments.slice(0, 6).map(j => `<article class="np-case-card">
      <div class="np-between"><div class="np-case-title">${esc(j.title)}</div>${verifyBadge(j.verification_status, j.is_demo_data, lang)}</div>
      <div class="np-meta-line">${[j.court, j.date ? formatDate(j.date, lang) : null, j.citation].filter(Boolean).map(x => `<span>${esc(x)}</span>`).join('')}</div>
      ${whyBox(j.relevance_reason || (j.relevance_label ? t('Matched your search by meaning and keywords (search relevance: ', 'आपकी खोज से अर्थ और शब्दों के आधार पर मेल खाया (खोज प्रासंगिकता: ') + j.relevance_label + ')' : ''), lang)}
      <div class="np-row" style="margin-top:12px">${j.judgment_id ? `<a class="btn btn-primary btn-sm" href="judgment.html?id=${encodeURIComponent(j.judgment_id)}">${t('Read Case', 'केस पढ़ें')}</a>
        <a class="btn btn-secondary btn-sm" href="judgment.html?id=${encodeURIComponent(j.judgment_id)}&explain=1">${t('Explain This Case', 'इस केस को समझाएं')}</a>` : ''}
        ${j.source_url ? `<a class="source-card" href="${esc(j.source_url)}" target="_blank" rel="noopener noreferrer">⚖ ${t('Original source', 'मूल स्रोत')} →</a>` : ''}</div></article>`).join('')}</div>`
    : `<p class="np-muted">${t('No matching case was found in the available records.', 'उपलब्ध रिकॉर्ड में कोई मेल खाता केस नहीं मिला।')}</p>`}
  <a class="btn btn-ghost btn-sm" style="margin-top:12px" href="research.html">${t('Search more legal information', 'और कानूनी जानकारी खोजें')} →</a>

  ${provisions.length ? `<hr class="np-divider"/><h2 class="np-h">${t('Laws & policies that may be relevant', 'संभावित रूप से प्रासंगिक कानून और नीतियाँ')}</h2>
    <div class="np-grid cols-2">${provisions.map(s => `<div>${sourceCard(s, lang)}${whyBox(s.relevance_reason, lang)}</div>`).join('')}</div>` : ''}

  <hr class="np-divider"/>
  <h2 class="np-h">${t('Your possible next steps', 'आपके संभावित अगले कदम')}</h2>
  ${steps.length ? `<div class="np-stepper">${steps.map((s, i) => `<div class="np-step"><div class="np-step-num">${String(i + 1).padStart(2, '0')}</div><div class="np-step-body">
    <div class="np-step-title">${esc(s.title)}</div><p>${esc(s.detail)}</p>
    <span class="badge ${s.source_backed ? 'badge-disposed' : 'badge-pending'}">${s.source_backed ? t('Source-backed', 'स्रोत-आधारित') : t('General suggestion', 'सामान्य सुझाव')}</span></div></div>`).join('')}</div>`
    : `<p class="np-muted">${t('Add a few more details to see possible next steps.', 'संभावित अगले कदम देखने के लिए कुछ और विवरण जोड़ें।')}</p>`}
  <a class="btn btn-primary" href="action-plan.html?auto=1">${t('View Complete Action Plan', 'पूरी कार्य योजना देखें')}</a>

  <hr class="np-divider"/>
  <h2 class="np-h">${t('Documents you can prepare', 'आप ये दस्तावेज़ तैयार कर सकते हैं')}</h2>
  <div class="np-row"><a class="btn btn-secondary" href="drafts.html">${t('Case Summary', 'केस सार')}</a><a class="btn btn-secondary" href="drafts.html">${t('Information Request', 'सूचना अनुरोध')}</a><a class="btn btn-secondary" href="drafts.html">${t('Lawyer Brief', 'वकील संक्षेप')}</a><a class="btn btn-ghost" href="documents.html">${t('Upload a court order', 'कोर्ट आदेश अपलोड करें')}</a></div>

  <hr class="np-divider"/>
  <div class="np-between"><strong>${t('Sources', 'स्रोत')}: ${allSources.length} ${t('references', 'संदर्भ')}</strong><span class="np-muted">${c.verification_status ? esc(c.verification_status) : ''}</span></div>
  <details style="margin-top:10px"><summary class="np-link-btn">${t('Show all sources', 'सभी स्रोत दिखाएं')}</summary><div class="np-grid cols-2" style="margin-top:12px">${allSources.map(s => sourceCard(s, lang)).join('') || `<p class="np-muted">${t('No source was used for this answer.', 'इस उत्तर के लिए कोई स्रोत उपयोग नहीं हुआ।')}</p>`}</div></details>
  ${(c.warnings || []).filter(w => w.code !== 'DEMO_DATA').map(w => `<div class="np-disclaimer">${esc(w.detail)}</div>`).join('')}
  ${disclaimerBanner(lang)}${c.disclaimer ? `<p class="np-muted">${esc(c.disclaimer)}</p>` : ''}`;

  root.querySelectorAll('[data-explain]').forEach(b => b.addEventListener('click', () => { const el = document.getElementById('ex-' + b.dataset.explain); el.hidden = !el.hidden; }));
}
render();

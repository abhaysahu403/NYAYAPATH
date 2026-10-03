import { Drafts, Cases } from '../api/endpoints.js';
import { friendlyMessage } from '../api/client.js';
import { initShell, loadingState, errorState, sourceCard, disclaimerBanner } from '../components/shell.js';
import { esc, formatDate, ssGet, showToast } from '../utils/helpers.js';

let lang = initShell('drafts', (l) => { lang = l; cards(); history(); shown && preview(shown); });
const $ = (id) => document.getElementById(id);
const t = (en, hi) => (lang === 'hi' ? hi : en);
let userCases = [], shown = null, lastReq = null, type = null;
const ctx = ssGet('nyayapath_context');

const TYPES = {
  summary: { fn: 'caseSummary', en: 'Case Summary', hi: 'केस सार', dEn: 'Create a concise summary of your case.', dHi: 'अपने केस का संक्षिप्त सार बनाएं।', extra: [] },
  brief: { fn: 'lawyerBrief', en: 'Lawyer Consultation Brief', hi: 'वकील परामर्श संक्षेप', dEn: 'Organize your facts, timeline, documents and questions for a lawyer.', dHi: 'वकील के लिए अपने तथ्य, समयरेखा, दस्तावेज़ और प्रश्न व्यवस्थित करें।',
    extra: [['lawyerName', 'Lawyer name (optional)', 'वकील का नाम (वैकल्पिक)'], ['courtName', 'Court name (optional)', 'न्यायालय का नाम (वैकल्पिक)']] },
  rti: { fn: 'rti', en: 'Information / RTI Request', hi: 'सूचना / RTI अनुरोध', dEn: 'Generate a reviewable information-request draft based on your information.', dHi: 'आपकी जानकारी पर आधारित समीक्षा योग्य सूचना-अनुरोध का मसौदा बनाएं।',
    extra: [['applicantName', 'Your name (optional)', 'आपका नाम (वैकल्पिक)'], ['publicAuthority', 'Public authority / office (optional)', 'लोक प्राधिकरण / कार्यालय (वैकल्पिक)'], ['informationSought', 'What information do you want? (optional)', 'आप कौन सी जानकारी चाहते हैं? (वैकल्पिक)']] },
};

function cards() {
  $('draftCards').innerHTML = Object.entries(TYPES).map(([k, v]) => `<div class="action-card" style="cursor:pointer"><div class="action-card-title">${lang === 'hi' ? v.hi : v.en}</div>
    <div class="action-card-desc">${lang === 'hi' ? v.dHi : v.dEn}</div><button class="btn btn-primary btn-sm" data-type="${k}" style="margin-top:12px">${t('Create Draft', 'मसौदा बनाएं')} →</button></div>`).join('') +
    `<div class="action-card" style="opacity:.6"><div class="action-card-title">${t('Other Application', 'अन्य आवेदन')}</div><div class="action-card-desc">${t('Not yet supported by the backend. It can be connected here later.', 'बैकएंड द्वारा अभी समर्थित नहीं। इसे बाद में यहाँ जोड़ा जा सकता है।')}</div><span class="badge badge-gold" style="margin-top:12px">${t('Coming later', 'जल्द आ रहा है')}</span></div>`;
  document.querySelectorAll('[data-type]').forEach(b => b.onclick = () => openModal(b.dataset.type));
}

function openModal(k) {
  type = k; const v = TYPES[k];
  $('dmTitle').textContent = lang === 'hi' ? v.hi : v.en;
  $('dmForm').innerHTML = `<label class="form-label" for="dmMsg">${t('Describe your situation', 'अपनी स्थिति बताएं')}</label>
    <textarea id="dmMsg" class="form-textarea" rows="4">${esc(ctx?.message || '')}</textarea>
    ${userCases.length ? `<label class="form-label" for="dmCase" style="margin-top:10px">${t('Link to a saved case (optional)', 'सहेजे गए केस से जोड़ें (वैकल्पिक)')}</label><select id="dmCase" class="form-select"><option value="">—</option>${userCases.map(c => `<option value="${c.id}">${esc(c.case_title || c.case_number || c.cnr_number || c.id.slice(0, 8))}</option>`).join('')}</select>` : ''}
    ${v.extra.map(([id, en, hi]) => `<label class="form-label" style="margin-top:10px" for="dm_${id}">${lang === 'hi' ? hi : en}</label><input id="dm_${id}" class="form-input"/>`).join('')}`;
  $('draftModal').classList.add('open'); $('dmMsg').focus();
}
window.closeDraftModal = () => $('draftModal').classList.remove('open');

async function create() {
  const v = TYPES[type], msg = $('dmMsg').value.trim();
  if (msg.length < 5) { showToast(t('Please describe your situation.', 'कृपया अपनी स्थिति बताएं।'), 'error'); return; }
  const req = { message: msg, language: lang, caseId: $('dmCase')?.value || null };
  v.extra.forEach(([id]) => { req[id] = $('dm_' + id).value.trim(); });
  lastReq = { type, req }; closeDraftModal();
  $('draftOut').innerHTML = loadingState('Preparing your draft from available information...', 'उपलब्ध जानकारी से आपका मसौदा तैयार हो रहा है...');
  $('draftOut').scrollIntoView({ behavior: 'smooth' });
  try { shown = await Drafts[v.fn](req); preview(shown); history(); }
  catch (e) { $('draftOut').innerHTML = errorState(friendlyMessage(e), create); }
}
$('dmGo').onclick = create;

function bodyOf(d) { return (lang === 'hi' ? (d.content_hindi || d.content_english) : (d.content_english || d.content_hindi)) || ''; }

function preview(d) {
  const text = bodyOf(d);
  const prov = d.field_provenance || {};
  $('draftOut').innerHTML = `<div class="np-split">
    <div><div class="np-paper"><div class="np-label">${esc(d.title)}</div><div id="docBody" class="np-doc-text">${esc(text)}</div></div></div>
    <div class="np-noprint"><h3 class="np-h">${t('Actions', 'कार्य')}</h3>
      <div class="np-row"><button class="btn btn-primary btn-sm" id="aPdf">${t('Save as PDF', 'PDF के रूप में सहेजें')}</button><button class="btn btn-secondary btn-sm" id="aDoc">${t('Download Word (.doc)', 'Word (.doc) डाउनलोड')}</button>
      <button class="btn btn-secondary btn-sm" id="aCopy">${t('Copy Text', 'पाठ कॉपी करें')}</button><button class="btn btn-secondary btn-sm" id="aEdit">${t('Edit', 'संपादित करें')}</button><button class="btn btn-ghost btn-sm" id="aRegen">${t('Regenerate', 'फिर से बनाएं')}</button></div>
      <div class="demo-notice" style="margin-top:12px">${t('Review the document carefully and, where appropriate, have it checked by a qualified legal professional before filing.', 'दस्तावेज़ को ध्यान से पढ़ें और जहाँ उचित हो, दाखिल करने से पहले योग्य कानूनी पेशेवर से जाँच कराएं।')}</div>
      ${(d.placeholders_used || []).length || Object.values(prov).includes('UNKNOWN') ? `<div class="np-disclaimer">${t('Some details were not provided. Fill every [PLACEHOLDER] before using this draft.', 'कुछ विवरण नहीं दिए गए। इस मसौदे के उपयोग से पहले हर [PLACEHOLDER] भरें।')}</div>` : ''}
      <h3 class="np-h" style="margin-top:20px">${t('Where to submit', 'कहाँ जमा करें')}</h3>
      ${d.filing_instructions ? `<div class="np-ai-box"><div class="np-ai-tag">${t('Template instructions — verify with the official office', 'टेम्पलेट निर्देश — आधिकारिक कार्यालय से सत्यापित करें')}</div><div class="np-doc-text" style="color:var(--text-secondary)">${esc(d.filing_instructions)}</div></div>`
        : `<div class="np-disclaimer">${t('Filing location could not be verified from the available sources.', 'उपलब्ध स्रोतों से दाखिल करने का स्थान सत्यापित नहीं हो सका।')}</div>`}
      <h4 class="np-h" style="margin-top:20px;font-size:1.1rem">${t('Documents you may need', 'आपको ये दस्तावेज़ चाहिए हो सकते हैं')}</h4>
      <p class="np-muted">${t('Potentially useful documents — not an official requirement. Confirm with the office or your lawyer.', 'संभावित रूप से उपयोगी दस्तावेज़ — आधिकारिक आवश्यकता नहीं। कार्यालय या वकील से पुष्टि करें।')}</p>
      <ul class="np-checklist">${[['Case number / CNR', 'केस नंबर / CNR'], ['Identity document', 'पहचान पत्र'], ['Previous court order', 'पिछला कोर्ट आदेश'], ['Relevant land / property record', 'संबंधित भूमि / संपत्ति रिकॉर्ड'], ['Supporting evidence', 'सहायक साक्ष्य']].map(([en, hi], i) => `<li><input type="checkbox" id="ck${i}"/><label for="ck${i}">${lang === 'hi' ? hi : en}</label></li>`).join('')}</ul>
      ${(d.important_notes || []).length ? `<h4 class="np-h" style="margin-top:20px;font-size:1.1rem">${t('Important notes', 'महत्वपूर्ण बातें')}</h4><ul>${d.important_notes.map(n => `<li>${esc(n)}</li>`).join('')}</ul>` : ''}
      ${(d.source_references || []).length ? `<h4 class="np-h" style="margin-top:20px;font-size:1.1rem">${t('Sources used', 'उपयोग किए गए स्रोत')}</h4><div class="np-grid">${d.source_references.map(s => sourceCard({ ...s, source_url: s.source_url || s.url }, lang)).join('')}</div>` : ''}
      ${disclaimerBanner(lang)}</div></div>`;
  $('aCopy').onclick = async () => { try { await navigator.clipboard.writeText($('docBody').innerText); showToast(t('Copied', 'कॉपी हो गया'), 'success'); } catch (_) { showToast(t('Copy failed', 'कॉपी नहीं हो सका'), 'error'); } };
  $('aEdit').onclick = () => { const b = $('docBody'), on = b.getAttribute('contenteditable') !== 'true'; b.setAttribute('contenteditable', on); if (on) b.focus(); $('aEdit').textContent = on ? t('Done editing', 'संपादन पूरा') : t('Edit', 'संपादित करें'); };
  $('aPdf').onclick = () => window.print();
  $('aDoc').onclick = () => {
    const html = `<html><head><meta charset="utf-8"><title>${esc(d.title)}</title></head><body style="font-family:Georgia,serif;white-space:pre-wrap;line-height:1.7"><h2>${esc(d.title)}</h2>${esc($('docBody').innerText).replace(/\n/g, '<br>')}</body></html>`;
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['\ufeff', html], { type: 'application/msword' }));
    a.download = (d.title || 'nyayapath-draft').replace(/[^\w\u0900-\u097F]+/g, '_').slice(0, 60) + '.doc'; a.click(); URL.revokeObjectURL(a.href);
  };
  $('aRegen').onclick = async () => { if (!lastReq) return showToast(t('Open “Create Draft” to regenerate.', 'दोबारा बनाने के लिए “मसौदा बनाएं” खोलें।'), 'info');
    $('draftOut').innerHTML = loadingState('Preparing your draft...', 'आपका मसौदा तैयार हो रहा है...');
    try { shown = await Drafts[TYPES[lastReq.type].fn](lastReq.req); preview(shown); history(); } catch (e) { $('draftOut').innerHTML = errorState(friendlyMessage(e)); } };
}

async function history() {
  try {
    const list = await Drafts.list();
    $('draftHistory').innerHTML = list.length ? list.map(d => `<div class="np-case-card"><div class="np-case-title">${esc(d.title)}</div><div class="np-meta-line"><span>${esc(d.draft_type)}</span><span>${formatDate(d.created_at, lang)}</span></div>
      <button class="btn btn-secondary btn-sm" data-show="${d.id}">${t('Open', 'खोलें')}</button></div>`).join('') : `<p class="np-muted">${t('No drafts yet. Create your first draft above.', 'अभी कोई मसौदा नहीं। ऊपर अपना पहला मसौदा बनाएं।')}</p>`;
    document.querySelectorAll('[data-show]').forEach(b => b.onclick = () => { shown = list.find(x => x.id === b.dataset.show); preview(shown); $('draftOut').scrollIntoView({ behavior: 'smooth' }); });
  } catch (e) { $('draftHistory').innerHTML = `<p class="np-muted">${esc(friendlyMessage(e))}</p>`; }
}

cards(); history();
Cases.list().then(r => { userCases = r; }).catch(() => {});

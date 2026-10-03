import { ActionPlans } from '../api/endpoints.js';
import { friendlyMessage } from '../api/client.js';
import { initShell, loadingState, emptyState, errorState, sourceCard, disclaimerBanner } from '../components/shell.js';
import { esc, formatDate, qs, ssGet, ssSet, showToast } from '../utils/helpers.js';

let lang = initShell('action-plan', (l) => { lang = l; plan && render(); });
const $ = (id) => document.getElementById(id);
const t = (en, hi) => (lang === 'hi' ? hi : en);
let plan = null, plans = [];

const ctx = ssGet('nyayapath_context');
if (ctx?.message) $('planMsg').value = ctx.message;

async function loadPlans() {
  try {
    plans = await ActionPlans.list();
    $('planPick').innerHTML = `<option value="">${t('Saved plans…', 'सहेजी गई योजनाएँ…')}</option>` + plans.map(p => `<option value="${p.id}">${esc((p.title || '').slice(0, 50))} · ${formatDate(p.created_at, lang)}</option>`).join('');
    const want = qs('id') || ssGet('nyayapath_plan_id');
    if (want && plans.find(p => p.id === want)) { plan = plans.find(p => p.id === want); render(); }
    else if (!plan && !qs('auto')) { $('planRoot').innerHTML = emptyState('Your case workspace is empty.', 'आपका केस वर्कस्पेस खाली है।', 'Describe your legal problem above to see possible next steps.', 'संभावित अगले कदम देखने के लिए ऊपर अपनी कानूनी समस्या लिखें।'); }
  } catch (e) { $('planRoot').innerHTML = errorState(friendlyMessage(e), loadPlans); }
}

async function generate() {
  const msg = $('planMsg').value.trim();
  if (msg.length < 5) { showToast(t('Please describe your situation.', 'कृपया अपनी स्थिति बताएं।'), 'error'); return; }
  $('planRoot').innerHTML = loadingState('Searching verified legal sources and organizing your steps...', 'सत्यापित कानूनी स्रोत खोजे जा रहे हैं और आपके कदम व्यवस्थित किए जा रहे हैं...');
  $('genBtn').disabled = true;
  try { plan = await ActionPlans.generate(msg, { language: lang }); ssSet('nyayapath_plan_id', plan.id); plans.unshift(plan); render(); loadPlans(); }
  catch (e) { $('planRoot').innerHTML = errorState(friendlyMessage(e), generate); }
  $('genBtn').disabled = false;
}

const kindLabel = (k) => k === 'INFORMATION_GATHERING' ? t('Information gathering', 'जानकारी जुटाना') : t('Possible next step', 'संभावित अगला कदम');
const diffLabel = (d) => ({ EASY: t('Easier', 'आसान'), MEDIUM: t('Moderate', 'मध्यम'), HARD: t('Complex', 'जटिल') }[d] || d);

function render() {
  const steps = plan.steps || [], done = steps.filter(s => s.status === 'COMPLETED').length, pct = steps.length ? Math.round(done / steps.length * 100) : 0;
  $('planRoot').innerHTML = `
    <div class="np-paper" style="margin-bottom:20px"><div class="np-label">${t('Situation as understood', 'हमने स्थिति ऐसे समझी')}</div>
      <h2 style="color:#211D19">${esc(plan.title)}</h2><p>${esc(plan.situation_assessment)}</p>
      ${plan.immediate_priority ? `<div class="np-label" style="margin-top:12px">${t('Possible first priority', 'संभावित पहली प्राथमिकता')}</div><p>${esc(plan.immediate_priority)}</p>` : ''}
      ${plan.delay_cause_analysis ? `<div class="np-label" style="margin-top:12px">${t('About the delay', 'देरी के बारे में')}</div><p>${esc(plan.delay_cause_analysis)}</p>` : ''}</div>
    ${(plan.warnings || []).map(w => `<div class="demo-notice">${esc(w)}</div>`).join('')}
    <div class="np-between" style="margin:20px 0 8px"><strong>${t('Progress', 'प्रगति')}: ${done}/${steps.length}</strong><span class="np-muted">${pct}%</span></div>
    <div class="np-progress" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><i style="width:${pct}%"></i></div>
    <div class="np-stepper" style="margin-top:28px">${steps.map(stepHTML).join('')}</div>
    ${(plan.supporting_sources || []).length ? `<h3 class="np-h" style="margin-top:24px">${t('Sources behind this plan', 'इस योजना के स्रोत')}</h3><div class="np-grid cols-2">${plan.supporting_sources.map(s => sourceCard(s, lang)).join('')}</div>` : `<div class="np-disclaimer">${t('No verified source was found for this plan. Treat every step as a general suggestion to discuss with a legal professional.', 'इस योजना के लिए कोई सत्यापित स्रोत नहीं मिला। हर कदम को सामान्य सुझाव मानें और कानूनी पेशेवर से चर्चा करें।')}</div>`}
    <div class="np-row np-noprint" style="margin-top:24px"><a class="btn btn-primary" href="drafts.html">${t('Prepare Documents', 'दस्तावेज़ तैयार करें')}</a><a class="btn btn-secondary" href="legal-aid.html">${t('Find Legal Aid', 'कानूनी सहायता खोजें')}</a><button class="btn btn-ghost" onclick="window.print()">${t('Print', 'प्रिंट')}</button></div>
    ${disclaimerBanner(lang)}${plan.disclaimer ? `<p class="np-muted">${esc(plan.disclaimer)}</p>` : ''}`;
  document.querySelectorAll('[data-step]').forEach(cb => cb.addEventListener('change', () => complete(cb)));
}

function stepHTML(s) {
  const done = s.status === 'COMPLETED';
  return `<div class="np-step ${done ? 'done' : ''}"><div class="np-step-num">${String(s.step_number).padStart(2, '0')}</div>
    <div class="np-step-body"><div class="np-step-title"><input type="checkbox" data-step="${s.id}" ${done ? 'checked disabled' : ''} aria-label="${t('Mark step complete', 'चरण पूर्ण चिह्नित करें')}"/>${esc(s.title)}</div>
      <div class="np-row" style="margin:8px 0"><span class="badge badge-gold">${kindLabel(s.kind)}</span><span class="badge badge-gold">${diffLabel(s.difficulty)}</span>
      ${s.source_backed ? `<span class="badge badge-disposed">${t('Source-backed', 'स्रोत-आधारित')}</span>` : `<span class="badge badge-pending">${t('General suggestion — not an official requirement', 'सामान्य सुझाव — आधिकारिक आवश्यकता नहीं')}</span>`}</div>
      <p>${esc(s.description)}</p>
      ${s.why_relevant ? `<div class="np-kv"><b>${t('Why', 'क्यों')}</b>${esc(s.why_relevant)}</div>` : ''}
      ${(s.documents_needed || []).length ? `<div class="np-kv"><b>${t('Documents that may help', 'सहायक हो सकने वाले दस्तावेज़')}</b>${s.documents_needed.map(esc).join(' · ')}</div>` : ''}
      ${s.legal_basis ? `<div class="np-kv"><b>${t('Legal basis (from source)', 'कानूनी आधार (स्रोत से)')}</b>${esc(s.legal_basis)}</div>` : ''}
      ${s.estimated_timeline ? `<div class="np-kv"><b>${t('Timeline', 'समयावधि')}</b>${esc(s.estimated_timeline)}</div>` : ''}</div></div>`;
}

async function complete(cb) {
  cb.disabled = true;
  try { const upd = await ActionPlans.completeStep(plan.id, cb.dataset.step); plan.steps = plan.steps.map(s => s.id === upd.id ? { ...s, ...upd } : s); render(); }
  catch (e) { cb.checked = false; cb.disabled = false; showToast(friendlyMessage(e), 'error'); }
}

$('genBtn').onclick = generate;
$('planPick').onchange = async (e) => { if (!e.target.value) return; plan = plans.find(p => p.id === e.target.value); ssSet('nyayapath_plan_id', plan.id); render(); };
loadPlans().then(() => { if (qs('auto') && $('planMsg').value.trim().length >= 5) generate(); });

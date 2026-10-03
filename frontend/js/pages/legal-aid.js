import { Courts } from '../api/endpoints.js';
import { friendlyMessage } from '../api/client.js';
import { initShell, loadingState, emptyState, errorState, pager } from '../components/shell.js';
import { esc } from '../utils/helpers.js';

let lang = initShell('legal-aid', (l) => { lang = l; national(); });
const $ = (id) => document.getElementById(id);
const t = (en, hi) => (lang === 'hi' ? hi : en);

// Fixed official portals / helpline. Not backend data. Verify on the official site.
const NATIONAL = [
  { en: 'NALSA — National Legal Services Authority', hi: 'नालसा — राष्ट्रीय विधिक सेवा प्राधिकरण', dEn: 'Free legal services for eligible persons through State and District Legal Services Authorities.', dHi: 'पात्र व्यक्तियों के लिए राज्य और जिला विधिक सेवा प्राधिकरणों के माध्यम से निःशुल्क कानूनी सेवाएँ।', url: 'https://nalsa.gov.in', contact: '15100' },
  { en: 'eCourts Services', hi: 'ई-कोर्ट सेवाएँ', dEn: 'Official portal for case status and court orders by CNR number.', dHi: 'CNR नंबर से केस स्थिति और कोर्ट आदेश देखने का आधिकारिक पोर्टल।', url: 'https://ecourts.gov.in', contact: null },
  { en: 'RTI Online (Central Government)', hi: 'RTI ऑनलाइन (केंद्र सरकार)', dEn: 'Official portal to file Right to Information requests with central public authorities.', dHi: 'केंद्रीय लोक प्राधिकरणों को सूचना का अधिकार अनुरोध भेजने का आधिकारिक पोर्टल।', url: 'https://rtionline.gov.in', contact: null },
];
function national() {
  $('national').innerHTML = NATIONAL.map(n => `<div class="np-case-card"><div class="np-source-label">${t('OFFICIAL RESOURCE', 'आधिकारिक संसाधन')}</div>
    <div class="np-case-title" style="margin-top:6px">${lang === 'hi' ? n.hi : n.en}</div><p class="np-snippet">${lang === 'hi' ? n.dHi : n.dEn}</p>
    ${n.contact ? `<p style="margin-top:8px"><b>${t('Helpline', 'हेल्पलाइन')}:</b> ${n.contact} <span class="np-muted">(${t('verify on official site', 'आधिकारिक साइट पर सत्यापित करें')})</span></p>` : ''}
    <a class="source-card" style="margin-top:10px;display:inline-flex" href="${n.url}" target="_blank" rel="noopener noreferrer">⚖ ${t('Open official site', 'आधिकारिक साइट खोलें')} →</a></div>`).join('');
}

async function courts(page = 1) {
  $('courts').innerHTML = loadingState('Finding courts in our records...', 'हमारे रिकॉर्ड में न्यायालय खोजे जा रहे हैं...');
  try {
    const list = await Courts.list({ state: $('cState').value.trim(), q: $('cQ').value.trim(), page });
    $('courts').innerHTML = list.length ? list.map(c => `<div class="np-case-card"><div class="np-case-title">${esc(c.name)}</div>
      <div class="np-meta-line"><span>${esc(c.court_type.replace('_', ' '))}</span>${c.state ? `<span>${esc(c.state)}</span>` : ''}${c.district ? `<span>${esc(c.district)}</span>` : ''}</div>
      ${c.address ? `<p class="np-snippet">${esc(c.address)}</p>` : `<p class="np-muted">${t('Address could not be verified from the available sources.', 'पता उपलब्ध स्रोतों से सत्यापित नहीं हो सका।')}</p>`}
      ${c.website && /^https?:\/\//.test(c.website) ? `<a class="source-card" href="${esc(c.website)}" target="_blank" rel="noopener noreferrer" style="margin-top:8px;display:inline-flex">⚖ ${t('Official website', 'आधिकारिक वेबसाइट')} →</a>` : ''}</div>`).join('')
      : emptyState('No matching court was found in the available records.', 'उपलब्ध रिकॉर्ड में कोई मेल खाता न्यायालय नहीं मिला।', '', '');
    $('cPager').innerHTML = pager(list.meta, courts);
  } catch (e) { $('courts').innerHTML = errorState(friendlyMessage(e), () => courts(page)); }
}
$('cGo').onclick = () => courts(1);
national(); courts(1);

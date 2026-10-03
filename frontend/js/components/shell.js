/**
 * Shared page shell: navbar, footer, language switching, common UI blocks.
 * Used by the pages added in this phase (research, judgment, documents, action-plan, drafts, legal-aid, result).
 * Every translatable node carries data-en / data-hi — the same convention as index/ask/case.
 */
import { getLang, setLang, esc } from '../utils/helpers.js';

const NAV = [
  ['home', '../index.html', 'Home', 'मुख्य पृष्ठ'],
  ['ask', 'ask.html', 'Ask NyayaPath', 'NyayaPath से पूछें'],
  ['case', 'case.html', 'My Case', 'मेरा केस'],
  ['research', 'research.html', 'Legal Research', 'कानूनी शोध'],
  ['documents', 'documents.html', 'Documents', 'दस्तावेज़'],
  ['action-plan', 'action-plan.html', 'Action Plan', 'कार्य योजना'],
  ['drafts', 'drafts.html', 'Prepare Drafts', 'मसौदे तैयार करें'],
  ['legal-aid', 'legal-aid.html', 'Legal Aid', 'कानूनी सहायता'],
];

const LOGO = `<svg viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="19" stroke="#C9A227" stroke-width="1.5" opacity=".4"/><line x1="20" y1="8" x2="20" y2="32" stroke="#C9A227" stroke-width="1.8"/><line x1="20" y1="14" x2="10" y2="20" stroke="#C9A227" stroke-width="1.5"/><line x1="20" y1="14" x2="30" y2="20" stroke="#C9A227" stroke-width="1.5"/><ellipse cx="10" cy="21.5" rx="5" ry="2.5" stroke="#C9A227" stroke-width="1.2" fill="rgba(201,162,39,.15)"/><ellipse cx="30" cy="21.5" rx="5" ry="2.5" stroke="#C9A227" stroke-width="1.2" fill="rgba(201,162,39,.15)"/><circle cx="20" cy="32" r="2" fill="#C9A227" opacity=".8"/></svg>`;

const t = (en, hi) => `data-en="${en}" data-hi="${hi}"`;

export function navHTML(active) {
  return `<nav class="navbar" role="navigation" aria-label="Main navigation"><div class="navbar-inner">
    <a href="../index.html" class="navbar-logo" aria-label="NyayaPath Home"><div class="logo-icon">${LOGO}</div>
      <div><span class="logo-text">NyayaPath</span><span class="logo-tagline" ${t('Your legal path, made clear', 'आपका कानूनी मार्ग, स्पष्ट')}>Your legal path, made clear</span></div></a>
    <ul class="navbar-nav" id="navMenu">${NAV.map(([k, href, en, hi]) =>
      `<li><a href="${href}" class="${k === active ? 'active' : ''}" ${t(en, hi)}>${en}</a></li>`).join('')}</ul>
    <div class="navbar-right">
      <div class="lang-switcher"><button class="lang-btn" id="langEn" onclick="switchLang('en')" aria-label="Switch to English">EN</button><span class="lang-sep">|</span><button class="lang-btn" id="langHi" onclick="switchLang('hi')" aria-label="हिंदी में बदलें">हिं</button></div>
      <a href="ask.html" class="btn btn-primary btn-sm" ${t('Start Your Case', 'केस शुरू करें')}>Start Your Case</a>
      <button class="navbar-hamburger" id="hamburger" aria-label="Toggle menu" onclick="toggleMenu()"><span></span><span></span><span></span></button>
    </div></div></nav>`;
}

export function footerHTML() {
  return `<footer class="footer" role="contentinfo"><div class="container"><div class="footer-grid">
    <div class="footer-brand"><div class="footer-logo-text">NyayaPath</div>
      <p class="footer-desc" ${t('AI-powered legal information and case navigation for Indian citizens. In Hindi and English.', 'भारतीय नागरिकों के लिए AI-संचालित कानूनी जानकारी और केस नेविगेशन। हिंदी और English में।')}>AI-powered legal information and case navigation for Indian citizens. In Hindi and English.</p></div>
    <div><div class="footer-heading" ${t('Navigate', 'नेविगेट करें')}>Navigate</div><ul class="footer-links">
      <li><a href="ask.html" ${t('Ask NyayaPath', 'NyayaPath से पूछें')}>Ask NyayaPath</a></li>
      <li><a href="research.html" ${t('Legal Research', 'कानूनी शोध')}>Legal Research</a></li>
      <li><a href="documents.html" ${t('Documents', 'दस्तावेज़')}>Documents</a></li>
      <li><a href="action-plan.html" ${t('Action Plan', 'कार्य योजना')}>Action Plan</a></li></ul></div>
    <div><div class="footer-heading" ${t('Support', 'सहायता')}>Support</div><ul class="footer-links">
      <li><a href="legal-aid.html" ${t('Find Legal Aid', 'कानूनी सहायता पाएं')}>Find Legal Aid</a></li>
      <li><a href="case.html" ${t('My Case', 'मेरा केस')}>My Case</a></li>
      <li><a href="drafts.html" ${t('Prepare Documents', 'दस्तावेज़ तैयार करें')}>Prepare Documents</a></li></ul></div>
  </div>
  <div class="footer-bottom"><p class="footer-disclaimer" ${t('NyayaPath provides legal information and navigation assistance. It is not a substitute for a qualified legal professional. Sources should always be independently verified.', 'NyayaPath कानूनी जानकारी और मार्गदर्शन प्रदान करता है। यह योग्य कानूनी पेशेवर का विकल्प नहीं है। स्रोतों को हमेशा स्वतंत्र रूप से सत्यापित करें।')}>NyayaPath provides legal information and navigation assistance. It is not a substitute for a qualified legal professional. Sources should always be independently verified.</p>
  <div class="footer-copy">© NyayaPath</div></div></div></footer>`;
}

export function applyLang(lang) {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-en]').forEach(el => {
    const txt = el.getAttribute('data-' + lang) || el.getAttribute('data-en');
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.placeholder = txt;
    else if (el.tagName === 'OPTION') el.textContent = txt;
    else el.innerHTML = txt;
  });
  document.getElementById('langEn')?.classList.toggle('active', lang === 'en');
  document.getElementById('langHi')?.classList.toggle('active', lang === 'hi');
}

/** Mount navbar + footer, wire language + hamburger. `onLang(lang)` re-renders dynamic content. */
export function initShell(active, onLang) {
  document.getElementById('app-nav').innerHTML = navHTML(active);
  document.getElementById('app-footer').innerHTML = footerHTML();
  window.switchLang = (lang) => { setLang(lang); applyLang(lang); onLang && onLang(lang); };
  window.toggleMenu = () => document.getElementById('navMenu').classList.toggle('open');
  document.addEventListener('click', (e) => {
    const m = document.getElementById('navMenu'), h = document.getElementById('hamburger');
    if (m && m.classList.contains('open') && !m.contains(e.target) && !h.contains(e.target)) m.classList.remove('open');
  });
  applyLang(getLang());
  return getLang();
}

/* ---------- reusable state blocks ---------- */
export function loadingState(msgEn, msgHi) {
  return `<div class="np-loading" role="status" aria-live="polite"><div class="np-skel"></div><div class="np-skel short"></div><div class="np-skel"></div>
    <p class="np-loading-text" ${t(msgEn, msgHi)}>${msgEn}</p></div>`;
}
export function emptyState(titleEn, titleHi, descEn, descHi, ctaHref, ctaEn, ctaHi) {
  return `<div class="state-container"><div class="state-icon" aria-hidden="true">⚖</div>
    <div class="state-title" ${t(titleEn, titleHi)}>${titleEn}</div>
    <div class="state-desc" ${t(descEn, descHi)}>${descEn}</div>
    ${ctaHref ? `<a class="btn btn-primary btn-sm" style="margin-top:16px" href="${ctaHref}" ${t(ctaEn, ctaHi)}>${ctaEn}</a>` : ''}</div>`;
}
export function errorState(message, retryFn) {
  const id = 'retry' + Math.random().toString(36).slice(2, 7);
  setTimeout(() => document.getElementById(id)?.addEventListener('click', retryFn), 0);
  return `<div class="state-container np-error" role="alert"><div class="state-icon" aria-hidden="true">!</div>
    <div class="state-title" ${t("We couldn't retrieve the information right now.", 'अभी जानकारी प्राप्त नहीं हो सकी।')}>We couldn't retrieve the information right now.</div>
    <div class="state-desc">${esc(message || '')}</div>
    ${retryFn ? `<button class="btn btn-secondary btn-sm" id="${id}" style="margin-top:16px" ${t('Try Again', 'पुनः प्रयास करें')}>Try Again</button>` : ''}</div>`;
}

/* ---------- source + verification display ---------- */
export function verifyBadge(status, isDemo, lang = 'en') {
  const hi = lang === 'hi';
  if (isDemo) return `<span class="badge badge-demo">${hi ? 'डेमो / नमूना डेटा' : 'Demo / Sample Data'}</span>`;
  if (status === 'VERIFIED') return `<span class="badge badge-disposed">${hi ? 'स्रोत सत्यापित' : 'Source verified'}</span>`;
  return `<span class="badge badge-gold">${hi ? 'सत्यापित नहीं' : 'Not yet verified'}</span>`;
}

export function sourceCard(s, lang = 'en') {
  const hi = lang === 'hi';
  const typeMap = { JUDGMENT: ['Judgment', 'निर्णय'], GOVERNMENT: ['Government source', 'सरकारी स्रोत'], OFFICIAL_COURT: ['Court record', 'न्यायालय रिकॉर्ड'],
    LEGAL_INFORMATION: ['Legal information', 'कानूनी जानकारी'], CASE_RECORD: ['Case record', 'केस रिकॉर्ड'], USER_DOCUMENT: ['Your document', 'आपका दस्तावेज़'] };
  const ty = (typeMap[s.source_type] || ['Source', 'स्रोत'])[hi ? 1 : 0];
  return `<div class="np-source"><div class="np-source-head"><span class="np-source-label">${hi ? 'स्रोत' : 'SOURCE'}</span>${verifyBadge(s.verification_status, s.is_demo_data, lang)}</div>
    <div class="np-source-title">${esc(s.title || ty)}</div>
    <div class="np-source-meta">${[ty, s.court, s.citation, s.date, s.locator || (s.page_number ? 'p. ' + s.page_number : '')].filter(Boolean).map(esc).join(' · ')}</div>
    ${s.source_url ? `<a class="source-card" href="${esc(s.source_url)}" target="_blank" rel="noopener noreferrer">⚖ ${hi ? 'मूल स्रोत खोलें' : 'Open original source'} →</a>`
      : `<span class="np-source-none">${hi ? 'इस जानकारी का मूल स्रोत लिंक उपलब्ध नहीं है।' : 'No original-source link is available for this item.'}</span>`}</div>`;
}

/** "Why this result?" disclosure */
export function whyBox(reason, lang = 'en') {
  if (!reason) return '';
  return `<details class="np-why"><summary>${lang === 'hi' ? 'यह परिणाम क्यों?' : 'Why this result?'}</summary><p>${esc(reason)}</p></details>`;
}

export function disclaimerBanner(lang = 'en') {
  return `<div class="np-disclaimer" role="note">${lang === 'hi'
    ? 'यह कानूनी जानकारी और मार्गदर्शन है, कानूनी सलाह नहीं। निर्णय लेने से पहले किसी योग्य कानूनी पेशेवर से चर्चा करें।'
    : 'This is legal information and navigation, not legal advice. Discuss with a qualified legal professional before acting.'}</div>`;
}

export function pager(meta, onPage) {
  const p = meta?.pagination;
  if (!p || p.total_pages <= 1) return '';
  setTimeout(() => document.querySelectorAll('[data-page]').forEach(b => b.addEventListener('click', () => onPage(+b.dataset.page))), 0);
  return `<div class="np-pager"><button class="btn btn-secondary btn-sm" data-page="${p.page - 1}" ${p.page <= 1 ? 'disabled' : ''}>←</button>
    <span>${p.page} / ${p.total_pages}</span><button class="btn btn-secondary btn-sm" data-page="${p.page + 1}" ${p.page >= p.total_pages ? 'disabled' : ''}>→</button></div>`;
}

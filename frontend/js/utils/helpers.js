/**
 * NyayaPath utility helpers
 */

// ── Date formatting ──────────────────────────────────────
export function formatDate(dateStr, lang = 'en') {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  return d.toLocaleDateString(lang === 'hi' ? 'hi-IN' : 'en-IN', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}

export function formatYear(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return isNaN(d) ? dateStr : d.getFullYear();
}

export function caseAge(filingDateStr) {
  if (!filingDateStr) return null;
  const filed = new Date(filingDateStr);
  if (isNaN(filed)) return null;
  const now = new Date();
  const years  = Math.floor((now - filed) / (365.25 * 24 * 3600 * 1000));
  const months = Math.floor(((now - filed) % (365.25 * 24 * 3600 * 1000)) / (30.44 * 24 * 3600 * 1000));
  if (years > 0) return `${years} yr ${months > 0 ? months + ' mo' : ''}`.trim();
  return `${months} months`;
}

// ── Status labels ────────────────────────────────────────
const STATUS_LABELS = {
  PENDING:     { en: 'Pending',     hi: 'लंबित',        cls: 'badge-pending' },
  DISPOSED:    { en: 'Disposed',    hi: 'निपटारा',       cls: 'badge-disposed' },
  DECIDED:     { en: 'Decided',     hi: 'निर्णित',       cls: 'badge-disposed' },
  TRANSFERRED: { en: 'Transferred', hi: 'स्थानांतरित',    cls: 'badge-gold' },
  ABATED:      { en: 'Abated',      hi: 'समाप्त',        cls: 'badge-gold' },
  UNKNOWN:     { en: 'Unknown',     hi: 'अज्ञात',        cls: 'badge-gold' },
};

export function statusBadge(status, lang = 'en') {
  const s = STATUS_LABELS[status] || { en: status, hi: status, cls: 'badge-gold' };
  return `<span class="badge ${s.cls}">${s[lang] || s.en}</span>`;
}

const CASE_TYPE_LABELS = {
  CIVIL:    { en: 'Civil',    hi: 'सिविल'     },
  CRIMINAL: { en: 'Criminal', hi: 'आपराधिक'   },
  WRIT:     { en: 'Writ',     hi: 'रिट'        },
  APPEAL:   { en: 'Appeal',   hi: 'अपील'      },
  REVISION: { en: 'Revision', hi: 'पुनरीक्षण' },
  OTHER:    { en: 'Other',    hi: 'अन्य'       },
};

export function caseTypeLabel(type, lang = 'en') {
  return (CASE_TYPE_LABELS[type] || {})[lang] || type || '—';
}

const TOPIC_LABELS = {
  LAND_DISPUTE:     { en: 'Land Dispute',         hi: 'भूमि विवाद'           },
  PROPERTY_DISPUTE: { en: 'Property Dispute',      hi: 'संपत्ति विवाद'        },
  CIVIL_DISPUTE:    { en: 'Civil Dispute',         hi: 'दीवानी विवाद'         },
  CASE_PENDENCY:    { en: 'Case Pendency',         hi: 'मामले की लंबितता'     },
  COURT_PROCEDURE:  { en: 'Court Procedure',       hi: 'न्यायालय प्रक्रिया'   },
  RTI:              { en: 'Right to Information',  hi: 'सूचना का अधिकार'      },
  CRIMINAL_CASE:    { en: 'Criminal Case',         hi: 'आपराधिक मामला'        },
  BAIL:             { en: 'Bail',                  hi: 'जमानत'                },
  FAMILY_DISPUTE:   { en: 'Family Dispute',        hi: 'पारिवारिक विवाद'      },
  CONSUMER_DISPUTE: { en: 'Consumer Dispute',      hi: 'उपभोक्ता विवाद'       },
  LABOUR_DISPUTE:   { en: 'Labour Dispute',        hi: 'श्रम विवाद'           },
  GOVERNMENT_SERVICE: { en: 'Government Service', hi: 'सरकारी सेवा'           },
  MOTOR_ACCIDENT:   { en: 'Motor Accident',        hi: 'मोटर दुर्घटना'        },
  CONSTITUTIONAL:   { en: 'Constitutional',        hi: 'संवैधानिक'            },
  OTHER:            { en: 'Other',                 hi: 'अन्य'                 },
};

export function topicLabel(topic, lang = 'en') {
  return (TOPIC_LABELS[topic] || {})[lang] || topic || '—';
}

// ── HTML escaping ────────────────────────────────────────
export function esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Toast notifications ──────────────────────────────────
export function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { info: '⚖', success: '✓', error: '✕' };
  toast.innerHTML = `<span>${icons[type] || '•'}</span><span>${esc(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = '0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Modal helpers ────────────────────────────────────────
export function openModal(id) {
  const el = document.getElementById(id);
  if (el) { el.classList.add('open'); document.body.style.overflow = 'hidden'; }
}

export function closeModal(id) {
  const el = document.getElementById(id);
  if (el) { el.classList.remove('open'); document.body.style.overflow = ''; }
}

// ── Debounce ─────────────────────────────────────────────
export function debounce(fn, ms = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ── Language ─────────────────────────────────────────────
export function getLang() {
  try { return localStorage.getItem('nyayapath_lang') || 'en'; } catch (_) { return 'en'; }
}

export function setLang(lang) {
  try { localStorage.setItem('nyayapath_lang', lang); } catch (_) {}
  document.documentElement.lang = lang;
}

// ── Truncate ─────────────────────────────────────────────
export function truncate(str, n = 120) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

// ── Format file size ─────────────────────────────────────
export function fileSize(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// ── Added in phase 2 ─────────────────────────────────────
export function qs(name) { return new URLSearchParams(window.location.search).get(name); }
export function ssGet(key) { try { return JSON.parse(sessionStorage.getItem(key)); } catch (_) { return null; } }
export function ssSet(key, val) { try { sessionStorage.setItem(key, JSON.stringify(val)); } catch (_) {} }
export function isSafeUrl(u) { return typeof u === 'string' && /^https?:\/\//i.test(u); }
export function debounceFn(fn, ms = 300) { return debounce(fn, ms); }

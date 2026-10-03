/**
 * NyayaPath API client — the ONLY place that calls fetch().
 * Backend envelope: success -> { success:true, data, meta? } ; failure -> { success:false, error:{code,message,details?} }
 * request() resolves to `data`. Pagination/meta is attached as a non-enumerable `.meta` property.
 */
import CONFIG from '../config.js';

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status; this.code = code; this.details = details;
  }
}

// Citizen-friendly messages (never show raw server text for these statuses)
const FRIENDLY = {
  0:   "We couldn't reach the server. Please check that the backend is running and try again.",
  401: "We couldn't verify access to this information right now.",
  403: "You don't have access to this information.",
  404: 'No matching record was found in the available records.',
  422: 'Some of the information provided could not be used. Please check and try again.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: "We couldn't retrieve the information right now. Please try again.",
  502: "The AI service couldn't complete this request. Please try again.",
  503: 'This service is temporarily unavailable. Please try again shortly.',
};
const FRIENDLY_HI = {
  0: 'सर्वर से संपर्क नहीं हो सका। कृपया बैकएंड चालू होने की जाँच करें और पुनः प्रयास करें।',
  401: 'अभी इस जानकारी तक पहुँच सत्यापित नहीं हो सकी।',
  403: 'इस जानकारी तक आपकी पहुँच नहीं है।',
  404: 'उपलब्ध रिकॉर्ड में कोई मेल खाता रिकॉर्ड नहीं मिला।',
  422: 'दी गई कुछ जानकारी का उपयोग नहीं हो सका। कृपया जाँचकर पुनः प्रयास करें।',
  429: 'बहुत अधिक अनुरोध। कृपया थोड़ी देर बाद पुनः प्रयास करें।',
  500: 'अभी जानकारी प्राप्त नहीं हो सकी। कृपया पुनः प्रयास करें।',
  502: 'AI सेवा यह अनुरोध पूरा नहीं कर सकी। कृपया पुनः प्रयास करें।',
  503: 'यह सेवा अभी उपलब्ध नहीं है। कृपया कुछ देर बाद प्रयास करें।',
};

export function friendlyMessage(err) {
  let lang = 'en';
  try { lang = localStorage.getItem('nyayapath_lang') || 'en'; } catch (_) {}
  const table = lang === 'hi' ? FRIENDLY_HI : FRIENDLY;
  if (!err) return table[500];
  // Validation errors from the backend carry useful, user-safe text
  if (err.status === 400 && err.message) return err.message;
  return table[err.status] || (err.status >= 500 ? table[500] : err.message) || table[500];
}

const store = {
  get access() { try { return localStorage.getItem('nyayapath_access'); } catch (_) { return null; } },
  set access(v) { try { v ? localStorage.setItem('nyayapath_access', v) : localStorage.removeItem('nyayapath_access'); } catch (_) {} },
};

let loginPromise = null;
async function devLogin() {
  if (!CONFIG.DEV_AUTO_LOGIN) return false;
  if (!loginPromise) {
    loginPromise = (async () => {
      try {
        const res = await fetch(`${CONFIG.API_BASE}/auth/login/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: CONFIG.DEV_EMAIL, password: CONFIG.DEV_PASSWORD }),
        });
        const json = await res.json();
        const token = json?.data?.tokens?.access;
        if (res.ok && token) { store.access = token; return true; }
      } catch (_) { /* fall through */ }
      return false;
    })().finally(() => { setTimeout(() => { loginPromise = null; }, 2000); });
  }
  return loginPromise;
}

function withMeta(data, meta) {
  if (meta && data !== null && typeof data === 'object') {
    Object.defineProperty(data, 'meta', { value: meta, enumerable: false, configurable: true });
  }
  return data;
}

async function request(method, path, { body, form, query, retried = false } = {}) {
  const headers = {};
  let payload;
  if (form) payload = form; // browser sets multipart boundary
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body); }
  const token = store.access;
  if (token) headers.Authorization = `Bearer ${token}`;

  let qs = '';
  if (query) {
    const p = new URLSearchParams();
    Object.entries(query).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') p.append(k, v); });
    qs = p.toString() ? `?${p}` : '';
  }

  let res;
  try { res = await fetch(`${CONFIG.API_BASE}${path}${qs}`, { method, headers, body: payload }); }
  catch (_) { throw new ApiError(0, 'NETWORK_ERROR', FRIENDLY[0]); }

  if (res.status === 204) return null;

  // Expired/missing token: sign in silently (dev) and retry once; otherwise retry as a guest
  if (res.status === 401 && !retried && !path.startsWith('/auth/')) {
    store.access = null;
    await devLogin();
    return request(method, path, { body, form, query, retried: true });
  }

  let json = {};
  try { json = await res.json(); } catch (_) { /* non-JSON error page */ }

  if (!res.ok || json.success === false) {
    const e = json.error || {};
    let msg = e.message;
    if (e.details && typeof e.details === 'object') {
      const first = Object.values(e.details).flat()[0];
      if (typeof first === 'string') msg = first;
    }
    throw new ApiError(res.status, e.code || String(res.status), msg || FRIENDLY[res.status] || FRIENDLY[500], e.details);
  }
  return withMeta('data' in json ? json.data : json, json.meta);
}

const api = {
  get:    (path, query)       => request('GET', path, { query }),
  post:   (path, body, query) => request('POST', path, { body: body ?? {}, query }),
  patch:  (path, body)        => request('PATCH', path, { body }),
  delete: (path)              => request('DELETE', path),
  upload: (path, formData)    => request('POST', path, { form: formData }),
  health: () => request('GET', '/health/'),
  BASE_URL: CONFIG.API_BASE,
};

export default api;

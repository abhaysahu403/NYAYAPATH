/**
 * NyayaPath endpoint map — one function per real backend route (see FRONTEND_BACKEND_INTEGRATION.md).
 * Nothing here is invented: every path exists in the Django URLconf.
 */
import api from './client.js';

export const Core = {
  health: () => api.health(),
  legalTopics: () => api.get('/legal-topics/'),
};

export const AI = {
  chat: (message, { language, caseId, conversationId } = {}) =>
    api.post('/ai/chat/', { message, language: language || null, case_id: caseId || null, conversation_id: conversationId || null }),
  similarCases: (message, { language, state, court, topic, topK = 6 } = {}) =>
    api.post('/ai/similar-cases/', { message, language, state, court, topic, top_k: topK }),
  explainJudgment: (id, { question = '', language = 'en' } = {}) =>
    api.post(`/ai/judgments/${id}/explain/`, { question, language }),
  feedback: (responseId, rating, comment = '') => api.post(`/ai/responses/${responseId}/feedback/`, { rating, comment }),
};

export const Cases = {
  list:   (page = 1) => api.get('/cases/', { page }),
  get:    (id)       => api.get(`/cases/${id}/`),
  create: (data)     => api.post('/cases/', data),
  update: (id, data) => api.patch(`/cases/${id}/`, data),
  remove: (id)       => api.delete(`/cases/${id}/`),
  search: (filters)  => api.post('/cases/search/', filters),
  timeline: (id)     => api.get(`/cases/${id}/timeline/`),
  hearings: (id)     => api.get(`/cases/${id}/hearings/`),
  parties:  (id)     => api.get(`/cases/${id}/parties/`),
  addEvent:   (id, d) => api.post(`/cases/${id}/timeline/`, d),
  addHearing: (id, d) => api.post(`/cases/${id}/hearings/`, d),
  addParty:   (id, d) => api.post(`/cases/${id}/parties/`, d),
};

export const Judgments = {
  search: (body, { page = 1, pageSize = 10 } = {}) => api.post('/judgments/search/', body, { page, page_size: pageSize }),
  list:   (params = {}) => api.get('/judgments/', params),
  get:    (id) => api.get(`/judgments/${id}/`),
};

export const Documents = {
  list:   (params = {}) => api.get('/documents/', params),
  get:    (id, includeText = false) => api.get(`/documents/${id}/`, includeText ? { include_text: 1 } : undefined),
  upload: (file, caseId) => { const f = new FormData(); f.append('file', file); if (caseId) f.append('case', caseId); return api.upload('/documents/upload/', f); },
  analyze:   (id, language = 'en') => api.post(`/documents/${id}/analyze/`, { language }),
  ask:       (id, question, language = 'en') => api.post(`/documents/${id}/ask/`, { question, language }),
  reprocess: (id) => api.post(`/documents/${id}/reprocess/`, {}),
  downloadLink: (id) => api.post(`/documents/${id}/download-link/`, {}),
  remove: (id) => api.delete(`/documents/${id}/`),
};

export const ActionPlans = {
  list: (page = 1) => api.get('/action-plans/', { page }),
  get:  (id) => api.get(`/action-plans/${id}/`),
  generate: (message, { language = 'en', caseId } = {}) => api.post('/action-plans/generate/', { message, language, case_id: caseId || null }),
  completeStep: (planId, stepId) => api.post(`/action-plans/${planId}/steps/${stepId}/complete/`, {}),
  remove: (id) => api.delete(`/action-plans/${id}/`),
};

export const Drafts = {
  list: (page = 1) => api.get('/drafts/', { page }),
  get:  (id) => api.get(`/drafts/${id}/`),
  caseSummary: ({ message, language = 'en', caseId }) => api.post('/drafts/case-summary/', { message, language, case_id: caseId || null }),
  lawyerBrief: ({ message, language = 'en', caseId, lawyerName = '', courtName = '' }) =>
    api.post('/drafts/lawyer-brief/', { message, language, case_id: caseId || null, lawyer_name: lawyerName, court_name: courtName }),
  rti: ({ message, language = 'en', caseId, applicantName = '', publicAuthority = '', informationSought = '' }) =>
    api.post('/drafts/rti/', { message, language, case_id: caseId || null, applicant_name: applicantName, public_authority: publicAuthority, information_sought: informationSought }),
  remove: (id) => api.delete(`/drafts/${id}/`),
};

export const Courts  = { list: (params = {}) => api.get('/courts/', params), get: (id) => api.get(`/courts/${id}/`) };
export const Sources = { list: (params = {}) => api.get('/sources/', params), get: (id) => api.get(`/sources/${id}/`) };

// Auth hooks are intentionally NOT exposed in the UI during this phase.
export const Auth = {
  profile: () => api.get('/auth/profile/'),
};

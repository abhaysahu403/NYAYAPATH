# NyayaPath — Frontend ↔ Backend Integration Map

Base URL: `http://localhost:8000/api/v1` (change in `js/config.js` or `window.NYAYAPATH_API_BASE`).
Envelope: success `{success:true, data, meta?}` · error `{success:false, error:{code,message,details?}}`.
`js/api/client.js` unwraps `data`, exposes pagination as `result.meta`, and turns errors into friendly messages (401/403/404/422/429/5xx).
**Auth:** no login UI. Endpoints marked 🔒 need a JWT; in development the client silently signs in as the seeded demo user (`js/config.js`, `DEV_AUTO_LOGIN`). Disable for production.
Status: **Real** = implemented in backend and wired here.

| Endpoint | Method | Request | Response (key fields) | Page(s) | Auth | Status |
|---|---|---|---|---|---|---|
| `/health/` | GET | – | status, database | (client.health) | public | Real |
| `/legal-topics/` | GET | – | [{code,label}] | research | public | Real |
| `/ai/chat/` | POST | message, language, case_id?, conversation_id? | answer, entities, detected_intent, follow_up_questions, sources, judgment_references, case_references, claims, next_steps, unknowns, warnings, verification_status, disclaimer | index→ask, result | public (guest limit) | Real |
| `/ai/similar-cases/` | POST | message, language, state?, court?, topic?, top_k | results[{judgment_id,title,court,date,citation,relevance_label,relevance_reason,source_url,snippet,verification_status,is_demo_data}], similarity_note | ask, result | public | Real |
| `/ai/judgments/<id>/explain/` | POST | question?, language | judgment, explanation{plain_summary,key_facts,legal_issue,court_reasoning,outcome}, grounding, warnings, note | judgment, research | 🔒 | Real |
| `/judgments/search/?page=` | POST | query, state, court, district, topic, date_from/to, source_type | paginated hit list | research | public | Real |
| `/judgments/` | GET | state, topic, court, q | judgment list | research (recent) | public | Real |
| `/judgments/<id>/` | GET | – | full judgment record | judgment | public | Real |
| `/cases/`, `/cases/<id>/` | GET/POST/PATCH | case fields | Case + events, hearings, parties | case, drafts | 🔒 | Real |
| `/cases/search/` | POST | cnr, case_number, status, … | paginated cases | case (client wrapper ready) | 🔒 | Real |
| `/cases/<id>/timeline|hearings|parties/` | GET/POST | – | events / hearings / parties | case | 🔒 | Real |
| `/documents/` | GET | – | document list | documents | 🔒 | Real |
| `/documents/upload/` | POST multipart | file, case? | document (status) | documents | 🔒 | Real |
| `/documents/<id>/?include_text=1` | GET | – | document + extracted_text, analysis_result | documents | 🔒 | Real |
| `/documents/<id>/analyze/` | POST | language | analysis{document_type,plain_summary,key_facts,important_dates,parties,suggested_questions} | documents | 🔒 | Real |
| `/documents/<id>/ask/` | POST | question, language | answer, sources(page), unknowns, notice | documents | 🔒 | Real |
| `/documents/<id>/reprocess/`, `/download-link/`, DELETE | POST/DELETE | – | document / url | documents | 🔒 | Real |
| `/action-plans/`, `/generate/`, `/<id>/` | GET/POST | message, language, case_id? | plan + steps | action-plan | 🔒 | Real |
| `/action-plans/<id>/steps/<sid>/complete/` | POST | – | step | action-plan | 🔒 | Real (complete only; backend has no "un-complete") |
| `/drafts/case-summary|lawyer-brief|rti/` | POST | message, language, case_id?, + type fields | draft{content_english/hindi, filing_instructions, important_notes, source_references} | drafts | 🔒 | Real |
| `/drafts/`, `/drafts/<id>/` | GET | – | drafts | drafts | 🔒 | Real |
| `/courts/` | GET | state, q, court_type | courts | legal-aid | public | Real |
| `/sources/` | GET | – | sources | (api ready) | public | Real |

## Not provided by the backend (so not faked)
- **Legal-aid directory** (DLSA/SLSA contacts): no endpoint. `legal-aid.html` shows 3 fixed official portals (NALSA, eCourts, RTI Online) clearly labelled as static, plus the backend court list.
- **PDF/DOCX export of drafts:** no endpoint. Drafts offer *Save as PDF* (browser print), *Word (.doc)* generated in the browser, and copy.
- **Verified filing office/fees/deadlines:** backend returns only generic `filing_instructions`; the UI labels them "template instructions — verify" and otherwise shows *"Filing location could not be verified from the available sources."*
- **Live case status (eCourts):** only cases stored in the database.
- **Un-completing an action step**, **"Other application" draft**, **voice** (browser Web Speech API only).

## Data-honesty rules implemented
Demo records are badged "Demo / Sample Data"; verified vs unverified badge on every source; AI text sits in separate "AI explanation" boxes (dashed gold) away from original text (ivory paper); relevance shown as "search relevance", never a similarity %.

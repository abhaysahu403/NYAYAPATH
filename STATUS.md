# NyayaPath backend — status (final backend drop)

## Verified by running (PostgreSQL 16 + pgvector, mock AI provider)
health, legal-topics, register, login, profile, password reset, AI chat (auth + guest, Hindi demo flow, follow-ups, sources,
next steps), conversations, judgment search / list / detail / explain, similar cases, courts, sources, cases (list/search/detail/
timeline/create), documents (upload with OCR, ask, analyze, expiring download link, bad-file rejection, ownership 403),
action plans (generate/get/complete step), drafts (case summary, lawyer brief, RTI), audit (403 for non-admin), OpenAPI schema.
Run `PYTHONPATH=. python scripts/smoke_test.py` to repeat.

## Not done / know before launch
- No automated pytest suite yet (scripts/smoke_test.py is a manual end-to-end check).
- Not run against the real Gemini API. Set AI_PROVIDER=gemini + GEMINI_API_KEY and re-test chat quality; change of
  embedding provider needs `generate_embeddings --rebuild`.
- All seeded data is DEMO; nothing is VERIFIED. Check citations against official sources before showing real users.
- Case search only covers cases stored in this DB (no live eCourts integration).
- File storage is local-private only (S3 not wired). Document processing is synchronous (job table ready for a worker).
- OpenAPI schema is generated but many APIView endpoints lack serializer annotations (warnings only).

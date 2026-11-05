# API reference

Run the backend and use `/docs` for request models, field constraints and all routes, or export `/openapi.json`. Responses include HTTP 422 for invalid input, 404 for unknown resources, 409 for duplicate product IDs, 413 for oversized uploads, 415 for unsupported upload formats, and 401 when configured API-key protection fails. Upload parsing failures are persisted as document records with `status=error` and a bounded error field, returned with HTTP 201 because the processing record was created.

| Group | Routes |
|---|---|
| Health | GET `/api/health`, GET `/api/system/status` |
| Products | GET/POST `/api/products`, GET/PUT/DELETE `/api/products/{id}`, POST `/api/products/compare` |
| Documents | GET `/api/documents`, POST `/api/documents/upload`, GET/DELETE `/api/documents/{id}`, POST `/api/documents/{id}/process` |
| Graph | GET `/api/graph/statistics`, GET `/api/graph/nodes`, GET `/api/graph/relationships`, GET `/api/graph/product/{id}`, POST `/api/graph/build` |
| Retrieval | POST `/api/graphrag/query`, POST `/api/graphrag/search`, GET `/api/graphrag/history` |
| Agents | POST `/api/agents/execute`, GET `/api/agents/status`, GET `/api/agents/traces/{id}` |
| Explainability | POST `/api/explainability/explain`, GET `/api/explainability/evidence/{id}` |
| Evaluation | POST `/api/evaluation/run`, GET `/api/evaluation/results`, GET `/api/evaluation/metrics` |
| Analytics | GET `/api/analytics/overview`, GET `/api/analytics/retrieval`, GET `/api/analytics/agents` |
| Settings | GET/PUT `/api/settings` |

Query example:

```json
{"query":"Find laptops with 16GB RAM and SSD under $1200","top_k":5,"method":"hybrid"}
```

Methods: `hybrid`, `graph`, `vector`, `keyword`. Responses include answer, claims, evidence, interpreted requirements, validation, explanation, trace ID, agent traces and measured latency. Search currently executes the same full pipeline and returns evidence plus its saved query identity.

Products/document/history list routes return `{items,total,offset,limit}`. Product filters: `q`, `domain`, `brand`. Documents filter by `origin`. List limits are bounded at 100. Product comparison accepts `{"product_ids":["P0001","P0008"]}`. Explain accepts `{"query_id":"<saved query ID>"}`. Upload uses multipart `file` plus optional boolean `synthetic`. Settings accepts retrieval weights (sum 1), top_k 1–30 and retry_limit 0–3.

When `PG_API_KEY` is set, send `X-API-Key` on API requests. The health route remains public. Production reverse proxies should also restrict the interactive documentation and enforce HTTPS and rate limits. Provider keys are only environment variables and are never sent to the frontend.

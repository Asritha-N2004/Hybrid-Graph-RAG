# Data dictionary

| Record | Main fields and meaning |
|---|---|
| Product | Stable ID, display name, brand/category IDs and labels, domain, description, optional price, ISO-style currency string, specification map, feature/compatibility arrays, synthetic flag |
| Brand | B001–B050, fictional name, synthetic flag |
| Category | C001–C100, domain and subcategory label |
| Specification CSV | product_id, key, value; linked to products by exact ID |
| Relationship CSV | source, target, type; synthetic generation records specification, brand and category links |
| FAQ | FAQ001–FAQ100, product_id, question, answer, synthetic flag |
| Document | ID, filename, status, size, content hash, synthetic flag, origin, product_ids, pages, chunks, optional parsing error |
| Chunk | Deterministic ID, text and page; provenance inherited from parent document |
| Query | ID/trace_id, original text, method, timestamps, answer, claims, evidence, validation, explanation, traces, attempt count, latencies |
| Claim | Product ID where applicable, structured field, value, evidence_ids |
| Evidence | Chunk/source identity, page, text, synthetic flag, product IDs, per-channel scores, weighted contributions, fusion/rerank score, real graph paths |
| Trace | Agent, status, start/end timestamps, elapsed milliseconds, input/output summaries, error, trace ID |
| Evaluation | ID, timestamp, per-query results, per-method metrics, protocol and explicit RAGAS not-run status |

RAM/storage/VRAM use GB; battery duration hours; battery capacity mAh; price is a fictional USD amount; weights grams; power watts; capacity liters. Specification names encode units. These generated values are not validated hardware configurations or vendor specifications. Distinguish the canonical structured source from an independently verified source: canonical means the app's authoritative product record, not real-world truth.

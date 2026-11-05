# User guide

1. Start backend and frontend using README. Overview metrics initially show empty query history rather than fabricated activity.
2. Open Product knowledge to search by name, ID or text; choose a category, page through records and inspect a product's features/specifications.
3. In Knowledge graph enter a product ID such as P0001. Pan, zoom, select nodes or edges, and filter node types. The badge states which graph backend is active.
4. In GraphRAG chat ask a question with clear requirements. Select a retrieval method for comparison. Inspect source cards for page/chunk IDs, weighted score contributions, and graph paths. Clicking a source title reveals full extracted text.
5. Explainability shows intent, constraints, inferences, source evidence and validation. Trace expanders reveal input/output summaries and timings, not hidden model chain-of-thought.
6. Agent monitor shows ten task functions, aggregate execution metrics, and saved trace inspection. Refresh after running additional queries.
7. Compare products by selecting two to eight records and clicking Compare. Missing fields remain unavailable; source availability is explicit.
8. Upload a TXT/PDF/DOCX/CSV/JSON source in Documents. Check synthetic if appropriate. For structured imports use the exact schema in `datasets/products.json` or CSV. Successful indexing is synchronous and may take several seconds. Preview, reprocess or delete source records from the table.
9. Run a benchmark in Evaluation to compute actual metrics. Read the protocol and limitations; no LLM judge scores are fabricated.
10. Settings edits fusion weights, top K, and retry limits. Provider/model credentials live on the server. Enter a backend access key only if your backend is configured to require it.

Source support is not external verification. Synthetic records and uploaded information cannot be used as verified market information without independent checking.

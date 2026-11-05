# Methodology

1. **Dataset generation:** seed 42; 500 fictional records spanning seven domains, 100 subcategories and 50 fictional brands. Prices and specs are generated, never scraped or represented as current market facts.
2. **Cleaning:** UTF-8 input, control-character removal, bounded parsing, deterministic identity fields, Pydantic structured-product validation.
3. **Entity extraction:** exact existing product IDs and known names in document text. CSV/JSON with the Product schema can add/update structured entities. Unknown prose entities are not automatically promoted to verified products.
4. **Graph construction:** materialize product/specification/brand/category/feature/price/compatibility/document nodes and relationship types; resolve stable IDs and sync the dedicated Neo4j namespace when available.
5. **Chunking:** document page boundaries retained; 1,100-character windows at 900-character stride; deterministic chunk IDs. Logical page conventions are documented explicitly.
6. **Embedding and indexing:** selected provider embeds identical text/query representations, with matching dimensions. Persistent collections are separated by provider/model/dimension. BM25 uses independent term frequencies and IDF.
7. **Hybrid retrieval:** independently retrieve channels, normalize, fuse, enforce category and numeric constraints, rerank, deduplicate products, aggregate canonical source evidence.
8. **Orchestration:** ten real functions in a LangGraph with parallel retrieval and validation-controlled retry, capped at settings.retry_limit + 1 attempts.
9. **Explainability:** persist source identities, page/chunk positions, graph edges, component scores, weighted contributions, interpreted requirements, unsupported claims and execution summaries.
10. **Evaluation:** four retriever configurations on five deterministic synthetic constraint queries; structured ground truth independent of retrieved IDs. Report measured retrieval metrics separately from unrun LLM-judged metrics.

No claim of statistical significance is made. Additional held-out natural-language queries, human annotation, trained semantic embeddings and repeated external-provider trials are required for publishable comparative conclusions.

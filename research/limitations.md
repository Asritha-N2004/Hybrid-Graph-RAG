# Limitations and deployment boundary

- This is a runnable single-process research application prepared for deployment, not a certified production service or published cloud deployment.
- The default hashing embedding is lexical; it does not satisfy learned semantic retrieval quality. Sentence Transformers/API integration is available but must be installed/configured and independently tested.
- The LLM adapter selects evidence-backed claim indices; natural-language factual content is rendered deterministically. Open-ended prose generation, streaming, and conversation-context resolution are not implemented.
- Intent and requirement extraction use patterns, not unrestricted NLP. Positive numeric minimums and an upper price bound are supported. Negative constraints, complicated disjunctions, many units, arbitrary categories and vague price comparisons are not generally supported.
- For machine-learning queries, GPU VRAM >=8 GB is a disclosed heuristic. It does not establish CUDA availability, training performance, software support, or suitability for a particular workload.
- Prose extraction resolves known product IDs/names. Full ontology induction, unrestricted NER, general relation extraction and multi-hop graph reasoning are not implemented. CustomerRequirement is represented in query state rather than a persistent graph node.
- Graph nodes carry eight domain types and generic Neo4j labels. Some requested relationship kinds (such as arbitrary RELATED_TO) are not generated without a supported source.
- Numeric contradiction detection looks for exact keyed fields; it cannot detect all contradictions or verify uploaded documents. Boolean and qualitative contradictions need further work.
- Evidence validation establishes exact source-field agreement, not real-world verification or full semantic entailment. Uploaded narrative excerpts are quotations, not independently verified facts.
- Original binary uploads are not retained. Successful documents retain extracted page text, allowing re-chunk/reindex. Failed parsing requires a corrected re-upload. Scanned PDF OCR is not implemented.
- Dataset generation currently writes complete synthetic fixtures on a fresh database. Document deletion removes its index evidence but leaves structured product records; comparison reports missing canonical sources explicitly.
- SQLAlchemy stores JSON payload records rather than normalized tables. In-memory full-index rebuilds are suitable for the sample scale, not millions of products. One backend worker is required; mutations and queries use a process-local gate.
- API-key protection is optional for local development. Multi-user identity, per-record authorization, rate limits, antivirus scanning, background job queues, migration tooling and distributed consistency are future production work.
- Optional Neo4j, PostgreSQL, FAISS, API embeddings, Sentence Transformers and LLM integrations require separate integration tests. Docker/cloud deployment is supplied as configuration and is not represented as verified execution unless recorded in the verification report.
- Five synthetic query cases and deterministic ground truth are insufficient for publication-level performance claims. RAGAS faithfulness/answer relevance are not run and are never substituted by fabricated percentages.

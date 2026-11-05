# ProductGraph Intelligence

**A Hybrid GraphRAG and Multi-Agent Architecture for Explainable Product Knowledge Retrieval**

A connected Next.js / FastAPI application with a real ten-agent LangGraph workflow, three independent retrievers, persistent source provenance, a product knowledge graph, upload processing, explainability, and a reproducible synthetic benchmark. All generated products, prices, brands, specifications, and manuals are **fictional synthetic data**.

## Sign in and deployment

The app includes `/login`, one-time owner-account setup, scrypt password hashes, revocable HTTP-only sessions (12 hours), sign-out, failed-login throttling and API authentication. Public self-registration is disabled. Set a private `PG_SETUP_TOKEN` on the backend and open `/login#setup=<token>` to create the first owner account. The token cannot create a second owner. Never commit setup tokens or passwords. `PG_REQUIRE_AUTH=0` is available only for explicit local testing; authentication is enabled by default.

The project now supports a combined **Vercel Services** deployment: Next.js frontend plus FastAPI backend, with durable records and extracted documents in dedicated PostgreSQL. Run `python scripts/prepare_vercel.py` to stage `cloud-backend`, connect `DATABASE_URL` to a dedicated database, and set `PG_VERCEL_SERVICES=1` for the frontend build. The root `vercel.json` routes `/api/*` to Python and other paths to Next.js. Hosted graph/vector indexes are rebuildable NetworkX/NumPy caches; the offline SHA-256 hashing vectors are explicitly lexical. Local Chroma/Sentence Transformers modes remain available. Hosted uploads are limited to 3 MB. Secrets are excluded from source uploads and source archives.

## Start locally

Requirements: Python 3.12, Node 22 or newer, and pnpm 11. The default mode needs no paid API or external database.

In a terminal in `backend`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal in `frontend`:

```powershell
corepack enable
pnpm install --frozen-lockfile
pnpm dev
```

On macOS/Linux activate the virtual environment with `source .venv/bin/activate`. Open [the dashboard](http://localhost:3000), [interactive API documentation](http://localhost:8000/docs), or [OpenAPI JSON](http://localhost:8000/openapi.json). First startup generates the dataset, seeds SQLite, and builds the graph and vector collection. This can take a minute on Windows. Keep one backend worker for this local in-process indexing design.

Try: `Find laptops suitable for machine learning with 16GB RAM and SSD`.

## What works

- Ten connected dashboard sections: overview, product explorer, React Flow graph, chat/history, agent traces, explainability, comparison, document management, evaluation, settings.
- 500 synthetic products, 50 fictional brands, 100 category records, over 1,000 specifications and relationships, 100 FAQs, 50 sample manuals. CSV and JSON files are in `datasets`.
- Product CRUD, specification filters, budget parsing, explicit ID lookup, comparison, and source index updates.
- CSV/JSON structured-product imports and PDF/DOCX/TXT uploads; content hashes, source IDs, chunk IDs, page provenance, processing errors, preview, reprocessing, and deletion.
- Independent BM25, cosine-vector, and graph retrievers; normalized configurable weighted fusion, deduplication, explicit requirement reranking, and canonical source expansion for claim support.
- Real LangGraph StateGraph with parallel retrieval, validation-driven bounded retries, ten agent functions, and persisted per-agent traces.
- Claim-level evidence checks, synthetic labeling, contradiction warnings for explicitly keyed numeric specifications, and missing-evidence abstention.
- Persistent Chroma collections; Neo4j synchronization and parameterized graph queries when configured; clearly labeled NetworkX fallback.
- Live analytics; benchmark runs across four methods with product-level Precision@5, Recall@5, MRR, context metrics, latency, and claim coverage.
- Dockerfiles, Docker Compose, backend API-key protection, environment configuration, architecture and research documentation, integration tests, and frontend production build.

## Providers and honest operating modes

The default embedding provider is a 1,024-dimensional normalized hashing vectorizer. This is a **lexical offline fallback**, not a learned semantic model. Chroma persists those explicitly identified vectors. If Chroma is unavailable the engine uses FAISS when installed, otherwise NumPy cosine search. System status always reports the active implementation.

To enable learned semantic search:

```powershell
python -m pip install -r requirements-ai.txt
$env:EMBEDDING_PROVIDER='sentence-transformers'
$env:EMBEDDING_MODEL='sentence-transformers/all-MiniLM-L6-v2'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The model downloads on first use. For API embeddings, set `EMBEDDING_PROVIDER=api`, `API_EMBEDDING_MODEL`, `OPENAI_API_KEY`, and `OPENAI_BASE_URL`. Model identity and dimensions produce a separate Chroma collection. Provider initialization errors are visible rather than silently swapping models.

With `OPENAI_API_KEY`, the OpenAI-compatible chat endpoint selects relevant evidence-backed claim indices. Factual responses are rendered from those source fields, preventing arbitrary generated prose from bypassing validation. Without a key, deterministic evidence rendering is used. This implementation deliberately constrains LLM generation; it does not claim unrestricted conversational reasoning or streaming support.

Neo4j: configure `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`, then restart. The app uses the dedicated `PGEntity`/`productgraph` namespace, a uniqueness constraint and type index, and parameterized Cypher. Reserve this namespace for this app. The in-process NetworkX graph remains a local traversal mirror; status shows fallback if Neo4j is unavailable. Domain types and relationship kinds are properties of generic Neo4j entities/edges, not separate physical labels.

Use a PostgreSQL URL such as `postgresql+psycopg://user:password@host/productgraph` to change the relational store. The default SQLite schema stores typed JSON records behind SQLAlchemy; JSON fields are not normalized into relational tables.

## Container deployment

Create a root `.env` file with a strong `NEO4J_PASSWORD`. Then:

```sh
docker compose up --build
```

Compose runs frontend, backend, and Neo4j with persistent volumes and localhost-bound ports. It is a deployment starting point, not a claim that cloud infrastructure was provisioned or tested. For Render/Railway use the backend Dockerfile with a persistent disk, `PG_DATA_DIR`, an API key, and exact CORS origins. For Vercel import `frontend`, set `BACKEND_URL` to the reachable HTTPS backend, and deploy; do not place provider credentials in `NEXT_PUBLIC_*` variables. Neo4j Aura can be selected with its TLS URI and server-side credentials. See `docs/deployment.md` before exposing services publicly.

## Verify

```sh
# backend (active environment)
python -m pytest
# frontend
pnpm typecheck
pnpm build
```

The test suite covers dataset integrity, agent execution, numeric requirements, score consistency, citations, bounded retry/abstention, input validation, duplicate uploads, PDF/DOCX parsing, CRUD/index freshness, graph paths, and benchmark calculations. See `docs/verification.md` for checks actually run in this delivery. Optional external providers require their own credentials and integration runs.

## Research scope

The attached brief ended at research phase 5. The implemented protocol continues through indexing, retrieval, orchestration, validation, and a reproducible benchmark; no missing attachment text was assumed to be supplied. Read `research/methodology.md`, `research/evaluation_protocol.md`, and `research/limitations.md`. LLM-judged RAGAS faithfulness and answer relevance remain **not run**, not invented scores. Suitability for machine learning is a disclosed GPU-memory heuristic, not a real benchmark or purchase recommendation.

MIT licensed. Source code and synthetic samples may be reused under `LICENSE`.

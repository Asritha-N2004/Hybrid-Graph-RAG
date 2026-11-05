# Verification performed

Verified locally on Windows with Python 3.12.10 and Node 24.22.1 on 5 November 2026.

## Hosted login deployment update

Vercel production deployment `dpl_Ffdi5KBYFMp2zhVoRpEytTYFqmn8` reached READY at `https://productgraph-intelligence.vercel.app`. The app uses a dedicated Neon Free PostgreSQL database. The hosted build includes Next.js frontend and FastAPI backend services. The Python dependency manifest is explicit in the generated cloud-backend pyproject.

After authentication was added, **15 backend tests passed** (including first-owner setup, invalid setup token, scrypt storage, HTTP-only cookies, login, logout/revocation, session expiry, throttling, origin checks and retrieval regression tests). Frontend TypeScript passed and Vercel completed the production build with `/login` present.

Live checks: `/login` HTTP 200; `/api/health` HTTP 200; `/api/auth/status` reports authentication and first-owner setup required; `/api/auth/me` reports unauthenticated; `/api/products` rejects unauthenticated requests with HTTP 401. Browser review confirmed `/dashboard` redirects to `/login`. A separate cloud-profile smoke test used the dedicated PostgreSQL store and the lightweight SHA-256 hashing/NumPy cache, confirming 500 records, ten-agent query validation, upload, index rebuild and deletion.

The owner has not been assigned a default password. A private setup link is provided separately from project source so the owner can choose an email and password. The production owner-account creation step remains for the user; it is not claimed as completed. Private environment files and setup credentials are excluded from the source ZIP and Vercel uploads.

The table below records the earlier local-only verification and is superseded above for cloud/login capabilities.

| Check | Observed result |
|---|---|
| Backend integration suite | **13 passed**, 2 third-party deprecation warnings; final run 37.78 seconds |
| Frontend TypeScript | Passed standalone typecheck and Next.js build-time checks |
| Production build | Next.js 16.4.5 webpack build completed, including route generation and build traces |
| Live HTTP smoke test | All ten dashboard routes returned HTTP 200; API proxy returned backend status |
| Browser query | Returned synthetic laptop recommendations satisfying parsed RAM, SSD and GPU VRAM conditions, canonical source citations, evidence cards and validation results |
| Browser graph | Rendered product neighborhood, real relationship edges, controls and node-type filtering |
| Browser agent monitor | Displayed all ten agents and the saved execution trace with durations |
| Browser settings | Reported ChromaDB persistent, NetworkX fallback, hashing-1024 lexical embeddings, SQLite and deterministic generation; no API model configured |
| Responsive check | 390×844 viewport: navigation toggle opened and Documents navigation completed; viewport override reset |
| Dataset integrity | 500 products, 50 brands, 100 category records, 100 FAQs, 50 manuals; relational IDs checked |
| Parsing | PDF pages and DOCX text parsed using real format libraries; DOCX pagination deliberately unavailable |
| Final exports | Live OpenAPI schema, measured 20-run benchmark and source-backed example response included |

Regression tests additionally cover duplicate uploads, malformed files, byte/format constraints, product CRUD/index refresh, graph path integrity, requirement filtering, exact score provenance, citations, abstention, retry bounds, keyed numerical contradictions, API-key guard and headphone/phone disambiguation.

Third-party warnings: the installed AnyIO test plugin references a pytest alias scheduled for removal in pytest 10; Starlette recommends its newer httpx2 test transport. Neither warning caused a failed test. Dependency ranges keep pytest below 10.

Turbopack failed to spawn its CSS compiler subprocess within the Windows sandbox. The verified frontend scripts explicitly select webpack. SQLite/Chroma and loopback networking also required execution outside that sandbox; final test/build/HTTP checks ran successfully with approved local execution. This is an execution-environment constraint, not an asserted cloud test.

The actual runtime exercised **NetworkX**, **ChromaDB**, **offline hashing vectors**, **SQLite**, **LangGraph**, and **deterministic answer rendering**. Neo4j, PostgreSQL, Sentence Transformers, FAISS, API embeddings, OpenAI-compatible LLM requests, Docker builds, GitHub Actions and cloud hosting were **not executed** in this environment. Their configuration/adapters are supplied, not claimed verified.

No LLM-judged RAGAS evaluation was run. Faithfulness and answer relevance remain null. The synthetic benchmark is small and constraint-heavy; no claim of hybrid superiority or statistical significance is made. See `research/limitations.md` for incomplete production and research scope.

Exact key package versions exercised: FastAPI 0.141.1, Pydantic 2.13.4, SQLAlchemy 2.0.57, Uvicorn 0.52.1, LangGraph 1.2.11, langchain-core 1.6.0, ChromaDB 1.5.9, NumPy 2.5.1, scikit-learn 1.9.0, NetworkX 3.6.1, PyMuPDF 1.28.2, python-docx 1.2.0, pytest 9.2.0. Frontend direct and transitive versions are recorded in `frontend/pnpm-lock.yaml`.

Dependency documentation consulted: [Next.js installation](https://nextjs.org/docs/app/getting-started/installation), [LangGraph package metadata](https://pypi.org/project/langgraph/), and [LangGraph API reference](https://reference.langchain.com/python/langgraph/overview). Package installation and actual build/test results, rather than a claim about latest versions, determined compatibility here.

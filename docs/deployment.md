# Deployment preparation

The repository is designed for local execution and contains deployable service definitions. No account, repository, cloud database, or public deployment is created automatically.

## Containers

Build context is the project root for both Dockerfiles. Compose binds ports to loopback and uses persistent backend and Neo4j volumes. Set root `.env` NEO4J_PASSWORD before starting. The sample Compose enables Neo4j and offline hashing embeddings; to use Sentence Transformers create an image that installs `backend/requirements-ai.txt`, set EMBEDDING_PROVIDER and provide model cache storage. Keep one backend worker.

The Next.js API proxy uses BACKEND_URL; standalone builds bake rewrite destinations during the build. For the provided Compose deployment the frontend Dockerfile builds with `BACKEND_URL=http://backend:8000`. For a separate hosting platform set the correct backend URL at build time and runtime. Never use a localhost destination in a remotely hosted frontend.

## Render / Railway backend

Use `backend/Dockerfile` with project-root context, a persistent mounted directory assigned to PG_DATA_DIR, one worker, Python 3.12, and `/api/health` for readiness. Use PostgreSQL for the record store where desired. Set exact CORS_ORIGINS, PG_API_KEY, and optional provider credentials via the platform secret manager. Ensure vector storage is writable and persistent.

## Vercel frontend

Set project root `frontend`, Node >=22, pnpm install using the lockfile, and build `pnpm build`. Configure HTTPS BACKEND_URL at build time. Users may enter PG_API_KEY as a tab-scoped backend access key; for a multi-user deployment replace this shared-key design with an authenticated server session and proper per-user authorization.

## Neo4j Aura

Use the supplied encrypted URI, credentials in backend secrets, and an application-specific database/namespace. Startup sync replaces only this app's `PGEntity` namespace. Do not share this namespace among independent deployments. Generic entity type and relationship type properties are indexed/queried by parameterized Cypher.

## Production gaps

Add multi-user identity and authorization, API/parse rate limiting, worker queues, upload malware inspection, migrations, encrypted backups, observability, distributed indexing and mutation coordination before treating this as a multi-tenant production service. Scope request body size at the reverse proxy as well as the application. External services and cloud deployment must be exercised with real credentials. Do not report them as verified from local tests alone.

# Vercel deployment handoff

The deployable Next.js project is `frontend/`. Set that as the Vercel project root, use the Next.js preset, and use the committed pnpm lockfile. `frontend/vercel.json` declares the build and install commands. Deploy only after configuring a reachable HTTPS `BACKEND_URL` in Vercel for the target environment.

The current backend requires persistent writable storage for SQLite/Chroma and a single backend worker. Deploy it as the supplied container on a suitable host with a persistent disk, or migrate the persistence layer before running it as serverless functions. Pointing a Vercel frontend at localhost will not connect it to the developer's machine.

## Required inputs

- A connected Vercel account with permission to create/deploy the project.
- A hosted backend HTTPS base URL, without `/api` (the proxy adds `/api`).
- If the hosted backend enables `PG_API_KEY`, use the dashboard's tab-scoped backend access-key field. Provider credentials stay on the backend.

## Deploy and verify

1. Configure `BACKEND_URL` on the Vercel project before the build. The configuration fails early on missing, non-HTTPS, or localhost targets in Vercel.
2. Deploy `frontend/` to the chosen Vercel project.
3. Wait for a successful deployment, then verify `/dashboard`, `/api/health`, and `/api/system/status` on the returned deployment URL.
4. Submit a synthetic query, confirm evidence/source cards, and check document access through the deployed frontend.
5. Report the actual returned deployment URL only after deployment succeeds; a local build or prepared configuration is not a deployment.

This preparation does not create a Vercel deployment, provision backend hosting, or incur a paid hosting subscription.

# Live Vercel deployment

- Login: https://productgraph-intelligence.vercel.app/login
- Vercel workspace/project: resum-projects / productgraph-intelligence
- Production deployment: dpl_Ffdi5KBYFMp2zhVoRpEytTYFqmn8
- Frontend: Next.js service.
- Backend: FastAPI service, Python 3.12.
- Durable records, extracted documents, accounts and sessions: dedicated Neon Free PostgreSQL database.
- Retrieval caches: NetworkX graph and NumPy cosine vectors, rebuilt from persisted source records. Hosted SHA-256 hashing is an explicitly lexical fallback, not a semantic embedding model.
- First sign-in: use the separately supplied private owner setup link to choose an email and password. Subsequent visits use `/login`.
- Source staging: run `python scripts/prepare_vercel.py` before redeploying the project root.

No paid plan upgrade was selected. Free-tier resource limits and availability still apply. Multi-user tenancy, password-reset email delivery and MFA are outside the implemented single-owner workspace scope.

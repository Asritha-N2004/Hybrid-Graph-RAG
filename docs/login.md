# Dashboard authentication

- `/login`: responsive sign-in page with email/password, password visibility toggle, loading and validation states.
- Owner setup: the deployment owner receives a private fragment-based setup link. It permits first-account creation only; the password is chosen in the browser. There is no hardcoded/default password and public self-registration is disabled.
- Password storage: random 16-byte salt and scrypt (N=16384, r=8, p=1, 32-byte output). Plain passwords are never persisted or returned.
- Sessions: random 48-byte bearer token in an HTTP-only cookie, Secure on Vercel, SameSite=Lax, 12-hour expiry. Only the SHA-256 digest of the session token is stored in PostgreSQL. Logout revokes that session.
- API protection: `/api/*` requires a valid session except health and explicit authentication endpoints. Authentication-disabled mode is opt-in for local tests. Mutation requests check Origin when present.
- Throttling: five unsuccessful attempts per normalized email within 15 minutes trigger a 15-minute lockout. Distributed requests are serialized in the serverless profile with a PostgreSQL advisory lock.
- Deployment: user/session/attempt records persist in the dedicated PostgreSQL database. Vercel Deployment Protection may additionally require the project owner's Vercel sign-in.

This is a single-owner research workspace. Password reset email delivery, MFA, multiple workspace memberships and public account registration are not implemented. Email addresses are login identifiers, not verified email ownership. Recovering a lost owner password requires a controlled backend administration flow; do not expose a public reset endpoint without verification.

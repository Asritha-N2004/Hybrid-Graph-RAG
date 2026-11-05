# Login and opening latency

The initial Vercel deployment ran backend functions in iad1 while the dedicated PostgreSQL database was provisioned in sin1. Live measurements from the user's machine showed warm health/session requests around 1.76–1.91 seconds and owner-status requests around 2.66 seconds.

The optimized deployment pins functions to sin1, beside the database. Read-only health, owner-status and session checks no longer enter the distributed index lock. Retrieval caches initialize on demand for graph/query/settings/overview operations, instead of loading during every authentication cold start. Relational reads run without the index lock; mutations retain distributed serialization, and index-consuming requests still check the persisted revision to avoid serving stale indexes.

Authentication checks remain server-side. Password hashing, session expiry, cookie protections, origin checks and failed-login throttling are unchanged. A free-tier cold start or database resume can still add latency after inactivity; warm endpoint measurements do not guarantee every login duration.

Verified production deployment: `dpl_DVajNSWrgx9V4Fu978nrgAXsHRhr`, READY. Live response headers confirm execution in sin1. After rollout, warm session check was 198 ms (previously 1759 ms), owner-status check 153 ms (previously 2674 ms), and health check 346 ms (previously 1764 ms). The first three new-deployment samples were 702/642/432 ms. These are endpoint/network measurements from the user's machine, not full authenticated password-submit or dashboard render measurements. All 15 regression tests and cloud PostgreSQL retrieval/upload checks passed. Unauthenticated products access still returns HTTP 401. Raw post-rollout samples are in `performance-measurements.json`.

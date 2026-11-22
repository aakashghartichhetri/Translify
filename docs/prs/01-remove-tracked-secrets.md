# PR 1 — security: remove tracked environment configuration

**Head:** `security/remove-tracked-secrets`  
**Base:** `main` (upstream SHA `c2e648cdd6fc9ee67bb1e841c3b28e500f13d667`)

**Problem / evidence:** `server_core/.env` is tracked by Git despite ignore patterns. The repository has previous commits involving environment configuration. It is unsafe to assume all historical versions contain non-secret placeholders.

**Solution / reasoning:** Remove the file from the *Git index* (not user disk), strengthen repository ignore rules, add placeholder-only `.env.example` and Docker ignore patterns. Keep runtime credentials in environment variables/deployment secret manager.

**Tests:** The CI security job checks that no dotenv file except `.env.example` remains tracked; this is **not yet executed** against GitHub. Verify locally with `git ls-files '*/.env'` and inspect the diff without dumping secret contents.

**Risks / follow-up:** Old commits and forks can still contain values; credential owners must privately determine rotation, exposure, and any history-rewrite response. No secrets were rotated, history rewritten, or remote changes made.

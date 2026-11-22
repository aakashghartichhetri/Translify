# PR 7 — docs: factual README, architecture, risks and attribution

**Head:** `docs/readme-and-architecture`  
**Base:** `ci/flutter-fastapi-verification`

**Problem / evidence:** README claims about LibreTranslate/real-time performance and code paths were not aligned with the current NLLB and service implementations. Original team attribution needed to be preserved while documenting new work distinctly.

**Solution / reasoning:** Replace the root README with a concise capstone overview (500–750 words), architecture diagram, commands, test status, privacy boundaries, limitations, and all four contributor names. Add technical review, credential response, and performance/quality evaluation notes. Include a script for preparing stacked local branches without pushing.

**Tests:** README word count checked locally; Python test results documented precisely. Installation and Flutter commands are documented but not claimed to have been run successfully in a fresh environment.

**Risks / follow-up:** Update factual metrics only after real demonstrations; verify individual attribution with contributors and git blame. Do not claim sole ownership or independently validated translation quality.

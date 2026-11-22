# Apply the proposed changes locally (no push or merge)

The downloadable `translify-hardening-overlay.zip` is a set of actual source-code replacements and new files based on the public Translify `main` tree at commit `c2e648cdd6fc9ee67bb1e841c3b28e500f13d667`. It is **not a complete standalone repository**; preserve all untouched upstream files.

1. Obtain a **complete, clean** upstream checkout from a trusted source. Check `git rev-parse main` and confirm the audited SHA; if it changed, re-audit and rebase rather than forcing these patches.
2. Unzip the overlay next to that checkout. The unzipped top directory is `translify-hardening-overlay`.
3. Verify your own Git author identity (`git config user.name` and `git config user.email`).
4. Run the following **local-only** command from the directory containing both folders:

```bash
bash translify-hardening-overlay/scripts/prepare_local_branches.sh \
  ./Translify ./translify-hardening-overlay
```

The script checks the base SHA and clean working tree, then creates seven stacked local branches with descriptive commits. It copies replacement files, *de-indexes without deleting* `server_core/.env` and the generated OCR snapshot, and stops. It does **not** call `git push`, open PRs, merge, deploy, rotate secrets, or rewrite published history. Check `git diff main...docs/readme-and-architecture --stat` and each `docs/prs/*.md` PR description before publishing anything. You should review whether either de-indexed file contained sensitive information without displaying its values in public output.

`translify-hardening-local-review-branches.bundle` is a **separate proposal-only history** assembled locally, so you can inspect seven review branches even without the upstream checkout. **It is not based on upstream Git objects and must not be merged into the real repository as though it were an upstream PR.** The source overlay and branch-preparation script are the supported way to apply changes onto the authentic upstream history.

```bash
# Optional: inspect the proposal-only branch history (not the upstream checkout)
git clone translify-hardening-local-review-branches.bundle review-proposal
git -C review-proposal branch -a
```

Before merging any branch, run the Python suite and smoke tests, Flutter analysis/tests and Android/iOS builds, real-model processing checks, and PostgreSQL-specific migration tests. The PR notes distinguish tests completed locally from those that still require verification. No approval or green GitHub CI run is implied.

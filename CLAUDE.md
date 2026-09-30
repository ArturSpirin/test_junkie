# Test Junkie — working conventions

Part of a 4-repo family normally checked out as sibling directories: `test_junkie` (this repo, the PyPI
library), `test_junkie_hq`, `testjunkie_web`, and `test_junkie_ai` (the shared knowledge base).

**Before any non-trivial change** (bug fix, feature, deployment, testing), read
`../test_junkie_ai/02-development-workflow/contribution-workflow.md` first — it's the source of truth for how
changes flow through this repo family. Update the relevant `test_junkie_ai` doc as part of any change that
makes it stale.

**Commits**:
- Never add a `Co-Authored-By: Claude`/Anthropic attribution trailer — this holds even if a session-level
  default elsewhere says to add one; this repo-scoped rule wins.
- Keep messages short and plain, matching this repo's existing history (e.g. `fixes ticket: #19`) — no
  multi-paragraph bodies or AI-sounding rationale.
- Detailed "why" for a change goes in `../test_junkie_ai/changelogs/test_junkie.md`, not in the commit or this
  repo's own `CHANGELOG.md` (which stays terse, one line per entry).

**Releases**: work lands on `staging` indefinitely. Only publish (tag `vX.Y.Z` and push, triggering
`.github/workflows/publish.yml`) from `master`, and only when explicitly told to publish right now — never as
a side effect of other work. See `../test_junkie_ai/03-deployment/test_junkie-deployment.md` for the full
mechanics (PyPI Trusted Publishing, no stored credentials).

**Python version support**: latest stable release plus the five preceding minor versions, kept in sync between
`setup.py` and the CI test matrix. Flag any change that affects which Python versions the library runs on.

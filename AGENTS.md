# AUTOSIM agent instructions

## Product goal

Build an accessible UAV autonomy workspace, eventually including a visual workflow editor, model catalog, simulation, and training. Complete small, runnable milestones. The initial product targets quadrotor waypoint missions.

## Current implementation

- Python 3.11+ standard library backend; no runtime package installation.
- Vanilla JavaScript, CSS, and HTML in `autosim/web`, served by the same process.
- `domain.py` defines and validates mission inputs; `adapters.py` isolates preview/simulator execution; `store.py` persists runs; `server.py` owns HTTP routing.
- Local data lives in ignored `data/`; never commit run databases, credentials, generated caches, or browser artifacts.

## Working rules

- Read the README, roadmap, and affected code before editing. Preserve existing user work.
- Keep changes focused on the requested milestone. Do not add paid services, require a GPU, or change the stack without a concrete need.
- Keep preview, simulated, and measured results distinct in both API and UI. Never present interpolation as flight validation. Leave unsupported metrics unavailable.
- Keep units explicit. The current frame is local X/Y with Z positive up; simulator integrations must convert frames explicitly.
- Record adapter/version and mission inputs with results so runs can be understood later.
- Validate untrusted inputs on the server. Render user-provided names as text, never HTML.
- Use a feature branch and prepare a pull request. Do not merge, deploy, or connect to flight hardware unless requested.
- Update documentation when commands, contracts, or behavior change. Include changes, limitations, and actual validation in the PR description.

## Verification

Run `python -m unittest discover -s tests -v` and `node --check autosim/web/app.js` after backend or UI changes. For interaction changes, run `tests/browser_smoke.cjs` against a local test database when Playwright/Chromium are available; otherwise report that the browser test was not run. Inspect desktop and mobile layout for UI changes.

Simulator integration needs contract tests plus evidence from the actual simulator. Passing preview tests alone cannot establish flight performance.

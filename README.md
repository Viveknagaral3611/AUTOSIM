# AUTOSIM

A foundation for an accessible UAV autonomy platform: configure an aircraft, plan a waypoint mission, and inspect a saved route preview.

**Status: local development prototype.** The current adapter interpolates waypoints at constant speed. It does not simulate flight physics, run a controller, train a model, or connect to hardware. Mass and sensor selections are saved as metadata. Flight success and tracking error are explicitly `null`, not measured results.

## Run locally

Install Python 3.11 or newer. No third-party Python packages, API keys, GPU, or frontend build step are required.

```bash
git clone https://github.com/Viveknagaral3611/AUTOSIM.git
cd AUTOSIM
# Until the starter PR is merged:
git switch feat/initial-workspace
python -m autosim
```

On Windows, use `py -m autosim` if `python` is unavailable. Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Stop the server with Ctrl+C.

1. Enter an aircraft name, mass, sensor payload, and route speed.
2. Edit the waypoint coordinates or use the example route. Coordinates are local X/Y with Z positive up, all in meters. The first waypoint is the starting position; takeoff and landing are not modeled.
3. Select **Generate preview**. Inspect the route, planned 3D distance, and nominal duration.
4. Scrub the position samples, play the eight-second inspection animation, or export the full run as JSON. Playback speed is independent of nominal flight duration.
5. Select a recent run to restore its saved configuration. Editing a field clears the active result so old metrics cannot be mistaken for the new configuration.

Runs persist in `data/autosim.sqlite3`, relative to the working directory. Restarting the app preserves them. Keep this file if you want to preserve your runs; it is excluded from Git. Run history shows the latest 20; older runs remain retrievable by ID.

```bash
python -m autosim --port 8080 --db data/my-workspace.sqlite3
```

This is a local, single-user workspace. Keep the default loopback host. It has no authentication or production deployment configuration; Python's development HTTP server is [not intended for production](https://docs.python.org/3/library/http.server.html).

## Included

- Responsive browser interface with drone settings, 2–20 editable waypoints, XY route view, altitude readout, playback, saved history, and JSON export.
- Same-origin JSON API with bounded requests and validated mission inputs.
- Replaceable simulator adapter and a deterministic, clearly labeled preview implementation.
- SQLite persistence, Python unit/integration tests, browser smoke script, and GitHub Actions checks.
- [Architecture](docs/architecture.md), [API contract](docs/api.md), [roadmap](docs/roadmap.md), and [agent instructions](AGENTS.md).

## Checks

```bash
python -m unittest discover -s tests -v
node --check autosim/web/app.js
```

Node.js is only needed for JavaScript checks and optional browser tests; the application runs with Python alone.

For the browser smoke test, use a second terminal with the app running and Node.js 22+ available:

```bash
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install chromium
node tests/browser_smoke.cjs
```

The script creates local test runs. Use a separate `--db data/browser-test.sqlite3` when testing. Set `AUTOSIM_URL` to override the default server URL. Optional `AUTOSIM_SCREENSHOT` and `AUTOSIM_MOBILE_SCREENSHOT` environment variables save desktop and mobile QA screenshots. CI runs the Python matrix, JavaScript syntax checks, and a separate Chromium browser job.

## Next milestone

Connect a real simulator and baseline flight controller, then validate one waypoint mission end to end. The visual workflow editor, model catalog, training jobs, and hardware deployment follow that foundation. See the [acceptance criteria](docs/roadmap.md).

No project license has been selected yet. Public repository visibility alone does not grant an open-source license. Review and choose a license before distributing the platform or importing third-party models and datasets.

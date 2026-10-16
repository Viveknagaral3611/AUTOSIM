# Development roadmap

## 1. Local mission workspace — implemented in the starter PR

- [x] Drone metadata form and validated waypoint mission contract.
- [x] Responsive XY route view with altitude readout and inspection playback.
- [x] Explicitly labeled deterministic preview adapter.
- [x] SQLite run history, configuration restore, and JSON export.
- [x] API tests, validation tests, JavaScript syntax check, and optional browser smoke test.
- [x] Setup instructions and agent guidelines.

Acceptance: a fresh checkout runs with `python -m autosim`; a user can submit a mission, inspect and export it, restart, and retrieve the persisted run. Unavailable flight metrics remain unavailable.

## 2. One real simulated flight — next

Scope: one quadrotor, one environment, one waypoint mission, one baseline autopilot/controller. Start by evaluating a PX4 SITL + Gazebo adapter; confirm current compatibility and licenses before committing to versions. Preserve the no-GPU preview mode.

- [ ] Select and pin simulator/autopilot builds; document host requirements.
- [ ] Define airframe parameters, sensor configuration, environment and local frame conversions.
- [ ] Add an isolated worker with job status, timeout, cancellation, logs, and cleanup.
- [ ] Execute one baseline mission from the UI and return actual simulated position samples.
- [ ] Define and compute tracking error, completion conditions, and collision/failure status from simulator evidence.
- [ ] Store simulator/controller versions, configuration, seed, and artifacts with every run.

Acceptance: reproduce a documented mission and a documented failure in the real simulator. Compare planned and simulated paths. Verify reported metrics against simulator logs. Do not infer success from a generated route.

## 3. Visual workflows

- [ ] Define typed nodes for aircraft, environment, planner/controller, and evaluation.
- [ ] Build the drag-and-drop editor against the working mission/job contracts.
- [ ] Validate incompatible connections, save workflows, and reproduce a run from a saved graph.

Acceptance: create and rerun the milestone 2 flight from a graph without editing code.

## 4. Curated model catalog

- [ ] Begin with a small set of compatible, verified open models and baseline policies.
- [ ] Record license, source, version, observation/action spaces, hardware needs, supported sensors, and known limitations.
- [ ] Define shared benchmarks and compare models on the same scenarios.

Acceptance: swap compatible models and compare reproducible evaluations. Avoid promising that arbitrary models or hardware work automatically.

## 5. Training and customization

- [ ] Add dataset provenance, training jobs, experiment tracking, artifact storage, and resource budgets.
- [ ] Add reproducible RL environments, reward configuration, and domain randomization.
- [ ] Evaluate held-out scenarios before reporting improvement.

Acceptance: train or fine-tune one policy, reproduce the run, and compare it with the baseline using a documented benchmark.

## 6. Hardware and broader vehicles

- [ ] Define hardware capability manifests and deployment packaging.
- [ ] Validate hardware-in-the-loop and a supervised flight test workflow.
- [ ] Expand to additional UAV types and flying/ground hybrid robots after quadrotor support is established.

Acceptance: demonstrate the documented compatibility and deployment path for one specific hardware configuration before expanding claims.

## Decisions still open

Project license, production stack, hosting, simulator version, supported flight controller, initial model licenses, and training infrastructure. Make each decision when its milestone requires evidence; no cloud spending or hardware action is part of the starter.

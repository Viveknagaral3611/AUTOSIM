# Architecture

## First milestone

One Python process serves static browser files and the JSON API. The browser submits a validated mission; the server executes the preview adapter synchronously, writes the full result to SQLite, and returns it. A 201 response means the preview was saved successfully.

| Component | File | Responsibility |
| --- | --- | --- |
| Mission contract | `autosim/domain.py` | Drone metadata, units, waypoint and speed validation |
| Adapter boundary | `autosim/adapters.py` | `SimulatorAdapter` protocol and `PreviewAdapter` |
| Run storage | `autosim/store.py` | Store complete runs and list recent summaries |
| HTTP API | `autosim/server.py` | Validate requests, execute adapter, serve fixed static paths |
| Local entry point | `autosim/__main__.py` | Host, port, database options and server lifecycle |
| Frontend | `autosim/web/` | Mission editing, route view, results, playback and history |

## Preview semantics

The first waypoint is the initial position. The route traverses each subsequent waypoint in order at a requested constant speed, with instantaneous turns. Distance is the sum of 3D Euclidean segment lengths. Duration is that distance divided by speed. The adapter returns 201 uniformly spaced samples along the total distance, including both endpoints; it does not guarantee that every intermediate waypoint is a sample.

Adjacent duplicate vertices are skipped for interpolation. They remain in the original mission metadata and waypoint count. Requests whose points are all identical are rejected. The view is an equal-scale XY projection, so vertical legs may overlap; use the altitude readout and exported trajectory for Z.

The adapter ignores mass and sensors. There are no actuator, airframe, battery, weather, collision, sensing, takeoff, or landing models. `mission_success` and `tracking_error_m` are `null`. There is no learned model or control policy.

## Persistence and execution

SQLite uses a separate connection for each operation. Runs include UUID, UTC timestamp, submitted configuration, adapter identifier, fidelity, limitations, metrics, and trajectory. There is no user/account layer. The database is local and not included in Git. Recent summaries are limited to 20; there is no deletion or retention policy yet.

The preview is bounded and cheap, so it runs inline. A real simulator requires a worker process, queued/running/completed/failed states, timeouts, cancellation, logs, and cleanup before using the same API for long jobs. Do not block HTTP requests for model training.

## Evolution boundary

`make_server(..., adapter=...)` accepts an adapter implementing `name` and `run(mission)`. Its output currently follows the preview result schema. Before adding a physics adapter, version the schema to include environment, controller, simulator build, seed, and model parameters. Define which metrics are measured, how they are computed, and their units.

The current frame has Z up. PX4/Gazebo integration must explicitly handle coordinate and orientation conversions. Mass and sensor capabilities must become validated simulator inputs rather than metadata. Preserve old run readability with schema versioning as contracts evolve.

The standard-library HTTP server is a deliberate local bootstrap choice. A multi-user service will need a production server, authentication, access controls, resource quotas, durable jobs, artifact storage, and deployment configuration.

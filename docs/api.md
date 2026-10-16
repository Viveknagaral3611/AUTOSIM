# API contract: initial workspace

Base URL: `http://127.0.0.1:8000`. JSON responses use UTF-8. All endpoints are local and unauthenticated. No CORS access is enabled.

| Method | Route | Response |
| --- | --- | --- |
| GET | `/api/health` | 200: service status and active adapter |
| POST | `/api/missions` | 201: generated, persisted preview run |
| GET | `/api/runs` | 200: `{ "runs": [...] }`, latest 20 summaries |
| GET | `/api/runs/{id}` | 200: full run; 404 if absent |

## Submit a mission

Use `Content-Type: application/json` and a nonempty body no larger than 32,768 bytes. The current endpoint is synchronous. A response is returned after the run has been saved, not merely accepted into a queue.

```json
{
  "drone": {
    "name": "Explorer Q1",
    "mass_kg": 1.5,
    "sensors": ["gps", "imu"]
  },
  "speed_mps": 3,
  "waypoints": [
    {"x_m": 0, "y_m": 0, "z_m": 10},
    {"x_m": 30, "y_m": 0, "z_m": 10},
    {"x_m": 30, "y_m": 25, "z_m": 20},
    {"x_m": 0, "y_m": 25, "z_m": 10}
  ]
}
```

Save this JSON to `mission.json`, then use:

```bash
curl -X POST http://127.0.0.1:8000/api/missions -H 'Content-Type: application/json' --data-binary @mission.json
```

| Field | Validation |
| --- | --- |
| Name | Trimmed length 1–80 characters |
| Mass | 0.05–100 kg |
| Sensors | Nonempty unique selection of `gps`, `imu`, `camera`, `lidar` |
| Speed | 0.1–30 m/s |
| Waypoints | 2–20 positions; at least two different positions |
| X/Y | −500 to +500 m |
| Z | 0–120 m, positive up |

Numbers must be finite numeric values, not strings or booleans. Extra keys are rejected at mission, drone, and waypoint levels. These ranges are prototype input bounds, not regulatory guidance or validated aircraft limits.

## Response

Full runs contain `id`, `created_at` (UTC), `mission`, `adapter` (`waypoint-preview-v1`), `status` (`preview_complete`), `fidelity` (`kinematic_preview`), `limitations`, `metrics`, and `trajectory`.

`metrics` contains `planned_distance_m`, `nominal_duration_s`, `waypoint_count`, `mission_success: null`, and `tracking_error_m: null`. `trajectory` contains 201 records with `t_s`, `x_m`, `y_m`, and `z_m`. These are ideal path samples, not measured telemetry. Mass and sensors do not affect them.

History summaries omit `trajectory`, `limitations`, and `fidelity`; retrieve a run by ID for the full result.

Errors have the shape `{ "error": "Human-readable explanation." }`: 400 for invalid JSON/mission, 404 for missing routes/runs, 413 for missing/invalid/oversize body length, 415 for the wrong content type, and 500 if execution or persistence fails. Chunked request transfer is unsupported (400).

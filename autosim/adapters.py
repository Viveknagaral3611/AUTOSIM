"""Adapters return one stable result contract; preview has no flight physics."""

from bisect import bisect_right
from math import dist
from typing import Protocol

from .domain import Mission


class SimulatorAdapter(Protocol):
    name: str

    def run(self, mission: Mission) -> dict: ...


class PreviewAdapter:
    name = "waypoint-preview-v1"

    def run(self, mission: Mission) -> dict:
        points = [(p.x_m, p.y_m, p.z_m) for p in mission.waypoints]
        # Ignore repeated adjacent positions so interpolation never divides by zero.
        vertices = [points[0]]
        for point in points[1:]:
            if point != vertices[-1]:
                vertices.append(point)
        lengths = [0.0]
        for start, end in zip(vertices, vertices[1:]):
            lengths.append(lengths[-1] + dist(start, end))
        total = lengths[-1]
        duration = total / mission.speed_mps
        trajectory = []
        # Bounded output size even for long routes or very slow requests.
        for i in range(201):
            traveled = total * i / 200
            segment = min(bisect_right(lengths, traveled) - 1, len(vertices) - 2)
            fraction = (traveled - lengths[segment]) / (lengths[segment + 1] - lengths[segment])
            position = [a + fraction * (b - a)
                        for a, b in zip(vertices[segment], vertices[segment + 1])]
            trajectory.append(dict(t_s=round(duration * i / 200, 6),
                                   x_m=position[0], y_m=position[1], z_m=position[2]))
        return {
            "adapter": self.name,
            "status": "preview_complete",
            "fidelity": "kinematic_preview",
            "limitations": [
                "Straight-line interpolation at constant speed; no dynamics or controller.",
                "Mass and sensors are recorded as metadata and do not affect this preview.",
                "No obstacles, wind, battery model, collision checks, or hardware connection.",
                "The first waypoint is the start; takeoff and landing are not modeled.",
            ],
            "metrics": {
                "planned_distance_m": round(total, 3),
                "nominal_duration_s": round(duration, 3),
                "waypoint_count": len(points),
                "mission_success": None,
                "tracking_error_m": None,
            },
            "trajectory": trajectory,
        }

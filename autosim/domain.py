"""Validate the small, explicit mission contract shared by the UI and adapters."""

from dataclasses import asdict, dataclass
import math


class ValidationError(ValueError):
    pass


def number(value, label, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label} must be a number.")
    if not minimum <= value <= maximum or not math.isfinite(value):
        raise ValidationError(f"{label} must be between {minimum} and {maximum}.")
    return float(value)


def object_with_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValidationError(f"{label} must contain exactly: {', '.join(keys)}.")


@dataclass(frozen=True)
class Drone:
    name: str
    mass_kg: float
    sensors: list[str]


@dataclass(frozen=True)
class Waypoint:
    x_m: float
    y_m: float
    z_m: float


@dataclass(frozen=True)
class Mission:
    drone: Drone
    speed_mps: float
    waypoints: list[Waypoint]

    def to_dict(self):
        return asdict(self)


def parse_mission(payload):
    object_with_keys(payload, ("drone", "speed_mps", "waypoints"), "Mission")
    drone = payload["drone"]
    object_with_keys(drone, ("name", "mass_kg", "sensors"), "Drone")
    name = drone["name"]
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValidationError("Drone name must contain 1–80 characters.")
    mass = number(drone["mass_kg"], "Mass (kg)", 0.05, 100)
    sensors = drone["sensors"]
    supported = {"gps", "imu", "camera", "lidar"}
    if (not isinstance(sensors, list) or not sensors
            or any(not isinstance(s, str) or s not in supported for s in sensors)
            or len(set(sensors)) != len(sensors)):
        raise ValidationError("Select unique sensors from gps, imu, camera, lidar.")
    speed = number(payload["speed_mps"], "Speed (m/s)", 0.1, 30)
    points = payload["waypoints"]
    if not isinstance(points, list) or not 2 <= len(points) <= 20:
        raise ValidationError("Provide between 2 and 20 waypoints.")
    waypoints = []
    for index, point in enumerate(points, 1):
        object_with_keys(point, ("x_m", "y_m", "z_m"), f"Waypoint {index}")
        waypoints.append(Waypoint(
            number(point["x_m"], f"Waypoint {index} X (m)", -500, 500),
            number(point["y_m"], f"Waypoint {index} Y (m)", -500, 500),
            number(point["z_m"], f"Waypoint {index} altitude (m)", 0, 120),
        ))
    if all(point == waypoints[0] for point in waypoints):
        raise ValidationError("At least two waypoints must have different positions.")
    return Mission(Drone(name.strip(), mass, sensors), speed, waypoints)

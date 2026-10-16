import copy
import math
import unittest

from autosim.adapters import PreviewAdapter
from autosim.domain import ValidationError, parse_mission


def example():
    return {"drone": {"name": "Test quad", "mass_kg": 1.5, "sensors": ["gps", "imu"]},
            "speed_mps": 2,
            "waypoints": [{"x_m": 0, "y_m": 0, "z_m": 0},
                          {"x_m": 3, "y_m": 4, "z_m": 0}]}


class MissionTests(unittest.TestCase):
    def test_valid_mission_round_trip(self):
        self.assertEqual(parse_mission(example()).to_dict(), example())

    def test_reject_invalid_shapes(self):
        for value in [None, [], {}, {**example(), "unexpected": True}]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                parse_mission(value)

    def test_reject_invalid_numbers(self):
        for value in [True, "2", None, math.nan, math.inf, -math.inf, 0, 101, 10**1000]:
            payload = example()
            payload["drone"]["mass_kg"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError):
                parse_mission(payload)

    def test_reject_invalid_sensors(self):
        for value in [[], ["gps", "gps"], ["radar"], [1], [["gps"]], "gps"]:
            payload = example()
            payload["drone"]["sensors"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError):
                parse_mission(payload)

    def test_reject_bad_waypoints_and_speed(self):
        payloads = []
        for points in [[], example()["waypoints"][:1], example()["waypoints"] * 11,
                       [{"x_m": 0, "y_m": 0, "z_m": 0}] * 2, [None, None]]:
            payloads.append({**example(), "waypoints": points})
        for axis, value in [("z_m", -1), ("z_m", 121), ("x_m", 501), ("y_m", -501)]:
            payload = copy.deepcopy(example())
            payload["waypoints"][0][axis] = value
            payloads.append(payload)
        for speed in [0, 31, True]:
            payloads.append({**example(), "speed_mps": speed})
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                parse_mission(payload)

    def test_preview_known_distance_and_no_validation_claims(self):
        run = PreviewAdapter().run(parse_mission(example()))
        self.assertEqual(run["metrics"]["planned_distance_m"], 5)
        self.assertEqual(run["metrics"]["nominal_duration_s"], 2.5)
        self.assertIsNone(run["metrics"]["mission_success"])
        self.assertIsNone(run["metrics"]["tracking_error_m"])
        self.assertEqual(len(run["trajectory"]), 201)
        self.assertEqual(run["trajectory"][0], {"t_s": 0, "x_m": 0, "y_m": 0, "z_m": 0})
        self.assertEqual(run["trajectory"][-1], {"t_s": 2.5, "x_m": 3, "y_m": 4, "z_m": 0})

    def test_preview_repeated_vertices_and_3d_distance(self):
        payload = example()
        payload["waypoints"] = [payload["waypoints"][0]] * 2 + [{"x_m": 0, "y_m": 0, "z_m": 12}] * 2
        run = PreviewAdapter().run(parse_mission(payload))
        self.assertEqual(run["metrics"]["planned_distance_m"], 12)
        self.assertEqual(run["trajectory"][-1]["z_m"], 12)
        self.assertEqual(run["metrics"]["waypoint_count"], 4)

    def test_metadata_does_not_change_preview(self):
        first = example()
        second = copy.deepcopy(first)
        second["drone"] = {"name": "Other", "mass_kg": 20, "sensors": ["camera"]}
        self.assertEqual(PreviewAdapter().run(parse_mission(first)),
                         PreviewAdapter().run(parse_mission(second)))


if __name__ == "__main__":
    unittest.main()

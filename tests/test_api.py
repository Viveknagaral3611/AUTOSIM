from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest

from autosim.server import make_server
from autosim.store import RunStore
from test_domain import example


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp.name) / "runs.sqlite3"
        cls.server = make_server(port=0, db_path=cls.db_path)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, path, method="GET", body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = (response.status, dict(response.getheaders()), response.read())
        connection.close()
        return result

    def submit(self):
        status, _, body = self.request("/api/missions", "POST", json.dumps(example()),
                                       {"Content-Type": "application/json"})
        self.assertEqual(status, 201)
        return json.loads(body)

    def test_health_and_static_assets(self):
        status, _, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["adapter"], "waypoint-preview-v1")
        for path, expected in [("/", b"AUTOSIM"), ("/app.js", b"readPoints"), ("/styles.css", b":root")]:
            status, headers, body = self.request(path)
            self.assertEqual(status, 200)
            self.assertIn(expected, body)
            self.assertIn("Content-Security-Policy", headers)

    def test_submit_retrieve_and_persistence(self):
        run = self.submit()
        status, _, body = self.request(f'/api/runs/{run["id"]}')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), run)
        self.assertEqual(RunStore(self.db_path).get(run["id"]), run)
        status, _, body = self.request("/api/runs")
        self.assertEqual(status, 200)
        self.assertIn(run["id"], [r["id"] for r in json.loads(body)["runs"]])

    def test_concurrent_submissions(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            runs = list(executor.map(lambda _: self.submit(), range(8)))
        self.assertEqual(len({r["id"] for r in runs}), 8)

    def test_invalid_requests_do_not_create_runs(self):
        before = len(RunStore(self.db_path).recent())
        for body in ["{", "null", "[]", "{}", '{"drone": NaN}', b"\xff", "[" * 1500]:
            status, _, response = self.request("/api/missions", "POST", body,
                                               {"Content-Type": "application/json"})
            self.assertEqual(status, 400)
            self.assertIn("error", json.loads(response))
        self.assertEqual(len(RunStore(self.db_path).recent()), before)

    def test_content_type_and_body_limits(self):
        status, _, _ = self.request("/api/missions", "POST", "{}")
        self.assertEqual(status, 415)
        for body in ["", " " * 32769]:
            status, _, _ = self.request("/api/missions", "POST", body,
                                        {"Content-Type": "application/json"})
            self.assertEqual(status, 413)

    def test_missing_routes_and_path_traversal(self):
        for path in ["/api/runs/missing", "/../autosim/server.py", "/%2e%2e/server.py", "/data/autosim.sqlite3"]:
            self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request("/missing", "POST", "{}")[0], 404)


if __name__ == "__main__":
    unittest.main()

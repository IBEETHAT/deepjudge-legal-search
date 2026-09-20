import io
import json
import unittest

from deepjudge_client.app import DeepJudgeWebApp


class StubClient:
    def __init__(self):
        self.search_calls = []
        self.analysis_calls = []

    def search_firm_knowledge(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"items": [{"title": "Result"}], "query": kwargs["query"]}

    def _make_request(self, method, endpoint, payload):
        self.analysis_calls.append((method, endpoint, payload))
        return {"ok": True, "payload": payload}


class FailingClient(StubClient):
    def search_firm_knowledge(self, **kwargs):
        raise RuntimeError("upstream details should stay private")


class DeepJudgeWebAppTests(unittest.TestCase):
    def _request(self, app, method, path, payload=None):
        body = b""
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        response_body = b"".join(app(environ, start_response))
        return captured, response_body

    def test_serves_installable_home_page(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, body = self._request(app, "GET", "/")

        self.assertEqual(captured["status"], "200 OK")
        self.assertIn("text/html", captured["headers"]["Content-Type"])
        self.assertIn(b"Add to Home Screen", body)

    def test_search_endpoint_uses_client(self):
        client = StubClient()
        app = DeepJudgeWebApp(client=client)

        captured, body = self._request(app, "POST", "/api/search", {"query": "indemnification", "top_k": 3})

        self.assertEqual(captured["status"], "200 OK")
        payload = json.loads(body)
        self.assertEqual(payload["query"], "indemnification")
        self.assertEqual(client.search_calls[0]["top_k"], 3)

    def test_analysis_endpoint_validates_type(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, body = self._request(app, "POST", "/api/analyze", {"analysis_type": "bad", "prompt": "x"})

        self.assertEqual(captured["status"], "400 Bad Request")
        payload = json.loads(body)
        self.assertIn("analysis_type", payload["error"])

    def test_search_endpoint_rejects_invalid_query_type(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, body = self._request(app, "POST", "/api/search", {"query": 123})

        self.assertEqual(captured["status"], "400 Bad Request")
        self.assertEqual(json.loads(body)["error"], "query must be a string")

    def test_search_endpoint_rejects_invalid_top_k(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, body = self._request(app, "POST", "/api/search", {"query": "x", "top_k": 0})

        self.assertEqual(captured["status"], "400 Bad Request")
        self.assertEqual(json.loads(body)["error"], "'top_k' must be an integer between 1 and 20.")

    def test_search_endpoint_rejects_invalid_filters_type(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, body = self._request(app, "POST", "/api/search", {"query": "x", "filters": []})

        self.assertEqual(captured["status"], "400 Bad Request")
        self.assertEqual(json.loads(body)["error"], "filters must be a JSON object")

    def test_analysis_endpoint_rejects_non_string_type(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, body = self._request(app, "POST", "/api/analyze", {"analysis_type": [], "prompt": "x"})

        self.assertEqual(captured["status"], "400 Bad Request")
        self.assertIn("analysis_type", json.loads(body)["error"])

    def test_rejects_non_utf8_json_body(self):
        app = DeepJudgeWebApp(client=StubClient())
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/search",
            "CONTENT_LENGTH": "1",
            "wsgi.input": io.BytesIO(b"\x80"),
        }
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        body = b"".join(app(environ, start_response))

        self.assertEqual(captured["status"], "400 Bad Request")
        self.assertEqual(json.loads(body)["error"], "request body must be valid JSON")

    def test_internal_errors_are_sanitized(self):
        app = DeepJudgeWebApp(client=FailingClient())

        captured, body = self._request(app, "POST", "/api/search", {"query": "indemnification"})

        self.assertEqual(captured["status"], "500 Internal Server Error")
        self.assertEqual(json.loads(body)["error"], "Internal server error")


if __name__ == "__main__":
    unittest.main()

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


class ErrorClient(StubClient):
    def search_firm_knowledge(self, **kwargs):
        raise RuntimeError("sensitive internal failure details")


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

    def test_search_validation_rejects_invalid_types(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, _ = self._request(app, "POST", "/api/search", {"query": 123})
        self.assertEqual(captured["status"], "400 Bad Request")

        captured, _ = self._request(app, "POST", "/api/search", {"query": "ok", "top_k": "3"})
        self.assertEqual(captured["status"], "400 Bad Request")

        captured, _ = self._request(app, "POST", "/api/search", {"query": "ok", "top_k": 0})
        self.assertEqual(captured["status"], "400 Bad Request")

        captured, _ = self._request(app, "POST", "/api/search", {"query": "ok", "filters": []})
        self.assertEqual(captured["status"], "400 Bad Request")

    def test_analysis_validation_rejects_non_string_prompt(self):
        app = DeepJudgeWebApp(client=StubClient())

        captured, _ = self._request(
            app,
            "POST",
            "/api/analyze",
            {"analysis_type": "grey_area", "prompt": 1},
        )
        self.assertEqual(captured["status"], "400 Bad Request")

        captured, _ = self._request(
            app,
            "POST",
            "/api/analyze",
            {"analysis_type": "grey_area", "prompt": "topic", "jurisdiction": 1},
        )
        self.assertEqual(captured["status"], "400 Bad Request")

    def test_internal_errors_do_not_leak_details(self):
        app = DeepJudgeWebApp(client=ErrorClient())

        captured, body = self._request(app, "POST", "/api/search", {"query": "ok"})

        self.assertEqual(captured["status"], "500 Internal Server Error")
        payload = json.loads(body)
        self.assertEqual(payload["error"], "Internal server error")


if __name__ == "__main__":
    unittest.main()

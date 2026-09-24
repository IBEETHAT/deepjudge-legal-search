"""
Mobile-friendly DeepJudge web app with installable PWA assets.
"""

from __future__ import annotations

import json
import logging
import mimetypes
from dataclasses import dataclass
from http import HTTPStatus
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Tuple
from wsgiref.simple_server import make_server

from .client import DeepJudgeClient

logger = logging.getLogger(__name__)

STATIC_PACKAGE = "deepjudge_client.static"
ANALYSIS_TYPES = {
    "grey_area": "grey_area",
    "risk_assessment": "risk_assessment",
    "defense_strategy": "defense_strategy",
    "compliance_optimization": "compliance_optimization",
}


@dataclass
class Response:
    status: HTTPStatus
    body: bytes
    content_type: str
    headers: Optional[Iterable[Tuple[str, str]]] = None


class DeepJudgeWebApp:
    """Simple WSGI app for the installable mobile interface."""

    def __init__(self, client: Optional[DeepJudgeClient] = None):
        self.client = client or DeepJudgeClient()

    def __call__(
        self,
        environ: Dict[str, Any],
        start_response: Callable[[str, Iterable[Tuple[str, str]]], None],
    ) -> Iterable[bytes]:
        try:
            response = self._dispatch(environ)
        except ValueError as exc:
            response = self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception:  # pragma: no cover - defensive logging path
            logger.exception("Unhandled web app error")
            response = self._json_response(
                {"error": "Internal server error"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        headers = [("Content-Type", response.content_type), ("Content-Length", str(len(response.body)))]
        if response.headers:
            headers.extend(list(response.headers))
        start_response(f"{response.status.value} {response.status.phrase}", headers)
        return [response.body]

    def _dispatch(self, environ: Dict[str, Any]) -> Response:
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        if method == "GET":
            if path == "/":
                return self._serve_static("index.html")
            if path in {"/manifest.webmanifest", "/service-worker.js", "/styles.css"}:
                return self._serve_static(path.lstrip("/"))
            if path in {"/icons/icon-192.png", "/icons/icon-512.png", "/icons/apple-touch-icon.png"}:
                return self._serve_static(path.lstrip("/"))
        elif method == "POST":
            if path == "/api/search":
                return self._json_response(self._handle_search(environ))
            if path == "/api/analyze":
                return self._json_response(self._handle_analysis(environ))

        return self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_search(self, environ: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._read_json(environ)
        query = self._coerce_string(payload.get("query"), "query", required=True)
        matter_id = self._coerce_string(payload.get("matter_id"), "matter_id")

        top_k = payload.get("top_k", 5)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ValueError("'top_k' must be an integer between 1 and 20.")

        if "filters" in payload and payload["filters"] is not None and not isinstance(payload["filters"], dict):
            raise ValueError("filters must be a JSON object")
        filters = payload.get("filters")

        return self.client.search_firm_knowledge(
            query=query,
            matter_id=matter_id,
            top_k=top_k,
            filters=filters,
        )

    def _handle_analysis(self, environ: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._read_json(environ)
        analysis_type_key = self._coerce_string(payload.get("analysis_type"), "analysis_type", required=True).lower()
        analysis_type = ANALYSIS_TYPES.get(analysis_type_key)
        if not analysis_type:
            raise ValueError("analysis_type must be one of: grey_area, risk_assessment, defense_strategy, compliance_optimization")

        prompt = self._coerce_string(payload.get("prompt"), "prompt", required=True)

        request_payload: Dict[str, Any] = {"analysis_type": analysis_type}

        if analysis_type == "grey_area":
            request_payload["topic"] = prompt
            request_payload["jurisdiction"] = self._coerce_string(payload.get("jurisdiction"), "jurisdiction", default="US")
        elif analysis_type == "risk_assessment":
            request_payload["scenario"] = prompt
            request_payload["context"] = self._coerce_context(payload.get("context"))
        elif analysis_type == "defense_strategy":
            request_payload["charge_or_claim"] = prompt
            request_payload["jurisdiction"] = self._coerce_string(payload.get("jurisdiction"), "jurisdiction", default="US")
        else:
            request_payload["activity"] = prompt
            request_payload["context"] = self._coerce_context(payload.get("context"))

        return self.client._make_request("POST", "/analyze", request_payload)

    def _read_json(self, environ: Dict[str, Any]) -> Dict[str, Any]:
        body_stream = environ.get("wsgi.input")
        if body_stream is None:
            return {}

        content_length = environ.get("CONTENT_LENGTH")
        if content_length in (None, ""):
            raw_body = body_stream.read()
        else:
            try:
                length = int(content_length)
            except (TypeError, ValueError) as exc:
                raise ValueError("CONTENT_LENGTH must be an integer") from exc

            if length < 0:
                raise ValueError("CONTENT_LENGTH must be non-negative")

            raw_body = body_stream.read(length) if length > 0 else b""

        try:
            if not isinstance(raw_body, (bytes, bytearray)):
                raise ValueError("request body must be bytes")
            raw_body_bytes = bytes(raw_body)
        except TypeError as exc:
            raise ValueError("request body must be bytes") from exc

        if not raw_body_bytes:
            return {}

        try:
            data = json.loads(raw_body_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be valid JSON") from exc

        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")

        return data

    def _serve_static(self, relative_path: str) -> Response:
        resource = resources.files(STATIC_PACKAGE).joinpath(relative_path)
        content = resource.read_bytes()
        content_type = mimetypes.guess_type(str(Path(relative_path)))[0] or "application/octet-stream"
        if relative_path.endswith(".webmanifest"):
            content_type = "application/manifest+json"
        if relative_path.endswith(".js"):
            content_type = "application/javascript"
        return Response(status=HTTPStatus.OK, body=content, content_type=content_type)

    def _json_response(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> Response:
        return Response(
            status=status,
            body=json.dumps(payload).encode("utf-8"),
            content_type="application/json; charset=utf-8",
        )

    @staticmethod
    def _coerce_context(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        raise ValueError("context must be a JSON object")

    @staticmethod
    def _coerce_string(
        value: Any,
        field_name: str,
        required: bool = False,
        default: Optional[str] = None,
    ) -> Optional[str]:
        if value is None:
            if required:
                raise ValueError(f"{field_name} is required")
            return default

        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")

        cleaned_value = value.strip()
        if required and not cleaned_value:
            raise ValueError(f"{field_name} is required")

        if not cleaned_value:
            return default

        return cleaned_value


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the mobile web app."""
    app = DeepJudgeWebApp()
    with make_server(host, port, app) as httpd:
        logger.info("DeepJudge mobile web app running at http://%s:%s", host, port)
        httpd.serve_forever()

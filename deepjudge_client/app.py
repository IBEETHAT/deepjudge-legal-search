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
    "regulatory_loopholes": "regulatory_loopholes",
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
        except Exception as exc:  # pragma: no cover - defensive logging path
            logger.exception("Unhandled web app error")
            response = self._json_response(
                {"error": str(exc) or "Internal server error"},
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
        query = (payload.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")

        matter_id = (payload.get("matter_id") or "").strip() or None
        top_k = int(payload.get("top_k") or 5)
        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else None

        return self.client.search_firm_knowledge(
            query=query,
            matter_id=matter_id,
            top_k=top_k,
            filters=filters,
        )

    def _handle_analysis(self, environ: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._read_json(environ)
        analysis_type = ANALYSIS_TYPES.get(payload.get("analysis_type"))
        if not analysis_type:
            raise ValueError("analysis_type must be one of: grey_area, regulatory_loopholes, risk_assessment, defense_strategy, compliance_optimization")

        prompt = (payload.get("prompt") or "").strip()
        if not prompt:
            raise ValueError("prompt is required")

        request_payload: Dict[str, Any] = {"analysis_type": analysis_type}

        if analysis_type == "grey_area":
            request_payload["topic"] = prompt
            request_payload["jurisdiction"] = (payload.get("jurisdiction") or "US").strip() or "US"
        elif analysis_type == "regulatory_loopholes":
            request_payload["regulation"] = prompt
            request_payload["context"] = self._coerce_context(payload.get("context"))
        elif analysis_type == "risk_assessment":
            request_payload["scenario"] = prompt
            request_payload["context"] = self._coerce_context(payload.get("context"))
        elif analysis_type == "defense_strategy":
            request_payload["charge_or_claim"] = prompt
            request_payload["jurisdiction"] = (payload.get("jurisdiction") or "US").strip() or "US"
        else:
            request_payload["activity"] = prompt
            request_payload["context"] = self._coerce_context(payload.get("context"))

        return self.client._make_request("POST", "/analyze", request_payload)

    def _read_json(self, environ: Dict[str, Any]) -> Dict[str, Any]:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            length = 0

        raw_body = environ["wsgi.input"].read(length) if length > 0 else b""
        if not raw_body:
            return {}

        try:
            data = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
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


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the mobile web app."""
    app = DeepJudgeWebApp()
    with make_server(host, port, app) as httpd:
        logger.info("DeepJudge mobile web app running at http://%s:%s", host, port)
        httpd.serve_forever()

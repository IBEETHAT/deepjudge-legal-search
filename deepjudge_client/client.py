"""
Main DeepJudge Client with optimized API communication
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv():
        return False

from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class DeepJudgeClient:
    """
    Production-ready client for DeepJudge legal knowledge search API

    Features:
    - Automatic retries with exponential backoff
    - Connection pooling for performance
    - Rate limiting awareness
    - Request/response logging
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        backoff_factor: float = 0.5,
    ):
        """
        Initialize DeepJudge client

        Args:
            api_key: DeepJudge API key (defaults to DEEPJUDGE_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry strategy
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("DEEPJUDGE_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided and DEEPJUDGE_API_KEY not set")

        self.base_url = base_url or os.getenv("DEEPJUDGE_BASE_URL", "https://api.deepjudge.ai/v1")
        self.timeout = int(timeout if timeout is not None else os.getenv("REQUEST_TIMEOUT", "30"))
        resolved_retries = int(max_retries if max_retries is not None else os.getenv("MAX_RETRIES", "3"))
        self.session = self._create_session(resolved_retries, backoff_factor)
        self._request_history: List[Dict[str, Any]] = []

    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """Create requests session with retry strategy and connection pooling"""
        session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=backoff_factor,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "deepjudge-client/1.0.0",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling and logging

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            payload: Request payload
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response JSON

        Raises:
            requests.HTTPError: On HTTP errors
            requests.Timeout: On timeout
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.debug("Making %s request to %s", method, url)

            response = self.session.request(
                method=method,
                url=url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                **kwargs,
            )

            response.raise_for_status()
            result = response.json()

            self._request_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": True,
                }
            )

            return result

        except requests.exceptions.Timeout:
            logger.error("Request timeout to %s", url)
            raise
        except requests.exceptions.HTTPError as error:
            logger.error("HTTP error %s: %s", error.response.status_code, error.response.text)
            raise
        except requests.exceptions.RequestException as error:
            logger.error("Request failed: %s", error)
            raise

    def search_firm_knowledge(
        self,
        query: str,
        matter_id: Optional[str] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search firm knowledge base

        Args:
            query: Search query
            matter_id: Optional matter ID to filter by
            top_k: Number of top results to return
            filters: Additional filter criteria

        Returns:
            Search results with metadata
        """
        payload = {
            "query": query,
            "top_k": top_k,
            "filters": filters or {},
        }

        if matter_id:
            payload["filters"]["matter_id"] = matter_id

        return self._make_request("POST", "/search", payload)

    def get_request_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent request history for monitoring"""
        return self._request_history[-limit:]

    def clear_request_history(self):
        """Clear request history"""
        self._request_history.clear()

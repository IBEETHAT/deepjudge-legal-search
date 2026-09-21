import unittest
from unittest.mock import MagicMock

from deepjudge_client.client import DeepJudgeClient


class DeepJudgeClientTests(unittest.TestCase):
    def test_headers_include_bearer_token(self):
        client = DeepJudgeClient(api_key="secret-key")

        self.assertTrue(client.headers["Authorization"].startswith("Bearer "))
        self.assertTrue(client.headers["Authorization"].endswith("secret-key"))

    def test_explicit_zero_max_retries_is_preserved(self):
        client = DeepJudgeClient(api_key="secret-key", max_retries=0)

        self.assertEqual(client.session.get_adapter("https://").max_retries.total, 0)

    def test_search_filters_are_copied_before_matter_mutation(self):
        client = DeepJudgeClient(api_key="secret-key")
        client._make_request = MagicMock(return_value={})
        filters = {"jurisdiction": "US"}

        client.search_firm_knowledge(query="indemnification", matter_id="M-1", filters=filters)

        self.assertEqual(filters, {"jurisdiction": "US"})
        payload = client._make_request.call_args.args[2]
        self.assertEqual(payload["filters"], {"jurisdiction": "US", "matter_id": "M-1"})


if __name__ == "__main__":
    unittest.main()

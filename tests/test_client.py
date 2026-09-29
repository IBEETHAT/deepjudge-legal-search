import unittest

from deepjudge_client.client import DeepJudgeClient


class DeepJudgeClientTests(unittest.TestCase):
    def test_headers_include_bearer_token(self):
        client = DeepJudgeClient(api_key="secret-key")

        self.assertTrue(client.headers["Authorization"].startswith("Bearer "))
        self.assertTrue(client.headers["Authorization"].endswith("secret-key"))

    def test_max_retries_zero_is_preserved(self):
        client = DeepJudgeClient(api_key="secret-key", max_retries=0)
        adapter = client.session.get_adapter("https://")
        self.assertEqual(adapter.max_retries.total, 0)


if __name__ == "__main__":
    unittest.main()

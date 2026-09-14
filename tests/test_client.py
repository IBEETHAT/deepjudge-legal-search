import unittest

from deepjudge_client.client import DeepJudgeClient


class DeepJudgeClientTests(unittest.TestCase):
    def test_headers_include_bearer_token(self):
        client = DeepJudgeClient(api_key="secret-key")

        self.assertTrue(client.headers["Authorization"].startswith("Bearer "))
        self.assertTrue(client.headers["Authorization"].endswith("secret-key"))


if __name__ == "__main__":
    unittest.main()

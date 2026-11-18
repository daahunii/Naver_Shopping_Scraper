import os
import unittest
from unittest.mock import Mock, patch
import requests
import naverShopping as client
from naverShopping_api import app


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.web = app.test_client()

    def test_missing_credentials_never_calls_provider(self):
        with patch.object(client.requests, "get") as get:
            with self.assertRaises(client.ShoppingAPIError):
                client.search_naver_shopping("book")
            get.assert_not_called()

    def test_client_contract_and_timeout(self):
        os.environ.update(NAVER_CLIENT_ID="test-id", NAVER_CLIENT_SECRET="test-secret")
        item = dict(title="Book", link="url", image="image", lprice="100", mallName="shop")
        response = Mock(status_code=200)
        response.json.return_value = {"items": [item]}
        with patch.object(client.requests, "get", return_value=response) as get:
            self.assertEqual(client.search_naver_shopping("book"), [item])
            self.assertEqual(get.call_args.kwargs["timeout"], (3.05, 10))
            self.assertFalse(get.call_args.kwargs["allow_redirects"])

    def test_provider_exception_is_sanitized(self):
        os.environ.update(NAVER_CLIENT_ID="test-id", NAVER_CLIENT_SECRET="test-secret")
        with patch.object(client.requests, "get", side_effect=requests.Timeout("private-test-secret")):
            response = self.web.get("/search?query=book")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private-test-secret", response.get_data(as_text=True))

    def test_invalid_batch_causes_no_provider_calls(self):
        with patch("naverShopping_api.search_naver_shopping") as search:
            for payload in [[], {}, {"keywords": ["book", 42]},
                            {"keywords": ["book"], "count": True},
                            {"keywords": ["book"] * 11}, {"keywords": ["()"]}]:
                self.assertEqual(self.web.post("/recommend", json=payload).status_code, 400)
            search.assert_not_called()

    def test_existing_response_shapes(self):
        with patch("naverShopping_api.search_naver_shopping", return_value=[]) as search:
            self.assertEqual(self.web.get("/search?query=book").json, [])
            response = self.web.post("/recommend", json={"keywords": ["book (gift)"]})
            self.assertEqual(response.json, {"book (gift)": []})
            search.assert_called_with("book", display=3)

    def test_optional_bearer_auth(self):
        os.environ["SHOPPING_API_TOKEN"] = "test-token"
        self.assertEqual(self.web.get("/search?query=book").status_code, 401)
        with patch("naverShopping_api.search_naver_shopping", return_value=[]):
            self.assertEqual(self.web.get("/search?query=book", headers={"Authorization": "Bearer test-token"}).status_code, 200)

    def test_body_limit_and_json_errors(self):
        self.assertEqual(self.web.post("/recommend", data="{" , content_type="application/json").status_code, 400)
        self.assertEqual(self.web.post("/recommend", data="x" * 17000, content_type="application/json").status_code, 413)


if __name__ == "__main__":
    unittest.main()

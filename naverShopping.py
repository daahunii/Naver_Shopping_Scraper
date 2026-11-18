"""Naver Shopping Search API client and command-line example."""
import os
import requests


class ShoppingAPIError(RuntimeError):
    """A sanitized configuration or upstream API failure."""


def search_naver_shopping(query, display=5):
    client_id = os.environ.get("NAVER_CLIENT_ID", "").strip()
    client_secret = os.environ.get("NAVER_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise ShoppingAPIError("Naver API credentials are not configured")
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError("query must contain 1 to 200 characters")
    if type(display) is not int or not 1 <= display <= 100:
        raise ValueError("display must be an integer from 1 to 100")
    try:
        response = requests.get(
            "https://openapi.naver.com/v1/search/shop.json",
            headers={"X-Naver-Client-Id": client_id,
                     "X-Naver-Client-Secret": client_secret},
            params={"query": query, "display": display, "start": 1, "sort": "sim"},
            timeout=(3.05, 10),
            allow_redirects=False,
        )
        if response.status_code != 200:
            raise ShoppingAPIError("Naver Shopping API request failed")
        data = response.json()
        items = data["items"]
        if not isinstance(items, list):
            raise ValueError("Invalid items")
        fields = ("title", "link", "image", "lprice", "mallName")
        return [{key: item[key] for key in fields} for item in items]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        raise ShoppingAPIError("Naver Shopping API response unavailable") from None


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Search Naver Shopping")
    parser.add_argument("query")
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    try:
        print(json.dumps(search_naver_shopping(args.query, args.count),
                         ensure_ascii=False, indent=2))
    except (ShoppingAPIError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")

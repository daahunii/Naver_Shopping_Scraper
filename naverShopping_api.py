"""Giftoyou shopping API. Credentials are supplied by the server environment."""
import hmac
import os
import re
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from naverShopping import ShoppingAPIError, search_naver_shopping

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


def clean_keyword(raw_keyword):
    if not isinstance(raw_keyword, str) or not 1 <= len(raw_keyword) <= 200:
        raise ValueError("Each keyword must contain 1 to 200 characters")
    cleaned = re.sub(r"\(.*?\)", "", raw_keyword)
    cleaned = re.sub(r"[&(),]", "", cleaned).strip()
    if not cleaned:
        raise ValueError("Keyword is empty after normalization")
    return cleaned


@app.before_request
def authenticate():
    token = os.environ.get("SHOPPING_API_TOKEN", "")
    if token and request.path != "/":
        supplied = request.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
            return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(ValueError)
def invalid_input(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(ShoppingAPIError)
def upstream_error(error):
    return jsonify({"error": "Shopping provider unavailable"}), 502


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify({"error": error.name}), error.code


@app.route("/")
def index():
    return jsonify({"service": "Naver Shopping API", "endpoints": ["GET /search", "POST /recommend"]})


@app.route("/search", methods=["GET"])
def naver_shopping_api():
    query = clean_keyword(request.args.get("query"))
    return jsonify(search_naver_shopping(query, display=3))


@app.route("/recommend", methods=["POST"])
def recommend_multiple():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    keywords = data.get("keywords")
    count = data.get("count", 3)
    if not isinstance(keywords, list) or not 1 <= len(keywords) <= 10:
        raise ValueError("keywords must be an array of 1 to 10 strings")
    if type(count) is not int or not 1 <= count <= 100:
        raise ValueError("count must be an integer from 1 to 100")
    # Validate the entire request before consuming provider quota.
    queries = [(keyword, clean_keyword(keyword)) for keyword in keywords]
    return jsonify({keyword: search_naver_shopping(query, display=count)
                    for keyword, query in queries})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=False)

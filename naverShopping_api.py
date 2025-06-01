from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

# 🔐 네이버 API 정보
CLIENT_ID = "TslSB2EtDRRaX0RpzoM7"
CLIENT_SECRET = "O2noGteTaV"


def clean_keyword(raw_keyword):
    """
    괄호 안의 내용 및 특수문자 제거하여 검색어를 정리합니다.
    """
    cleaned = re.sub(r"\(.*?\)", "", raw_keyword)  # 괄호 내용 제거
    cleaned = re.sub(r"[&(),]", "", cleaned)       # 특수문자 제거
    return cleaned.strip()


def search_naver_shopping(query, display=3):
    """
    네이버 쇼핑 API를 사용해 query에 대한 검색 결과를 반환합니다.
    """
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,
        "start": 1,
        "sort": "sim",  # 관련도순
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        results = []
        for item in data["items"]:
            results.append({
                "title": item["title"],
                "link": item["link"],
                "image": item["image"],
                "lprice": item["lprice"],
            })
        return results
    else:
        print("❌ API 호출 실패:", response.status_code, response.text)
        return []


# ✅ 루트 안내 페이지
@app.route('/')
def index():
    return '''
    <h2>🛍️ Naver 쇼핑 검색 API</h2>
    <p>이 API는 키워드로 네이버 쇼핑 상품 데이터를 가져옵니다.</p>
    <h3>✅ 단일 검색:</h3>
    <pre><code>GET /search?query=천체망원경</code></pre>
    <h3>✅ 다중 검색 (POST):</h3>
    <pre><code>POST /recommend  {"keywords": ["키워드1", "키워드2", ...]}</code></pre>
    '''


# ✅ 단일 검색
@app.route('/search', methods=['GET'])
def naver_shopping_api():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    items = search_naver_shopping(clean_keyword(query))
    return jsonify(items)


# ✅ 다중 키워드 검색 (제미나이 추천용)
@app.route('/recommend', methods=['POST'])
def recommend_multiple():
    try:
        data = request.get_json()
        keywords = data.get("keywords", [])
        count = data.get("count", 3)

        results = {}
        for keyword in keywords:
            safe_query = clean_keyword(keyword)
            print(f"🔍 검색어: {safe_query}")
            items = search_naver_shopping(safe_query, display=count)
            results[keyword] = items

        return jsonify(results)

    except Exception as e:
        print("❌ recommend 오류:", e)
        return jsonify({"error": str(e)}), 500


# ✅ 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
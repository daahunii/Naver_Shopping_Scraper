import requests
import json

CLIENT_ID = "T"       # 🔐 발급받은 ID -> 임의로 넣음
CLIENT_SECRET = "O"  # 🔐 발급받은 시크릿 -> 임의로 넣음

def search_naver_shopping(query, display=5):
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
                "mallName": item["mallName"],
            })

        return results
    else:
        print("❌ API 호출 실패:", response.status_code, response.text)
        return []

# ✅ 테스트
if __name__ == "__main__":
    keyword = "천체망원경"
    items = search_naver_shopping(keyword)

    print(f"\n🔎 '{keyword}' 검색 결과:")
    for idx, item in enumerate(items, 1):
        print(f"{idx}. {item['title']}")
        print(f"   💰 {item['lprice']}원 | 🛒 {item['mallName']}")
        print(f"   🔗 {item['link']}")
        print(f"   🖼️  {item['image']}\n")
# Naver Shopping API for Giftoyou

Giftoyou에서 생성한 선물 키워드를 네이버 쇼핑 상품 정보로 연결하는 Python/Flask 서버입니다. 저장소 이름은 Scraper이지만 상품 조회에는 HTML 스크래핑이 아닌 네이버 공식 검색 API를 사용합니다.

## 구성

- `naverShopping.py`: 공통 검색 클라이언트 및 CLI
- `naverShopping_api.py`: Flask HTTP API
- `.env.example`: 필요한 환경변수 이름 (실제 키 없음)

흐름: Giftoyou의 Gemini 생성 키워드 → Flask 서버 → 네이버 쇼핑 검색 API → 상품 목록. 이 저장소 자체는 Gemini 호출, 사용자 인증 시스템, DB 저장을 구현하지 않습니다.

## 설치 및 실행

Python 3.10 이상을 권장합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

네이버 개발자센터에서 검색 API 사용 권한이 있는 애플리케이션을 등록한 뒤, 실행 환경에 `NAVER_CLIENT_ID`와 `NAVER_CLIENT_SECRET`을 설정하세요. 셸 기록에 키를 직접 남기지 않는 입력 예시입니다 (bash):

```bash
read -r -p "Client ID: " NAVER_CLIENT_ID
read -r -s -p "Client Secret: " NAVER_CLIENT_SECRET
export NAVER_CLIENT_ID NAVER_CLIENT_SECRET
python naverShopping_api.py
```

기본 주소는 `http://127.0.0.1:8081`이며 디버그 모드는 꺼져 있습니다. `.env.example`은 설정 항목 안내용이며, `.env` 파일을 자동으로 읽지는 않습니다. 배포 환경에서는 secret 관리 기능으로 환경변수를 주입하세요.

CLI 사용:

```bash
python naverShopping.py "천체망원경" --count 5
```

## API

### GET /search

```bash
curl --get http://127.0.0.1:8081/search --data-urlencode 'query=천체망원경'
```

상품 최대 3개를 배열로 반환합니다. 각 상품의 필드는 `title`, `link`, `image`, `lprice`, `mallName`입니다. 가격은 공급자가 반환한 문자열이며 상품명에는 HTML 강조 태그가 포함될 수 있으므로 클라이언트에서 텍스트로 처리하세요.

### POST /recommend

```bash
curl http://127.0.0.1:8081/recommend \
  -H 'Content-Type: application/json' \
  -d '{"keywords":["텀블러","책"],"count":3}'
```

원래 키워드를 키로, 상품 배열을 값으로 갖는 JSON 객체를 반환합니다. `keywords`는 1~10개의 문자열, 각 문자열은 정리 전 1~200자입니다. 괄호 안 내용과 일부 특수문자를 제거하며 정리 후 빈 검색어는 거부합니다. `count`는 1~100의 정수이고 기본값은 3입니다. 같은 키워드가 중복되면 응답 객체에서는 하나의 키로 표시됩니다.

- 400: 잘못된 입력 또는 JSON
- 401: 설정된 서버 접근 토큰 불일치
- 413: 요청 본문 16 KiB 초과
- 415: JSON Content-Type 누락/불일치
- 502: 공급자 호출 실패·인증 정보 누락·잘못된 공급자 응답

외부 요청에는 연결/읽기 타임아웃을 적용하며 리디렉션을 따라가지 않습니다. 공급자의 응답 본문이나 인증 정보는 오류 응답에 포함하지 않습니다. 다중 검색은 순차 처리되며 중간 실패 시 502를 반환합니다.

## 접근 제어와 배포 범위

`SHOPPING_API_TOKEN`을 설정하면 `/`를 제외한 요청에 `Authorization: Bearer <token>` 헤더가 필요합니다. 기본 로컬 실행에서는 기존 Giftoyou 요청과의 호환성을 위해 토큰을 강제하지 않습니다.

외부에 공개할 때는 서버 토큰을 설정하고 HTTPS, 사용자 인증, 요청 속도 제한을 갖춘 프록시 또는 게이트웨이를 구성하세요. 공용 앱에 공유 서버 토큰을 내장하는 방식은 사용자별 인증을 대신하지 않습니다. Flask 개발 서버를 인터넷에 직접 노출하지 마세요. 이 프로젝트에는 사용자별 쿼터·분산 속도 제한·작업 큐가 포함되어 있지 않습니다.

## 공개된 인증 정보 처리

이전 커밋에는 인증 정보가 포함되어 있었습니다. 현재 코드에서 제거해도 과거 Git 커밋이나 기존 복제본에서 사라지지 않습니다. 기존 키는 네이버 개발자센터에서 폐기·재발급하고, 이전 키가 더 이상 유효하지 않은지 확인해야 합니다. 새로운 키는 환경변수에만 보관하세요.

`.env`와 로컬 가상환경은 Git에서 제외합니다. Git 기록 재작성은 기존 복제본까지 지우지 않으므로 키 교체를 대신할 수 없습니다.

## 검증

```bash
python -m unittest discover -s tests -v
```

테스트는 외부 API 호출을 모킹하여 인증 정보 누락, 입력 검증, 오류 비노출, 기존 응답 형식을 확인합니다. 실제 키로 네이버 API를 호출하는 통합 테스트나 운영 배포 검증은 포함하지 않습니다.

공식 API 문서: https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md

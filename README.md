# 🎁 생일선물 추천 사이트 - 전체 코드 설명서

> 리눅스 8조 프로젝트  
> Flask + MySQL + Docker 기반 풀스택 웹 애플리케이션

---

## 📑 목차

1. [프로젝트 전체 구조](#1-프로젝트-전체-구조)
2. [백엔드 (Python + Flask)](#2-백엔드-python--flask)
   - [requirements.txt](#21-requirementstxt)
   - [Dockerfile](#22-backenddockerfile)
   - [models.py - DB 모델](#23-modelspy)
   - [main.py - API 서버](#24-mainpy)
   - [seed.py - 초기 데이터 시드](#25-seedpy)
3. [프론트엔드 (HTML + CSS + JS)](#3-프론트엔드-html--css--js)
   - [Dockerfile](#31-frontenddockerfile)
   - [nginx.conf](#32-nginxconf)
   - [index.html - 사용자 페이지](#33-indexhtml)
   - [admin.html - 관리자 페이지](#34-adminhtml)
   - [app.js - 사용자 로직](#35-appjs)
   - [admin.js - 관리자 로직](#36-adminjs)
   - [styles.css - 디자인](#37-stylescss)
4. [인프라 (Docker)](#4-인프라-docker)
   - [docker-compose.yml](#41-docker-composeyml)
5. [데이터](#5-데이터)
   - [cleaned_gifts.json](#51-cleaned_giftsjson)

---

## 1. 프로젝트 전체 구조

### 폴더 트리

```
birthday-gift-app-v2/
├── backend/                  # 백엔드 서버
│   ├── app/
│   │   ├── main.py          # API 엔드포인트 + 추천 로직
│   │   └── models.py        # DB 테이블 정의
│   ├── scripts/
│   │   └── seed.py          # 초기 데이터 시드
│   ├── requirements.txt     # Python 패키지 의존성
│   └── Dockerfile           # 백엔드 이미지 빌드
├── frontend/                 # 프론트엔드
│   ├── index.html           # 사용자 페이지
│   ├── admin.html           # 관리자 페이지
│   ├── app.js               # 사용자 페이지 JS
│   ├── admin.js             # 관리자 페이지 JS
│   ├── styles.css           # 디자인 (CSS)
│   ├── nginx.conf           # nginx 설정
│   └── Dockerfile           # 프론트엔드 이미지 빌드
├── data/
│   └── cleaned_gifts.json   # 111개 상품 데이터
└── docker-compose.yml       # 3개 컨테이너 통합 관리
```

### 시스템 동작 원리

```
[브라우저]
    ↓ HTTP 요청
[프론트엔드 nginx:8080] → 정적 파일(HTML/CSS/JS) 서빙
    ↓
[브라우저 자바스크립트]
    ↓ fetch() API 호출
[백엔드 Flask:5000] → 비즈니스 로직 처리
    ↓ SQLAlchemy ORM
[MySQL DB:3306] → 데이터 저장/조회
```

**핵심 개념:**
- **3-Tier 아키텍처**: 프론트(UI) - 백엔드(로직) - DB(데이터) 3계층 분리
- **REST API**: 백엔드가 JSON으로 응답하는 API 서버
- **컨테이너화**: 각 서비스가 독립된 Docker 컨테이너에서 실행

---

## 2. 백엔드 (Python + Flask)

### 2.1 requirements.txt

**역할**: 백엔드에 필요한 Python 패키지 목록

```txt
Flask==3.0.0
Flask-Cors==4.0.0
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.0
cryptography==42.0.0
```

**각 패키지 설명:**

| 패키지 | 역할 |
|---|---|
| **Flask** | 웹 서버 프레임워크 (요청 받고 응답해줌) |
| **Flask-Cors** | CORS 허용 (다른 포트끼리 통신 가능하게) |
| **Flask-SQLAlchemy** | Flask에서 DB 쉽게 다루기 |
| **PyMySQL** | Python ↔ MySQL 연결 드라이버 |
| **cryptography** | MySQL 보안 인증 |

**왜 버전을 고정하나요?**
→ `==3.0.0`처럼 버전을 정확히 명시. 다른 컴퓨터에서도 똑같은 버전이 깔리도록 해서 "내 컴퓨터에선 되는데..." 문제 방지.

---

### 2.2 backend/Dockerfile

**역할**: 백엔드 Docker 이미지를 어떻게 만들지 정의

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 캐싱
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 + 시드 스크립트 복사
COPY app/ ./app/
COPY scripts/ ./scripts/

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD python scripts/seed.py && python app/main.py
```

**한 줄씩 설명:**

| 명령어 | 설명 |
|---|---|
| `FROM python:3.11-slim` | Python 3.11 이미지를 베이스로 사용 (slim은 가벼운 버전) |
| `WORKDIR /app` | 컨테이너 내부 작업 폴더를 `/app`으로 설정 |
| `COPY requirements.txt .` | requirements.txt를 컨테이너로 복사 |
| `RUN pip install ...` | 패키지 설치 (`--no-cache-dir`은 캐시 안 남겨 용량 절약) |
| `COPY app/ ./app/` | 앱 코드 복사 |
| `EXPOSE 5000` | 5000번 포트 사용 알림 |
| `ENV PYTHONUNBUFFERED=1` | print 출력이 즉시 보이게 |
| `CMD ...` | 컨테이너 시작 시 실행할 명령 (시드 후 서버 실행) |

**왜 requirements.txt를 먼저 복사할까?**
→ Docker는 레이어 캐싱을 함. 코드만 바뀌고 패키지는 그대로면 패키지 설치 단계는 캐시 재사용 → 빌드 속도 ↑

---

### 2.3 models.py

**역할**: 데이터베이스 테이블 구조를 Python 클래스로 정의

```python
"""
DB 모델 정의 (SQLAlchemy ORM)

엑셀 데이터 구조에 맞춰 gifts 테이블 하나로 단순화.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Gift(db.Model):
    __tablename__ = "gifts"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    price = db.Column(db.Integer, nullable=False, index=True)
    gender = db.Column(db.Enum("male", "female", "unisex"), nullable=False, index=True)
    min_age = db.Column(db.Integer, nullable=False)
    max_age = db.Column(db.Integer, nullable=False)
    target = db.Column(db.String(100), nullable=True)
    link = db.Column(db.String(2000), nullable=True)
    
    def to_dict(self):
        """JSON 응답용 dict 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "gender": self.gender,
            "min_age": self.min_age,
            "max_age": self.max_age,
            "target": self.target,
            "link": self.link,
        }
```

**핵심 개념: ORM (Object-Relational Mapping)**

ORM은 **DB 테이블을 Python 클래스로 다루는 방식**이에요.

| SQL 방식 | ORM 방식 |
|---|---|
| `INSERT INTO gifts (name) VALUES ('립스틱')` | `Gift(name='립스틱'); db.session.add(gift)` |
| `SELECT * FROM gifts WHERE price < 50000` | `Gift.query.filter(Gift.price < 50000).all()` |
| `UPDATE gifts SET price=10000 WHERE id=5` | `gift.price = 10000` |

**장점:**
1. SQL 안 써도 됨 (Python 문법으로!)
2. **SQL 인젝션 자동 방지** (보안 ↑)
3. DB 종류 바꿔도 코드 그대로 (MySQL → PostgreSQL 등)

**컬럼 설명:**

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | Integer | 기본키, 자동 증가 |
| `name` | String(255) | 상품명 (최대 255자) |
| `category` | String(50), **index=True** | 카테고리 (인덱스 → 빠른 검색) |
| `price` | Integer, **index=True** | 가격 |
| `gender` | **Enum** | 'male', 'female', 'unisex' 중 하나만 허용 |
| `min_age` ~ `max_age` | Integer | 추천 나이 범위 |
| `target` | String(100) | 특수 대상 (임산부 등, 선택사항) |
| `link` | String(2000) | 구매 링크 (긴 쿠팡 링크 대응) |

**왜 index를 걸까?**
→ 자주 조회하는 컬럼에 인덱스 걸면 검색 속도 빠름. 우리 추천 로직에서 `category`, `price`, `gender`로 자주 필터링하니까 인덱스 필수.

---

### 2.4 main.py

**역할**: API 엔드포인트 정의 + 추천 로직 구현

전체 코드가 길어서 **부분별로 나눠** 설명할게요.

#### 📍 2.4.1 임포트와 앱 초기화

```python
import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import or_, and_
from sqlalchemy.exc import OperationalError

from app.models import db, Gift


def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # MySQL 연결 설정 (환경변수에서 읽음)
    db_user = os.environ.get("DB_USER", "giftuser")
    db_pass = os.environ.get("DB_PASSWORD", "giftpass")
    db_host = os.environ.get("DB_HOST", "mysql")  # Docker 서비스명
    db_port = os.environ.get("DB_PORT", "3306")
    db_name = os.environ.get("DB_NAME", "giftdb")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    db.init_app(app)
```

**환경변수 사용 이유:**
- DB 비밀번호를 코드에 직접 쓰면 Git에 노출됨 → 보안 위험
- 환경변수로 분리하면 운영 환경마다 다르게 설정 가능

**`mysql+pymysql://...?charset=utf8mb4`** 분석:
- `mysql+pymysql`: MySQL을 PyMySQL 드라이버로 사용
- `charset=utf8mb4`: 한글, 이모지까지 안전하게 저장

#### 📍 2.4.2 MySQL 부팅 대기 (재시도 로직)

```python
    with app.app_context():
        for attempt in range(30):
            try:
                db.create_all()
                print(f"✓ DB 연결 성공 (시도 {attempt + 1})")
                break
            except OperationalError as e:
                print(f"DB 연결 대기 중... ({attempt + 1}/30)")
                time.sleep(2)
        else:
            print("❌ DB 연결 실패")
```

**왜 필요한가?**
- MySQL 컨테이너는 시작 후 1~2분 후에야 실제로 쿼리 받음
- 백엔드가 너무 빨리 연결 시도하면 실패
- → **30번 재시도** (2초씩, 최대 1분 대기)

#### 📍 2.4.3 공개 API: 헬스체크 & 카테고리

```python
@app.route("/")
def health():
    return jsonify({"status": "ok", "message": "생일선물 추천 API"})

@app.route("/categories", methods=["GET"])
def get_categories():
    """카테고리 목록 (프론트엔드 폼에서 사용)"""
    rows = db.session.query(Gift.category).distinct().all()
    return jsonify({"categories": [r[0] for r in rows]})
```

- `/` : 서버 작동 확인용
- `/categories` : `DISTINCT`로 중복 제거한 카테고리 목록 반환

#### 📍 2.4.4 추천 API (핵심!)

```python
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json() or {}
    
    try:
        age = int(data.get("age", 0))
        gender = data.get("gender", "unisex").lower()
        budget = int(data.get("budget", 0))
        categories = data.get("categories", [])
    except (ValueError, TypeError):
        return jsonify({"error": "입력값 형식이 잘못되었습니다"}), 400
    
    if age <= 0 or budget <= 0:
        return jsonify({"error": "나이와 예산은 0보다 커야 합니다"}), 400
    
    # ⭐ 1단계: SQL WHERE로 필터링 (성능 ↑)
    query = Gift.query.filter(
        Gift.min_age <= age,                                   # 나이 조건
        Gift.max_age >= age,
        Gift.price <= budget,                                  # 예산 조건
        or_(Gift.gender == gender, Gift.gender == "unisex"),   # 성별 조건
    )
    
    # 카테고리 선택 시 필터 추가
    if categories:
        query = query.filter(Gift.category.in_(categories))
    
    candidates = query.limit(100).all()
    
    # ⭐ 2단계: Python에서 점수 계산
    scored = []
    for g in candidates:
        score = 0
        if g.price <= budget / 2:               # 가성비 보너스
            score += 3
        if categories and g.category in categories:  # 카테고리 매칭
            score += 5
        mid = (g.min_age + g.max_age) / 2
        if abs(age - mid) <= 5:                 # 연령대 적합도
            score += 2
        
        d = g.to_dict()
        d["score"] = score
        scored.append(d)
    
    # ⭐ 3단계: 랜덤 셔플 (매번 다른 추천!)
    import random
    random.shuffle(scored)
    
    return jsonify({
        "input": data,
        "count": len(scored[:6]),
        "recommendations": scored[:6]
    })
```

**3단계 알고리즘:**

**1단계 - SQL 필터링** (DB에서 처리, 빠름)
- 나이가 추천 범위에 들어가는가? (`min_age ≤ age ≤ max_age`)
- 가격이 예산 이하인가? (`price ≤ budget`)
- 성별이 맞거나 공용인가? (`gender == X OR gender == 'unisex'`)

**2단계 - Python 점수 계산** (필터 통과한 것만)
- 가성비 보너스 (+3점): 예산 절반 이하
- 카테고리 매칭 (+5점): 사용자가 선택한 카테고리
- 연령 적합도 (+2점): 받는 사람 나이가 범위 중앙에 가까움

**3단계 - 랜덤 셔플**
- 점수와 무관하게 무작위로 섞음 → 같은 조건이어도 매번 다른 결과
- `random.shuffle(scored)`: 리스트를 무작위로 섞는 Python 함수

**왜 SQL 필터링과 Python 점수를 나눴나?**
- 필터링(=대량 데이터 거르기)은 DB가 잘함 → 인덱스 활용 가능
- 점수 계산(=복잡한 비즈니스 로직)은 Python이 표현하기 좋음

#### 📍 2.4.5 관리자 CRUD API

**Create (생성):**
```python
@app.route("/admin/gifts", methods=["POST"])
def admin_create():
    data = request.get_json() or {}
    
    # 필수 필드 검증
    required = ["name", "category", "price", "gender", "min_age", "max_age"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify({"error": f"필수 필드 누락: {', '.join(missing)}"}), 400
    
    if data["gender"] not in ("male", "female", "unisex"):
        return jsonify({"error": "gender는 male/female/unisex 중 하나"}), 400
    
    gift = Gift(
        name=data["name"],
        category=data["category"],
        price=int(data["price"]),
        gender=data["gender"],
        min_age=int(data["min_age"]),
        max_age=int(data["max_age"]),
        target=data.get("target") or None,
        link=data.get("link") or None,
    )
    db.session.add(gift)
    db.session.commit()
    return jsonify(gift.to_dict()), 201
```

**Read (조회):**
```python
@app.route("/admin/gifts", methods=["GET"])
def admin_list():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search = request.args.get("search", "").strip()
    
    query = Gift.query
    if search:
        query = query.filter(Gift.name.like(f"%{search}%"))
    
    pagination = query.order_by(Gift.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
        "gifts": [g.to_dict() for g in pagination.items]
    })
```

**핵심 기능:**
- **페이지네이션**: 한 번에 다 안 가져오고 페이지별로 (성능 ↑)
- **검색**: `LIKE '%키워드%'` SQL로 부분 일치 검색

**Update (수정):**
```python
@app.route("/admin/gifts/<int:gift_id>", methods=["PUT"])
def admin_update(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    data = request.get_json() or {}
    
    updatable = ["name", "category", "price", "gender", "min_age", "max_age", "target", "link"]
    for field in updatable:
        if field in data:
            value = data[field]
            if field in ("price", "min_age", "max_age"):
                value = int(value)
            setattr(gift, field, value or None if field in ("target", "link") else value)
    
    db.session.commit()
    return jsonify(gift.to_dict())
```

- `<int:gift_id>`: URL 경로의 숫자를 자동으로 `gift_id` 변수로 받음
- `get_or_404`: 없으면 404 에러 자동 반환
- 들어온 필드만 업데이트 (부분 수정)

**Delete (삭제):**
```python
@app.route("/admin/gifts/<int:gift_id>", methods=["DELETE"])
def admin_delete(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    db.session.delete(gift)
    db.session.commit()
    return jsonify({"deleted": gift_id})
```

**RESTful API 설계 원칙:**

| 동작 | HTTP 메서드 | URL |
|---|---|---|
| 전체 조회 | GET | `/admin/gifts` |
| 단일 조회 | GET | `/admin/gifts/123` |
| 생성 | POST | `/admin/gifts` |
| 수정 | PUT | `/admin/gifts/123` |
| 삭제 | DELETE | `/admin/gifts/123` |

→ **URL은 명사(자원), 동작은 HTTP 메서드로 표현**

---

### 2.5 seed.py

**역할**: 컨테이너 시작 시 cleaned_gifts.json을 MySQL에 자동 입력

```python
"""
초기 데이터 시드 스크립트

cleaned_gifts.json → MySQL gifts 테이블 INSERT
중복 실행 시 기존 데이터를 모두 지우고 다시 넣음.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.models import db, Gift


JSON_PATH = os.environ.get("SEED_PATH", "/app/data/cleaned_gifts.json")


def seed():
    with app.app_context():
        # 기존 데이터 모두 삭제
        existing = Gift.query.count()
        if existing > 0:
            print(f"기존 {existing}개 삭제 중...")
            Gift.query.delete()
            db.session.commit()
        
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for item in data:
            gift = Gift(
                name=item["name"],
                category=item["category"],
                price=item["price"],
                gender=item["gender"],
                min_age=item["min_age"],
                max_age=item["max_age"],
                target=item.get("target"),
                link=(item.get("link") or "")[:2000] or None,
            )
            db.session.add(gift)
        
        db.session.commit()
        total = Gift.query.count()
        print(f"✓ {total}개 선물 시드 완료")


if __name__ == "__main__":
    seed()
```

**왜 매번 비우고 다시 넣나?**
- 학습용이라 데이터를 항상 깨끗한 상태로 유지
- 실서비스라면 `INSERT IGNORE` 또는 중복 체크 후 추가

**`[:2000]`은 왜?**
- 쿠팡 링크가 너무 길어서 (1500자+) DB 컬럼 크기(2000) 초과 방지

---

## 3. 프론트엔드 (HTML + CSS + JS)

### 3.1 frontend/Dockerfile

**역할**: nginx 웹서버에 정적 파일들 올려서 이미지 만들기

```dockerfile
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html admin.html styles.css app.js admin.js /usr/share/nginx/html/

EXPOSE 80
```

- `nginx:alpine`: Alpine Linux 기반의 가벼운 nginx 이미지 (50MB도 안 됨)
- `/usr/share/nginx/html/`: nginx가 기본으로 정적 파일 서빙하는 폴더
- 80번 포트로 HTTP 응답 (docker-compose에서 8080:80으로 매핑)

---

### 3.2 nginx.conf

**역할**: nginx 서버 설정

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1d;
    }
}
```

- `listen 80`: 80번 포트로 요청 받음
- `root`: 정적 파일이 있는 폴더
- `try_files`: 요청 URL에 해당하는 파일 찾기
- `expires 1d`: CSS/JS 등은 브라우저에서 1일간 캐시 (속도 ↑)

---

### 3.3 index.html

**역할**: 사용자 페이지의 HTML 구조 (뼈대)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>생일선물 추천</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="top-nav">
        <a href="/" class="nav-active">추천받기</a>
        <a href="/admin.html">관리자</a>
    </nav>

    <div class="container">
        <header>
            <h1>생일선물 추천</h1>
            <p class="subtitle">조건에 맞는 선물을 찾아드립니다</p>
        </header>

        <main>
            <section class="form-section">
                <h2>받는 분 정보</h2>
                <form id="giftForm">
                    <div class="form-group">
                        <label for="age">나이</label>
                        <input type="number" id="age" min="1" max="100" value="25" required>
                    </div>

                    <div class="form-group">
                        <label>성별</label>
                        <div class="radio-group">
                            <label class="radio-label">
                                <input type="radio" name="gender" value="female" checked>
                                <span>여성</span>
                            </label>
                            <label class="radio-label">
                                <input type="radio" name="gender" value="male">
                                <span>남성</span>
                            </label>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="budget">예산 (원)</label>
                        <input type="number" id="budget" min="1000" step="any" value="100000" required>
                    </div>

                    <div class="form-group">
                        <label>선호 카테고리 (선택 안 하면 전체)</label>
                        <div id="categoryGroup" class="checkbox-group"></div>
                    </div>

                    <button type="submit" class="submit-btn">추천받기</button>
                </form>
            </section>

            <section id="results" class="results-section hidden">
                <h2>추천 결과</h2>
                <div id="resultsList" class="results-grid"></div>
            </section>

            <div id="loading" class="hidden">추천 중...</div>
            <div id="error" class="error hidden"></div>
        </main>

        <footer><p>Flask · MySQL · Docker</p></footer>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

**구조 분석:**

| 요소 | 역할 |
|---|---|
| `<meta charset="UTF-8">` | 한글 깨짐 방지 |
| `<meta name="viewport">` | 모바일 반응형 대응 |
| `<nav>` | 상단 메뉴 |
| `<form id="giftForm">` | 입력 폼 (JS에서 이 id로 접근) |
| `step="any"` | **가격을 자유롭게 입력 가능** (100000, 200000 등 모두 OK) |
| `<div id="categoryGroup">` | JS로 카테고리 동적 생성 (API에서 받아옴) |
| `<section id="results" class="hidden">` | 결과 영역 (처음엔 숨김) |
| `<script src="app.js">` | JS 로드 (HTML 끝에 두는 게 표준) |

**중요한 학습 포인트:**
- HTML은 **구조만** 담당, 스타일은 CSS, 동작은 JS (관심사 분리)
- `id`/`class`: JS와 CSS에서 요소를 찾을 때 사용

---

### 3.4 admin.html

**역할**: 관리자 페이지 구조 (목록 + 검색 + 모달)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>관리자 - 생일선물</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="top-nav">
        <a href="/">추천받기</a>
        <a href="/admin.html" class="nav-active">관리자</a>
    </nav>

    <div class="container container-wide">
        <header>
            <h1>선물 관리</h1>
            <p class="subtitle">DB 데이터를 추가/수정/삭제할 수 있습니다</p>
        </header>

        <div class="admin-toolbar">
            <input type="text" id="searchInput" placeholder="상품명으로 검색">
            <button class="btn btn-secondary" onclick="loadGifts(1)">검색</button>
            <button class="btn btn-primary" onclick="openModal()">새 선물 추가</button>
        </div>

        <div id="totalInfo"></div>

        <table class="gift-table">
            <thead>
                <tr>
                    <th>ID</th><th>상품명</th><th>카테고리</th>
                    <th>가격</th><th>성별</th><th>나이대</th><th>관리</th>
                </tr>
            </thead>
            <tbody id="giftTableBody"></tbody>
        </table>

        <div id="pagination" class="pagination"></div>
    </div>

    <!-- 추가/수정 모달 -->
    <div id="modal" class="modal-overlay hidden">
        <div class="modal">
            <h3 id="modalTitle">새 선물 추가</h3>
            <form id="giftEditForm">
                <input type="hidden" id="editId">
                <div class="form-group">
                    <label>상품명 *</label>
                    <input type="text" id="editName" required>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>카테고리 *</label>
                        <input type="text" id="editCategory" required>
                    </div>
                    <div class="form-group">
                        <label>가격 (원) *</label>
                        <input type="number" id="editPrice" required min="0">
                    </div>
                </div>
                <!-- ... 더 많은 입력 필드 ... -->
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">취소</button>
                    <button type="submit" class="btn btn-primary">저장</button>
                </div>
            </form>
        </div>
    </div>

    <script src="admin.js"></script>
</body>
</html>
```

**핵심 개념: 모달(Modal)**
- 다른 화면 위에 떠 있는 작은 창
- `class="hidden"`으로 처음엔 숨겨두고, 버튼 클릭 시 보이게
- 추가/수정 모두 같은 모달 재사용

---

### 3.5 app.js

**역할**: 사용자 페이지의 동작 (카테고리 로딩, 추천 요청, 결과 렌더링)

```javascript
const API_URL = "http://localhost:5000";

const form = document.getElementById("giftForm");
const resultsSection = document.getElementById("results");
const resultsList = document.getElementById("resultsList");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const categoryGroup = document.getElementById("categoryGroup");
```

**페이지 로드 시 카테고리 가져오기:**

```javascript
window.addEventListener("DOMContentLoaded", async () => {
    try {
        const res = await fetch(`${API_URL}/categories`);
        const data = await res.json();
        data.categories.forEach(cat => {
            const label = document.createElement("label");
            label.innerHTML = `<input type="checkbox" value="${cat}"> ${cat}`;
            categoryGroup.appendChild(label);
        });
    } catch (err) {
        categoryGroup.innerHTML = `<small>카테고리 로딩 실패 (백엔드 확인 필요)</small>`;
    }
});
```

**핵심 개념:**
- `DOMContentLoaded`: HTML 다 로드되면 실행
- `async/await`: 비동기 통신을 동기처럼 깔끔하게 작성
- `fetch()`: 백엔드 API 호출
- `createElement()` + `appendChild()`: 동적으로 HTML 요소 생성

**폼 제출 시 추천 요청:**

```javascript
form.addEventListener("submit", async (e) => {
    e.preventDefault();  // 페이지 새로고침 방지
    errorBox.classList.add("hidden");
    resultsSection.classList.add("hidden");
    loading.classList.remove("hidden");

    const age = parseInt(document.getElementById("age").value);
    const gender = document.querySelector('input[name="gender"]:checked').value;
    const budget = parseInt(document.getElementById("budget").value);
    const categories = Array.from(
        document.querySelectorAll('#categoryGroup input:checked')
    ).map(cb => cb.value);

    try {
        const response = await fetch(`${API_URL}/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ age, gender, budget, categories })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "서버 오류");
        }

        const data = await response.json();
        displayResults(data.recommendations);
    } catch (err) {
        errorBox.textContent = `❌ ${err.message}`;
        errorBox.classList.remove("hidden");
    } finally {
        loading.classList.add("hidden");
    }
});
```

**핵심 개념:**
- `e.preventDefault()`: 폼 제출 시 페이지 새로고침 막기 (SPA 방식)
- `fetch(URL, options)`: POST 요청 보낼 때 method/headers/body 명시
- `JSON.stringify()`: JavaScript 객체 → JSON 문자열 변환
- `try/catch/finally`: 에러 처리 + 항상 실행할 코드

**결과 화면에 그리기:**

```javascript
function displayResults(gifts) {
    resultsList.innerHTML = "";

    if (gifts.length === 0) {
        resultsList.innerHTML = `<div>조건에 맞는 선물을 찾지 못했어요.</div>`;
    } else {
        const emojiMap = {
            "뷰티/케어": "💄", "식품/간식": "🍫", "패션/잡화": "👜",
            "리빙/인테리어": "🏠", "디지털/가전": "📱", "취미/여가": "🎨",
            "상품권": "🎫", "캐릭터/굿즈": "🧸"
        };

        gifts.forEach(gift => {
            const card = document.createElement("div");
            card.className = "gift-card";
            const emoji = emojiMap[gift.category] || "🎁";
            const linkBtn = gift.link 
                ? `<a href="${gift.link}" target="_blank" class="gift-link">바로가기 →</a>`
                : '';
            card.innerHTML = `
                <div class="gift-emoji">${emoji}</div>
                <div class="gift-category">${gift.category}</div>
                <div class="gift-name">${gift.name}</div>
                <div class="gift-price">${gift.price.toLocaleString()}원</div>
                ${gift.target ? `<div class="gift-target">${gift.target}</div>` : ''}
                <div class="gift-score">매칭 +${gift.score}</div>
                ${linkBtn}
            `;
            resultsList.appendChild(card);
        });
    }

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
}
```

**핵심 개념:**
- **템플릿 리터럴** (`` ` ``): 백틱으로 감싸면 변수 삽입 가능 (`${변수}`)
- **삼항 연산자** (`A ? B : C`): 조건부 표시
- `toLocaleString()`: 100000 → "100,000" 천 단위 콤마

---

### 3.6 admin.js

**역할**: 관리자 페이지의 모든 CRUD 동작

```javascript
const API_URL = "http://localhost:5000";

let currentPage = 1;
const PER_PAGE = 15;

window.addEventListener("DOMContentLoaded", () => loadGifts(1));

// Enter로 검색
document.getElementById("searchInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") loadGifts(1);
});
```

**목록 불러오기:**

```javascript
async function loadGifts(page = 1) {
    currentPage = page;
    const search = document.getElementById("searchInput").value;
    const url = `${API_URL}/admin/gifts?page=${page}&per_page=${PER_PAGE}&search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        renderTable(data.gifts);
        renderPagination(data);
        document.getElementById("totalInfo").textContent = 
            `총 ${data.total}개 / ${data.pages}페이지`;
    } catch (err) {
        showError(`데이터 로딩 실패: ${err.message}`);
    }
}
```

**핵심:**
- URL에 `?page=1&per_page=15&search=립스틱` 같은 **쿼리 파라미터** 추가
- `encodeURIComponent()`: 한글이나 특수문자를 URL 안전하게 변환

**테이블 렌더링:**

```javascript
function renderTable(gifts) {
    const tbody = document.getElementById("giftTableBody");
    tbody.innerHTML = "";

    gifts.forEach(g => {
        const tr = document.createElement("tr");
        const genderLabel = { female: "여", male: "남", unisex: "공용" }[g.gender];
        tr.innerHTML = `
            <td>${g.id}</td>
            <td>${g.name}</td>
            <td>${g.category}</td>
            <td>${g.price.toLocaleString()}</td>
            <td>${genderLabel}</td>
            <td>${g.min_age}~${g.max_age}</td>
            <td class="actions">
                <button class="btn btn-secondary" onclick='editGift(${JSON.stringify(g)})'>수정</button>
                <button class="btn btn-danger" onclick="deleteGift(${g.id}, '${g.name}')">삭제</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
```

**모달 열기/닫기:**

```javascript
function openModal(gift = null) {
    document.getElementById("modal").classList.remove("hidden");
    document.getElementById("modalTitle").textContent = gift ? "선물 수정" : "새 선물 추가";
    
    if (gift) {
        // 수정 모드: 기존 값 채우기
        document.getElementById("editId").value = gift.id;
        document.getElementById("editName").value = gift.name;
        document.getElementById("editCategory").value = gift.category;
        document.getElementById("editPrice").value = gift.price;
        document.getElementById("editGender").value = gift.gender;
        document.getElementById("editAgeRange").value = `${gift.min_age}-${gift.max_age}`;
        document.getElementById("editTarget").value = gift.target || "";
        document.getElementById("editLink").value = gift.link || "";
    } else {
        // 추가 모드: 폼 초기화
        document.getElementById("giftEditForm").reset();
        document.getElementById("editId").value = "";
    }
}

function closeModal() {
    document.getElementById("modal").classList.add("hidden");
}
```

**핵심 기법:**
- **하나의 모달로 추가/수정 둘 다 처리** (gift가 있으면 수정, 없으면 추가)
- `classList.add/remove("hidden")`로 표시/숨김

**저장 (생성 또는 수정):**

```javascript
document.getElementById("giftEditForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("editId").value;
    const [min_age, max_age] = document.getElementById("editAgeRange").value.split("-").map(Number);
    
    const payload = {
        name: document.getElementById("editName").value,
        category: document.getElementById("editCategory").value,
        price: parseInt(document.getElementById("editPrice").value),
        gender: document.getElementById("editGender").value,
        min_age, max_age,
        target: document.getElementById("editTarget").value || null,
        link: document.getElementById("editLink").value || null,
    };

    // ID 있으면 PUT(수정), 없으면 POST(생성)
    const url = id ? `${API_URL}/admin/gifts/${id}` : `${API_URL}/admin/gifts`;
    const method = id ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("저장 실패");
        closeModal();
        loadGifts(currentPage);
    } catch (err) {
        alert(`❌ ${err.message}`);
    }
});
```

**핵심:**
- `id`의 존재 여부로 **HTTP 메서드 분기** (PUT vs POST)
- 저장 후 `loadGifts(currentPage)`로 목록 새로고침 → 즉시 반영!

**삭제:**

```javascript
async function deleteGift(id, name) {
    if (!confirm(`정말 "${name}"을(를) 삭제하시겠습니까?`)) return;
    try {
        const res = await fetch(`${API_URL}/admin/gifts/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("삭제 실패");
        loadGifts(currentPage);
    } catch (err) {
        alert(`❌ ${err.message}`);
    }
}
```

- `confirm()`: 확인/취소 팝업
- DELETE 메서드로 API 호출

---

### 3.7 styles.css

**역할**: 전체 디자인 (색상, 레이아웃, 모달 등)

**핵심: CSS 변수**

```css
:root {
    --primary: #1a1a1a;           /* 메인 색 */
    --bg: #fafafa;                /* 배경 */
    --card: #ffffff;              /* 카드 */
    --text: #1a1a1a;              /* 글자 */
    --text-light: #666666;        /* 보조 글자 */
    --border: #e5e5e5;            /* 테두리 */
    --border-strong: #cccccc;     /* 진한 테두리 */
    --danger: #c0392b;            /* 빨간색 (삭제) */
    --success: #27ae60;           /* 초록색 (성공) */
}
```

**왜 변수를 쓰나?**
- 모든 색이 한 곳에 정의 → 디자인 변경이 쉬움
- 일관성 유지 (같은 회색을 여러 곳에서 정의하면 미묘하게 달라짐)
- 예: 핑크 톤으로 바꾸고 싶으면 `--primary: #ff6b9d`로만 바꾸면 전체 적용

**사용 예시:**
```css
.submit-btn {
    background: var(--text);     /* CSS 변수 사용 */
    color: var(--card);
}
```

**주요 디자인 컴포넌트:**

```css
/* 입력 필드 */
input[type="number"], input[type="text"], select {
    width: 100%;
    padding: 0.7rem 0.9rem;
    border: 1px solid var(--border-strong);
    border-radius: 4px;
    font-size: 0.95rem;
    transition: border-color 0.15s;
}

input:focus, select:focus {
    outline: none;
    border-color: var(--text);
}
```

```css
/* 카드 그리드 (반응형) */
.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
}
```

**`repeat(auto-fill, minmax(220px, 1fr))`** 분석:
- `220px` 이상 크기의 카드가 들어갈 만큼 자동으로 컬럼 개수 결정
- 화면이 커지면 카드 자동 추가, 작아지면 자동 감소 → **반응형!**

```css
/* 모달 오버레이 */
.modal-overlay {
    position: fixed;
    inset: 0;                                    /* 화면 전체 덮음 */
    background: rgba(0, 0, 0, 0.4);             /* 반투명 검정 */
    display: flex;
    align-items: center;
    justify-content: center;                     /* 중앙 정렬 */
    z-index: 100;
}
```

- `position: fixed; inset: 0`: 스크롤해도 화면에 고정
- `z-index: 100`: 다른 요소들 위로 (높을수록 위)

```css
/* 호버 효과 */
.gift-card:hover { 
    border-color: var(--border-strong);
    transform: translateY(-2px);   /* 살짝 떠오르는 느낌 */
}
```

```css
/* 애니메이션 */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.gift-card {
    animation: fadeIn 0.3s ease-out;
}
```

- 결과가 나올 때 부드럽게 페이드 인

**반응형 (모바일 대응):**

```css
@media (max-width: 600px) {
    h1 { font-size: 1.6rem; }
    .form-section { padding: 1.5rem; }
    .container { padding: 2rem 1rem; }
}
```

- 화면 너비 600px 이하일 때만 적용 → 모바일에서 글자/여백 조정

---

## 4. 인프라 (Docker)

### 4.1 docker-compose.yml

**역할**: 3개 컨테이너(mysql, backend, frontend)를 한 번에 관리

```yaml
version: '3.8'

services:
  # ========== MySQL DB ==========
  mysql:
    image: mysql:8.0
    container_name: gift-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: giftdb
      MYSQL_USER: giftuser
      MYSQL_PASSWORD: giftpass
      TZ: Asia/Seoul
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-prootpass"]
      interval: 5s
      timeout: 3s
      retries: 20

  # ========== Flask 백엔드 ==========
  backend:
    build: ./backend
    container_name: gift-backend
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: giftuser
      DB_PASSWORD: giftpass
      DB_NAME: giftdb
    volumes:
      - ./data:/app/data:ro
      - ./backend/app:/app/app
    depends_on:
      mysql:
        condition: service_healthy

  # ========== nginx 프론트엔드 ==========
  frontend:
    build: ./frontend
    container_name: gift-frontend
    restart: unless-stopped
    ports:
      - "8080:80"
    depends_on:
      - backend

volumes:
  mysql_data:
```

**각 옵션 자세히:**

**MySQL 서비스:**

| 옵션 | 의미 |
|---|---|
| `image: mysql:8.0` | 미리 만들어진 MySQL 8.0 이미지 사용 |
| `restart: unless-stopped` | 죽으면 자동 재시작 (수동 중지 제외) |
| `environment` | DB 계정/비밀번호 환경변수 설정 |
| `ports: "3306:3306"` | 호스트:컨테이너 포트 매핑 |
| `volumes: mysql_data:/var/lib/mysql` | 데이터 영속성 (컨테이너 삭제해도 유지) |
| `command: --character-set-server=utf8mb4` | 한글 안 깨지게 |
| `healthcheck` | MySQL 준비됐는지 5초마다 확인 |

**핵심: 볼륨(Volume)**

```
컨테이너 (일시적)        볼륨 (영구적)
[gift-mysql]            [mysql_data]
     ↓ 데이터 저장           ↑
     └─────────────────────┘
     
컨테이너 삭제해도 → 볼륨 데이터는 살아있음
```

**핵심: 헬스체크**
- MySQL이 진짜 쿼리 받을 준비됐는지 확인
- 백엔드가 너무 빨리 연결 시도하다 실패하는 거 방지

**백엔드 서비스:**

| 옵션 | 의미 |
|---|---|
| `build: ./backend` | 해당 폴더의 Dockerfile로 이미지 빌드 |
| `DB_HOST: mysql` | **서비스명으로 DB 접근** (Docker 내부 통신) |
| `volumes: ./backend/app:/app/app` | 호스트 코드를 컨테이너에 마운트 (코드 수정 즉시 반영) |
| `depends_on: mysql: condition: service_healthy` | MySQL 준비된 후 시작 |

**🔑 가장 헷갈리는 부분: 네트워크**

```
컨테이너 사이 (같은 네트워크 내부)
  backend → mysql:3306 ✅ 서비스명으로!

브라우저에서 (외부)
  브라우저 → localhost:5000 ✅ 호스트 포트로!
```

→ `frontend/app.js`에 `API_URL = "http://localhost:5000"`인 이유  
→ `backend/app/main.py`에 `DB_HOST = "mysql"`인 이유

**프론트엔드 서비스:**

| 옵션 | 의미 |
|---|---|
| `ports: "8080:80"` | 호스트의 8080 ↔ 컨테이너 내부 80(nginx 기본 포트) |
| `depends_on: backend` | 백엔드 먼저 떠야 시작 |

---

## 5. 데이터

### 5.1 cleaned_gifts.json

**역할**: 111개 선물 데이터 (DB 시드용)

**구조:**

```json
[
  {
    "name": "헤어퍼퓸 에센스 오일+기프트 (6종 택1)",
    "category": "뷰티/케어",
    "price": 23000,
    "gender": "female",
    "min_age": 10,
    "max_age": 19,
    "target": null,
    "link": "https://example.com/..."
  },
  ...
]
```

**왜 JSON?**
- 사람이 읽기 쉬움
- 모든 프로그래밍 언어에서 지원
- DB로 옮기기 쉬움

**왜 정제했나?**
원본 엑셀에는:
- 성별이 `"여자"`, `"남자, 여자"`, `"여자/남자"` 등 7가지 표기
- 카테고리가 `"뷰티/케어"`와 `"뷰티,케어"` 혼재
- 나이대가 `"20대"` 같은 문자열

→ Python pandas로 정제하여 `male/female/unisex` + 표준 카테고리 + 숫자 나이로 통일

---

## 📖 전체 흐름 요약

### 사용자가 추천받을 때:

```
1. 브라우저에서 http://localhost:8080 접속
   → nginx가 index.html 보내줌
   
2. index.html 로드 → app.js 실행
   → fetch("http://localhost:5000/categories")
   → 백엔드 Flask가 SQLAlchemy로 MySQL 조회
   → JSON으로 응답 → 화면에 체크박스 동적 생성

3. 사용자가 폼 입력 → "추천받기" 클릭
   → fetch("http://localhost:5000/recommend", POST)
   → Flask가 SQL WHERE로 필터링
   → Python에서 점수 계산
   → 랜덤 셔플
   → JSON 응답
   
4. app.js가 결과를 받아 카드 UI로 렌더링
```

### 관리자가 선물 추가할 때:

```
1. admin.html에서 "새 선물 추가" 클릭
   → 모달 창 열림

2. 폼 입력 후 "저장" 클릭
   → fetch("http://localhost:5000/admin/gifts", POST)
   → Flask가 SQLAlchemy로 MySQL에 INSERT
   → 새 상품 정보 JSON 응답

3. 모달 닫힘 → 목록 자동 새로고침
   → 새로 추가된 상품이 맨 위에 보임
```

---

## 🎯 핵심 학습 정리

### 1. 3-Tier 아키텍처
**UI ← API ← DB** 분리 → 각각 독립 개발/수정 가능

### 2. ORM (SQLAlchemy)
SQL 안 써도 됨 + 자동 보안 + DB 종류 자유

### 3. RESTful API
URL=자원, HTTP 메서드=동작 → 직관적이고 표준적

### 4. Docker 컨테이너화
"내 컴퓨터에선 되는데" 문제 해결 → 환경 일관성

### 5. CSS 변수
한 곳만 바꿔서 전체 디자인 변경

### 6. async/await
복잡한 비동기 통신을 깔끔하게

### 7. 환경 변수
민감 정보(비밀번호 등) 코드에서 분리 → 보안 ↑

---

## 🛠️ 트러블슈팅 경험

### 1. 포트 충돌
**문제**: `failed to bind host port 0.0.0.0:3306/tcp: address already in use`  
**원인**: 호스트에 기존 MySQL 실행 중  
**해결**: `systemctl stop mysql`

### 2. DB 컬럼 크기 부족
**문제**: `Data too long for column 'link' at row 1`  
**원인**: 쿠팡 트래킹 링크가 1500자+  
**해결**: `String(500)` → `String(2000)` 확장

### 3. MySQL 부팅 타이밍
**문제**: 백엔드가 너무 빨리 연결 시도해서 실패  
**해결**: healthcheck + 30회 재시도 루프

### 4. 가격 step 제약
**문제**: `step="10000"`이라 200000 같은 값 입력 시 검증 실패  
**해결**: `step="any"`로 변경

### 5. 한글 입력 안 됨
**문제**: Ubuntu에 한글 입력기 미설치  
**해결**: `apt install -y dbus-x11 ibus-hangul` + `ibus-setup`

---

## 📚 사용한 기술 스택 한눈에

| 영역 | 기술 | 역할 |
|---|---|---|
| **언어** | Python 3.11 | 백엔드 |
| | JavaScript ES6+ | 프론트엔드 |
| | HTML5/CSS3 | 구조/디자인 |
| | SQL | DB 쿼리 (ORM이 자동 생성) |
| **프레임워크** | Flask 3.0 | 웹 서버 |
| | Flask-SQLAlchemy | ORM |
| | Flask-Cors | CORS 처리 |
| **데이터베이스** | MySQL 8.0 | RDBMS |
| | PyMySQL | DB 드라이버 |
| **웹서버** | nginx (Alpine) | 정적 파일 서빙 |
| **인프라** | Docker | 컨테이너화 |
| | Docker Compose | 다중 컨테이너 관리 |
| **데이터 처리** | pandas | 엑셀 → JSON 변환 |
| **환경** | Ubuntu Linux | 실행 환경 |
| | VirtualBox | 가상화 |

---

## 🎤 발표 시 강조 포인트

1. **"풀스택 + 인프라"** 직접 구현 — 단순 코딩 이상의 통합 경험
2. **실데이터** (조원 8명이 직접 수집한 111개) — 단순 더미 데이터 아님
3. **트러블슈팅** — 5가지 실제 에러 → 직접 해결 (포트, DB, 타이밍, 검증, 입력기)
4. **컨테이너 이식성** — 어디서든 `docker compose up` 한 번이면 끝
5. **확장 가능 구조** — ORM/REST/모듈화로 향후 기능 추가 쉬움

---

발표 화이팅! 🎉

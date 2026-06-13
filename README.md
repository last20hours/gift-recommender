# 🎁 생일선물 추천 사이트 🎁  

> 리눅스 8조 ♾️무한도전♾️  
> Flask + MySQL + Docker 기반 풀스택 웹 애플리케이션  


## 💻  개발 환경
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS-1572B6?style=flat-square&logo=css3&logoColor=white&v=1)

---


## ✨ 서비스 장점 (Key Features) ✨
1. **시간 절약:** 선물을 고를 때 고민하는 시간이 획기적으로 줄어듭니다!
2. **맞춤형 추천:** 나이, 성별, 취미, 예산 등 개인화된 조건으로 최적의 선물을 추천받아보세요!
3. **정보 통합:** 다양한 선물 정보를 한곳에서 편리하게 찾아보세요!
4. **관리자 페이지 지원:** 전용 관리자 페이지를 통해 데이터를 손쉽게 관리할 수 있어, 지속적인 정보 업데이트가 가능합니다!
5. **원스톱 접근:** 실제 구매 링크가 연동되어 있어 추천받은 상품을 즉시 구매할 수 있습니다!

---  

### 🌲 폴더 트리

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

### 6. css 테마 미적용
**문제**: 수정된 스타일 파일('styles.css')이 브라우저에 즉시 반영되지 않음
**해결**: 'docker compose up -d --build' 명령어로 도커 재빌드 및 브라우저 강제 새로고침

### 7. 관리자 페이지 버튼 오작동
**문제**: 스타일 중복 선언으로 인해 관리자 페이지 버튼 UI 깨짐 및 기능 동작 불가
**해결**: 중복 코드 제거, 스타일 단위 분리, 속성 범위 정리






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

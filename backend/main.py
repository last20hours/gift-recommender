import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import or_, and_
from sqlalchemy.exc import OperationalError

from app.models import db, Gift



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
            @app.route("/")
def health():
    return jsonify({"status": "ok", "message": "생일선물 추천 API"})

@app.route("/categories", methods=["GET"])
def get_categories():
    """카테고리 목록 (프론트엔드 폼에서 사용)"""
    rows = db.session.query(Gift.category).distinct().all()
    return jsonify({"categories": [r[0] for r in rows]})
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
    @app.route("/admin/gifts/<int:gift_id>", methods=["DELETE"])
def admin_delete(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    db.session.delete(gift)
    db.session.commit()
    return jsonify({"deleted": gift_id})
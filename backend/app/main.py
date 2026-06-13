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
    
    # MySQL 컨테이너 부팅 대기 (Docker 환경에서 흔한 문제)
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
    
    register_routes(app)
    return app


def register_routes(app):
    # ==================== 공개 API ====================
    
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
        """
        조건 기반 선물 추천
        
        요청 예시:
        {
          "age": 25,
          "gender": "female",
          "budget": 100000,
          "categories": ["뷰티/케어", "패션/잡화"]  // 선택 사항
        }
        """
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
        
        # ⭐ 필터링을 SQL WHERE로 처리 (성능 ↑)
        query = Gift.query.filter(
            Gift.min_age <= age,
            Gift.max_age >= age,
            Gift.price <= budget,
            or_(Gift.gender == gender, Gift.gender == "unisex"),
        )
        
        # 카테고리 선택 시 필터 추가
        if categories:
            query = query.filter(Gift.category.in_(categories))
        
        # 너무 많이 가져오지 않도록 우선 100개로 자르기
        candidates = query.limit(100).all()
        
        # 점수 계산 (Python에서)
        scored = []
        for g in candidates:
            score = 0
            # 가성비 보너스: 예산 절반 이하
            if g.price <= budget / 2:
                score += 3
            # 카테고리 매칭 보너스
            if categories and g.category in categories:
                score += 5
            # 나이대 중심 매칭 (받는 사람 나이가 범위 중앙에 가까우면 보너스)
            mid = (g.min_age + g.max_age) / 2
            if abs(age - mid) <= 5:
                score += 2
            
            d = g.to_dict()
            d["score"] = score
            scored.append(d)
        
        import random
        random.shuffle(scored)
        
        return jsonify({
            "input": data,
            "count": len(scored[:6]),
            "recommendations": scored[:6]
        })
    
    # ==================== 관리자 CRUD ====================
    
    @app.route("/admin/gifts", methods=["GET"])
    def admin_list():
        """전체 선물 (검색 + 페이지네이션)"""
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
    
    @app.route("/admin/gifts/<int:gift_id>", methods=["GET"])
    def admin_get(gift_id):
        gift = Gift.query.get_or_404(gift_id)
        return jsonify(gift.to_dict())
    
    @app.route("/admin/gifts", methods=["POST"])
    def admin_create():
        """새 선물 추가"""
        data = request.get_json() or {}
        
        # 필수 필드 검증
        required = ["name", "category", "price", "gender", "min_age", "max_age"]
        missing = [f for f in required if data.get(f) in (None, "")]
        if missing:
            return jsonify({"error": f"필수 필드 누락: {', '.join(missing)}"}), 400
        
        if data["gender"] not in ("male", "female", "unisex"):
            return jsonify({"error": "gender는 male/female/unisex 중 하나"}), 400
        
        try:
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
        except (ValueError, TypeError) as e:
            db.session.rollback()
            return jsonify({"error": f"입력값 오류: {e}"}), 400
    
    @app.route("/admin/gifts/<int:gift_id>", methods=["PUT"])
    def admin_update(gift_id):
        """선물 수정"""
        gift = Gift.query.get_or_404(gift_id)
        data = request.get_json() or {}
        
        # 들어온 필드만 업데이트
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
        """선물 삭제"""
        gift = Gift.query.get_or_404(gift_id)
        db.session.delete(gift)
        db.session.commit()
        return jsonify({"deleted": gift_id})


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
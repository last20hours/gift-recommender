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
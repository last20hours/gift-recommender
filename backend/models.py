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
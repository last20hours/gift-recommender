FROM python:3.11-slim

WORKDIR /app

# 의존성 캐싱
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#시드 스크립트 복사
COPY . .
COPY scripts/ ./scripts/

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD python scripts/seed.py && python app/main.py
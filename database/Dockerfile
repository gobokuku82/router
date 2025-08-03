# 빌드 스테이지
FROM python:3.11-slim as builder

WORKDIR /app

# 빌드 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ML 의존성 먼저 설치 (자주 변경되지 않음)
COPY requirements-ml.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-ml.txt && \
    rm -rf ~/.cache/pip/*

# 기본 Python 의존성 설치 (더 자주 변경됨)
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt && \
    rm -rf ~/.cache/pip/*

# 실행 스테이지
FROM python:3.11-slim

WORKDIR /app

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# 빌드 스테이지에서 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사 (자주 변경되지 않는 것부터)
COPY config/ ./config/
COPY models/ ./models/
COPY schemas/ ./schemas/
COPY services/ ./services/
COPY routers/ ./routers/

# 메인 애플리케이션 파일 복사
COPY main.py .

# 포트 노출
EXPOSE 8000

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/routers", "--reload-dir", "/app/services", "--reload-dir", "/app/models", "--reload-dir", "/app/schemas", "--reload-dir", "/app/config", "--reload-dir", "/app/main.py"] 
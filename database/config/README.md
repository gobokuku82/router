# 중앙화된 설정 관리 시스템

## 개요

이 프로젝트는 모든 환경변수를 중앙화된 설정 시스템으로 관리합니다. 
`backend/config/settings.py`에서 모든 설정을 정의하고 검증합니다.

## 구조

```
backend/config/
├── __init__.py          # 패키지 초기화
├── settings.py          # 메인 설정 클래스
└── README.md           # 이 문서
```

## 설정 클래스

### 1. DatabaseSettings
PostgreSQL 데이터베이스 연결 설정

```python
from backend.config import settings

# 데이터베이스 URL 가져오기
db_url = settings.get_database_url()
# 또는 직접 접근
db_url = settings.database.database_url
```

### 2. MinIOSettings
MinIO 객체 저장소 설정

```python
# MinIO 설정 가져오기
minio_config = settings.get_minio_config()
# 또는 직접 접근
endpoint = settings.minio.endpoint
bucket = settings.minio.bucket_name
```

### 3. OpenSearchSettings
OpenSearch 검색 엔진 설정

```python
# OpenSearch 설정 가져오기
opensearch_config = settings.get_opensearch_config()
# 또는 직접 접근
host = settings.opensearch.host
port = settings.opensearch.port
```

### 4. JWTSettings
JWT 토큰 인증 설정

```python
# JWT 설정 가져오기
jwt_config = settings.get_jwt_config()
# 또는 직접 접근
secret_key = settings.jwt.secret_key.get_secret_value()
```

### 5. PgAdminSettings
PgAdmin 관리 도구 설정

```python
# PgAdmin 설정 직접 접근
email = settings.pgadmin.default_email
password = settings.pgadmin.default_password.get_secret_value()
```

### 6. AppSettings
애플리케이션 전체 설정

```python
# 애플리케이션 설정 직접 접근
env = settings.app.env
debug = settings.app.debug
```

## 사용 방법

### 1. 서비스에서 설정 사용

```python
from backend.config import settings

# 데이터베이스 연결
from sqlalchemy import create_engine
engine = create_engine(settings.get_database_url())

# MinIO 클라이언트
import boto3
s3_client = boto3.client("s3", **settings.get_minio_config())

# OpenSearch 클라이언트
from opensearchpy import OpenSearch
opensearch_config = settings.get_opensearch_config()
client = OpenSearch(
    hosts=[{"host": opensearch_config["host"], "port": opensearch_config["port"]}],
    http_auth=(opensearch_config["user"], opensearch_config["password"])
)
```

### 2. 라우터에서 설정 사용

```python
from backend.config import settings

# JWT 설정 사용
jwt_config = settings.get_jwt_config()
SECRET_KEY = jwt_config["secret_key"]
ALGORITHM = jwt_config["algorithm"]
```

## 환경변수 검증

앱 시작 시 모든 필수 환경변수가 자동으로 검증됩니다:

```python
# settings.py에서 자동 실행
try:
    settings.validate_all()
    print("✅ 모든 환경변수가 올바르게 설정되었습니다.")
except ValueError as e:
    print(f"❌ 환경변수 설정 오류: {e}")
    raise
```

## 보안 기능

- **SecretStr**: 민감한 정보(비밀번호, 시크릿 키)는 `SecretStr`로 래핑
- **자동 검증**: 필수 환경변수 누락 시 즉시 에러 발생
- **타입 안전성**: Pydantic을 통한 타입 검증

## 장점

1. **중앙화**: 모든 설정이 한 곳에서 관리
2. **타입 안전성**: Pydantic을 통한 자동 타입 검증
3. **보안**: 민감한 정보의 안전한 처리
4. **유지보수성**: 설정 변경 시 한 곳만 수정
5. **검증**: 앱 시작 시 모든 설정 자동 검증
6. **IDE 지원**: 자동완성 및 타입 힌트 지원

## 환경변수 목록

필수 환경변수:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET_NAME`
- `OPENSEARCH_HOST`, `OPENSEARCH_PORT`, `OPENSEARCH_INITIAL_ADMIN_PASSWORD`
- `JWT_SECRET_KEY`
- `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`

선택적 환경변수:
- `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `APP_ENV`, `APP_DEBUG`
- `OPENSEARCH_CA_CERTS` 
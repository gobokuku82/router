# 환경변수를 아래와 같이 설정해주세요. 이 환경변수는 docker-compose.yml에서 사용되며, config\settings.py에서 로드되어 사용됩니다.
# 하단의 JWT 키는 generate_jwt_secret.py 파일을 실행하여 나온 값을 넣어주세요. JWT에 대한 자세한 설명은 JWT_SECURITY_GUIDE.md를 참고해주세요.

# Database Configuration
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydatabase
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# OpenSearch Configuration
OPENSEARCH_HOST=opensearch-node1
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_INITIAL_ADMIN_PASSWORD=G7!kz@2pQw

# MinIO Configuration
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_BUCKET_NAME=documents

# PgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin1234

# JWT Configuration
JWT_SECRET_KEY=생성된 키 값

# OpenAI Configuration
OPENAI_API_KEY=private-your-key

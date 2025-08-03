import boto3
from config import settings

# 중앙화된 설정에서 MinIO 설정 가져오기
minio_config = settings.get_minio_config()
MINIO_BUCKET = minio_config["bucket_name"]
MINIO_ENDPOINT = minio_config["endpoint_url"]

# boto3 클라이언트 생성 시 bucket_name 제외
s3_config = {k: v for k, v in minio_config.items() if k != "bucket_name"}
s3_client = boto3.client("s3", **s3_config)

def upload_file(file_bytes, filename, content_type):
    # 버킷이 없으면 생성
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)
    # 파일 업로드
    import io
    s3_client.upload_fileobj(io.BytesIO(file_bytes), MINIO_BUCKET, filename, ExtraArgs={"ContentType": content_type})
    url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{filename}"
    return url

def delete_file_from_s3(file_name: str):
    """MinIO에서 파일을 삭제합니다."""
    try:
        s3_client.delete_object(Bucket=MINIO_BUCKET, Key=file_name)
        return True
    except Exception as e:
        print(f"[S3] 파일 삭제 실패: {e}")
        return False 
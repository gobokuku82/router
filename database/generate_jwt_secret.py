#!/usr/bin/env python3
"""
안전한 JWT_SECRET_KEY 생성 스크립트

이 스크립트는 암호학적으로 안전한 JWT_SECRET_KEY를 생성합니다.
"""

import secrets
import string
import base64
import os

def generate_secure_jwt_secret(length: int = 64) -> str:
    """
    암호학적으로 안전한 JWT_SECRET_KEY를 생성합니다.
    
    Args:
        length: 생성할 키의 길이 (기본값: 64)
    
    Returns:
        안전한 JWT_SECRET_KEY 문자열
    """
    # 사용할 문자 세트 정의
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # 암호학적으로 안전한 랜덤 문자열 생성
    jwt_secret = ''.join(secrets.choice(characters) for _ in range(length))
    
    return jwt_secret

def generate_base64_jwt_secret(length: int = 64) -> str:
    """
    Base64 인코딩된 JWT_SECRET_KEY를 생성합니다.
    
    Args:
        length: 원본 바이트 길이 (기본값: 64)
    
    Returns:
        Base64 인코딩된 JWT_SECRET_KEY
    """
    # 암호학적으로 안전한 랜덤 바이트 생성
    random_bytes = secrets.token_bytes(length)
    
    # Base64로 인코딩
    jwt_secret = base64.b64encode(random_bytes).decode('utf-8')
    
    return jwt_secret

def main():
    """메인 함수"""
    print("🔐 안전한 JWT_SECRET_KEY 생성기")
    print("=" * 50)
    
    # 방법 1: 문자 기반 생성
    print("\n📝 방법 1: 문자 기반 JWT_SECRET_KEY (64자)")
    jwt_secret_1 = generate_secure_jwt_secret(64)
    print(f"JWT_SECRET_KEY={jwt_secret_1}")
    
    # 방법 2: Base64 인코딩 생성
    print("\n📝 방법 2: Base64 인코딩 JWT_SECRET_KEY (64바이트)")
    jwt_secret_2 = generate_base64_jwt_secret(64)
    print(f"JWT_SECRET_KEY={jwt_secret_2}")
    
    # 방법 3: 더 긴 키 생성
    print("\n📝 방법 3: 긴 JWT_SECRET_KEY (128자)")
    jwt_secret_3 = generate_secure_jwt_secret(128)
    print(f"JWT_SECRET_KEY={jwt_secret_3}")
    
    print("\n" + "=" * 50)
    print("💡 사용 방법:")
    print("1. 위의 키 중 하나를 선택하세요.")
    print("2. .env 파일에 JWT_SECRET_KEY=선택한키 형태로 추가하세요.")
    print("3. 운영 환경에서는 반드시 강력한 키를 사용하세요.")
    print("4. 키를 안전한 곳에 백업해두세요.")
    
    print("\n⚠️  보안 주의사항:")
    print("- 절대 Git에 커밋하지 마세요.")
    print("- 운영 환경마다 다른 키를 사용하세요.")
    print("- 정기적으로 키를 교체하세요.")
    print("- 키가 노출되면 즉시 교체하세요.")

if __name__ == "__main__":
    main() 
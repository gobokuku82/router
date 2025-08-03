# JWT_SECRET_KEY 보안 가이드

## 🔐 JWT_SECRET_KEY란?

JWT_SECRET_KEY는 JSON Web Token(JWT)을 서명하고 검증하는 데 사용되는 비밀키입니다. 
이 키가 노출되면 공격자가 유효한 토큰을 생성할 수 있어 보안상 매우 중요합니다.

## ⚠️ 보안 위험

### 1. 약한 키 사용 시 위험
- **토큰 위조**: 공격자가 유효한 토큰을 생성
- **세션 하이재킹**: 다른 사용자의 세션 탈취
- **권한 상승**: 관리자 권한으로 접근

### 2. 키 노출 시 위험
- **전체 시스템 침해**: 모든 인증 시스템 무력화
- **사용자 데이터 유출**: 개인정보 및 민감한 데이터 노출
- **법적 책임**: 개인정보보호법 위반

## 🛠️ 안전한 JWT_SECRET_KEY 생성 방법

### 방법 1: Python 스크립트 사용
```bash
python generate_jwt_secret.py
```

### 방법 2: 터미널 명령어

#### Linux/Mac (OpenSSL 사용)
```bash
# 64자 랜덤 문자열 생성
openssl rand -base64 64

# 128자 랜덤 문자열 생성
openssl rand -base64 128

# 32바이트 랜덤 데이터를 16진수로 출력
openssl rand -hex 32
```

#### Windows (PowerShell 사용)
```powershell
# 64자 랜덤 문자열 생성
$bytes = New-Object Byte[] 64
(New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
[Convert]::ToBase64String($bytes)

# 128자 랜덤 문자열 생성
$bytes = New-Object Byte[] 128
(New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

#### Python 원라이너
```bash
# Python 3.6+ 사용
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 또는
python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(64)))"
```

## 📋 JWT_SECRET_KEY 요구사항

### 최소 요구사항
- **길이**: 최소 32자 이상 (권장: 64자 이상)
- **복잡성**: 대문자, 소문자, 숫자, 특수문자 포함
- **예측 불가능성**: 암호학적으로 안전한 랜덤 생성

### 권장 사양
- **길이**: 64-128자
- **인코딩**: Base64 또는 URL-safe Base64
- **생성**: 암호학적으로 안전한 난수 생성기 사용

## 🔧 설정 방법

### 1. .env 파일에 추가
```env
# 안전한 JWT_SECRET_KEY 설정
JWT_SECRET_KEY=your-generated-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 2. 예시 키 (실제 사용 금지!)
```env
# ❌ 절대 사용하지 마세요! (예시용)
JWT_SECRET_KEY=K8x#mP2$vL9nQ4@jR7wE1&hF5tY3*uI6oA8sD0zX9cV4bN2mK7pL1qW5eR3tY8uI2oP9a

# ✅ 이렇게 생성된 키를 사용하세요
JWT_SECRET_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

## 🚨 보안 체크리스트

### 개발 환경
- [ ] 강력한 JWT_SECRET_KEY 사용 (최소 64자)
- [ ] .env 파일을 .gitignore에 추가
- [ ] 키를 안전한 곳에 백업
- [ ] 정기적으로 키 교체

### 운영 환경
- [ ] 환경별로 다른 키 사용
- [ ] 키 관리 시스템 사용 (AWS Secrets Manager, HashiCorp Vault 등)
- [ ] 키 로테이션 정책 수립
- [ ] 키 접근 권한 제한
- [ ] 키 사용 로그 모니터링

### 긴급 상황
- [ ] 키 노출 시 즉시 교체
- [ ] 모든 사용자 세션 무효화
- [ ] 보안 사고 보고 및 대응
- [ ] 원인 분석 및 재발 방지

## 📚 추가 보안 권장사항

### 1. 토큰 만료 시간 설정
```env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1시간
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7     # 7일
```

### 2. 토큰 블랙리스트 구현
- 로그아웃 시 토큰을 블랙리스트에 추가
- Redis나 데이터베이스에 블랙리스트 저장

### 3. 토큰 페이로드 최소화
- 민감한 정보를 토큰에 포함하지 않음
- 필요한 최소한의 정보만 포함

### 4. HTTPS 사용
- 프로덕션 환경에서는 반드시 HTTPS 사용
- 토큰 전송 시 암호화 보장

## 🔍 키 강도 테스트

### 온라인 도구
- [Password Strength Checker](https://www.passwordmonster.com/)
- [How Secure Is My Password](https://howsecureismypassword.net/)

## 📞 문제 발생 시 대응

### 1. 키 노출 의심 시
1. 즉시 키 교체
2. 모든 사용자 세션 무효화
3. 보안 로그 확인
4. 침해 범위 분석

### 2. 키 분실 시
1. 백업에서 복구
2. 백업이 없으면 새 키 생성
3. 모든 사용자 재인증 요구

### 3. 키 관리 시스템 장애 시
1. 백업 키 사용
2. 시스템 복구 후 키 교체
3. 장애 원인 분석 및 재발 방지 
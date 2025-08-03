# 제약영업 챗봇 시스템 백엔드/DB 설계 및 운영 총정리

---

## 1. 프로젝트 개요 및 목표

이 프로젝트는 **제약영업 챗봇 시스템**의 데이터베이스 및 API 백엔드 구축을 목표로 한다. 
- **주요 기술스택**: FastAPI, PostgreSQL, Alembic, S3/MinIO, OpenSearch
- **주요 요구사항**: 실전 제약영업 데이터(직원, 거래처, 제품, 실적, 문서 등) 관리, 문서 업로드/검색/임베딩, 관리자/직원 권한 분리, 운영 환경 신뢰성, 확장성, 보안

---

## 2. 전체 폴더/파일 구조 및 역할

```
jjs_narutalk/
├─ backend/
│  └─ app/
│     └─ database_api/
│        ├─ models/         # ERD 기반 SQLAlchemy ORM 모델
│        ├─ schemas/        # Pydantic 스키마
│        ├─ services/       # DB, S3, OpenSearch 등 서비스 모듈
│        ├─ routers/        # (확장용) API 라우터
│        ├─ alembic/        # Alembic 마이그레이션 환경
│        ├─ alembic.ini     # Alembic 설정
│        ├─ requirements.txt# DB/마이그레이션 관련 의존성
│        ├─ db_api.py       # FastAPI 엔트리포인트 및 API 구현
│        └─ readmd.md       # 이 문서(전체 구조/운영/이슈/의사결정 총정리)
├─ database/
│  ├─ docker-compose.yml    # (이전) 인프라/DB 컨테이너 관리
│  └─ ...                   # (이전) Alembic, DB 초기화 등
└─ ...
```

---

## 3. 데이터베이스(ERD) 및 테이블 설계

### 3.1 핵심 테이블
- **employees**: 직원 정보, 관리자/일반직원 구분, 권한 관리
- **customers**: 거래처 정보
- **products**: 제품 정보
- **interaction_logs**: 영업활동 기록
- **sales_records**: 판매실적
- **customer_monthly_performance_mv**: 거래처별 월별 실적(Materialized View)
- **documents**: 문서 메타데이터(업로드 파일)
- **document_relations, document_interaction_map, document_sales_map**: 문서-실적/활동/거래처 등 매핑
- **chat_history**: 챗봇 대화 로그
- **system_trace_logs**: 시스템 내부 동작/오류 로그
- **assignment_map**: 직원-거래처 매핑

### 3.2 설계 원칙
- 모든 테이블은 PK/FK, 인덱스, 역할, 관계를 명확히 정의
- Materialized View는 Alembic에서 raw SQL로 생성/관리
- ERD 기반으로 Pydantic 스키마, SQLAlchemy 모델, 마이그레이션 스크립트 일관성 유지

---

## 4. Alembic 마이그레이션 전략 및 운영 방식

### 4.1 개발/테스트 환경
- (과거) docker-compose up 시 alembic 서비스로 자동 마이그레이션 시도
- **문제점**: import 경로, PYTHONPATH, 마운트 경로 불일치로 인한 반복적인 실패
- **결론**: 컨테이너 자동 마이그레이션은 개발/테스트에만 한정, 운영 환경에서는 비권장

### 4.2 운영 환경/실전 배포
- **API 기반 수동 마이그레이션**으로 전환
- `/admin/migrate` 엔드포인트에서 subprocess로 alembic upgrade head 실행
- 운영 환경에서는 반드시 인증/권한 체크 필요(현재는 데모용으로 생략)
- Alembic 환경(ini/env.py/versions)은 모두 backend/app/database_api 내부에 통합 관리
- 마이그레이션 실행 시 PYTHONPATH를 프로젝트 루트로 명시적으로 지정하여 import 문제 해결

---

## 5. API/서비스 구조 및 주요 기능

### 5.1 FastAPI 엔트리포인트: db_api.py
- **문서 업로드/조회/삭제**: S3/MinIO 업로드, 메타데이터 저장, 리스트/상세/삭제
- **문서 청킹/임베딩/검색**: 업로드 시 문장 단위 청킹, 임베딩 생성(임시/실제), OpenSearch 인덱싱(향후 고도화)
- **직원/관리자 등록**: 최초 1회만 허용되는 관리자 등록(`/init-admin`), 이후 직원 등록 및 권한 관리 확장 예정
- **Alembic 마이그레이션 API**: `/admin/migrate`에서 DB 마이그레이션 트리거(운영 환경에서는 인증 필수)
- **기타**: ERD 기반 모델/스키마/서비스 구조화, 확장성/유지보수성 확보

### 5.2 서비스/유틸 구조
- **services/db.py**: DB 세션/연결 관리, 환경변수 기반 설정
- **services/s3_service.py, opensearch_service.py**: 파일 저장, 벡터 검색 등 외부 서비스 연동
- **models, schemas**: ERD 기반 ORM/Pydantic 구조화

---

## 6. 주요 이슈 및 해결 과정

### 6.1 DB 연결/마이그레이션 이슈
- docker-compose 환경에서 볼륨/포트/환경변수/로컬 PostgreSQL 충돌로 인한 접속 실패
- Alembic 마이그레이션 시 import 경로, PYTHONPATH, 마운트 경로 불일치로 인한 반복적인 ImportError
- **해결**: 운영 환경에서는 API 기반 수동 마이그레이션, PYTHONPATH 명시, 절대경로 import로 통일

### 6.2 운영/개발 환경 분리
- 개발/테스트는 자동화, 운영은 명시적 수동화로 전략 분리
- .env, requirements.txt, alembic.ini 등 환경/설정 파일 경로 일관성 유지

### 6.3 권한/보안/실전 운영 고려
- 관리자/직원 권한 분리, 최초 1회 관리자 등록, 운영 환경에서는 인증/인가 필수
- DB/서비스 구조를 ERD 기반으로 일관성 있게 설계하여 유지보수성/확장성 확보

---

## 7. 실전 운영/개발 팁 및 주의사항

- **DB 볼륨/포트 충돌**: 로컬 PostgreSQL과 docker 컨테이너가 동시에 5432 포트 사용 시 반드시 로컬 서버 중지
- **.env/requirements.txt 경로**: 실제 마운트/실행 경로와 일치해야 함
- **alembic env.py import**: 운영 환경에서는 반드시 절대경로 import, PYTHONPATH 명시
- **마이그레이션 API**: 운영 환경에서는 인증/권한 체크 필수, 개발/테스트에서는 편의상 생략 가능
- **문서 업로드/임베딩/검색**: 실제 서비스에서는 임베딩/검색 모델 연동 필요(현재는 임시/테스트용)
- **ERD/모델/스키마/마이그레이션**: 항상 일관성 유지, 변경 시 ERD-모델-스키마-마이그레이션 동시 관리

---

## 8. 향후 작업 및 확장 방향

- **ERD 기반 핵심 테이블/모델/스키마 확장 및 리팩토링**
- **문서 청킹/임베딩/검색 고도화(OpenSearch, AI 연동 등)**
- **관리자/직원 권한 관리, 인증/인가 강화**
- **운영 환경 배포, CI/CD, 보안 강화**
- **실전 데이터/업무 프로세스 반영, 대시보드/통계/분석 기능 확장**

---

## 9. 의사결정/구조 설계 요약

- **자동 vs 수동 마이그레이션**: 개발/테스트는 자동화, 운영은 수동화(명시적/안전)
- **폴더/모듈 구조**: backend/app/database_api 내부에 모든 핵심 코드/설정 통합, 유지보수성/확장성 극대화
- **import 경로**: 운영 환경에서는 절대경로 import, PYTHONPATH 명시로 일관성 확보
- **API 기반 관리**: 마이그레이션, 관리자 등록 등 주요 관리 기능을 API로 제공(운영 환경에서는 인증 필수)

---

## 10. 문의/요청/참고 사항

- 추가 기능 요청, 구조 개선, 운영 환경 배포, 실전 데이터 반영 등 필요한 사항은 언제든 문의/요청 가능
- 이 문서 하나로 프로젝트 전체 구조, 운영 전략, 주요 이슈/해결, 실전 운영/개발 팁, 향후 방향까지 모두 파악 가능 
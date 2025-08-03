# Database ERD (Entity Relationship Diagram)

## --- Entities Definition ---

Table Employees as E {
  employee_id int [pk, increment, note: '직원 고유 식별자']
  username varchar(50) [unique, not null, note: '시스템 로그인 아이디']
  password varchar(255) [not null, note: '암호화된 비밀번호']
  name varchar(50) [not null, note: '직원 실명']
  team varchar(50) [note: '소속 부서']
  position varchar(50) [note: '직급']
  business_unit varchar(50) [note: '사업부']
  branch varchar(50) [note: '지점']
  contact_number varchar(20) [note: '연락처']
  responsibilities text [note: '주요 책임 업무']
  base_salary int [note: '기본급 (₩)']
  incentive_pay int [note: '성과급 (₩)']
  avg_monthly_budget int [note: '월평균 사용 예산 (₩)']
  latest_evaluation varchar(100) [note: '최근 평가 등급 또는 요약']
  role varchar(20) [not null, note: '시스템 권한 (admin, manager, user)']
  created_at timestamp [note: '계정 생성일']
}

Table Customers as C {
  customer_id int [pk, increment, note: '거래처 고유 식별자']
  customer_name varchar(100) [not null, note: '거래처 이름']
  address varchar(255) [note: '거래처 주소']
  doctor_name varchar(50) [note: '주요 담당 의사/약사 이름']
  total_patients int [note: '총 환자 수']
  customer_grade varchar(10) [note: '고객 등급']
  notes text [note: '성향, 특징 등 기타 메모']
  created_at timestamp [note: '정보 최초 등록일']
  
  indexes {
    (customer_name, address) [unique, note: '같은 지역의 같은 이름은 중복 불가']
  }
}

Table Customer_Monthly_Performance_MV as CMP [note: 'Materialized View'] {
  performance_id int [pk, increment, note: '월별 실적 고유 식별자']
  customer_id int [ref: > C.customer_id, not null, note: '거래처 참조 키']
  year_month date [not null, note: '실적 년월 (예: 2025-07-01)']
  monthly_sales int [note: '해당 월의 총 매출액']
  budget_used int [note: '해당 월에 사용한 예산']
  visit_count int [note: '해당 월의 총 방문 횟수']

  indexes {
    (customer_id, year_month) [unique]
  }
}

Table Products as P {
  product_id int [pk, increment, note: '제품 고유 식별자']
  product_name varchar(100) [not null, note: '제품명']
  description text [note: '제품 상세 설명']
  category varchar(50) [note: '제품 분류']
  is_active boolean [note: '현재 판매 여부']
}

Table Documents as D {
  doc_id int [pk, increment, note: '문서 고유 식별자']
  uploader_id int [ref: > E.employee_id, not null, note: '업로드한 직원 참조 키']
  doc_title varchar(255) [not null, note: '문서 제목']
  doc_type varchar(50) [note: '문서 종류 (보고서, 계약서 등)']
  file_path varchar(512) [not null, note: 'S3에 저장된 실제 파일 경로']
  version float [note: '문서 버전']
  created_at timestamp [note: '문서 업로드 시각']
}

Table Document_Relations as DR {
  relation_id int [pk, increment, note: '문서 관계 고유 식별자']
  source_doc_id int [ref: > D.doc_id, not null, note: '기준이 되는 문서 참조 키']
  related_doc_id int [ref: > D.doc_id, not null, note: '참조되거나 관련된 문서 참조 키']
  relation_type varchar(20) [not null, note: "관계 종류 ('reference', 'similar')"]

  indexes {
    (source_doc_id, related_doc_id) [unique]
  }
}

Table Interaction_Logs as IL {
  log_id int [pk, increment, note: '영업 활동 기록 고유 식별자']
  employee_id int [ref: > E.employee_id, not null, note: '활동을 수행한 직원 참조 키']
  customer_id int [ref: > C.customer_id, not null, note: '활동 대상 거래처 참조 키']
  interaction_type varchar(20) [note: '활동 종류 (방문, 전화 등)']
  summary text [note: '활동 요약 내용']
  sentiment varchar(20) [note: '대화 감성 분석 결과']
  compliance_risk text [note: '규정 위반 가능성 메모']
  interacted_at timestamp [note: '활동 발생 시각']
}

Table Sales_Records as SR {
  record_id int [pk, increment, note: '판매 실적 고유 식별자']
  employee_id int [ref: > E.employee_id, not null, note: '판매 담당 직원 참조 키']
  customer_id int [ref: > C.customer_id, not null, note: '판매 대상 거래처 참조 키']
  product_id int [ref: > P.product_id, not null, note: '판매된 제품 참조 키']
  sale_amount decimal(15, 2) [not null, note: '판매 금액']
  sale_date date [not null, note: '판매 확정일']
}

Table Assignment_Map as AM {
  assignment_id int [pk, increment, note: '담당 관계 고유 식별자']
  employee_id int [ref: > E.employee_id, not null, note: '담당 직원 참조 키']
  customer_id int [ref: > C.customer_id, not null, note: '담당 거래처 참조 키']
  
  indexes {
    (employee_id, customer_id) [unique]
  }
} 

Table Document_Interaction_Map as DIM {
  link_id int [pk, increment, note: '문서-활동 연결 고유 식별자']
  doc_id int [ref: > D.doc_id, not null, note: '문서 참조 키']
  interaction_id int [ref: > IL.log_id, not null, note: '영업 활동 기록 참조 키']

  indexes {
    (doc_id, interaction_id) [unique]
  }
}

Table Document_Sales_Map as DSM {
  link_id int [pk, increment, note: '문서-실적 연결 고유 식별자']
  doc_id int [ref: > D.doc_id, not null, note: '문서 참조 키']
  sales_record_id int [ref: > SR.record_id, not null, note: '판매 실적 참조 키']

  indexes {
    (doc_id, sales_record_id) [unique]
  }
}

// 신규 추가: 사용자 채팅 기록
Table Chat_History as CH {
  message_id bigserial [pk, note: '메시지 고유 식별자']
  session_id varchar(100) [not null, note: '동일 대화 세션을 묶는 ID']
  employee_id int [ref: > E.employee_id, not null, note: '대화 직원 참조 키']
  user_query text [note: '사용자 입력 메시지']
  system_response text [note: '챗봇 답변 메시지']
  created_at timestamp [not null, note: '메시지 생성 시각']

  indexes {
    session_id
  }
}

// 신규 추가: 시스템 내부 동작 로그
Table System_Trace_Logs as STL {
  trace_id bigserial [pk, note: '내부 로그 고유 식별자']
  message_id bigint [ref: > CH.message_id, not null, note: '채팅 메시지 참조 키']
  event_type varchar(50) [note: "이벤트 종류 ('rag_search', 'llm_call' 등)"]
  log_data jsonb [note: '이벤트 관련 상세 데이터 (JSON 형식)']
  latency_ms int [note: '이벤트 처리 소요 시간 (ms)']
  created_at timestamp [not null, note: '로그 생성 시각']
}

## 테이블 관계 설명

### 핵심 테이블 (Core Tables)
- **Employees (E)**: 직원 정보 및 권한 관리
- **Customers (C)**: 거래처 정보 관리
- **Products (P)**: 제품 정보 관리
- **Documents (D)**: 문서 메타데이터 관리

### 활동 및 실적 테이블 (Activity & Performance Tables)
- **Interaction_Logs (IL)**: 영업 활동 기록
- **Sales_Records (SR)**: 판매 실적 데이터
- **Customer_Monthly_Performance_MV (CMP)**: 거래처 월별 성과 (Materialized View)

### 매핑 테이블 (Mapping Tables)
- **Assignment_Map (AM)**: 직원-거래처 담당 관계
- **Document_Relations (DR)**: 문서 간 관계
- **Document_Interaction_Map (DIM)**: 문서-영업활동 연결
- **Document_Sales_Map (DSM)**: 문서-판매실적 연결

### 웹로그 테이블 (Web Log Tables)
- **Chat_History (CH)**: 사용자 채팅 기록
- **System_Trace_Logs (STL)**: 시스템 내부 동작 로그

## 주요 특징

1. **단일 기본키 + 유니크 인덱스**: 매핑 테이블들은 단일 기본키와 유니크 인덱스를 조합하여 중복 방지
2. **외래키 참조**: 모든 관계가 명확한 외래키로 정의됨
3. **타임스탬프**: 대부분의 테이블에 생성 시각 기록
4. **Materialized View**: 성능 최적화를 위한 월별 성과 뷰
5. **JSONB 지원**: 시스템 로그에서 유연한 데이터 저장 
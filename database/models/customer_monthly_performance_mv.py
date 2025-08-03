from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base

Base = declarative_base()
metadata = MetaData()

# 실제 사용 시 engine을 import해서 autoload_with=engine로 사용해야 함
# 예시: from backend.app.database_api.db import engine
# 아래는 구조 예시

def get_customer_monthly_performance_mv_table(engine):
    """고객별 월간 성과를 관리하는 Materialized View 테이블"""
    return Table(
        "customer_monthly_performance_mv",
        metadata,
        Column("performance_id", Integer, primary_key=True),  # 성과 기록 고유 ID (기본키)
        Column("customer_id", Integer),  # 고객 ID (외래키)
        Column("year_month", String),  # 년월 (예: 2024-01)
        Column("monthly_sales", Integer),  # 월간 매출액 (원 단위)
        Column("budget_used", Integer),  # 사용된 예산 (원 단위)
        Column("visit_count", Integer),  # 방문 횟수
        autoload_with=engine
    )

# 실제 사용 시 아래처럼 동적으로 __table__을 할당해야 함
#
# CustomerMonthlyPerformanceMV = type(
#     "CustomerMonthlyPerformanceMV",
#     (Base,),
#     {"__table__": get_customer_monthly_performance_mv_table(engine)}
# ) 

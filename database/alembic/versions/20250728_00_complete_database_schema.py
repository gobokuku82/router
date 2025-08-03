"""Complete database schema with all tables and views

Revision ID: 20250728_00
Revises: 
Create Date: 2025-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '20250728_00'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # employees (계정 정보만)
    op.create_table(
        'employees',
        sa.Column('employee_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('email', sa.String, unique=True, nullable=False),
        sa.Column('username', sa.String, unique=True, nullable=False),
        sa.Column('password', sa.String, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('role', sa.String, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime),
    )
    
    # employee_info (인사 정보)
    op.create_table(
        'employee_info',
        sa.Column('employee_info_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('employees.employee_id'), nullable=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('employee_number', sa.String, unique=True),  # 사번 (고유값, 동명이인 구분용)
        sa.Column('team', sa.String),
        sa.Column('position', sa.String),
        sa.Column('business_unit', sa.String),
        sa.Column('branch', sa.String),
        sa.Column('contact_number', sa.String),
        sa.Column('base_salary', sa.Integer),
        sa.Column('incentive_pay', sa.Integer),
        sa.Column('avg_monthly_budget', sa.Integer),
        sa.Column('latest_evaluation', sa.String),
        sa.Column('responsibilities', sa.String),  # 책임업무/담당업무
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    
    # customers
    op.create_table(
        'customers',
        sa.Column('customer_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('customer_name', sa.String, nullable=False),
        sa.Column('address', sa.String),
        sa.Column('doctor_name', sa.String),
        sa.Column('total_patients', sa.Integer),
        sa.Column('customer_grade', sa.String),
        sa.Column('notes', sa.String),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime),
        sa.UniqueConstraint('customer_name', 'address', name='uq_customer_name_address'),
    )
    
    # products
    op.create_table(
        'products',
        sa.Column('product_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('product_name', sa.String, nullable=False),
        sa.Column('description', sa.String),
        sa.Column('category', sa.String),
        sa.Column('is_active', sa.Boolean, default=True),
    )
    
    # interaction_logs
    op.create_table(
        'interaction_logs',
        sa.Column('log_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('employee_info.employee_info_id'), nullable=False),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('customers.customer_id'), nullable=False),
        sa.Column('interaction_type', sa.String, nullable=False),
        sa.Column('summary', sa.String),
        sa.Column('sentiment', sa.String),
        sa.Column('compliance_risk', sa.String),
        sa.Column('interacted_at', sa.DateTime),
    )
    
    # sales_records
    op.create_table(
        'sales_records',
        sa.Column('record_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('employee_info.employee_info_id', ondelete='SET NULL'), nullable=True),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('customers.customer_id', ondelete='SET NULL'), nullable=True),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('products.product_id', ondelete='SET NULL'), nullable=True),
        sa.Column('sale_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('sale_date', sa.Date, nullable=False),
    )
    
    # documents
    op.create_table(
        'documents',
        sa.Column('doc_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('uploader_id', sa.Integer, sa.ForeignKey('employees.employee_id'), nullable=False),
        sa.Column('doc_title', sa.String, nullable=False),
        sa.Column('doc_type', sa.String),
        sa.Column('file_path', sa.String, nullable=False),
        sa.Column('version', sa.String),
        sa.Column('created_at', sa.DateTime),
    )
    
    # chat_history
    op.create_table(
        'chat_history',
        sa.Column('message_id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String, nullable=False),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('employees.employee_id'), nullable=False),
        sa.Column('user_query', sa.Text, nullable=False),
        sa.Column('system_response', sa.Text, nullable=False),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # system_trace_logs
    op.create_table(
        'system_trace_logs',
        sa.Column('trace_id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('message_id', sa.BigInteger, sa.ForeignKey('chat_history.message_id'), nullable=False),
        sa.Column('event_type', sa.String, nullable=False),
        sa.Column('log_data', sa.dialects.postgresql.JSONB),
        sa.Column('latency_ms', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # assignment_map
    op.create_table(
        'assignment_map',
        sa.Column('assignment_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('employee_info.employee_info_id'), nullable=False),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('customers.customer_id'), nullable=False),
        sa.UniqueConstraint('employee_id', 'customer_id', name='uq_assignment_employee_customer'),
    )
    
    # document_relations
    op.create_table(
        'document_relations',
        sa.Column('relation_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('doc_id', sa.Integer, sa.ForeignKey('documents.doc_id'), nullable=False),
        sa.Column('related_entity_type', sa.String, nullable=False),
        sa.Column('related_entity_id', sa.Integer, nullable=False),
        sa.Column('confidence_score', sa.Integer, default=100),
        sa.Column('created_at', sa.DateTime),
        sa.UniqueConstraint('doc_id', 'related_entity_type', 'related_entity_id', name='uq_doc_relation_unique'),
    )
    
    # document_interaction_map
    op.create_table(
        'document_interaction_map',
        sa.Column('link_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('doc_id', sa.Integer, sa.ForeignKey('documents.doc_id'), nullable=False),
        sa.Column('interaction_id', sa.Integer, sa.ForeignKey('interaction_logs.log_id'), nullable=False),
        sa.UniqueConstraint('doc_id', 'interaction_id', name='uq_doc_interaction_doc_interaction'),
    )
    
    # document_sales_map
    op.create_table(
        'document_sales_map',
        sa.Column('link_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('doc_id', sa.Integer, sa.ForeignKey('documents.doc_id'), nullable=False),
        sa.Column('sales_record_id', sa.Integer, sa.ForeignKey('sales_records.record_id'), nullable=False),
        sa.UniqueConstraint('doc_id', 'sales_record_id', name='uq_doc_sales_doc_sales'),
    )
    
    # customer_monthly_performance_mv (Materialized View)
    op.execute("""
    CREATE MATERIALIZED VIEW customer_monthly_performance_mv AS
    SELECT
        ROW_NUMBER() OVER () AS performance_id,
        c.customer_id,
        to_char(sr.sale_date, 'YYYY-MM') AS year_month,
        SUM(sr.sale_amount) AS monthly_sales,
        SUM(sr.sale_amount) FILTER (WHERE sr.sale_amount IS NOT NULL) AS budget_used,
        COUNT(il.log_id) AS visit_count
    FROM
        customers c
    LEFT JOIN sales_records sr ON c.customer_id = sr.customer_id
    LEFT JOIN interaction_logs il ON c.customer_id = il.customer_id
    GROUP BY
        c.customer_id, to_char(sr.sale_date, 'YYYY-MM');
    """)

def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL의 DROP TABLE IF EXISTS 사용
    connection = op.get_bind()
    
    # Materialized View 삭제
    try:
        connection.execute("DROP MATERIALIZED VIEW IF EXISTS customer_monthly_performance_mv CASCADE")
    except Exception:
        pass
    
    # 테이블 목록 (외래키 의존성 순서 고려)
    tables = [
        'document_sales_map',
        'document_interaction_map', 
        'document_relations',
        'assignment_map',
        'system_trace_logs',
        'chat_history',
        'sales_records',
        'interaction_logs',
        'documents',
        'products',
        'customers',
        'employee_info',
        'employees'
    ]
    
    for table in tables:
        try:
            connection.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        except Exception:
            # 테이블이 없거나 삭제 실패해도 계속 진행
            pass 
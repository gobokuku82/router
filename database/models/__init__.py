from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .employees import Employee
from .employee_info import EmployeeInfo
from .customers import Customer
from .products import Product
from .interaction_logs import InteractionLog
from .sales_records import SalesRecord
from .customer_monthly_performance_mv import get_customer_monthly_performance_mv_table
from .documents import Document
from .chat_history import ChatHistory
from .system_trace_logs import SystemTraceLog
from .assignment_map import AssignmentMap
from .document_relations import DocumentRelation
from .document_interaction_map import DocumentInteractionMap
from .document_sales_map import DocumentSalesMap
 

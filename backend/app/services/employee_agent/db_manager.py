import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import os

class EmployeeDBManager:
    """직원 실적 및 목표 데이터베이스 관리 클래스"""
    
    def __init__(self):
        # 프로젝트 루트에서의 상대 경로 설정
        # 현재 파일: backend/app/services/employee_agent/db_manager.py
        # 프로젝트 루트까지: 5번의 parent 필요
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        self.performance_db_path = base_dir / "database" / "relationdb" / "performance_swest_sua.sqlite"
        self.target_db_path = base_dir / "database" / "relationdb" / "joonpharma_target.sqlite"
        
        print(f"[DB] 경로 확인:")
        print(f"   기준 디렉토리: {base_dir}")
        print(f"   실적 DB 경로: {self.performance_db_path}")
        print(f"   실적 DB 존재: {self.performance_db_path.exists()}")
        print(f"   목표 DB 경로: {self.target_db_path}")
        print(f"   목표 DB 존재: {self.target_db_path.exists()}")
        
        # 경로 문제 해결을 위한 대안 경로 체크
        if not self.performance_db_path.exists():
            print("[WARNING] 기본 경로에서 실적 DB를 찾을 수 없습니다. 대안 경로를 시도합니다.")
            # 현재 작업 디렉토리 기준으로 다시 시도
            cwd_base = Path.cwd()
            alt_performance_path = cwd_base / "database" / "relationdb" / "performance_swest_sua.sqlite"
            alt_target_path = cwd_base / "database" / "relationdb" / "joonpharma_target.sqlite"
            
            print(f"   현재 작업 디렉토리: {cwd_base}")
            print(f"   대안 실적 DB 경로: {alt_performance_path}")
            print(f"   대안 실적 DB 존재: {alt_performance_path.exists()}")
            
            if alt_performance_path.exists():
                print("[OK] 대안 경로에서 데이터베이스를 찾았습니다.")
                self.performance_db_path = alt_performance_path
                self.target_db_path = alt_target_path
    
    def get_connection(self, db_type: str) -> sqlite3.Connection:
        """데이터베이스 연결을 반환합니다."""
        if db_type == "performance":
            db_path = self.performance_db_path
        elif db_type == "target":
            db_path = self.target_db_path
        else:
            raise ValueError("db_type은 'performance' 또는 'target'이어야 합니다.")
        
        # 파일 존재 확인
        if not db_path.exists():
            raise FileNotFoundError(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
        
        return sqlite3.connect(str(db_path))
    
    def get_available_employees(self) -> List[str]:
        """사용 가능한 직원 목록을 반환합니다."""
        try:
            with self.get_connection("performance") as conn:
                query = "SELECT DISTINCT 담당자 FROM sales_performance WHERE 담당자 IS NOT NULL"
                df = pd.read_sql_query(query, conn)
                return df['담당자'].tolist()
        except Exception as e:
            print(f"직원 목록 조회 오류: {e}")
            return []
    
    def get_employee_performance_data(self, employee_name: str = None,
                                     start_period: str = None,
                                     end_period: str = None) -> pd.DataFrame:
        """직원의 실적 데이터를 조회합니다."""
        try:
            with self.get_connection("performance") as conn:
                # 기본 쿼리 (실제 테이블 구조에 맞게 수정)
                base_query = "SELECT * FROM sales_performance WHERE 1=1"
                params = []
                
                # 담당자 필터링
                if employee_name:
                    base_query += " AND 담당자 = ?"
                    params.append(employee_name)
                
                base_query += " ORDER BY 담당자, 품목"
                
                df = pd.read_sql_query(base_query, conn, params=params)
                print(f"[DATA] 실적 데이터 로드: {len(df)}개 레코드")
                return df
                
        except Exception as e:
            print(f"실적 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_employee_target_data(self, employee_name: str = None,
                                start_period: str = None,
                                end_period: str = None) -> pd.DataFrame:
        """직원의 목표 데이터를 조회합니다."""
        try:
            with self.get_connection("target") as conn:
                # 기본 쿼리: 지점, 담당자, 년월, 목표 칼럼만 사용
                base_query = "SELECT 지점, 담당자, 년월, 목표 FROM monthly_target WHERE 1=1"
                params = []
                
                # 담당자 필터링
                if employee_name:
                    base_query += " AND 담당자 = ?"
                    params.append(employee_name)
                
                # 기간 필터링
                if start_period:
                    base_query += " AND 년월 >= ?"
                    params.append(int(start_period))
                
                if end_period:
                    base_query += " AND 년월 <= ?"
                    params.append(int(end_period))
                
                base_query += " ORDER BY 담당자, 년월"
                
                df = pd.read_sql_query(base_query, conn, params=params)
                print(f"[DATA] 목표 데이터 로드: {len(df)}개 레코드")
                return df
                
        except Exception as e:
            print(f"목표 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_performance_summary(self, employee_name: str, 
                              start_period: str, end_period: str) -> Dict[str, Any]:
        """직원의 실적 요약을 반환합니다."""
        try:
            df = self.get_employee_performance_data(employee_name)
            
            # pandas boolean을 Python bool로 변환
            if bool(df.empty):
                return {
                    "employee_name": employee_name,
                    "period": f"{start_period}~{end_period}",
                    "total_performance": 0,
                    "monthly_breakdown": [],
                    "product_breakdown": [],
                    "client_breakdown": []
                }
            
            # 월별 컬럼 추출 (202312, 202401 등)
            month_columns = [col for col in df.columns if str(col).isdigit() and len(str(col)) == 6]
            
            # 분석 기간에 해당하는 월만 필터링
            if start_period and end_period:
                start_num = int(start_period)
                end_num = int(end_period)
                analysis_months = [col for col in month_columns if start_num <= int(col) <= end_num]
            else:
                analysis_months = month_columns
            
            print(f"[DATE] 분석 대상 월: {analysis_months}")
            
            # 총 실적 계산
            total_performance = 0
            monthly_breakdown = []
            product_breakdown = {}
            client_breakdown = {}
            
            for month in analysis_months:
                month_total = 0
                for idx, row in df.iterrows():
                    # pandas boolean을 Python bool로 변환
                    is_not_na = bool(pd.notna(row[month]))  # numpy.bool → bool 변환
                    value_check = bool(row[month] > 0) if is_not_na else False
                    
                    if is_not_na and value_check:
                        amount = float(row[month])
                        month_total += amount
                        
                        # 제품별 집계
                        product = row.get('품목', 'Unknown')
                        if product not in product_breakdown:
                            product_breakdown[product] = 0
                        product_breakdown[product] += amount
                        
                        # 거래처별 집계
                        client = row.get('ID', 'Unknown')
                        if client not in client_breakdown:
                            client_breakdown[client] = 0
                        client_breakdown[client] += amount
                
                if month_total > 0:
                    monthly_breakdown.append({
                        "month": month,
                        "amount": int(month_total)  # numpy 타입 방지
                    })
                    total_performance += month_total
            
            # numpy 타입을 Python 기본 타입으로 변환
            product_list = [
                {"name": name, "amount": int(amount)} 
                for name, amount in sorted(product_breakdown.items(), key=lambda x: x[1], reverse=True)
            ]
            
            client_list = [
                {"name": name, "amount": int(amount)}
                for name, amount in sorted(client_breakdown.items(), key=lambda x: x[1], reverse=True)
            ]
            
            return {
                "employee_name": employee_name,
                "period": f"{start_period}~{end_period}",
                "total_performance": int(total_performance),  # numpy 타입 방지
                "monthly_breakdown": monthly_breakdown,
                "product_breakdown": product_list,
                "client_breakdown": client_list
            }
            
        except Exception as e:
            print(f"실적 요약 계산 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                "employee_name": employee_name,
                "period": f"{start_period}~{end_period}",
                "total_performance": 0,
                "monthly_breakdown": [],
                "product_breakdown": [],
                "client_breakdown": []
            }
    
    def analyze_performance_trend(self, employee_name: str,
                                start_period: str, end_period: str) -> Dict[str, Any]:
        """실적 트렌드를 분석합니다."""
        try:
            summary = self.get_performance_summary(employee_name, start_period, end_period)
            monthly_data = summary["monthly_breakdown"]
            
            if len(monthly_data) < 2:
                return {
                    "trend": "데이터 부족",
                    "analysis": "트렌드 분석을 위해서는 최소 2개월 이상의 데이터가 필요합니다."
                }
            
            # 월별 실적 추이 분석
            amounts = [data["amount"] for data in monthly_data]
            
            # 단순 트렌드 계산
            if len(amounts) >= 3:
                recent_avg = sum(amounts[-2:]) / 2
                early_avg = sum(amounts[:2]) / 2
                
                if recent_avg > early_avg * 1.1:
                    trend = "상승"
                elif recent_avg < early_avg * 0.9:
                    trend = "하락"
                else:
                    trend = "안정"
            else:
                if amounts[-1] > amounts[0]:
                    trend = "상승"
                elif amounts[-1] < amounts[0]:
                    trend = "하락"
                else:
                    trend = "안정"
            
            return {
                "trend": trend,
                "analysis": f"분석 기간 동안 실적은 {trend} 추세를 보이고 있습니다.",
                "monthly_amounts": [int(amount) for amount in amounts]  # numpy 타입 방지
            }
            
        except Exception as e:
            print(f"트렌드 분석 오류: {e}")
            return {
                "trend": "분석 실패",
                "analysis": "트렌드 분석 중 오류가 발생했습니다."
            }
    
    def get_target_vs_performance(self, employee_name: str,
                                 start_period: str, end_period: str) -> Dict[str, Any]:
        """목표 대비 실적을 비교 분석합니다."""
        performance_summary = self.get_performance_summary(employee_name, start_period, end_period)
        
        # 목표 데이터 직접 조회 (간단한 쿼리 사용)
        target_df = self.get_employee_target_data(employee_name, start_period, end_period)
        
        total_performance = performance_summary["total_performance"]
        total_target = 0
        
        # 목표 데이터 계산
        if not bool(target_df.empty):  # pandas boolean → Python bool 변환
            try:
                # 목표 칼럼의 합계 계산
                numeric_targets = pd.to_numeric(target_df['목표'], errors='coerce')
                total_target = float(numeric_targets.sum())  # numpy 타입 방지
                print(f"[TARGET] 목표 데이터: {employee_name}의 목표 {total_target:,.0f}원")
                
            except Exception as e:
                print(f"목표 데이터 계산 오류: {e}")
                total_target = 0.0
        
        # 목표가 0이면 실적 기반으로 가상 목표 설정
        if float(total_target) <= 0:  # Python float로 비교
            print(f"[WARNING] '{employee_name}'의 목표 데이터가 없거나 0입니다.")
            # 실적의 80%를 목표로 가정 (실제 환경에서는 별도 설정 필요)
            total_target = float(total_performance) * 0.8
            print(f"[INFO] 실적의 80%({total_target:,.0f}원)를 가상 목표로 설정합니다.")
        
        # 달성률 계산 (Python float로 연산)
        achievement_rate = (float(total_performance) / float(total_target) * 100) if float(total_target) > 0 else 0.0
        
        # 달성률 평가 (Python float로 비교)
        achievement_rate_val = float(achievement_rate)
        if achievement_rate_val >= 120:
            evaluation = "매우 우수"
            grade = "A+"
        elif achievement_rate_val >= 100:
            evaluation = "우수"
            grade = "A"
        elif achievement_rate_val >= 80:
            evaluation = "양호"
            grade = "B"
        elif achievement_rate_val >= 60:
            evaluation = "보통"
            grade = "C"
        else:
            evaluation = "개선 필요"
            grade = "D"
        
        return {
            "total_performance": int(total_performance),  # numpy 타입 방지
            "total_target": int(total_target),
            "achievement_rate": float(achievement_rate),  # numpy 타입 방지
            "gap_amount": int(total_performance - total_target),
            "evaluation": evaluation,
            "grade": grade
        } 
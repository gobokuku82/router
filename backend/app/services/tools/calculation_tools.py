import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics

class PerformanceCalculationTools:
    """실적 분석 계산 도구 클래스"""
    
    @staticmethod
    def calculate_achievement_rate(performance: float, target: float) -> Dict[str, Any]:
        """달성률을 계산합니다."""
        if target <= 0:
            return {
                "achievement_rate": 0.0,
                "gap_amount": float(performance),
                "evaluation": "목표 없음"
            }
        
        achievement_rate = (performance / target) * 100
        gap_amount = performance - target
        
        if achievement_rate >= 120:
            evaluation = "매우 우수"
        elif achievement_rate >= 100:
            evaluation = "우수"
        elif achievement_rate >= 80:
            evaluation = "양호"
        elif achievement_rate >= 60:
            evaluation = "보통"
        else:
            evaluation = "개선 필요"
        
        return {
            "achievement_rate": float(achievement_rate),  # numpy 타입 방지
            "gap_amount": float(gap_amount),
            "evaluation": evaluation
        }
    
    @staticmethod
    def calculate_growth_rate(current: float, previous: float) -> float:
        """성장률을 계산합니다."""
        if previous <= 0:
            return 0.0
        return float((current - previous) / previous * 100)  # numpy 타입 방지
    
    @staticmethod
    def calculate_trend_analysis(amounts: List[float]) -> Dict[str, Any]:
        """트렌드 분석을 수행합니다."""
        if len(amounts) < 2:
            return {
                "trend": "데이터 부족",
                "trend_strength": "없음",
                "r_squared": 0.0,
                "slope": 0.0,
                "analysis": "분석에 필요한 데이터가 부족합니다."
            }
        
        try:
            # 선형 회귀 분석
            x = np.arange(len(amounts))
            y = np.array(amounts)
            
            # 기본 통계
            n = len(amounts)
            x_mean = np.mean(x)
            y_mean = np.mean(y)
            
            # 기울기와 절편 계산
            numerator = np.sum((x - x_mean) * (y - y_mean))
            denominator = np.sum((x - x_mean) ** 2)
            
            if denominator == 0:
                slope = 0
            else:
                slope = numerator / denominator
            
            intercept = y_mean - slope * x_mean
            
            # R² 계산
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y_mean) ** 2)
            
            # numpy boolean 연산을 Python bool로 변환
            if float(ss_tot) == 0:
                r_squared = 1.0 if float(ss_res) == 0 else 0.0
            else:
                r_squared = 1 - (ss_res / ss_tot)
            
            # 트렌드 분류 (numpy boolean을 Python bool로 변환)
            slope_val = float(slope)
            y_mean_val = float(y_mean)
            
            if abs(slope_val) < y_mean_val * 0.01:  # 평균의 1% 미만
                trend = "안정"
                trend_strength = "낮음"
            elif slope_val > y_mean_val * 0.05:  # 평균의 5% 이상 증가
                trend = "강한 상승"
                trend_strength = "높음"
            elif slope_val > 0:
                trend = "상승"
                trend_strength = "보통"
            elif slope_val < -y_mean_val * 0.05:  # 평균의 5% 이상 감소
                trend = "강한 하락"
                trend_strength = "높음"
            else:
                trend = "하락"
                trend_strength = "보통"
            
            return {
                "trend": trend,
                "trend_strength": trend_strength,
                "r_squared": float(r_squared),  # numpy 타입 방지
                "slope": float(slope),
                "intercept": float(intercept),
                "analysis": f"{trend} 트렌드 (신뢰도: {r_squared:.2f})"
            }
            
        except Exception as e:
            return {
                "trend": "분석 실패",
                "trend_strength": "없음",
                "r_squared": 0.0,
                "slope": 0.0,
                "analysis": f"트렌드 분석 중 오류: {e}"
            }
    
    @staticmethod
    def calculate_variance_analysis(amounts: List[float]) -> Dict[str, Any]:
        """분산 분석을 수행합니다."""
        if len(amounts) < 2:
            return {
                "variance": 0.0,
                "std_deviation": 0.0,
                "coefficient_of_variation": 0.0,
                "stability": "데이터 부족"
            }
        
        try:
            amounts_array = np.array(amounts)
            mean_val = float(np.mean(amounts_array))  # numpy 타입 방지
            variance = float(np.var(amounts_array))
            std_dev = float(np.std(amounts_array))
            
            # numpy boolean을 Python bool로 변환
            if float(mean_val) > 0:
                cv = (std_dev / mean_val) * 100
            else:
                cv = 0.0
            
            # 안정성 평가 (float 값으로 비교)
            cv_val = float(cv)
            if cv_val < 10:
                stability = "매우 안정"
            elif cv_val < 20:
                stability = "안정"
            elif cv_val < 30:
                stability = "보통"
            elif cv_val < 50:
                stability = "불안정"
            else:
                stability = "매우 불안정"
            
            return {
                "variance": variance,
                "std_deviation": std_dev,
                "coefficient_of_variation": float(cv),
                "stability": stability,
                "mean": mean_val
            }
            
        except Exception as e:
            return {
                "variance": 0.0,
                "std_deviation": 0.0,
                "coefficient_of_variation": 0.0,
                "stability": "분석 실패"
            }
    
    @staticmethod
    def calculate_seasonal_analysis(monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """계절성 분석 계산"""
        if len(monthly_data) < 4:
            return {
                "has_seasonality": False,
                "peak_months": [],
                "low_months": [],
                "seasonal_factor": {}
            }
        
        # 월별 평균 계산
        month_totals = {}
        for data in monthly_data:
            month = data["month"][-2:]  # YYYYMM에서 MM 추출
            amount = data["amount"]
            
            if month not in month_totals:
                month_totals[month] = []
            month_totals[month].append(amount)
        
        # 각 월의 평균 계산
        month_averages = {}
        for month, amounts in month_totals.items():
            month_averages[month] = float(np.mean(amounts))  # numpy 타입 방지
        
        if len(month_averages) < 2:
            return {
                "has_seasonality": False,
                "peak_months": [],
                "low_months": [],
                "seasonal_factor": {}
            }
        
        overall_average = float(np.mean(list(month_averages.values())))  # numpy 타입 방지
        
        # 계절성 지수 계산
        seasonal_factors = {}
        for month, avg in month_averages.items():
            seasonal_factors[month] = float(avg / overall_average)  # numpy 타입 방지
        
        # 피크와 저점 월 찾기
        sorted_months = sorted(month_averages.items(), key=lambda x: x[1], reverse=True)
        peak_months = [month for month, _ in sorted_months[:2]]
        low_months = [month for month, _ in sorted_months[-2:]]
        
        # 계절성 존재 여부 판단 (최고와 최저의 차이가 평균의 20% 이상)
        max_avg = float(max(month_averages.values()))  # numpy 타입 방지
        min_avg = float(min(month_averages.values()))  # numpy 타입 방지
        has_seasonality = bool((max_avg - min_avg) / overall_average > 0.2)  # numpy.bool → bool 변환
        
        # seasonality_strength 계산에서도 Python float 사용
        strength_ratio = (max_avg - min_avg) / overall_average
        if strength_ratio > 0.5:
            seasonality_strength = "강함"
        elif strength_ratio > 0.2:
            seasonality_strength = "보통"
        else:
            seasonality_strength = "약함"
        
        return {
            "has_seasonality": has_seasonality,  # 이제 Python bool
            "peak_months": peak_months,
            "low_months": low_months,
            "seasonal_factor": {k: float(round(v, 3)) for k, v in seasonal_factors.items()},  # numpy 타입 방지
            "seasonality_strength": seasonality_strength
        }
    
    @staticmethod
    def calculate_pareto_analysis(items: List[Dict[str, Any]], value_key: str = "amount") -> Dict[str, Any]:
        """파레토 분석 (80-20 법칙) 계산"""
        if not items:
            return {
                "total_items": 0,
                "top_20_percent": [],
                "cumulative_contribution": [],
                "pareto_point": None
            }
        
        # 값 기준으로 내림차순 정렬
        sorted_items = sorted(items, key=lambda x: x[value_key], reverse=True)
        total_value = float(sum(item[value_key] for item in sorted_items))  # numpy 타입 방지
        
        # 누적 기여도 계산
        cumulative_contribution = []
        cumulative_value = 0.0
        
        for i, item in enumerate(sorted_items):
            cumulative_value += float(item[value_key])  # numpy 타입 방지
            contribution_percent = (cumulative_value / total_value) * 100
            cumulative_contribution.append({
                "rank": int(i + 1),  # numpy 타입 방지
                "item": item,
                "cumulative_percent": float(round(contribution_percent, 2))  # numpy 타입 방지
            })
        
        # 80% 지점 찾기
        pareto_point = None
        for contrib in cumulative_contribution:
            if float(contrib["cumulative_percent"]) >= 80:  # numpy boolean 방지
                pareto_point = int(contrib["rank"])  # numpy 타입 방지
                break
        
        # 상위 20% 항목
        top_20_count = max(1, int(len(sorted_items) * 0.2))
        top_20_percent = sorted_items[:top_20_count]
        
        return {
            "total_items": int(len(sorted_items)),  # numpy 타입 방지
            "top_20_percent": top_20_percent,
            "cumulative_contribution": cumulative_contribution,
            "pareto_point": pareto_point,  # 이미 int로 변환됨
            "pareto_efficiency": f"상위 {pareto_point}개 항목이 전체의 80% 차지" if pareto_point else "파레토 지점 없음"
        }
    
    @staticmethod
    def calculate_correlation_analysis(x_values: List[float], y_values: List[float]) -> Dict[str, Any]:
        """상관관계 분석 계산"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return {
                "correlation": 0,
                "strength": "계산 불가",
                "relationship": "데이터 부족"
            }
        
        # 피어슨 상관계수 계산
        correlation_matrix = np.corrcoef(x_values, y_values)
        correlation = float(correlation_matrix[0, 1])  # numpy scalar → float 변환
        
        # 상관관계 강도 분류
        abs_corr = float(abs(correlation))  # numpy 타입 방지
        if abs_corr >= 0.8:
            strength = "매우 강함"
        elif abs_corr >= 0.6:
            strength = "강함"
        elif abs_corr >= 0.4:
            strength = "보통"
        elif abs_corr >= 0.2:
            strength = "약함"
        else:
            strength = "매우 약함"
        
        # 관계 방향 (float 값으로 비교)
        if correlation > 0:
            relationship = "양의 상관관계"
        elif correlation < 0:
            relationship = "음의 상관관계"
        else:
            relationship = "상관관계 없음"
        
        return {
            "correlation": round(correlation, 3),
            "strength": strength,
            "relationship": relationship
        }
    
    @staticmethod
    def calculate_benchmark_comparison(current_performance: float, benchmarks: Dict[str, float]) -> Dict[str, Any]:
        """벤치마크 비교 분석"""
        if not benchmarks:
            return {
                "performance_level": "벤치마크 없음",
                "comparisons": {},
                "ranking": None
            }
        
        comparisons = {}
        for benchmark_name, benchmark_value in benchmarks.items():
            benchmark_val = float(benchmark_value)  # numpy 타입 방지
            if benchmark_val > 0:  # Python float 비교
                ratio = float(current_performance / benchmark_val)  # numpy 타입 방지
                percentage = float((ratio - 1) * 100)
                
                # Python float 비교
                if ratio >= 1.2:
                    level = "우수"
                elif ratio >= 1.0:
                    level = "양호"
                elif ratio >= 0.8:
                    level = "보통"
                else:
                    level = "미흡"
                
                comparisons[benchmark_name] = {
                    "benchmark_value": benchmark_val,  # Python float
                    "ratio": float(round(ratio, 3)),  # numpy 타입 방지
                    "percentage_diff": float(round(percentage, 2)),
                    "level": level
                }
        
        # 전체 성과 수준 결정
        if comparisons:
            avg_ratio = float(np.mean([comp["ratio"] for comp in comparisons.values()]))  # numpy 타입 방지
            # Python float 비교
            if avg_ratio >= 1.2:
                performance_level = "업계 상위"
            elif avg_ratio >= 1.0:
                performance_level = "업계 평균 이상"
            elif avg_ratio >= 0.8:
                performance_level = "업계 평균"
            else:
                performance_level = "업계 평균 이하"
        else:
            performance_level = "비교 불가"
        
        return {
            "performance_level": performance_level,
            "comparisons": comparisons,
            "current_performance": float(current_performance)  # numpy 타입 방지
        }
    
    @staticmethod
    def calculate_forecast(historical_data: List[float], periods: int = 3) -> Dict[str, Any]:
        """단순 예측 계산 (이동평균, 선형회귀)"""
        if len(historical_data) < 3:
            return {
                "method": "데이터 부족",
                "forecast": [],
                "confidence": "낮음"
            }
        
        # 이동평균 예측
        window = min(3, len(historical_data))
        moving_avg = float(np.mean(historical_data[-window:]))  # numpy 타입 방지
        
        # 선형회귀 예측
        x = np.arange(len(historical_data))
        y = np.array(historical_data)
        
        # 최소자승법 (numpy scalar을 Python 기본 타입으로 변환)
        n = len(historical_data)
        sum_x = float(np.sum(x))  # numpy 타입 방지
        sum_y = float(np.sum(y))
        sum_xy = float(np.sum(x * y))
        sum_x2 = float(np.sum(x * x))
        
        slope = float((n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x))  # numpy 타입 방지
        intercept = float((sum_y - slope * sum_x) / n)
        
        # 예측값 생성
        forecast = []
        for i in range(periods):
            future_x = len(historical_data) + i
            linear_pred = slope * future_x + intercept
            
            # 이동평균과 선형회귀의 가중 평균 (Python float 비교)
            weight_linear = 0.7 if float(slope) > 0 else 0.3  # numpy boolean 방지
            weight_moving = 1 - weight_linear
            
            combined_pred = weight_linear * linear_pred + weight_moving * moving_avg
            forecast.append(float(max(0, round(combined_pred, 2))))  # numpy 타입 방지
        
        # 신뢰도 계산 (데이터 수와 트렌드 일관성 기반)
        data_confidence = float(min(1.0, len(historical_data) / 12))  # numpy 타입 방지
        
        # 트렌드 일관성 확인
        recent_changes = []
        for i in range(1, min(6, len(historical_data))):
            prev_val = float(historical_data[-i-1])  # numpy 타입 방지
            if prev_val != 0:  # Python float 비교
                change = float((historical_data[-i] - prev_val) / prev_val)  # numpy 타입 방지
                recent_changes.append(change)
        
        trend_consistency = float(1 - (np.std(recent_changes) if recent_changes else 0))  # numpy 타입 방지
        trend_consistency = float(max(0, min(1, trend_consistency)))
        
        overall_confidence = float((data_confidence + trend_consistency) / 2)  # numpy 타입 방지
        
        # Python float 비교
        if overall_confidence > 0.7:
            confidence = "높음"
        elif overall_confidence > 0.4:
            confidence = "보통"
        else:
            confidence = "낮음"
        
        return {
            "method": "가중 평균 (선형회귀 + 이동평균)",
            "forecast": forecast,  # 이미 Python float 리스트
            "confidence": confidence,
            "confidence_score": float(round(overall_confidence, 3))  # numpy 타입 방지
        } 
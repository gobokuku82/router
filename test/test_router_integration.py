"""
라우터 통합 테스트
1. 각 에이전트로 분류가 잘 되는지 검증
2. docs_agent가 잘 작동하는지 검증
"""
import sys
from pathlib import Path
import asyncio
import json
from typing import Dict, Any

# 경로 설정
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
app_path = backend_path / "app"

# sys.path에 추가
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(app_path))

# 필요한 모듈 임포트
from app.services.router_agent import RouterAgent, AgentClassifier
from app.services.docs_agent.create_document_agent import CreateDocumentAgent
from app.services.employee_agent.employee_agent import EnhancedEmployeeAgent


class TestColors:
    """테스트 출력용 색상"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(test_name: str):
    """테스트 헤더 출력"""
    print(f"\n{TestColors.BOLD}{TestColors.BLUE}{'='*60}")
    print(f"테스트: {test_name}")
    print(f"{'='*60}{TestColors.RESET}")


def print_result(success: bool, message: str):
    """테스트 결과 출력"""
    if success:
        print(f"{TestColors.GREEN}[PASS] {message}{TestColors.RESET}")
    else:
        print(f"{TestColors.RED}[FAIL] {message}{TestColors.RESET}")


def test_agent_classifier():
    """에이전트 분류기 테스트"""
    print_test_header("에이전트 분류기 테스트")
    
    classifier = AgentClassifier()
    
    # 테스트 케이스
    test_cases = [
        # docs_agent 케이스
        {
            "query": "영업방문 결과보고서 작성해줘",
            "expected": "docs_agent",
            "description": "영업방문 보고서"
        },
        {
            "query": "제품설명회 시행 신청서를 만들어주세요",
            "expected": "docs_agent",
            "description": "제품설명회 신청서"
        },
        {
            "query": "제품설명회 결과보고서 준비해줘",
            "expected": "docs_agent",
            "description": "제품설명회 결과보고서"
        },
        {
            "query": "문서 작성이 필요해",
            "expected": "docs_agent",
            "description": "일반 문서 작성"
        },
        
        # employee_agent 케이스
        {
            "query": "김도윤 직원의 실적을 분석해줘",
            "expected": "employee_agent",
            "description": "직원 실적 분석"
        },
        {
            "query": "최수아의 2024년 1분기 영업 성과를 보여줘",
            "expected": "employee_agent",
            "description": "기간별 성과 조회"
        },
        {
            "query": "직원들의 목표 달성률이 어떻게 되나요?",
            "expected": "employee_agent",
            "description": "목표 달성률 조회"
        },
        {
            "query": "이번 달 매출 트렌드 분석해줘",
            "expected": "employee_agent",
            "description": "매출 트렌드 분석"
        }
    ]
    
    # 테스트 실행
    success_count = 0
    total_count = len(test_cases)
    
    for test_case in test_cases:
        query = test_case["query"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        print(f"\n{TestColors.YELLOW}[테스트] {description}{TestColors.RESET}")
        print(f"질문: {query}")
        
        # 분류 실행
        agent, confidence, analysis = classifier.classify(query)
        
        # 결과 확인
        is_correct = agent == expected
        success_count += 1 if is_correct else 0
        
        print_result(is_correct, f"예상: {expected}, 결과: {agent} (신뢰도: {confidence:.2f})")
        
        # 상세 분석 정보
        if not is_correct:
            print(f"  키워드 분석: {analysis.get('keyword_analysis', {}).get('matched_keywords', [])}")
            print(f"  LLM 분석: {analysis.get('llm_analysis', {}).get('reasoning', 'N/A')}")
    
    # 최종 결과
    print(f"\n{TestColors.BOLD}분류 테스트 결과: {success_count}/{total_count} 성공{TestColors.RESET}")
    return success_count == total_count


def test_router_agent():
    """라우터 에이전트 통합 테스트"""
    print_test_header("라우터 에이전트 통합 테스트")
    
    router = RouterAgent()
    
    # 테스트 케이스
    test_queries = [
        "영업방문 결과보고서 작성해줘 방문일은 2025년 1월 15일이야",
        "김도윤 직원의 이번 분기 실적을 분석해줘"
    ]
    
    for query in test_queries:
        print(f"\n{TestColors.YELLOW}[통합 테스트] {query[:30]}...{TestColors.RESET}")
        
        try:
            # 라우터 실행
            result = router.run(query)
            
            print(f"세션 ID: {result.get('session_id')}")
            print(f"대상 에이전트: {result.get('target_agent')}")
            print(f"분류 신뢰도: {result.get('classification_confidence', 0):.2f}")
            print(f"성공 여부: {result.get('success')}")
            
            if result.get('requires_interrupt'):
                print(f"{TestColors.YELLOW}인터럽트 발생 - 사용자 입력 필요{TestColors.RESET}")
            
            if result.get('error'):
                print(f"{TestColors.RED}오류: {result.get('error')}{TestColors.RESET}")
            
        except Exception as e:
            print(f"{TestColors.RED}테스트 실행 중 오류: {str(e)}{TestColors.RESET}")
            import traceback
            traceback.print_exc()


def test_docs_agent_direct():
    """docs_agent 직접 테스트"""
    print_test_header("docs_agent 직접 테스트")
    
    try:
        agent = CreateDocumentAgent()
        
        # 테스트 쿼리
        test_query = """
        영업방문 결과보고서 작성해줘.
        방문 제목은 ABC병원 신약 소개,
        방문일은 2025년 1월 15일,
        client는 ABC병원,
        방문site는 서울시 강남구,
        담당자는 김철수 과장이야.
        """
        
        print(f"테스트 쿼리: {test_query[:50]}...")
        
        # 에이전트 실행
        result = agent.run(user_input=test_query)
        
        if result.get("success"):
            print_result(True, "문서 생성 성공")
            print(f"생성된 문서: {result.get('result', {}).get('final_doc', 'N/A')}")
        elif result.get("thread_id"):
            print(f"{TestColors.YELLOW}인터럽트 발생{TestColors.RESET}")
            print(f"스레드 ID: {result.get('thread_id')}")
            print("사용자 입력이 필요합니다.")
            
            # 인터럽트 시뮬레이션
            print("\n인터럽트 처리 시뮬레이션...")
            
            # 1. 분류 확인에 "네" 응답
            resume_result = agent.resume(
                thread_id=result["thread_id"],
                user_reply="네",
                input_type="verification_reply"
            )
            
            if resume_result.get("success"):
                print_result(True, "인터럽트 처리 완료")
            else:
                print_result(False, "인터럽트 처리 실패")
                
        else:
            print_result(False, f"실행 실패: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print_result(False, f"예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()


def test_path_issues():
    """경로 및 임포트 문제 확인"""
    print_test_header("경로 및 임포트 검증")
    
    # 1. 경로 확인
    print("\n1. 경로 확인:")
    print(f"프로젝트 루트: {project_root}")
    print(f"백엔드 경로: {backend_path}")
    print(f"앱 경로: {app_path}")
    
    # 2. 중요 파일 존재 확인
    print("\n2. 중요 파일 존재 확인:")
    important_files = [
        app_path / "services" / "router_agent" / "router.py",
        app_path / "services" / "router_agent" / "classifier.py",
        app_path / "services" / "docs_agent" / "create_document_agent.py",
        app_path / "services" / "employee_agent" / "employee_agent.py",
        app_path / "services" / "common" / "state.py",
        app_path / "services" / "tools" / "common_tools.py",
        app_path / "api" / "router_api.py"
    ]
    
    for file_path in important_files:
        exists = file_path.exists()
        print_result(exists, f"{file_path.relative_to(project_root)}")
    
    # 3. 임포트 테스트
    print("\n3. 임포트 테스트:")
    imports_to_test = [
        ("common.state", "from app.services.common.state import BaseState"),
        ("router_agent", "from app.services.router_agent import RouterAgent"),
        ("classifier", "from app.services.router_agent.classifier import AgentClassifier"),
        ("docs_agent", "from app.services.docs_agent.create_document_agent import CreateDocumentAgent"),
        ("employee_agent", "from app.services.employee_agent.employee_agent import EnhancedEmployeeAgent")
    ]
    
    for name, import_stmt in imports_to_test:
        try:
            exec(import_stmt)
            print_result(True, f"{name} 임포트 성공")
        except Exception as e:
            print_result(False, f"{name} 임포트 실패: {str(e)}")


def main():
    """메인 테스트 실행"""
    print(f"{TestColors.BOLD}{TestColors.BLUE}")
    print("="*60)
    print("라우터 시스템 통합 테스트")
    print("="*60)
    print(TestColors.RESET)
    
    # 경로 검증
    test_path_issues()
    
    # 분류기 테스트
    classifier_success = test_agent_classifier()
    
    # 라우터 통합 테스트
    test_router_agent()
    
    # docs_agent 직접 테스트
    test_docs_agent_direct()
    
    print(f"\n{TestColors.BOLD}테스트 완료!{TestColors.RESET}")


if __name__ == "__main__":
    main()
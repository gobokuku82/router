"""
규정 위반 감지 개선 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트용 위반 문구들
VIOLATION_KEYWORDS = [
    "자사 판촉물",
    "로얄티",
    "메리트",
    "인센티브",
    "리베이트",
    "경품",
    "선물",
    "접대",
    "유흥",
    "골프"
]

def enhanced_violation_check(content: str) -> str:
    """향상된 규정 위반 검사"""
    violations = []
    
    # 키워드 기반 검사
    for keyword in VIOLATION_KEYWORDS:
        if keyword in content:
            violations.append(f"'{keyword}' 관련 내용이 포함되어 있습니다")
    
    # 금액 관련 검사
    import re
    amounts = re.findall(r'(\d+만\s*원|\d+원)', content)
    for amount in amounts:
        # 금액 추출
        num = int(re.search(r'\d+', amount).group())
        if '만' in amount:
            num *= 10000
        
        if num >= 50000:  # 5만원 이상
            violations.append(f"고액({amount})의 지출이 포함되어 있습니다")
    
    # 주류 관련 검사
    alcohol_keywords = ["술", "주류", "소주", "맥주", "와인", "위스키"]
    for keyword in alcohol_keywords:
        if keyword in content:
            violations.append(f"주류({keyword}) 관련 내용이 포함되어 있습니다")
    
    if violations:
        return "다음 규정 위반 사항이 발견되었습니다:\n" + "\n".join(f"- {v}" for v in violations)
    else:
        return "OK"

def test_enhanced_check():
    """테스트 실행"""
    test_content = """영업방문결과서 작성해줘. 내용은 방문 제목은 유미가정의학과 신약 홍보이고 
    방문일은 250725이고 client는 유미가정의학과 방문사이트는 www.yumibanplz.com 
    담담자는 손현성이고 소속은 영업팀 연락처는 010-1234-5678이야 
    영업제공자는 김도윤이고 연락처는 010-8765-4321이야 
    방문자는 허한결이고 소속은 영업팀이야 
    고객사 개요는 이번에 새로 오픈한 가정의학과로 사용 약품에 대해 많은 논의가 필요해보이는 잠재력이 있는 고객이야 
    프로젝트 개요는 신규고객 유치로 자사 약품홍보 후 로얄티 및 메리트 소개를 할거야 
    방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음 
    향후계획및일정은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야 
    협조사항으로 자사 판촉물 1개 지급 요망"""
    
    print("=== 향상된 규정 위반 검사 테스트 ===\n")
    print("테스트 내용:")
    print(test_content[:100] + "...\n")
    
    result = enhanced_violation_check(test_content)
    print("검사 결과:")
    print(result)
    
    if result != "OK":
        print("\n[성공] 규정 위반이 정상적으로 감지되었습니다!")
    else:
        print("\n[실패] 규정 위반을 감지하지 못했습니다.")

if __name__ == "__main__":
    test_enhanced_check()
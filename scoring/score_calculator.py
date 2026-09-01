# =========================
# 점수 평가 시스템 모듈
# =========================

from typing import Dict, List, Tuple, Any, Optional
import json


class ScoreCalculator:
    """
    보안 점검 결과를 기반으로 점수를 계산하는 클래스
    """

    def __init__(self):
        """점수 계산기 초기화"""
        self.check_weights = {
            # 보안 프로그램 관련 (높은 가중치)
            "CrowdStrike Falcon 설치 여부": 4,
            "CrowdStrike Falcon 프로세스 실행 여부": 4,
            "Privacy-I 설치 여부": 4,
            "Privacy-I 프로세스 실행 여부": 4,
            "Genian NAC 설치 여부": 4,
            "Genian NAC 프로세스 실행 여부": 4,
            
            # 시스템 보안 설정 (중간 가중치)
            "macOS 소프트웨어 업데이트 최신 여부": 4,
            "사용자 암호 설정 여부": 4,
            "사용자 암호 변경 정책 및 남은 기간": 4,
            "화면 보호기 설정 여부": 4,
            "방화벽 활성 여부": 4,
            
            # 계정 보안 (중간 가중치)
            "사용자 자동 로그인 기능 설정 여부": 4,
            "현재 사용자 계정 권한": 4,
            "Root 계정 활성 여부": 4,
            "다중 사용자 계정 여부": 4,
            "게스트 계정 활성 여부": 4,
            
            # 네트워크 보안 (중간 가중치)
            "FTP 서비스(포트) 활성 여부": 4,
            "HTTP 서버 활성 여부": 4,
            "SSH 원격 로그인 활성 여부": 4,
            "macOS 원격 관리 활성 여부": 4,
            
            # 공유 설정 (낮은 가중치)
            "파일 공유 활성 여부": 4,
            "화면 공유 활성 여부": 4,
            "블루투스 공유 활성 여부": 4,
            "인터넷 공유 활성 여부": 4,
            
            # 앱 보안 (낮은 가중치)
            "비인가 메신저 앱 설치 여부": 4
        }
        self.total_weight = sum(self.check_weights.values())

    @staticmethod
    def get_status_text(status: Optional[bool]) -> str:
        """상태 값을 텍스트로 변환하는 공통 함수"""
        if status is True:
            return "안전"
        elif status is False:
            return "취약"
        else:
            return "점검 불가"

    @staticmethod
    def get_inverse_status_text(status: Optional[bool]) -> str:
        """
        역상태 값을 텍스트로 변환하는 함수
        False일 때 안전, True일 때 취약인 항목용
        """
        if status is True:
            return "취약"
        elif status is False:
            return "안전"
        else:
            return "점검 불가"

    def evaluate_check_result(self, check_name: str, result: Tuple[Optional[bool], str]) -> Tuple[str, str]:
        """
        개별 점검 결과를 평가하는 함수 (점수는 가중치에서 PASS면 0, WARN/Error면 full 감점 처리)
        """
        status, message = result

        if status is None:
            return "ERROR", self.get_status_text(status)

        # 비인가 메신저 앱 체크
        if "비인가 메신저 앱" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "설치 여부" in check_name or "프로세스 실행 여부" in check_name:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)
        elif "소프트웨어 업데이트" in check_name:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)
        elif "암호 설정" in check_name:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)
        elif "암호 변경 정책" in check_name:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)
        elif "화면 보호기" in check_name:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)
        elif "자동 로그인" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "계정 권한" in check_name:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)
        elif "Root 계정" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "다중 사용자" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "게스트 계정" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "FTP 서비스" in check_name or "HTTP 서버" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "파일 공유" in check_name or "화면 공유" in check_name or "블루투스 공유" in check_name or "인터넷 공유" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "SSH 원격 로그인" in check_name or "원격 관리" in check_name:
            if status is False:
                return "PASS", self.get_inverse_status_text(status)
            else:
                return "WARN", self.get_inverse_status_text(status)
        elif "방화벽" in check_name:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)
        else:
            if status is True:
                return "PASS", self.get_status_text(status)
            else:
                return "WARN", self.get_status_text(status)

    def calculate_security_score(self, check_results: Dict[str, Tuple[Any, str]]) -> Dict[str, Any]:
        """
        보안 점수를 계산하는 함수 (가중치 기반)
        """
        total_available_score = 0
        total_score = 0  # 실점
        warning_count = 0
        error_count = 0
        pass_count = 0
        evaluation_details = []

        # 전체 가중치 구하기 및 실제 가중치 합 (측정 못하면 그 부분 반영해서)
        total_weight = 0
        for check_name in check_results:
            total_weight += self.check_weights.get(check_name, 4)

        for check_name, result in check_results.items():
            evaluation, status_text = self.evaluate_check_result(check_name, result)
            weight = self.check_weights.get(check_name, 4)
            total_available_score += weight
            if evaluation == "PASS":
                score = weight
                total_score += score
                pass_count += 1
            elif evaluation == "WARN":
                # 감점: 가중치만큼 감점(즉, 0점)
                score = 0
                warning_count += 1
            elif evaluation == "ERROR":
                score = 0
                error_count += 1

            evaluation_details.append({
                "name": check_name,
                "status": result[0],
                "evaluation": evaluation,
                "status_text": status_text,
                "weight": weight,
                "score": score if evaluation == "PASS" else 0,
            })

        # 점수 백분율 환산 (100점 만점으로 변환)
        final_score = 0.0
        if total_available_score > 0:
            final_score = (total_score / total_available_score) * 100
        final_score = round(final_score, 1)

        # 점수 등급 결정
        if final_score >= 90:
            grade = "우수"
        elif final_score >= 80:
            grade = "양호"
        elif final_score >= 70:
            grade = "보통"
        elif final_score >= 60:
            grade = "미흡"
        else:
            grade = "위험"

        penalty = round(total_available_score - total_score, 1)

        return {
            "final_score": final_score,
            "max_score": 100,
            "penalty": penalty,
            "pass_count": pass_count,
            "warning_count": warning_count,
            "error_count": error_count,
            "total_checks": len(check_results),
            "grade": grade
        }

    def generate_score_report(self, score_data: Dict[str, Any]) -> str:
        """
        점수 보고서를 생성하는 함수
        """
        report = f"""
=== 보안 점검 점수 보고서 ===

최종 점수: {score_data['final_score']:.1f}/{score_data['max_score']} 점
등급: {score_data['grade']}
감점: {score_data['penalty']:.1f} 점

점검 결과 요약:
- 통과: {score_data['pass_count']}개
- 경고: {score_data['warning_count']}개
- 오류: {score_data['error_count']}개
- 전체: {score_data['total_checks']}개
"""
        return report

    def save_score_to_json(self, score_data: Dict[str, Any], file_path: str) -> bool:
        """
        점수 데이터를 JSON 파일로 저장하는 함수
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(score_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False


# 테스트 함수
def test_score_calculator():
    """
    점수 계산기 테스트 함수
    """
    calculator = ScoreCalculator()

    # 테스트용 점검 결과 생성
    test_results = {
        "CrowdStrike Falcon 설치 여부": (True, "설치됨"),
        "CrowdStrike Falcon 프로세스 실행 여부": (True, "실행 중"),
        "Privacy-I 설치 여부": (False, "미설치"),
        "Privacy-I 프로세스 실행 여부": (False, "실행 안됨"),
        "방화벽 활성 여부": (True, "활성화됨"),
        "게스트 계정 활성 여부": (False, "비활성화됨"),
        "SSH 원격 로그인 활성 여부": (False, "비활성화됨")
    }

    score_data = calculator.calculate_security_score(test_results)
    print(calculator.generate_score_report(score_data))


if __name__ == "__main__":
    test_score_calculator()

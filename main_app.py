# =========================
# 메인 애플리케이션
# =========================

import os
import sys
import datetime
from typing import Dict, Any

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 모듈 임포트
from user_info.user_data_collector import UserDataCollector
from security_checks.security_checker import SecurityChecker
from scoring.score_calculator import ScoreCalculator
from reporting.pdf_report_generator import PDFReportGenerator
from reporting.json_server_uploader import JSONServerUploader
from utils.logger import SecurityLogger
from utils.command_executor import CommandExecutor


class SecurityCheckApp:
    """
    macOS 보안 점검 메인 애플리케이션
    """
    
    def __init__(self):
        """보안 점검 애플리케이션 초기화"""
        self.host_name = os.uname().nodename
        self.current_user = os.getenv('USER')
        self.start_time = datetime.datetime.now()
        
        # 결과 파일 경로 설정
        self.result_dir = "/Users/Shared"
        os.makedirs(self.result_dir, exist_ok=True)
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.pdf_report_path = os.path.join(self.result_dir, f"security_check_report_{self.host_name}_{timestamp}.pdf")
        self.json_backup_path = os.path.join(self.result_dir, f"security_check_data_{self.host_name}_{timestamp}.json")
        
        # 모듈 초기화
        self.logger = SecurityLogger()
        self.user_collector = UserDataCollector()
        self.security_checker = SecurityChecker()
        self.score_calculator = ScoreCalculator()
        self.pdf_generator = PDFReportGenerator()
        self.json_uploader = JSONServerUploader()
        self.command_executor = CommandExecutor()
        
        # 결과 데이터 저장
        self.user_info = {}
        self.check_results = {}
        self.score_data = {}
    
    def run_security_check(self) -> bool:
        """
        전체 보안 점검을 실행하는 함수
        
        Returns:
            bool: 점검 성공 여부
        """
        try:
            self.logger.log_info("=== macOS 보안 점검 시작 ===", "MAIN")
            
            # 1. 사용자 정보 수집
            self.logger.log_info("1단계: 사용자 정보 수집", "MAIN")
            self.user_info = self.user_collector.collect_all_user_info()
            self.logger.log_user_info(self.user_info)
            
            # 2. 보안 점검 실행
            self.logger.log_info("2단계: 보안 점검 실행", "MAIN")
            self.check_results = self.security_checker.run_all_security_checks()
            
            # 보안 점검 결과 로깅
            for check_name, result in self.check_results.items():
                status, message = result
                self.logger.log_security_check(check_name, status, message)
            
            # 3. 점수 계산
            self.logger.log_info("3단계: 점수 계산", "MAIN")
            self.score_data = self.score_calculator.calculate_security_score(self.check_results)
            self.logger.log_score_calculation(self.score_data)
            
            # 사용자 정보에 최종 점수 업데이트
            self.user_info['보안 평가 점수'] = self.score_data['final_score']
            
            # 4. PDF 보고서 생성
            self.logger.log_info("4단계: PDF 보고서 생성", "MAIN")
            pdf_success = self.pdf_generator.generate_pdf_report(
                self.user_info, self.check_results, self.score_data, self.pdf_report_path
            )
            self.logger.log_report_generation("PDF", self.pdf_report_path, pdf_success)
            
            # 5. JSON 로그 저장
            self.logger.log_info("5단계: JSON 로그 저장", "MAIN")
            
            # JSON 로그 저장 (이것이 메인 JSON 파일)
            self.json_backup_path = self.logger.json_log_file
            self.logger.save_json_log()
            
            # 6. 서버 업로드 시도
            self.logger.log_info("6단계: 서버 업로드", "MAIN")
            upload_result = self.json_uploader.upload_with_fallback(
                self.user_info, self.check_results, self.score_data, None  # 별도 백업 파일 생성하지 않음
            )
            self.logger.log_server_upload(upload_result)
            
            # 7. 명령어 로그 파일 종료
            self.command_executor.close_log_file()
            
            # 최종 결과 출력
            self._print_final_results()
            
            self.logger.log_info("=== macOS 보안 점검 완료 ===", "MAIN")
            return True
            
        except Exception as e:
            self.logger.log_error(f"보안 점검 중 오류 발생: {str(e)}", "MAIN")
            return False
    
    def _print_final_results(self) -> None:
        """
        최종 결과를 출력하는 함수
        """
        print("\n" + "="*60)
        print("=== macOS 보안 점검 결과 ===")
        print("="*60)
        
        # 사용자 정보 출력
        print("\n[사용자 정보]")
        for key, value in self.user_info.items():
            print(f"- {key}: {value}")
        
        # 점수 요약 출력
        print(f"\n[점수 요약]")
        print(f"- 최종 점수: {self.score_data['final_score']}/{self.score_data['max_score']}점")
        print(f"- 등급: {self.score_data['grade']}")
        print(f"- 통과: {self.score_data['pass_count']}개")
        print(f"- 경고: {self.score_data['warning_count']}개")
        print(f"- 오류: {self.score_data['error_count']}개")
        
        # 파일 경로 출력
        print(f"\n[생성된 파일]")
        print(f"- PDF 보고서: {self.pdf_report_path}")
        print(f"- JSON 백업: {self.json_backup_path}")
        print(f"- 로그 파일: {self.logger.log_file}")
        print(f"- JSON 로그: {self.logger.json_log_file}")
        print(f"- 명령어 실행 로그: {self.command_executor.get_log_file_path()}")
        
        print("\n" + "="*60)
    
    def run_quick_check(self) -> bool:
        """
        빠른 보안 점검을 실행하는 함수 (주요 항목만)
        
        Returns:
            bool: 점검 성공 여부
        """
        try:
            self.logger.log_info("=== 빠른 보안 점검 시작 ===", "MAIN")
            
            # 주요 보안 항목만 점검
            quick_checks = {
                "CrowdStrike Falcon 설치 여부": self.security_checker.check_crowdstrike_falcon_installation(),
                "CrowdStrike Falcon 프로세스 실행 여부": self.security_checker.check_crowdstrike_falcon_process(),
                "방화벽 활성 여부": self.security_checker.check_firewall_status(),
                "게스트 계정 활성 여부": self.security_checker.check_guest_account_status(),
                "SSH 원격 로그인 활성 여부": self.security_checker.check_ssh_remote_login()
            }
            
            # 결과 로깅
            for check_name, result in quick_checks.items():
                status, message = result
                self.logger.log_security_check(check_name, status, message)
            
            # 간단한 점수 계산
            score_data = self.score_calculator.calculate_security_score(quick_checks)
            self.logger.log_score_calculation(score_data)
            
            # 결과 출력
            print("\n=== 빠른 보안 점검 결과 ===")
            for check_name, result in quick_checks.items():
                status, message = result
                print(f"- {check_name}: {message}")
            
            print(f"\n점수: {score_data['final_score']}/{score_data['max_score']}점")
            print(f"등급: {score_data['grade']}")
            
            self.logger.log_info("=== 빠른 보안 점검 완료 ===", "MAIN")
            return True
            
        except Exception as e:
            self.logger.log_error(f"빠른 보안 점검 중 오류 발생: {str(e)}", "MAIN")
            return False
    
    def test_individual_modules(self) -> None:
        """
        개별 모듈을 테스트하는 함수
        """
        print("=== 개별 모듈 테스트 ===")
        
        # 사용자 정보 수집 테스트
        print("\n1. 사용자 정보 수집 테스트")
        user_info = self.user_collector.collect_all_user_info()
        for key, value in user_info.items():
            print(f"  - {key}: {value}")
        
        # 보안 점검 테스트
        print("\n2. 보안 점검 테스트")
        test_results = {
            "CrowdStrike Falcon 설치 여부": self.security_checker.check_crowdstrike_falcon_installation(),
            "방화벽 활성 여부": self.security_checker.check_firewall_status()
        }
        for check_name, result in test_results.items():
            status, message = result
            print(f"  - {check_name}: {message}")
        
        # 점수 계산 테스트
        print("\n3. 점수 계산 테스트")
        score_data = self.score_calculator.calculate_security_score(test_results)
        print(f"  - 점수: {score_data['final_score']}/{score_data['max_score']}점")
        print(f"  - 등급: {score_data['grade']}")
        
        # 로거 테스트
        print("\n4. 로거 테스트")
        self.logger.log_info("테스트 로그", "TEST")
        log_summary = self.logger.get_log_summary()
        print(f"  - 로그 개수: {log_summary['total_logs']}개")


def main():
    """
    메인 함수
    """
    print("=== macOS 보안 점검 애플리케이션 ===")
    print("버전: 1.0")
    print("개발자: NCSKorea")
    print("="*60)
    
    # 애플리케이션 초기화
    app = SecurityCheckApp()
    
    # 사용자 선택
    print("\n실행할 작업을 선택하세요:")
    print("1. 전체 보안 점검")
    print("2. 빠른 보안 점검")
    print("3. 개별 모듈 테스트")
    print("4. 종료")
    
    try:
        choice = input("\n선택 (1-4): ").strip()
        
        if choice == "1":
            print("\n전체 보안 점검을 시작합니다...")
            success = app.run_security_check()
            if success:
                print("\n보안 점검이 성공적으로 완료되었습니다.")
            else:
                print("\n보안 점검 중 오류가 발생했습니다.")
        
        elif choice == "2":
            print("\n빠른 보안 점검을 시작합니다...")
            success = app.run_quick_check()
            if success:
                print("\n빠른 보안 점검이 성공적으로 완료되었습니다.")
            else:
                print("\n빠른 보안 점검 중 오류가 발생했습니다.")
        
        elif choice == "3":
            print("\n개별 모듈 테스트를 시작합니다...")
            app.test_individual_modules()
        
        elif choice == "4":
            print("\n프로그램을 종료합니다.")
            return
        
        else:
            print("\n잘못된 선택입니다.")
    
    except KeyboardInterrupt:
        print("\n\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
1
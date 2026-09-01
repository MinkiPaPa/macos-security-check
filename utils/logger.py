# =========================
# 로깅 유틸리티 모듈
# =========================

import os
import datetime
import json
from typing import Dict, Any, Optional
from enum import Enum
import re


class LogLevel(Enum):
    """로그 레벨 열거형"""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


class SecurityLogger:
    """보안 점검 로깅을 담당하는 클래스"""
    
    def __init__(self, log_dir: str = "/Users/Shared", log_file_prefix: str = "security_check"):
        """
        보안 로거 초기화
        
        Args:
            log_dir: 로그 디렉토리
            log_file_prefix: 로그 파일 접두사
        """
        self.log_dir = log_dir
        self.log_file_prefix = log_file_prefix
        self.host_name = os.uname().nodename
        self.current_user = os.getenv('USER', 'unknown')
        
        # 로그 디렉토리 생성
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 로그 파일 경로 설정
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"{self.log_file_prefix}_{self.host_name}_{timestamp}.log")
        self.json_log_file = os.path.join(self.log_dir, f"{self.log_file_prefix}_{self.host_name}_{timestamp}.json")
        
        # JSON 로그 데이터 초기화
        self.json_log_data = {
            "metadata": {
                "hostname": self.host_name,
                "username": self.current_user,
                "start_time": datetime.datetime.now().isoformat(),
                "version": "1.0"
            },
            "logs": []
        }

    def _sanitize_upload_message(self, message: str) -> str:
        """
        업로드 실패 메시지에서 curl 명령어 내용을 제거하여 사용자에게 노출하지 않도록 보정
        """
        # curl 또는 subprocess.Command 부분을 감지해서 제거
        # 예시 메시지:
        # 서버 업로드 실패: FTP 업로드 도중 오류: Command '['curl', ...]...' timed out after ... (FTP 업로드 실패)

        # regex for Command '['curl', ...]' or Command "[curl ..." etc.
        pattern = r"(Command\s*\[.*?curl.*?\].*?timed out after [^)]*\))"
        if "curl" in message or "Command '['curl'" in message or "Command [\"curl\"" in message:
            # 앞의 설명부분은 살려두고 Command ... 부분만 깔끔하게 제거(혹은 (FTP 업로드 실패)는 살려둘 수도 있음)
            # 우선 패턴으로 찾아 해당 부분으로 대체
            sanitized = re.sub(pattern, "(FTP 업로드 실패: 시간 초과)", message)
            # 혹시라도 남으면, curl 이하로 잘라내기
            if "curl" in sanitized:
                curl_idx = sanitized.find("curl")
                prev_part = sanitized[:max(0, curl_idx - 20)]  # 근처 앞부분만 살림
                sanitized = prev_part.rstrip() + " (FTP 업로드 실패: 시간 초과)"
            return sanitized
        return message
    
    def log(self, level: LogLevel, message: str, category: str = "GENERAL", 
            details: Optional[Dict[str, Any]] = None) -> None:
        """
        로그를 기록하는 함수
        
        Args:
            level: 로그 레벨
            message: 로그 메시지
            category: 로그 카테고리
            details: 추가 세부 정보
        """
        # 업로드 실패 메시지인 경우 curl 명령어 노출 방지
        if category == "SERVER_UPLOAD" and "서버 업로드 실패" in message and "curl" in message:
            message = self._sanitize_upload_message(message)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 텍스트 로그 형식
        log_entry = f"[{timestamp}][{level.value}][{category}] {message}"
        
        # 텍스트 로그 파일에 기록
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"텍스트 로그 저장 중 오류 발생: {str(e)}")
        
        # JSON 로그 데이터에 추가
        json_entry = {
            "timestamp": timestamp,
            "level": level.value,
            "category": category,
            "message": message,
            "details": details or {}
        }
        self.json_log_data["logs"].append(json_entry)
        
        # 콘솔에 출력 (주석 처리하여 터미널 로그 숨김)
        # print(log_entry)
    
    def log_info(self, message: str, category: str = "GENERAL", details: Optional[Dict[str, Any]] = None) -> None:
        """INFO 레벨 로그 기록"""
        self.log(LogLevel.INFO, message, category, details)
    
    def log_warn(self, message: str, category: str = "GENERAL", details: Optional[Dict[str, Any]] = None) -> None:
        """WARN 레벨 로그 기록"""
        self.log(LogLevel.WARN, message, category, details)
    
    def log_error(self, message: str, category: str = "GENERAL", details: Optional[Dict[str, Any]] = None) -> None:
        """ERROR 레벨 로그 기록"""
        self.log(LogLevel.ERROR, message, category, details)
    
    def log_debug(self, message: str, category: str = "GENERAL", details: Optional[Dict[str, Any]] = None) -> None:
        """DEBUG 레벨 로그 기록"""
        self.log(LogLevel.DEBUG, message, category, details)
    
    def log_security_check(self, check_name: str, status: bool, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        보안 점검 결과를 로깅하는 함수
        
        Args:
            check_name: 점검 항목명
            status: 점검 결과 상태
            message: 점검 메시지
            details: 추가 세부 정보
        """
        # 점검 항목의 의미에 따라 로깅 레벨 결정
        level = self._determine_log_level(check_name, status, message)
        category = "SECURITY_CHECK"
        
        log_message = f"[{check_name}] {message}"
        check_details = {
            "check_name": check_name,
            "status": status,
            "message": message,
            **(details or {})
        }
        
        self.log(level, log_message, category, check_details)
    
    def _determine_log_level(self, check_name: str, status: bool, message: str) -> LogLevel:
        """
        점검 항목의 의미에 따라 로깅 레벨을 결정하는 함수
        
        Args:
            check_name: 점검 항목명
            status: 점검 결과 상태
            message: 점검 메시지
            
        """
        # 일반적인 보안 항목들 (True=안전, False=취약)
        normal_security_items = [
            "설치 여부", "프로세스 실행 여부", "소프트웨어 업데이트", 
            "암호 설정", "암호 변경 정책", "화면 보호기", "계정 권한", "방화벽"
        ]
        
        # 역상태 보안 항목들 (False=안전, True=취약)
        inverse_security_items = [
            "자동 로그인", "Root 계정", "다중 사용자", "게스트 계정",
            "FTP 서비스", "HTTP 서버", "파일 공유", "화면 공유", 
            "블루투스 공유", "인터넷 공유", "SSH 원격 로그인", "원격 관리"
        ]
        
        # 비인가 메신저 앱 (False=안전, True=취약)
        if "비인가 메신저 앱" in check_name:
            return LogLevel.INFO if not status else LogLevel.WARN
        
        # 역상태 항목들 처리
        for item in inverse_security_items:
            if item in check_name:
                return LogLevel.INFO if not status else LogLevel.WARN
        
        # 일반 보안 항목들 처리
        for item in normal_security_items:
            if item in check_name:
                return LogLevel.INFO if status else LogLevel.WARN
        
        # 기본값: status가 True면 INFO, False면 WARN
        return LogLevel.INFO if status else LogLevel.WARN
    
    def log_user_info(self, user_info: Dict[str, Any]) -> None:
        """
        사용자 정보를 로깅하는 함수
        
        Args:
            user_info: 사용자 정보
        """
        self.log_info("사용자 정보 수집 완료", "USER_INFO", user_info)
    
    def log_score_calculation(self, score_data: Dict[str, Any]) -> None:
        """
        점수 계산 결과를 로깅하는 함수
        
        Args:
            score_data: 점수 데이터
        """
        self.log_info(f"보안 점수 계산 완료: {score_data.get('final_score', 0)}점", 
                     "SCORE_CALCULATION", score_data)
    
    def log_report_generation(self, report_type: str, file_path: str, success: bool) -> None:
        """
        보고서 생성 결과를 로깅하는 함수
        
        Args:
            report_type: 보고서 유형
            file_path: 파일 경로
            success: 생성 성공 여부
        """
        if success:
            self.log_info(f"{report_type} 보고서 생성 완료: {file_path}", 
                         "REPORT_GENERATION", {"type": report_type, "path": file_path})
        else:
            self.log_error(f"{report_type} 보고서 생성 실패: {file_path}", 
                         "REPORT_GENERATION", {"type": report_type, "path": file_path})
    
    def log_server_upload(self, upload_result: Dict[str, Any]) -> None:
        """
        서버 업로드 결과를 로깅하는 함수
        
        Args:
            upload_result: 업로드 결과
        """
        # 메시지에서 curl 명령어 노출 방지
        msg = upload_result.get('message', '')
        if upload_result.get("success", False):
            self.log_info(f"서버 업로드 성공: {msg}", 
                         "SERVER_UPLOAD", upload_result)
        else:
            # 실패 메시지에서 curl 명령 제거
            safe_message = self._sanitize_upload_message(f"서버 업로드 실패: {msg}")
            self.log_error(safe_message, 
                         "SERVER_UPLOAD", upload_result)
    
    
    def save_json_log(self) -> bool:
        """
        JSON 로그 데이터를 파일로 저장하는 함수
        USER_INFO 카테고리의 로그만 저장 (사용자 정보만 포함)
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 종료 시간 추가
            self.json_log_data["metadata"]["end_time"] = datetime.datetime.now().isoformat()
            
            # === 기존 코드 (모든 로그 저장) - 주석 처리 ===
            # with open(self.json_log_file, 'w', encoding='utf-8') as f:
            #     json.dump(self.json_log_data, f, ensure_ascii=False, indent=2)
            
            # === 새로운 코드 (USER_INFO 카테고리만 저장) ===
            # USER_INFO 카테고리의 로그만 필터링
            user_info_logs = [
                log for log in self.json_log_data["logs"] 
                if log.get("category") == "USER_INFO"
            ]
            
            # 저장할 데이터 구성 (metadata + USER_INFO 로그만)
            filtered_data = {
                "metadata": self.json_log_data["metadata"],
                "logs": user_info_logs
            }
            
            # 필터링된 데이터를 JSON 파일로 저장
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"JSON 로그 저장 중 오류 발생: {str(e)}")
            return False
    
    def get_log_summary(self) -> Dict[str, Any]:
        """
        로그 요약 정보를 반환하는 함수
        
        Returns:
            Dict[str, Any]: 로그 요약
        """
        total_logs = len(self.json_log_data["logs"])
        info_count = sum(1 for log in self.json_log_data["logs"] if log["level"] == "INFO")
        warn_count = sum(1 for log in self.json_log_data["logs"] if log["level"] == "WARN")
        error_count = sum(1 for log in self.json_log_data["logs"] if log["level"] == "ERROR")
        debug_count = sum(1 for log in self.json_log_data["logs"] if log["level"] == "DEBUG")
        
        return {
            "total_logs": total_logs,
            "info_count": info_count,
            "warn_count": warn_count,
            "error_count": error_count,
            "debug_count": debug_count,
            "log_file": self.log_file,
            "json_log_file": self.json_log_file
        }


# 테스트 함수
def test_security_logger():
    """보안 로거 테스트 함수"""
    logger = SecurityLogger()
    
    print("=== 보안 로거 테스트 ===")
    
    # 다양한 레벨의 로그 테스트
    logger.log_info("정보 로그 테스트", "TEST")
    logger.log_warn("경고 로그 테스트", "TEST")
    logger.log_error("오류 로그 테스트", "TEST")
    logger.log_debug("디버그 로그 테스트", "TEST")
    
    # 보안 점검 로그 테스트
    logger.log_security_check("방화벽 점검", True, "방화벽이 활성화되어 있습니다.")
    logger.log_security_check("게스트 계정 점검", False, "게스트 계정이 활성화되어 있습니다.")
    
    # 사용자 정보 로그 테스트
    user_info = {"username": "testuser", "ip": "192.168.1.100"}
    logger.log_user_info(user_info)
    
    # 점수 계산 로그 테스트
    score_data = {"final_score": 85, "grade": "양호"}
    logger.log_score_calculation(score_data)
    
    # curl 타임아웃 실패 메시지 재현 예시
    fake_fail_result = {
        "success": False,
        "message": "FTP 업로드 도중 오류: Command '['curl', '-u', '***:***', '-T', '/tmp/security_check_backup.json', 'ftp://***', '-k', '-v', '--connect-timeout', '10']' timed out after 10 seconds (FTP 업로드 실패)"
    }
    logger.log_server_upload(fake_fail_result)
    
    # JSON 로그 저장
    success = logger.save_json_log()
    print(f"JSON 로그 저장 결과: {success}")
    
    # 로그 요약 출력
    summary = logger.get_log_summary()
    print(f"\n로그 요약: {summary}")


if __name__ == "__main__":
    test_security_logger()

# =========================
# JSON 서버 업로드 모듈 (FTP + curl로 변환)
# =========================

import json
import datetime
import os
import sys
import subprocess
import re
from typing import Dict, Any, Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scoring.score_calculator import ScoreCalculator

# GitHub 공개를 위해 실제 서버 주소/계정/비밀번호는 마스킹함
# Server address, account, and password are masked for public GitHub upload
FTP_SERVER = "***"
FTP_USER = "***"
FTP_PASSWORD = "***"
FTP_URL = f"ftp://{FTP_SERVER}/***/"
CURL_CMD_TEMPLATE = [
    "curl",
    "-u", f"{FTP_USER}:{FTP_PASSWORD}",
    "-T", "{file_path}",
    FTP_URL,
    "-k",
    "-v"
]

class JSONServerUploader:
    """
    JSON 데이터를 FTP 서버에 curl로 업로드하는 클래스
    """

    def __init__(self, ftp_server: str = FTP_SERVER, ftp_user: str = FTP_USER,
                 ftp_password: str = FTP_PASSWORD, timeout: int = 10):
        self.ftp_server = ftp_server
        self.ftp_user = ftp_user
        self.ftp_password = ftp_password
        self.timeout = timeout
    
    def _sanitize_error_message(self, error_message: str) -> str:
        """
        에러 메시지에서 curl 명령어와 민감한 정보(사용자명/비밀번호)를 제거
        """
        # subprocess.TimeoutExpired나 CalledProcessError 에러에서 Command [...] 부분 제거
        # 예: "Command '['curl', '-u', 'user:pass', ...]' timed out after 10 seconds"
        # -> "연결 시간 초과 (10초)"
        
        if "timed out after" in error_message:
            # 타임아웃 시간 추출
            timeout_match = re.search(r'timed out after (\d+)', error_message)
            if timeout_match:
                timeout_sec = timeout_match.group(1)
                return f"연결 시간 초과 ({timeout_sec}초)"
            return "연결 시간 초과"
        
        # Command [...] 패턴 제거
        if "Command" in error_message and ("[" in error_message or "'" in error_message):
            # Command 부분만 제거하고 나머지 메시지는 유지
            sanitized = re.sub(r"Command\s+['\"\[].*?['\"\]]\s*", "", error_message)
            # curl이나 민감한 정보가 남아있다면 추가 제거
            if "curl" in sanitized or self.ftp_user in sanitized or self.ftp_password in sanitized:
                return "FTP 업로드 실패"
            return sanitized.strip()
        
        # 사용자명이나 비밀번호가 직접 포함된 경우 제거
        if self.ftp_user in error_message or self.ftp_password in error_message:
            error_message = error_message.replace(self.ftp_user, "***")
            error_message = error_message.replace(self.ftp_password, "***")
        
        return error_message

    def prepare_upload_data(self, 
                           user_info: Dict[str, Any], 
                           check_results: Dict[str, Any], 
                           score_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        업로드할 데이터를 준비하는 함수
        로컬 JSON 파일과 동일한 형식으로 구성 (metadata + USER_INFO 로그만)
        """
        # === 기존 코드 (user_info, score_summary 형식) - 주석 처리 ===
        # upload_data = {
        #     "metadata": {
        #         "timestamp": datetime.datetime.now().isoformat(),
        #         "version": "1.0",
        #         "source": "macOS Security Check Tool"
        #     },
        #     "user_info": user_info,
        #     "score_summary": score_data
        # }
        
        # === 새로운 코드 (metadata + logs 형식, USER_INFO만) ===
        # 현재 시간
        current_time = datetime.datetime.now()
        
        # metadata 구성
        metadata = {
            "hostname": user_info.get("Hostname", os.uname().nodename),
            "username": user_info.get("사용자 이름", "unknown"),
            "start_time": current_time.isoformat(),
            "version": "1.0",
            "end_time": current_time.isoformat()
        }
        
        # USER_INFO 로그 구성
        user_info_log = {
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "category": "USER_INFO",
            "message": "사용자 정보 수집 완료",
            "details": user_info
        }
        
        # 최종 업로드 데이터 (metadata + USER_INFO 로그만)
        upload_data = {
            "metadata": metadata,
            "logs": [user_info_log]
        }
        
        return upload_data

    def save_to_local_file(self, data: Dict[str, Any], file_path: str) -> bool:
        """
        데이터를 로컬 파일로 저장하는 함수
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            # print(f"로컬 파일 저장 중 오류 발생: {str(e)}")
            return False

    def test_server_connection(self) -> Dict[str, Any]:
        """
        FTP 서버 연결을 테스트하는 함수 (curl을 이용)
        """
        try:
            # curl로 FTP 서버에 단순 접속을 시도한다.
            test_cmd = [
                "curl",
                "-u", f"{self.ftp_user}:{self.ftp_password}",
                f"ftp://{self.ftp_server}",
                "-k",
                "-v",
                "--connect-timeout", str(self.timeout),
                "--ftp-method", "nocwd"
            ]
            completed = subprocess.run(
                test_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout
            )
            stderr = completed.stderr.decode("utf-8", errors="replace")
            if completed.returncode == 0:
                return {
                    "success": True,
                    "message": "FTP 서버 연결 성공",
                    "status_code": 200
                }
            else:
                return {
                    "success": False,
                    "message": f"FTP 서버 연결 실패:\n{stderr}",
                    "status_code": None
                }
        except Exception as e:
            # 에러 메시지에서 민감한 정보 제거
            safe_message = self._sanitize_error_message(str(e))
            return {
                "success": False,
                "message": f"FTP 서버 연결 에러: {safe_message}",
                "status_code": None
            }

    def upload_to_server(self, json_file_path: str) -> Dict[str, Any]:
        """
        curl 명령어로 JSON 파일을 FTP 서버에 업로드
        """
        try:
            curl_cmd = [
                "curl",
                "-u", f"{self.ftp_user}:{self.ftp_password}",
                "-T", json_file_path,
                FTP_URL,
                "-k",
                "-v",
                "--connect-timeout", str(self.timeout)
            ]
            completed = subprocess.run(
                curl_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout
            )
            stdout = completed.stdout.decode("utf-8", errors="replace")
            stderr = completed.stderr.decode("utf-8", errors="replace")
            if completed.returncode == 0:
                return {
                    "success": True,
                    "message": "FTP 서버로 JSON 파일 업로드 성공",
                    "status_code": 200,
                    "response": stdout
                }
            else:
                # 실패 시 실행 커맨드는 출력하지 않음, 실패 메시지만 반환
                return {
                    "success": False,
                    "message": f"FTP 업로드 실패: {stderr}",
                    "status_code": None,
                    "response": None  # 실행 커맨드나 결과 미포함
                }
        except Exception as e:
            # 에러 메시지에서 민감한 정보 제거
            safe_message = self._sanitize_error_message(str(e))
            return {
                "success": False,
                "message": f"FTP 업로드 도중 오류: {safe_message}",
                "status_code": None,
                "response": None
            }

    def upload_with_fallback(self, 
                             user_info: Dict[str, Any], 
                             check_results: Dict[str, Any], 
                             score_data: Dict[str, Any],
                             fallback_file_path: str = None) -> Dict[str, Any]:
        """
        (1) 업로드할 JSON을 파일로 저장
        (2) curl로 FTP 서버에 업로드 시도
        (3) 실패 시 에러 메시지/성공 시 완료 메시지
        """
        if not fallback_file_path:
            # macOS에서 시리얼번호를 직접 조회
            try:
                import subprocess
                serial_cmd = ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
                cmd_output = subprocess.check_output(serial_cmd)
                serial_lines = cmd_output.decode(errors="replace").splitlines()
                serial_number = "unknown"
                for line in serial_lines:
                    if "IOPlatformSerialNumber" in line:
                        # 라인 예시: '    | |   "IOPlatformSerialNumber" = "XXXXXXXXXXX"'
                        parts = line.split('"')
                        if len(parts) >= 4:
                            serial_number = parts[3]
                        break
            except Exception:
                serial_number = "unknown"
            inspection_date = user_info.get("검사날짜", datetime.datetime.now().strftime("%Y%m%d"))
            fallback_file_path = f"/tmp/security_check_{serial_number}_{inspection_date}.json"

        # 업로드 데이터 준비 및 파일로 저장
        upload_data = self.prepare_upload_data(user_info, check_results, score_data)
        saved = self.save_to_local_file(upload_data, fallback_file_path)
        if not saved:
            return {
                "success": False,
                "message": f"JSON 파일을 {fallback_file_path}로 저장하지 못했습니다.",
                "status_code": None
            }

        # curl로 FTP 업로드 시도
        upload_result = self.upload_to_server(fallback_file_path)
        if upload_result["success"]:
            upload_result["message"] += f" (업로드 파일 경로: {fallback_file_path})"
        else:
            # 실패 시 실행한 명령/커맨드 출력 안 함, 실패 메시지만 출력(위에서 이미 구현됨)
            upload_result["message"] += f" (FTP 업로드 실패)"

        return upload_result

# 테스트 함수
def test_json_server_uploader():
    """
    JSON FTP 업로더 테스트 함수
    """
    # 테스트 데이터
    user_info = {
        '점검 시작': '2024-01-01 10:00:00',
        'IP 주소': '192.168.1.100',
        '사용자 이름': 'testuser',
        'OS 정보': 'macOS 14.0'
    }

    check_results = {
        'CrowdStrike Falcon 설치 여부': (True, '설치됨'),
        '방화벽 활성 여부': (True, '활성화됨')
    }

    score_data = {
        'final_score': 85,
        'max_score': 100,
        'grade': '양호'
    }

    uploader = JSONServerUploader()

    # FTP 서버 연결 테스트
    print("=== FTP 서버 연결 테스트 ===")
    connection_result = uploader.test_server_connection()
    print(f"결과: {connection_result['message']}")

    # 데이터 업로드 테스트
    print("\n=== FTP로 데이터 업로드 테스트 ===")
    upload_result = uploader.upload_with_fallback(
        user_info, check_results, score_data, fallback_file_path
    )
    print(f"결과: {upload_result['message']}")

if __name__ == "__main__":
    test_json_server_uploader()

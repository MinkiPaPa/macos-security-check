# =========================
# 사용자 정보 수집 모듈
# User Information Collection Module
# =========================

import os
import subprocess
import datetime
import socket
import platform
import json
from typing import Dict, Any, Optional


class UserDataCollector:
    """
    사용자 정보를 수집하는 클래스
    Class for collecting user information
    """
    
    def __init__(self):
        """사용자 정보 수집기 초기화 / Initialize user data collector"""
        self.host_name = os.uname().nodename
        self.current_user = os.getenv('USER')
        self.start_time = datetime.datetime.now()
    
    def get_ip_address(self) -> str:
        """
        IP 주소를 가져오는 함수
        Function to get IP address
        """
        try:
            # 외부 IP 주소 확인 시도
            # Try to get external IP address
            result = subprocess.run(
                "ifconfig | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}'",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            # 대체 방법: socket을 사용한 로컬 IP 확인
            # Alternative method: Get local IP using socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                return ip
            finally:
                s.close()
        except Exception:
            return "확인 불가 / Unable to determine"
    
    def get_hostname(self) -> str:
        """
        macOS ComputerName을 hostname으로 반환하는 함수
        Function to get hostname from macOS ComputerName
        """
        try:
            # Ensure UTF-8 environment for scutil output
            env = os.environ.copy()
            env["LC_CTYPE"] = "UTF-8"
            result = subprocess.run(
                ['scutil', '--get', 'ComputerName'],
                capture_output=True, text=True, timeout=3, env=env
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return socket.gethostname()  # fallback to Python's hostname
        except Exception:
            return "Unknown"
    
    def get_user_info(self) -> str:
        """
        사용자 부서(또는 사용자 정보)를 com.ncskorea.userinfo.plist의 FullName에서 가져오는 함수
        Function to get user info (department/user) from com.ncskorea.userinfo.plist's FullName
        """
        try:
            # macOS 환경에서 LC_CTYPE=UTF-8로 설정하여 문자셋 문제 방지
            env = os.environ.copy()
            env["LC_CTYPE"] = "UTF-8"
            env["LANG"] = "ko_KR.UTF-8"
            
            # plutil을 사용하여 JSON으로 변환 후 파싱 (한글이 제대로 처리됨)
            plist_path = '/Library/Managed Preferences/com.ncskorea.userinfo.plist'
            result = subprocess.run(
                ['plutil', '-convert', 'json', '-o', '-', plist_path],
                capture_output=True, text=True, timeout=3, env=env
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                plist_data = json.loads(result.stdout)
                full_name = plist_data.get('FullName', '미설정 / Not set')
                return full_name
            else:
                return "미설정 / Not set"
        except Exception as e:
            # 대체 방법: defaults read 사용 (유니코드 이스케이프 처리)
            try:
                result = subprocess.run(
                    ['defaults', 'read', '/Library/Managed Preferences/com.ncskorea.userinfo.plist', 'FullName'],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0 and result.stdout.strip():
                    user_info = result.stdout.strip()
                    # 유니코드 이스케이프 시퀀스를 실제 문자로 변환
                    # \uXXXX 형태를 처리
                    try:
                        # bytes로 변환 후 unicode_escape로 디코딩
                        decoded = user_info.encode('utf-8').decode('unicode_escape')
                        return decoded
                    except:
                        return user_info
                else:
                    return "미설정 / Not set"
            except:
                return "미설정 / Not set"
    
    def get_os_info(self) -> str:
        """
        OS 정보를 가져오는 함수
        Function to get OS information
        """
        try:
            result = subprocess.run(
                "sw_vers -productName && sw_vers -productVersion",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().replace('\n', ' ')
            else:
                return f"{platform.system()} {platform.release()}"
        except Exception:
            return f"{platform.system()} {platform.release()}"
    
    def get_crowdstrike_falcon_version(self) -> str:
        """
        CrowdStrike Falcon 버전을 확인하는 함수
        Function to check CrowdStrike Falcon version
        """
        try:
            # Falcon 앱 경로 확인
            # Check Falcon app path
            falcon_path = "/Applications/Falcon.app"
            if os.path.exists(falcon_path):
                # 버전 정보 확인 시도
                # Try to get version information
                result = subprocess.run(
                    f"defaults read {falcon_path}/Contents/Info CFBundleShortVersionString 2>/dev/null",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                return "설치됨 (버전 확인 불가) / Installed (version unknown)"
            else:
                return "미설치 / Not installed"
        except Exception:
            return "확인 불가 / Unable to check"
    
    def get_privacy_i_version(self) -> str:
        """
        Privacy-I 버전을 확인하는 함수
        Function to check Privacy-I version
        """
        try:
            # Privacy-I 앱 경로 확인
            # Check Privacy-I app path
            privacy_path = "/Applications/PICocoa.app"
            if os.path.exists(privacy_path):
                # 버전 정보 확인 시도
                # Try to get version information
                result = subprocess.run(
                    f"defaults read {privacy_path}/Contents/Info CFBundleShortVersionString 2>/dev/null",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                return "설치됨 (버전 확인 불가) / Installed (version unknown)"
            else:
                return "미설치 / Not installed"
        except Exception:
            return "확인 불가 / Unable to check"
    
    def get_genian_nac_version(self) -> str:
        """
        Genian NAC 버전을 확인하는 함수
        Function to check Genian NAC version
        """
        try:
            # Genian NAC 앱 경로 확인
            # Check Genian NAC app path
            genian_path = "/Applications/Genians.app"
            if os.path.exists(genian_path):
                # 버전 정보 확인 시도
                # Try to get version information
                result = subprocess.run(
                    f"defaults read {genian_path}/Contents/Info CFBundleShortVersionString 2>/dev/null",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                return "설치됨 (버전 확인 불가) / Installed (version unknown)"
            else:
                return "미설치 / Not installed"
        except Exception:
            return "확인 불가 / Unable to check"
    
    def get_serial_number(self) -> str:
        """
        Mac 시리얼 번호를 가져오는 함수
        Function to get Mac serial number
        """
        try:
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Serial Number' in line:
                        return line.split(':')[1].strip()
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def get_inspection_date(self) -> str:
        """
        검사 날짜를 가져오는 함수 (YYYYMMDD 형식)
        Function to get inspection date (YYYYMMDD format)
        """
        return self.start_time.strftime("%Y%m%d")
    
    def get_server_upload_status(self) -> bool:
        """
        점검 결과 서버 전송 여부를 확인하는 함수
        Function to check if results are uploaded to server
        """
        # 실제 환경에서는 서버 업로드 상태를 확인할 수 있습니다
        # In real environment, server upload status can be checked
        return True  # 기본값: 전송됨 / Default: Uploaded
    
    def get_security_score(self) -> int:
        """
        보안 평가 점수를 가져오는 함수 (기본값: 0)
        Function to get security evaluation score (default: 0)
        """
        # 실제 점수는 보안 점검 완료 후 계산됩니다
        # Actual score is calculated after security check completion
        return 0
    
    def collect_all_user_info(self) -> Dict[str, Any]:
        """
        모든 사용자 정보를 수집하는 함수
        Function to collect all user information
        """
        return {
            "점검 시작": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Hostname": self.get_hostname(),
            "IP 주소": self.get_ip_address(),
            "사용자 이름": self.get_user_info(),
            "시리얼번호": self.get_serial_number(),
            "OS 정보": self.get_os_info(),
            "CrowdStrike Falcon 버전": self.get_crowdstrike_falcon_version(),
            "Privacy-I 버전": self.get_privacy_i_version(),
            "Genian NAC 버전": self.get_genian_nac_version(),
            "보안 평가 점수": self.get_security_score()
        }
    
    def save_user_info_to_json(self, file_path: str) -> bool:
        """
        사용자 정보를 JSON 파일로 저장하는 함수
        Function to save user information to JSON file
        """
        try:
            user_info = self.collect_all_user_info()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(user_info, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"사용자 정보 저장 중 오류 발생 / Error saving user info: {str(e)}")
            return False


# 테스트 함수
# Test function
def test_user_data_collector():
    """
    사용자 정보 수집기 테스트 함수
    Test function for user data collector
    """
    collector = UserDataCollector()
    user_info = collector.collect_all_user_info()
    
    print("=== 사용자 정보 수집 테스트 / User Information Collection Test ===")
    # JSON 형식으로 한글이 제대로 표시되도록 출력
    print(json.dumps(user_info, ensure_ascii=False, indent=2))
    
    # JSON 파일로 저장 테스트
    # Test saving to JSON file
    test_file = "/tmp/user_info_test.json"
    if collector.save_user_info_to_json(test_file):
        print(f"\n사용자 정보가 JSON 파일로 저장되었습니다: {test_file}")
        print(f"User information saved to JSON file: {test_file}")
    else:
        print("\n사용자 정보 저장에 실패했습니다.")
        print("Failed to save user information.")


if __name__ == "__main__":
    test_user_data_collector()

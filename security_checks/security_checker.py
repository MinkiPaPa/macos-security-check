# =========================
# 보안 점검 모듈
# =========================

import os
import subprocess
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.command_executor import CommandExecutor


class SecurityChecker:
    """
    보안 점검을 수행하는 클래스
    """
    
    def __init__(self, progress_callback=None, progress_update_callback=None):
        """보안 점검기 초기화"""
        self.current_user = os.getenv('USER')
        self.host_name = os.uname().nodename
        self.check_results = {}
        self.admin_password = None
        # CommandExecutor 인스턴스 생성
        self.command_executor = CommandExecutor()
        # 실시간 진행 상황 콜백 함수
        self.progress_callback = progress_callback
        # 진행률 업데이트 콜백 함수
        self.progress_update_callback = progress_update_callback
    
    def execute_command(self, cmd: str, timeout: int = 180) -> str:
        """
        시스템 명령어를 실행하는 함수
        """
        # CommandExecutor를 사용하여 명령어 실행 및 로깅
        success, output = self.command_executor.execute_command(cmd, timeout)
        return output
    
    def check_crowdstrike_falcon_installation(self) -> Tuple[Optional[bool], str]:
        """
        CrowdStrike Falcon 설치 여부를 확인하는 함수
        """
        try:
            falcon_path = "/Applications/Falcon.app"
            installed = os.path.exists(falcon_path)
            status = "설치됨" if installed else "미설치"
            return installed, status
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_crowdstrike_falcon_process(self) -> Tuple[Optional[bool], str]:
        """
        CrowdStrike Falcon 프로세스 실행 여부를 확인하는 함수
        """
        try:
            result = self.execute_command('ps aux | grep -i "Falcon Notification" | grep -v grep')
            running = bool(result)
            status = "실행 중" if running else "실행 안됨"
            return running, status
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_privacy_i_installation(self) -> Tuple[Optional[bool], str]:
        """
        Privacy-I 설치 여부를 확인하는 함수
        """
        try:
            privacy_path = "/Applications/PICocoa.app"
            installed = os.path.exists(privacy_path)
            status = "설치됨" if installed else "미설치"
            return installed, status
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_privacy_i_process(self) -> Tuple[Optional[bool], str]:
        """
        Privacy-I 프로세스 실행 여부를 확인하는 함수
        """
        try:
            result = self.execute_command('ps aux | grep -i "PICocoa" | grep -v grep')
            running = bool(result)
            status = "실행 중" if running else "실행 안됨"
            return running, status
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_genian_nac_installation(self) -> Tuple[Optional[bool], str]:
        """
        Genian NAC 설치 여부를 확인하는 함수
        """
        try:
            genian_path = "/Applications/Genians.app"
            installed = os.path.exists(genian_path)
            status = "설치됨" if installed else "미설치"
            return installed, status
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_genian_nac_process(self) -> Tuple[Optional[bool], str]:
        """
        Genian NAC 프로세스 실행 여부를 확인하는 함수
        """
        try:
            result = self.execute_command('ps aux | grep -i "Genians" | grep -v grep')
            running = bool(result)
            status = "실행 중" if running else "실행 안됨"
            return running, status
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_unauthorized_messenger_apps(self) -> Tuple[Optional[bool], str]:
        """
        비인가 메신저 앱 설치 여부를 확인하는 함수
        KakaoTalk, 카카오톡 앱은 평가에서 제외 (설치되어 있어도 경고하지 않음)
        """
        try:
            unauthorized_apps = [
                "KakaoTalk", "Line", "Telegram", "WhatsApp", "Discord", "카카오톡", "라인", "텔레그램", "디스코드"
            ]
            exclude_apps = {"KakaoTalk", "카카오톡"}
            
            found_apps = []
            for app in unauthorized_apps:
                if app in exclude_apps:
                    continue  # KakaoTalk, 카카오톡은 무시
                app_path = f"/Applications/{app}.app"
                if os.path.exists(app_path):
                    found_apps.append(app)
            
            if found_apps:
                return True, f"비인가 메신저 앱 설치됨: {', '.join(found_apps)}"
            else:
                return False, "비인가 메신저 앱 없음"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_macos_software_updates(self) -> Tuple[Optional[bool], str]:
        """
        macOS 소프트웨어 업데이트 최신 여부를 확인하는 함수
        softwareupdate 명령어는 특히 긴 시간이 필요하므로 별도 처리
        """
        try:
            # 실시간 진행 상황 전달
            if self.progress_callback:
                self.progress_callback("softwareupdate 명령어 감지: 타임아웃 300초로 설정")
            
            # softwareupdate 명령어 결과 실행 및 재시도 로직
            result = self.execute_command("softwareupdate -l", timeout=300)  # 5분 타임아웃

            if not result or len(result.strip()) < 50:
                if self.progress_callback:
                    self.progress_callback("softwareupdate 결과가 불완전합니다. 재시도 중...")
                import time
                time.sleep(2)
                result = self.execute_command("softwareupdate -l", timeout=300)

            # 결과 분석: "Label: macOS" 문구가 몇 개 줄로 등장하는지 파악 (업데이트 여부)
            lines = result.splitlines() if result else []
            macos_update_lines = [line for line in lines if "Label: macOS" in line]
            macos_update_count = len(macos_update_lines)

            if macos_update_count > 0:
                return False, f"업데이트가 필요한 macOS 항목이 {macos_update_count}개 있습니다"
            
            # 참고: "No new software available", "No updates available" 등 메시지 식별
            result_lower = result.lower() if result else ""
            no_update_indicators = [
                "no new software available",
                "no updates available"
            ]
            if any(indicator in result_lower for indicator in no_update_indicators):
                return True, "모든 보안 업데이트가 적용되어 있습니다"

            # 만약 위에서 결정하지 못했으면 일반 업데이트 레이블 개수 기준 출력
            update_lines = [line for line in lines if line.strip().startswith('* Label: macOS')]
            update_count = len(update_lines)
            if update_count > 0:
                return False, f"업데이트가 필요한 항목이 {update_count}개 있습니다"
            else:
                return True, "모든 보안 업데이트가 적용되어 있습니다"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_user_password_setting(self) -> Tuple[Optional[bool], str]:
        """
        사용자 암호 설정 여부를 확인하는 함수
        """
        try:
            result = self.execute_command(f"dscl . -read /Users/{self.current_user} Password")
            if result and "Password:" in result:
                return True, "암호 설정됨"
            else:
                return False, "암호 미설정"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_password_policy_and_remaining_days(self) -> Tuple[Optional[bool], str, int]:
        """
        system_profiler SPConfigurationProfileDataType 명령 결과에서 
        Passcode Payload와 com.apple.mobiledevice.passwordpolicy 값이 함께 조회되는지 확인하여
        사용자 암호 정책이 설정되어 있는지 확인.

        암호 정책 만료 일수는 직접 산출 불가하므로 0으로 반환
        """
        try:
            # system_profiler SPConfigurationProfileDataType 명령 실행
            profiles_output = self.execute_command("system_profiler SPConfigurationProfileDataType")
            if not profiles_output:
                return None, "system_profiler 명령 결과 없음", 0

            # Passcode Payload, com.apple.mobiledevice.passwordpolicy 모두 있는지 확인
            has_passcode_payload = "Passcode Payload" in profiles_output
            has_password_policy = "com.apple.mobiledevice.passwordpolicy" in profiles_output

            if has_passcode_payload and has_password_policy:
                return True, "정책 설정됨 (Passcode Payload, com.apple.mobiledevice.passwordpolicy 존재)", 0
            else:
                return False, "암호 정책 미설정 또는 일부 값 누락", 0

        except Exception as e:
            return None, f"확인 불가: {str(e)}", 0
    
    def check_screensaver_setting(self) -> Tuple[Optional[bool], str]:
        """
        /Library/Managed Preferences 경로 내 com.apple.screensaver.plist에서 idleTime 값을 확인하는 함수
        """
        plist_path = "/Library/Managed Preferences/com.apple.screensaver.plist"
        try:
            # plist 파일이 존재하는지 먼저 체크
            if not os.path.exists(plist_path):
                return False, "화면 보호기 관리 설정(plist) 파일 없음"

            # defaults 명령으로 plist에서 idleTime 추출
            result = self.execute_command(
                f"defaults read '{plist_path}' idleTime 2>/dev/null"
            )
            result = result.strip() if result else ""

            if result and result.isdigit():
                timeout = int(result)
                if timeout <= 600:  # 10분 이하
                    return True, f"적절한 설정({timeout}초)"
                else:
                    return False, f"부적절한 설정({timeout}초)"
            else:
                return False, "idleTime이 설정되지 않았거나 올바른 값이 아님"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_auto_login_setting(self) -> Tuple[Optional[bool], str]:
        """
        사용자 자동 로그인 기능 설정 여부를 확인하는 함수
        """
        try:
            # 공통 실행기 사용 및 넉넉한 타임아웃 적용 / Use common executor with larger timeout
            _, output = self.command_executor.execute_command(
                "defaults read /Library/Preferences/com.apple.loginwindow autoLoginUser",
                timeout=180
            )
            if "does not exist" in output:
                # 자동 로그인이 비활성화된 것은 보안상 좋은 상태 (안전)
                return False, "자동 로그인 비활성화"  # False = 비활성화됨 (안전)
            else:
                # 자동 로그인이 활성화된 것은 보안상 취약한 상태 (취약)
                return True, f"자동 로그인 활성화: {output.strip()}"  # True = 활성화됨 (취약)
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_current_user_permissions(self) -> Tuple[Optional[bool], str]:
        """
        현재 사용자 계정 권한을 확인하는 함수
        """
        try:
            # 현재 콘솔 로그인된 사용자 확인 (_ 기호로 시작하는 사용자 계정은 제외)
            console_user = self.execute_command("who | grep console | awk '{print $1}' | grep -v '^_'").strip()
            
            # 해당 사용자의 관리자 권한 확인
            admin_check = self.execute_command(f"id -Gn {console_user} | grep -wq 'admin' && echo 'yes' || echo 'no'")
            
            if admin_check.strip() == "yes":
                return True, f"콘솔 사용자 {console_user}는 관리자 권한입니다"
            else:
                return False, f"콘솔 사용자 {console_user}는 일반 사용자 권한입니다"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_root_account_status(self) -> Tuple[Optional[bool], str]:
        """
        Root 계정 활성 여부를 확인하는 함수
        """
        try:
            result = self.execute_command("/usr/bin/dscl . -read /Users/root Password 2>&1", timeout=15)
            if "Password: ********" in result:
                return True, "Root 계정 활성화"
            elif "Password: *" in result:
                return False, "Root 계정 비활성화"
            else:
                return None, "Root 계정 상태 확인 불가"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_multiple_user_accounts(self) -> Tuple[Optional[bool], str]:
        """
        다중 사용자 계정 여부를 확인하는 함수
        """
        try:
            result = self.execute_command("dscl . -list /Users | grep -v '^_' | grep -v 'Jamf' | grep -v 'Guest' | grep -v 'daemon' | grep -v 'nobody' | grep -v 'root' | wc -l")
            user_count = int(result) if result.isdigit() else 0
            if user_count > 1:
                return True, f"다중 사용자 계정 ({user_count}개)"
            else:
                return False, f"단일 사용자 계정 ({user_count}개)"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_guest_account_status(self) -> Tuple[Optional[bool], str]:
        """
        게스트 계정 활성 여부를 확인하는 함수
        """
        try:
            # 게스트 계정 활성화 상태 확인
            guest_enabled = self.execute_command("defaults read /Library/Preferences/com.apple.loginwindow GuestEnabled 2>/dev/null")
            # 게스트 계정 인증 정보 확인 
            guest_status = self.execute_command("dscl . -read /Users/Guest AuthenticationAuthority 2>/dev/null")

            # 게스트 계정이 비활성화된 경우
            if "No such key" in guest_enabled or guest_enabled.strip() == "0":
                return False, "게스트 계정 비활성화"
            # 게스트 계정이 활성화된 경우
            elif guest_enabled.strip() == "1" or guest_status:
                return True, "게스트 계정 활성화"
            else:
                return False, "게스트 계정 비활성화"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_ftp_service(self) -> Tuple[Optional[bool], str]:
        """
        FTP 서비스(포트) 활성 여부를 확인하는 함수
        """
        try:
            result = self.execute_command("lsof -i :21 | grep LISTEN")
            if result:
                return True, "FTP 서비스 활성화"
            else:
                return False, "FTP 서비스 비활성화"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_http_server(self) -> Tuple[Optional[bool], str]:
        """
        HTTP 서버 활성 여부를 확인하는 함수
        """
        try:
            result = self.execute_command("ps aux | grep httpd | grep -v grep")
            if result.strip():
                return True, "HTTP 서버 활성화"
            else:
                return False, "HTTP 서버 비활성화"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_file_sharing(self) -> Tuple[Optional[bool], str]:
        """
        파일 공유 활성 여부를 확인하는 함수
        """
        try:
            result = self.execute_command("launchctl print system 2>&1 | grep 'com.apple.smbd'")
            if result and "=> enabled" in result:
                return True, "파일 공유 활성화"
            else:
                return False, "파일 공유 비활성화"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_screen_sharing(self) -> Tuple[Optional[bool], str]:
        """
        화면 공유(VNC) 활성 여부를 확인하는 함수
        Check Screen Sharing (VNC) status
        """
        try:
            system_status = self.execute_command("launchctl print system 2>&1 | grep 'com.apple.screensharing'")
            
            if system_status and "=> enabled" in system_status:
                return True, "화면 공유 활성화"
            else:
                return False, "화면 공유 비활성화"
            
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_bluetooth_sharing(self) -> Tuple[Optional[bool], str]:
        """
        블루투스 공유 활성 여부를 확인하는 함수
        """
        try:
            result = self.execute_command("/usr/bin/defaults -currentHost read com.apple.Bluetooth PrefKeyServicesEnabled")
            if result.strip() == "1":
                return True, "블루투스 공유 활성화"
            else:
                return False, "블루투스 공유 비활성화"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_internet_sharing(self) -> Tuple[Optional[bool], str]:
        """
        인터넷 공유 활성 여부를 확인하는 함수
        """
        try:
            # >nul은 Windows 명령어이므로 macOS에서는 /dev/null 사용
            # 2>&1도 불필요하므로 제거
            result = self.execute_command("/usr/bin/defaults read /Library/Preferences/SystemConfiguration/com.apple.nat | grep -c 'Enabled = 1'")
            
            # 결과값 검증
            try:
                count = int(result.strip())
                if count > 0:
                    return True, "인터넷 공유 활성화"
                return False, "인터넷 공유 비활성화"
            except ValueError:
                # grep 결과가 숫자가 아닌 경우
                return False, "인터넷 공유 비활성화"
                
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_ssh_remote_login(self) -> Tuple[Optional[bool], str]:
        """
        SSH 원격 로그인 활성 여부를 확인하는 함수
        SSH 포트(22번) 리스닝 여부로 확인
        Check SSH remote login status by checking SSH port (22) listening status
        """
        try:
            nc_result = self.execute_command("nc -z localhost 22 2>&1")
            
            if nc_result and "succeeded" in nc_result:
                return True, "SSH 원격 로그인 활성화"
            return False, "SSH 원격 로그인 비활성화"
            
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_macos_remote_management(self) -> Tuple[Optional[bool], str]:
        """
        macOS 원격 관리 활성 여부를 확인하는 함수
        Apple Remote Desktop (ARD) 에이전트 실행 상태로 확인
        Check macOS Remote Management status by checking ARD agent
        """
        try:
            ard_agent = self.execute_command("ps aux | grep -i 'ARDAgent' | grep -v grep")
            
            if ard_agent:
                return True, "macOS 원격 관리 활성화"
            return False, "macOS 원격 관리 비활성화"
            
        except Exception as e:
            return None, f"확인 불가: {str(e)}"
    
    def check_firewall_status(self) -> Tuple[Optional[bool], str]:
        """
        방화벽 활성 여부를 확인하는 함수
        """
        try:
            result = self.execute_command("/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate")
            # 'Firewall is enabled' 또는 'Firewall is Blocking' 이 결과에 있으면 활성화로 판정
            if ("Firewall is enabled" in result) or ("Firewall is blocking" in result):
                return True, "방화벽 활성화"
            else:
                return False, "방화벽 비활성화"
        except Exception as e:
            return None, f"확인 불가: {str(e)}"

    def run_all_security_checks(self) -> Dict[str, Any]:
        """
        모든 보안 점검을 순차적으로 실행하는 함수
        각 체크가 완전히 완료될 때까지 기다림
        실시간 진행 상황을 콜백으로 전달
        """
        import time
        
        checks = {}
        
        # 체크 항목들을 순차적으로 실행
        check_items = [
            ("CrowdStrike Falcon 설치 여부", self.check_crowdstrike_falcon_installation),
            ("CrowdStrike Falcon 프로세스 실행 여부", self.check_crowdstrike_falcon_process),
            ("Privacy-I 설치 여부", self.check_privacy_i_installation),
            ("Privacy-I 프로세스 실행 여부", self.check_privacy_i_process),
            ("Genian NAC 설치 여부", self.check_genian_nac_installation),
            ("Genian NAC 프로세스 실행 여부", self.check_genian_nac_process),
            ("비인가 메신저 앱 설치 여부", self.check_unauthorized_messenger_apps),
            ("macOS 소프트웨어 업데이트 최신 여부", self.check_macos_software_updates),
            ("사용자 암호 설정 여부", self.check_user_password_setting),
            ("사용자 암호 변경 정책 및 남은 기간", lambda: self.check_password_policy_and_remaining_days()[:2]),
            ("화면 보호기 설정 여부", self.check_screensaver_setting),
            ("사용자 자동 로그인 기능 설정 여부", self.check_auto_login_setting),
            ("현재 사용자 계정 권한", self.check_current_user_permissions),
            ("Root 계정 활성 여부", self.check_root_account_status),
            ("다중 사용자 계정 여부", self.check_multiple_user_accounts),
            ("게스트 계정 활성 여부", self.check_guest_account_status),
            ("FTP 서비스(포트) 활성 여부", self.check_ftp_service),
            ("HTTP 서버 활성 여부", self.check_http_server),
            ("파일 공유 활성 여부", self.check_file_sharing),
            ("화면 공유 활성 여부", self.check_screen_sharing),
            ("블루투스 공유 활성 여부", self.check_bluetooth_sharing),
            ("인터넷 공유 활성 여부", self.check_internet_sharing),
            ("SSH 원격 로그인 활성 여부", self.check_ssh_remote_login),
            ("macOS 원격 관리 활성 여부", self.check_macos_remote_management),
            ("방화벽 활성 여부", self.check_firewall_status)
        ]
        
        total_checks = len(check_items)
        
        for index, (check_name, check_func) in enumerate(check_items):
            try:
                # 진행률 계산 (10% ~ 80% 범위에서 보안 점검 진행)
                progress_percentage = 10 + int((index / total_checks) * 70)
                
                # 실시간 진행 상황 전달
                if self.progress_callback:
                    self.progress_callback(f"실행 중: {check_name}")
                
                # 진행률 업데이트
                if self.progress_update_callback:
                    self.progress_update_callback(progress_percentage, f"보안 점검 실행 중... ({index + 1}/{total_checks})")
                
                result = check_func()
                checks[check_name] = result
                
                # 완료 메시지 전달
                if self.progress_callback:
                    result_message = result[1] if isinstance(result, tuple) else str(result)
                    self.progress_callback(f"완료: {check_name} - {result_message}")
                
                time.sleep(0.5)  # 각 체크 간 짧은 대기
                
            except Exception as e:
                error_msg = f"오류 발생: {check_name} - {str(e)}"
                if self.progress_callback:
                    self.progress_callback(error_msg)
                checks[check_name] = (False, f"체크 중 오류: {str(e)}")
        
        self.check_results = checks
        return checks


# 테스트 함수
def test_security_checker():
    """
    보안 점검기 테스트 함수
    """
    checker = SecurityChecker()
    results = checker.run_all_security_checks()
    
    # print("=== 보안 점검 결과 ===")
    # for check_name, (status, message) in results.items():
    #     print(f"{check_name}: {status} - {message}")


if __name__ == "__main__":
    test_security_checker()

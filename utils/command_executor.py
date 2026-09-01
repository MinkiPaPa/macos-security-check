# =========================
# 명령어 실행 유틸리티 모듈
# =========================

import subprocess
import os
import re
import datetime
from typing import Tuple, Optional


class CommandExecutor:
    """
    시스템 명령어를 안전하게 실행하는 클래스
    """
    
    def __init__(self, timeout: int = 180, log_file_path: str = None):
        """
        명령어 실행기 초기화
        
        Args:
            timeout: 명령어 실행 타임아웃 (초)
            log_file_path: 명령어 로그 파일 경로
        """
        self.timeout = timeout
        self.host_name = os.uname().nodename
        self.current_user = os.getenv('USER', 'unknown')
        
        # 명령어 로그 파일 경로 설정
        if log_file_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file_path = f"/Users/Shared/command_execution_log_{self.host_name}_{timestamp}.txt"
        else:
            self.log_file_path = log_file_path
        
        # 로그 파일 초기화
        self._initialize_log_file()
    
    def _initialize_log_file(self):
        """
        명령어 로그 파일을 초기화하는 함수
        """
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("명령어 실행 로그\n")
                f.write("=" * 80 + "\n")
                f.write(f"호스트명: {self.host_name}\n")
                f.write(f"사용자: {self.current_user}\n")
                f.write(f"시작 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"명령어 로그 파일 초기화 중 오류 발생: {str(e)}")
    
    def _log_command_execution(self, cmd: str, success: bool, output: str, execution_time: float = None):
        """
        명령어 실행을 로그 파일에 기록하는 함수
        
        Args:
            cmd: 실행된 명령어
            success: 실행 성공 여부
            output: 명령어 출력
            execution_time: 실행 시간 (초)
        """
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status = "성공" if success else "실패"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {status}\n")
                f.write(f"명령어: {cmd}\n")
                if execution_time:
                    f.write(f"실행 시간: {execution_time:.2f}초\n")
                f.write(f"출력:\n{output}\n")
                f.write("-" * 80 + "\n\n")
        except Exception as e:
            print(f"명령어 로그 기록 중 오류 발생: {str(e)}")
    
    def execute_command(self, cmd: str, timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        시스템 명령어를 실행하는 함수
        
        Args:
            cmd: 실행할 명령어
            timeout: 타임아웃 (초)
            
        Returns:
            Tuple[bool, str]: (성공 여부, 출력 결과)
        """
        start_time = datetime.datetime.now()
        
        try:
            timeout = timeout or self.timeout
            
            # softwareupdate 명령어는 특히 긴 시간이 필요하므로 추가 대기
            # softwareupdate command requires additional wait time
            if "softwareupdate" in cmd:
                timeout = max(timeout, 300)  # 최소 5분
                print(f"softwareupdate 명령어 감지: 타임아웃 {timeout}초로 설정")
            
            # 명령 실행 및 완료까지 대기 / Run command and wait for completion
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            # 프로세스가 완전히 종료될 때까지 추가 대기
            # Additional wait to ensure process completion
            import time
            wait_time = 2.0 if "softwareupdate" in cmd else 0.1
            time.sleep(wait_time)
            
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # stdout/stderr 결합하여 정보 유실 방지 / Combine to avoid losing important info
            combined_output = (result.stdout or "") + ("\n" if result.stdout and result.stderr else "") + (result.stderr or "")
            output_text = combined_output.strip()
            
            if result.returncode == 0:
                # 명령어 실행 로그 기록
                self._log_command_execution(cmd, True, output_text, execution_time)
                return True, output_text
            else:
                # 명령어 실행 로그 기록
                self._log_command_execution(cmd, False, output_text, execution_time)
                return False, output_text
                
        except subprocess.TimeoutExpired as e:
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            # 부분 출력 포함하여 기록 / Include partial output on timeout
            partial_stdout = (e.output or "") if hasattr(e, 'output') else ""
            partial_stderr = (e.stderr or "") if hasattr(e, 'stderr') else ""
            combined = (partial_stdout + "\n" + partial_stderr).strip()
            error_msg = f"명령어 실행 시간 초과 ({timeout}초)"
            log_text = error_msg + ("\n" + combined if combined else "")
            # 명령어 실행 로그 기록
            self._log_command_execution(cmd, False, log_text, execution_time)
            return False, (combined if combined else error_msg)
        except Exception as e:
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            error_msg = f"명령어 실행 오류: {str(e)}"
            # 명령어 실행 로그 기록
            self._log_command_execution(cmd, False, error_msg, execution_time)
            return False, error_msg
    
    def execute_command_with_sudo(self, cmd: str, password: str = None, timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        sudo 권한으로 명령어를 실행하는 함수
        
        Args:
            cmd: 실행할 명령어
            password: sudo 암호
            timeout: 타임아웃 (초)
            
        Returns:
            Tuple[bool, str]: (성공 여부, 출력 결과)
        """
        try:
            if password:
                # 암호를 포함한 sudo 명령어 실행 (암호는 로그에서 마스킹)
                sudo_cmd = f"echo {password} | sudo -S {cmd}"
                masked_cmd = f"echo **** | sudo -S {cmd}"  # 로그용 마스킹된 명령어
            else:
                # 암호 없이 sudo 명령어 실행
                sudo_cmd = f"sudo {cmd}"
                masked_cmd = sudo_cmd
            
            # 실제 명령어 실행
            result = self.execute_command(sudo_cmd, timeout)
            
            # 로그에는 마스킹된 명령어 기록
            if not result[0]:  # 실패한 경우에만 추가 로그 기록
                self._log_command_execution(masked_cmd, False, result[1])
            
            return result
            
        except Exception as e:
            error_msg = f"sudo 명령어 실행 오류: {str(e)}"
            self._log_command_execution(f"sudo {cmd}", False, error_msg)
            return False, error_msg
    
    def mask_sensitive_info(self, text: str) -> str:
        """
        민감한 정보를 마스킹하는 함수
        
        Args:
            text: 마스킹할 텍스트
            
        Returns:
            str: 마스킹된 텍스트
        """
        # IP 주소 마스킹
        text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '***.***.***.***', text)
        
        # 암호 마스킹
        text = re.sub(r'password:\s*.*', 'password: ****', text, flags=re.IGNORECASE)
        
        # 토큰 마스킹
        text = re.sub(r'token:\s*.*', 'token: ****', text, flags=re.IGNORECASE)
        
        # API 키 마스킹
        text = re.sub(r'api[_-]?key:\s*.*', 'api-key: ****', text, flags=re.IGNORECASE)
        
        return text
    
    def save_command_log(self, cmd: str, output: str, file_path: str) -> bool:
        """
        명령어 실행 로그를 파일로 저장하는 함수
        
        Args:
            cmd: 실행된 명령어
            output: 명령어 출력
            file_path: 로그 파일 경로
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 민감한 정보 마스킹
            masked_cmd = self.mask_sensitive_info(cmd)
            masked_output = self.mask_sensitive_info(output)
            
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"명령어: {masked_cmd}\n")
                f.write(f"출력: {masked_output}\n")
                f.write("=" * 50 + "\n")
            
            return True
        except Exception as e:
            print(f"명령어 로그 저장 중 오류 발생: {str(e)}")
            return False
    
    def check_command_exists(self, cmd: str) -> bool:
        """
        명령어가 시스템에 존재하는지 확인하는 함수
        
        Args:
            cmd: 확인할 명령어
            
        Returns:
            bool: 명령어 존재 여부
        """
        try:
            result = subprocess.run(
                f"which {cmd}", 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_system_info(self) -> dict:
        """
        시스템 정보를 수집하는 함수
        
        Returns:
            dict: 시스템 정보
        """
        system_info = {}
        
        try:
            # 운영체제 정보
            success, output = self.execute_command("uname -a")
            if success:
                system_info['uname'] = output
            
            # 메모리 정보
            success, output = self.execute_command("system_profiler SPHardwareDataType | grep Memory")
            if success:
                system_info['memory'] = output
            
            # 디스크 정보
            success, output = self.execute_command("df -h")
            if success:
                system_info['disk'] = output
            
            # 네트워크 정보
            success, output = self.execute_command("ifconfig")
            if success:
                system_info['network'] = self.mask_sensitive_info(output)
            
        except Exception as e:
            system_info['error'] = f"시스템 정보 수집 중 오류 발생: {str(e)}"
        
        return system_info
    
    def get_log_file_path(self) -> str:
        """
        명령어 로그 파일 경로를 반환하는 함수
        
        Returns:
            str: 로그 파일 경로
        """
        return self.log_file_path
    
    def close_log_file(self):
        """
        로그 파일을 종료하는 함수
        """
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"종료 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
        except Exception as e:
            print(f"로그 파일 종료 중 오류 발생: {str(e)}")


# 테스트 함수
def test_command_executor():
    """
    명령어 실행기 테스트 함수
    """
    executor = CommandExecutor()
    
    print("=== 명령어 실행기 테스트 ===")
    
    # 기본 명령어 실행 테스트
    success, output = executor.execute_command("echo 'Hello World'")
    print(f"기본 명령어 실행: {success} - {output}")
    
    # 시스템 정보 수집 테스트
    print("\n=== 시스템 정보 ===")
    system_info = executor.get_system_info()
    for key, value in system_info.items():
        print(f"{key}: {value}")
    
    # 명령어 존재 확인 테스트
    print("\n=== 명령어 존재 확인 ===")
    commands = ['ls', 'echo', 'python3', 'nonexistent_command']
    for cmd in commands:
        exists = executor.check_command_exists(cmd)
        print(f"{cmd}: {'존재' if exists else '존재하지 않음'}")


if __name__ == "__main__":
    test_command_executor()

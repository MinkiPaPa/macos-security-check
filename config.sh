#!/bin/bash

# 시스템 설정
V3_INSTALL_PATH="/Library/Application Support/ahnlab/v3mac/"
V3_UPRESULT_PATH="/Library/Application Support/ahnlab/v3mac/log/v3upresult.dat"
MAX_AGE_DAYS=90
MAX_AGE_MINUTES=$((MAX_AGE_DAYS * 24 * 60))

# 현재 디렉토리 설정
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 파일 설정
host_name=$(hostname)
RESULT_FILE="/Users/Shared/${host_name}_result.txt"
CMD_OUTPUT_FILE="/Users/Shared/${host_name}_command.txt"

# 로그 레벨
LOG_LEVEL_INFO="INFO"
LOG_LEVEL_WARN="WARN"
LOG_LEVEL_ERROR="ERROR"

# 타임아웃 설정 (초) - 무거운 명령을 고려해 상향 조정
COMMAND_TIMEOUT=180

# sudo 비밀번호 설정
read -s -p "Enter sudo password: " SUDO_PASSWORD
echo

# 필수 명령어 목록 (macOS 기본 명령어)
REQUIRED_COMMANDS=("sudo" "dscl" "launchctl" "systemsetup" "spctl" "softwareupdate" "grep" "awk" "sed" "bc" "mktemp") 
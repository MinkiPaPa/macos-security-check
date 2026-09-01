#!/bin/bash

# 로깅 함수
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp][$level] $message" | tee -a "$RESULT_FILE"
}

# 임시 파일 생성
create_temp_file() {
    mktemp -t isms_check.XXXXXX
}

# 명령어 실행 함수
execute_command() {
    local cmd="$1"
    local output
    local retval
    local pid
    local temp_file
    
    # 명령어 실행 전 로깅
    log_message "$LOG_LEVEL_INFO" "Executing command: $cmd"
    
    # 임시 파일 생성
    temp_file=$(create_temp_file)
    
    # sudo 명령어인 경우 -S 옵션 추가
    if [[ "$cmd" == sudo* ]]; then
        cmd="echo '$SUDO_PASSWORD' | sudo -S ${cmd#sudo }"
    fi
    
    # 명령어를 백그라운드로 실행하고 PID 저장
    eval "$cmd" > "$temp_file" 2>&1 &
    pid=$!
    
    # 타임아웃 처리
    for i in $(seq 1 $COMMAND_TIMEOUT); do
        if ! kill -0 $pid 2>/dev/null; then
            # 프로세스가 종료된 경우
            break
        fi
        sleep 1
    done
    
    # 프로세스가 여전히 실행 중이면 종료하되, 부분 출력은 보존
    if kill -0 $pid 2>/dev/null; then
        # 부분 출력 확보
        output=$(cat "$temp_file")
        # 프로세스 종료
        kill $pid 2>/dev/null
        wait $pid 2>/dev/null
        log_message "$LOG_LEVEL_ERROR" "Command timed out: $cmd"
        # 민감한 정보 마스킹 후 출력 반환
        output=$(mask_sensitive_info "$output")
        echo "$output"
        rm -f "$temp_file"
        return 124
    fi
    
    # 명령어 실행 결과 가져오기
    wait $pid
    retval=$?
    output=$(cat "$temp_file")
    rm -f "$temp_file"
    
    # 결과 처리
    if [ $retval -eq 0 ]; then
        # 성공한 경우에도 stderr가 있을 수 있으므로 확인
        if [ -n "$(echo "$output" | grep -i "error\|warning\|fail")" ]; then
            log_message "$LOG_LEVEL_WARN" "Command completed with warnings: $cmd"
        fi
    else
        log_message "$LOG_LEVEL_ERROR" "Command failed with exit code $retval: $cmd"
    fi
    
    # 민감한 정보 마스킹
    output=$(mask_sensitive_info "$output")
    
    echo "$output"
    return $retval
}

# 민감한 정보 마스킹
mask_sensitive_info() {
    local input="$1"
    # 패스워드 마스킹
    input=$(echo "$input" | sed 's/password:.*/password: ****/g')
    # IP 주소 마스킹
    input=$(echo "$input" | sed 's/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}/***.***.***.***/g')
    echo "$input"
}

# 분을 일로 변환하는 함수
minutes_to_days() {
    local minutes=$1
    local days=$(echo "scale=6; $minutes / 60 / 24" | bc)
    echo "$days"
}

# 결과를 기록하는 함수
record_result() {
    local result=$1
    local message=$2
    log_message "$LOG_LEVEL_INFO" "$message: $result"
}

# 명령어 결과를 저장하는 함수
record_command_result() {
    local command=$1
    local result=$(execute_command "$command")
    echo "Command [$command] result: $result" >> "$CMD_OUTPUT_FILE"
    echo "$result"
}

# 파일 권한 설정
set_file_permissions() {
    # 결과 파일이 존재하는지 확인
    if [ ! -f "$RESULT_FILE" ]; then
        touch "$RESULT_FILE"
    fi
    if [ ! -f "$CMD_OUTPUT_FILE" ]; then
        touch "$CMD_OUTPUT_FILE"
    fi
    
    chmod 600 "$RESULT_FILE"
    chmod 600 "$CMD_OUTPUT_FILE"
}

# 필수 명령어 검증
validate_requirements() {
    local missing_commands=()
    
    for cmd in "${REQUIRED_COMMANDS[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        log_message "$LOG_LEVEL_ERROR" "Missing required commands: ${missing_commands[*]}"
        exit 1
    fi
}

# HTML 보고서 생성
generate_html_report() {
    local result_file="$1"
    local html_file="${result_file%.*}.html"
    
    cat > "$html_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Security Check Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .result { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .pass { background-color: #dff0d8; }
        .fail { background-color: #f2dede; }
        .warning { background-color: #fcf8e3; }
        .summary { margin: 20px 0; padding: 10px; background-color: #f5f5f5; }
    </style>
</head>
<body>
    <h1>Security Check Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total checks: $(grep -c "양호\|취약" "$result_file")</p>
        <p>Passed: $(grep -c "양호" "$result_file")</p>
        <p>Failed: $(grep -c "취약" "$result_file")</p>
    </div>
EOF

    while IFS= read -r line; do
        # Executing command나 Command failed 내용이 포함된 라인은 건너뜀
        if [[ "$line" == *"Executing command"* ]] || [[ "$line" == *"Command failed with exit code"* ]]; then
            continue
        fi
        
        if [[ "$line" == *"양호"* ]]; then
            echo "<div class='result pass'>$line</div>" >> "$html_file"
        elif [[ "$line" == *"취약"* ]]; then
            echo "<div class='result fail'>$line</div>" >> "$html_file"
        elif [[ "$line" == *"경고"* ]]; then
            echo "<div class='result warning'>$line</div>" >> "$html_file"
        else
            echo "<div class='result'>$line</div>" >> "$html_file"
        fi
    done < "$result_file"

    echo "</body></html>" >> "$html_file"
}

# 로그인 패스워드 설정 여부 확인
check_password_setting() {
    local result=$(record_command_result "dscl . -read /Users/$CURRENT_USER Password")
    if [ -n "$result" ]; then
        record_result "양호" "로그인 패스워드가 설정되어 있습니다."
    else
        record_result "취약" "로그인 패스워드가 설정되어 있지 않습니다."
    fi
}

# 사용자 패스워드 최대 사용일 확인
check_password_max_age() {
    local max_age=$(record_command_result "dscl . -read /Users/$CURRENT_USER PasswordPolicyOptions" | grep "maxMinutesUntilChangePassword" | awk '{print $2}')
    if [ -n "$max_age" ]; then
        local days=$(minutes_to_days "$max_age")
        if [ $(echo "$days <= $MAX_AGE_DAYS" | bc) -eq 1 ]; then
            record_result "양호" "패스워드 최대 사용일이 $days 일로 설정되어 있습니다."
        else
            record_result "취약" "패스워드 최대 사용일이 $days 일로 설정되어 있습니다. (권장: $MAX_AGE_DAYS 일 이하)"
        fi
    else
        record_result "취약" "패스워드 최대 사용일이 설정되어 있지 않습니다."
    fi
}

# 자동 로그인 활성화 여부 확인
# Check if auto login is enabled
check_auto_login() {
    # 자동 로그인 설정 확인을 위해 com.apple.loginwindow의 autoLoginUser 값 조회
    # Check autoLoginUser value in com.apple.loginwindow to determine auto login status
    local result=$(record_command_result "defaults read /Library/Preferences/com.apple.loginwindow autoLoginUser")
    
    # 명령어 실행 결과에 "does not exist" 문자열이 포함되어 있는지 확인
    # Check if command output contains "does not exist" string
    if echo "$result" | grep -q "does not exist"; then
        # autoLoginUser 키가 없으면 자동 로그인 비활성화 상태
        # If autoLoginUser key doesn't exist, auto login is disabled
        record_result "양호" "자동 로그인이 비활성화되어 있습니다."
    else
        # autoLoginUser 값이 존재하면 자동 로그인 활성화 상태
        # If autoLoginUser value exists, auto login is enabled
        local auto_login_user=$(echo "$result" | grep -v "does not exist")
        record_result "취약" "자동 로그인이 활성화되어 있습니다. (자동 로그인 계정: $auto_login_user)"
    fi
}

# 공유 폴더 제거 여부 확인
check_shared_folders() {
    local result=$(record_command_result "ls -la /Users/Shared/" | wc -l)
    if [ "$result" -le 3 ]; then
        record_result "양호" "공유 폴더가 적절히 관리되고 있습니다."
    else
        record_result "취약" "공유 폴더에 불필요한 파일이 존재합니다."
    fi
}

# 시작 서비스 점검
check_startup_services() {
    local result=$(record_command_result "launchctl list" | grep -v "com.apple" | wc -l)
    if [ "$result" -le 5 ]; then
        record_result "양호" "시작 서비스가 적절히 관리되고 있습니다."
    else
        record_result "취약" "확인이 필요한 일부 시작 서비스가 존재합니다."
    fi
}

# 최신 보안 업데이트 적용 여부 확인
check_security_updates() {
    local result=$(record_command_result "softwareupdate -l" | grep -i "security" | wc -l)
    if [ "$result" -eq 0 ]; then
        record_result "양호" "모든 보안 업데이트가 적용되어 있습니다."
    else
        record_result "취약" "보안 업데이트가 적용되지 않은 항목이 있습니다."
    fi
}

# 백신 설치 여부 확인 
# Check antivirus installation status
check_antivirus() {
    # V3 설치 경로와 업데이트 로그 파일 모두 확인
    # Check both V3 installation path and update log file
    if [ -d "$V3_INSTALL_PATH" ] && [ -f "$V3_UPRESULT_PATH" ]; then
        # V3 프로세스가 실행 중인지 확인
        # Check if V3 process is running
        local v3_process=$(ps aux | grep -i "v3mac" | grep -v grep)
        if [ -n "$v3_process" ]; then
            record_result "양호" "백신(V3)이 설치되어 있고 정상 실행 중입니다."
        else
            record_result "취약" "백신(V3)이 설치되어 있으나 실행되지 않고 있습니다."
        fi
    else
        record_result "취약" "백신(V3)이 설치되어 있지 않습니다."
    fi
}

# OS 제공 침입차단 기능 활성화 여부 확인
check_firewall() {
    local result=$(record_command_result "/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate")
    if [[ "$result" == *"enabled"* ]]; then
        record_result "양호" "방화벽이 활성화되어 있습니다."
    else
        record_result "취약" "방화벽이 비활성화되어 있습니다."
    fi
}

check_screensaver() {
    # 현재 콘솔에 로그인한 사용자 확인
    # Get current console logged-in user
    CURRENT_USER=$(who | awk '/console/{print $1}')

    # 화면보호기 설정 확인을 위한 여러 도메인 체크
    # Check multiple domains for screensaver settings
    local user_timeout
    local domains=("com.apple.screensaver" "com.apple.screensaver.plist" "com.apple.preference.security")

    # 각 도메인에서 화면보호기 설정 확인
    # Check screensaver settings in each domain
    for domain in "${domains[@]}"; do
        # defaults -currentHost read 명령어로 현재 호스트의 설정 확인
        # Check current host settings using defaults -currentHost read
        user_timeout=$(sudo -u $CURRENT_USER defaults -currentHost read $domain idleTime 2>/dev/null)
        if [ -n "$user_timeout" ]; then
            break
        fi
    done

    # 화면보호기 설정이 없는 경우 시스템 전역 설정 확인
    # If no user setting found, check system-wide settings
    if [ -z "$user_timeout" ]; then
        user_timeout=$(sudo -u $CURRENT_USER defaults read /Library/Preferences/com.apple.screensaver idleTime 2>/dev/null)
    fi

    # 설정값 평가 및 결과 기록 (10분 = 600초)
    # Evaluate settings and record results (10 minutes = 600 seconds)
    if [ -n "$user_timeout" ] && [ "$user_timeout" -le 600 ]; then
        record_result "양호" "화면보호기 대기시간이 적절합니다. (대기시간: ${user_timeout}초)"
    else
        record_result "취약" "화면보호기 대기시간이 부적절합니다. (대기시간: ${user_timeout:-'미설정'}초)"
    fi
}

# 원격지원 금지 정책 설정 여부 확인
check_remote_support() {
    local result=$(record_command_result "systemsetup -getremotelogin")
    if [[ "$result" == *"Off"* ]]; then
        record_result "양호" "원격 로그인이 비활성화되어 있습니다."
    else
        record_result "취약" "원격 로그인이 활성화되어 있습니다."
    fi
}

# 앱 보안설정 점검
check_app_security() {
    local result=$(record_command_result "spctl --status")
    if [[ "$result" == *"enabled"* ]]; then
        record_result "양호" "앱 보안설정이 활성화되어 있습니다."
    else
        record_result "취약" "앱 보안설정이 비활성화되어 있습니다."
    fi
} 
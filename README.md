# macOS Security Check

NCSKorea 사내 macOS 단말의 보안 상태를 점검하는 데스크톱 애플리케이션입니다.  
25개 항목을 확인한 뒤 100점 만점 점수와 PDF 보고서를 생성합니다.

This is an internal macOS security assessment tool for NCSKorea. It evaluates 25 checks, scores the result out of 100, and generates a PDF report.

> **Internal use only.** 이 저장소는 NCSKorea 내부 배포용입니다. 서버 주소, 계정, 비밀번호는 커밋하지 마세요.

## 요구 사항

- macOS (Apple Silicon / Intel)
- Python 3.9 이상 (개발 환경은 3.13에서 검증)
- [requirements.txt](requirements.txt)에 명시된 패키지

## 주요 기능

- 단말·사용자 정보 수집 (호스트명, IP, 시리얼, OS, 보안 에이전트 버전)
- 25개 보안 항목 점검
- 100점 환산 점수 및 등급 산출
- 한글 PDF 보고서 생성
- 점검 결과 JSON 저장 및 사내 서버 업로드 (설정은 로컬에서만 관리)

## 보안 점검 항목 (25)

**보안 프로그램**

- CrowdStrike Falcon 설치 / 프로세스
- Privacy-I 설치 / 프로세스
- Genian NAC 설치 / 프로세스

**시스템 보안**

- 비인가 메신저 앱
- macOS 소프트웨어 업데이트
- 사용자 암호 설정
- 사용자 암호 변경 정책
- 화면 보호기
- 자동 로그인

**계정 보안**

- 현재 사용자 계정 권한
- Root 계정 활성 여부
- 다중 사용자 계정
- 게스트 계정

**네트워크 보안**

- FTP 서비스, HTTP 서버
- 파일 공유, 화면 공유, 블루투스 공유, 인터넷 공유
- SSH 원격 로그인, macOS 원격 관리
- 방화벽

## 점수

통과한 항목 비율을 100점 만점으로 환산합니다. 점검 불가 항목은 0점으로 처리됩니다.

| 점수 | 등급 |
|------|------|
| 90 이상 | 우수 |
| 80 이상 | 양호 |
| 70 이상 | 보통 |
| 60 이상 | 미흡 |
| 60 미만 | 위험 |

## 설치 및 실행

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**GUI (배포용 진입점)** — 창이 열린 뒤 자동으로 점검을 시작합니다.

```bash
python main_gui_app.py
```

**CLI** — 전체 점검 / 빠른 점검 / 모듈 테스트를 선택할 수 있습니다.

```bash
python main_app.py
```

## 앱 패키징

PyInstaller로 `.app`을 만들 수 있습니다.

```bash
pip install pyinstaller
pyinstaller macOS_Security_Check_pyqt6.spec
```

DMG 생성은 `create_dmg.sh` 또는 `create_dmg_arm64.sh`를 사용합니다.

## 설정 (커밋 금지)

업로드 서버 정보는 `reporting/json_server_uploader.py`의 아래 상수로 관리합니다.  
공개 저장소에는 값이 `***`로 마스킹되어 있습니다. **실제 주소·계정·비밀번호는 로컬에서만 넣고 커밋하지 마세요.**

```python
FTP_SERVER = "***"
FTP_USER = "***"
FTP_PASSWORD = "***"
```

사용자 이름은 MDM 관리 프로파일의 `FullName`을 읽습니다.

```
/Library/Managed Preferences/com.ncskorea.userinfo.plist
```

## 출력 파일

GUI는 `/private/tmp`, CLI는 `/Users/Shared`에 결과를 저장합니다.

| 종류 | 파일명 예시 |
|------|-------------|
| PDF 보고서 | `security_check_report_[hostname]_[timestamp].pdf` |
| JSON 로그 | `security_check_[hostname]_[timestamp].json` |
| 텍스트 로그 | `security_check_[hostname]_[timestamp].log` |

## 프로젝트 구조

```
.
├── main_gui_app.py                 # GUI 진입점
├── main_app.py                     # CLI 진입점
├── requirements.txt
├── macOS_Security_Check_pyqt6.spec # PyInstaller 설정
├── assets/                         # 로고, 앱 아이콘
├── user_info/                      # 사용자·단말 정보 수집
├── security_checks/                # 25개 보안 점검
├── scoring/                        # 점수·등급 계산
├── reporting/                      # PDF 생성, 결과 업로드
├── utils/                          # 명령 실행, 로깅
└── gui/                            # GUI 패키지 (자리 표시)
```

`venv/`, `dist/`, `build/`, `__pycache__/`는 `.gitignore`에 포함되어 있습니다.

## 라이선스

NCSKorea 내부 사용 전용입니다. 무단 배포 및 외부 공개를 금지합니다.

**개발사:** NCSKorea  
**버전:** 1.0  
**플랫폼:** macOS

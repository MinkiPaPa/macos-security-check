<div align="center">

<img src="assets/NCSK_logo.png" alt="NCSKorea" width="220">

# macOS Security Check

**NCSKorea 사내 macOS 보안 점검 도구**

단말 보안 상태를 25개 항목으로 점검하고, 100점 만점 점수와 한글 PDF 보고서를 생성합니다.

[English summary](#english) · [설치](#설치-및-실행) · [점검 항목](#보안-점검-항목) · [라이선스](#라이선스)

![macOS](https://img.shields.io/badge/Platform-macOS-000000?logo=apple&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt&logoColor=white)
![Version](https://img.shields.io/badge/Version-1.0-1F6FEB)
![License](https://img.shields.io/badge/License-Internal-red)

</div>

---

> **Internal use only** — NCSKorea 내부 배포 전용입니다.  
> 서버 주소, 계정, 비밀번호는 저장소에 커밋하지 마세요.

## 개요

macOS Security Check는 사내 Mac 단말의 보안 준수 여부를 한 번에 확인하기 위한 데스크톱 앱입니다.  
창을 열면 점검을 자동으로 시작하고, 결과를 PDF와 JSON으로 남깁니다.

```mermaid
flowchart LR
    A[사용자·단말 정보] --> B[25개 보안 점검]
    B --> C[점수·등급 산출]
    C --> D[PDF 보고서]
    D --> E[JSON 저장]
    E --> F[사내 서버 업로드]
```

| 구분 | 내용 |
|:-----|:-----|
| 대상 | 사내 macOS 단말 |
| 점검 | 보안 에이전트, 계정, 공유 서비스, 방화벽 등 25항목 |
| 결과 | 100점 환산 점수, 등급, 한글 PDF, JSON |
| 실행 | GUI 자동 점검 / CLI 메뉴 |

## 주요 기능

| | 기능 | 설명 |
|:---:|:-----|:-----|
| 1 | 정보 수집 | 호스트명, IP, 시리얼, OS, CrowdStrike / Privacy-I / Genian 버전 |
| 2 | 보안 점검 | 설치·프로세스·계정·네트워크 설정을 순차 확인 |
| 3 | 점수 산출 | 통과 비율을 100점으로 환산하고 우수~위험 등급을 부여 |
| 4 | PDF 보고서 | 사용자 정보, 항목별 결과, 권고 사항을 한글로 출력 |
| 5 | 결과 전송 | JSON을 로컬에 저장하고, 설정된 사내 서버로 업로드 |

## 보안 점검 항목

총 **25개** 항목을 네 영역으로 점검합니다.

<table>
<tr>
<td width="25%" valign="top">

**보안 프로그램**

- CrowdStrike Falcon 설치
- CrowdStrike Falcon 프로세스
- Privacy-I 설치
- Privacy-I 프로세스
- Genian NAC 설치
- Genian NAC 프로세스

</td>
<td width="25%" valign="top">

**시스템 보안**

- 비인가 메신저 앱
- macOS 소프트웨어 업데이트
- 사용자 암호 설정
- 암호 변경 정책
- 화면 보호기
- 자동 로그인

</td>
<td width="25%" valign="top">

**계정 보안**

- 현재 사용자 권한
- Root 계정 활성 여부
- 다중 사용자 계정
- 게스트 계정

</td>
<td width="25%" valign="top">

**네트워크 보안**

- FTP / HTTP 서비스
- 파일·화면 공유
- 블루투스·인터넷 공유
- SSH 원격 로그인
- macOS 원격 관리
- 방화벽

</td>
</tr>
</table>

## 점수 체계

통과한 항목 비율을 100점 만점으로 환산합니다.  
점검이 불가능한 항목은 0점으로 처리됩니다.

```
최종 점수 = (통과 항목 수 / 전체 항목 수) × 100
```

| 점수 | 등급 | 의미 |
|:----:|:----:|:-----|
| 90 ~ 100 | **우수** | 사내 보안 기준을 충족 |
| 80 ~ 89 | **양호** | 일부 보완이 필요 |
| 70 ~ 79 | **보통** | 개선 항목을 확인해야 함 |
| 60 ~ 69 | **미흡** | 조치가 필요 |
| 0 ~ 59 | **위험** | 즉시 점검이 필요 |

## 설치 및 실행

**요구 사항:** macOS (Apple Silicon / Intel), Python 3.9 이상

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### GUI (배포용)

창이 열린 뒤 약 2초 후 점검이 자동으로 시작됩니다.

```bash
python main_gui_app.py
```

### CLI

전체 점검, 빠른 점검, 개별 모듈 테스트를 선택할 수 있습니다.

```bash
python main_app.py
```

## 앱 패키징

PyInstaller로 macOS `.app` 번들을 만들 수 있습니다.

```bash
pip install pyinstaller
pyinstaller macOS_Security_Check_pyqt6.spec
```

DMG는 아래 스크립트로 생성합니다.

```bash
./create_dmg.sh           # 일반
./create_dmg_arm64.sh     # Apple Silicon
```

## 설정

업로드 정보는 `reporting/json_server_uploader.py`에서 관리합니다.  
저장소에는 값이 마스킹되어 있습니다. **실제 값은 로컬에서만 넣고 커밋하지 마세요.**

```python
FTP_SERVER = "***"
FTP_USER = "***"
FTP_PASSWORD = "***"
```

사용자 표시 이름은 MDM 관리 프로파일에서 읽습니다.

```text
/Library/Managed Preferences/com.ncskorea.userinfo.plist
```

## 출력 파일

| 실행 방식 | 저장 위치 |
|:----------|:----------|
| GUI | `/private/tmp` |
| CLI | `/Users/Shared` |

| 종류 | 파일명 |
|:-----|:-------|
| PDF 보고서 | `security_check_report_[hostname]_[timestamp].pdf` |
| JSON 로그 | `security_check_[hostname]_[timestamp].json` |
| 텍스트 로그 | `security_check_[hostname]_[timestamp].log` |

## 프로젝트 구조

```text
macos-security-check/
├── main_gui_app.py                  # GUI 진입점
├── main_app.py                      # CLI 진입점
├── requirements.txt                 # Python 의존성
├── macOS_Security_Check_pyqt6.spec  # PyInstaller 설정
├── assets/                          # 로고, 앱 아이콘
├── user_info/                       # 사용자·단말 정보 수집
├── security_checks/                 # 25개 보안 점검
├── scoring/                         # 점수·등급 계산
├── reporting/                       # PDF 생성, 결과 업로드
├── utils/                           # 명령 실행, 로깅
└── gui/                             # GUI 패키지 자리
```

`venv/`, `dist/`, `build/`, `__pycache__/` 는 `.gitignore`에 포함되어 있습니다.

## 라이선스

NCSKorea 내부 사용 전용입니다. 무단 배포 및 외부 공개를 금지합니다.

| 항목 | 내용 |
|:-----|:-----|
| 개발사 | NCSKorea |
| 버전 | 1.0 |
| 플랫폼 | macOS |
| 언어 | Python 3.9+, PyQt6 |

---

<div align="center">

### English

Internal macOS security assessment app for NCSKorea.  
It runs 25 checks, scores the result out of 100, and writes a Korean PDF report.

**Do not commit server addresses, accounts, or passwords.**

</div>

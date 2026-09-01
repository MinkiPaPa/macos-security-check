# =========================
# macOS 보안 점검 GUI 애플리케이션
# =========================

import sys
import os
from datetime import datetime
from typing import Dict, Any

# Qt 관련 로그 메시지 억제
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'

# Qt 플랫폼 플러그인 경로 설정 (macOS 호환성)
# Qt platform plugin path configuration (macOS compatibility)
import site
site_packages = site.getsitepackages()[0] if site.getsitepackages() else None
if site_packages:
    qt_plugin_path = os.path.join(site_packages, 'PyQt6', 'Qt6', 'plugins')
    if os.path.exists(qt_plugin_path):
        os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_plugin_path, 'platforms')

# reportlab이 PIL을 정상적으로 사용할 수 있도록 설정
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QProgressBar, QGroupBox,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QPixmap

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from user_info.user_data_collector import UserDataCollector
from security_checks.security_checker import SecurityChecker
from scoring.score_calculator import ScoreCalculator
from reporting.pdf_report_generator import PDFReportGenerator
from reporting.json_server_uploader import JSONServerUploader
from utils.logger import SecurityLogger
from utils.command_executor import CommandExecutor

# 저장 및 로그 파일의 공통 경로 지정
COMMON_SAVE_DIR = "/private/tmp"
os.makedirs(COMMON_SAVE_DIR, exist_ok=True)

class SecurityCheckThread(QThread):
    """보안 점검을 백그라운드에서 실행하는 스레드"""
    
    progress_update = pyqtSignal(int, str)  # 진행률, 메시지
    check_complete = pyqtSignal(bool, str)  # 성공 여부, 메시지
    log_message = pyqtSignal(str)  # 로그 메시지
    security_progress_update = pyqtSignal(int, str)  # 보안 점검 진행률 업데이트
    
    def __init__(self):
        super().__init__()
        self.user_data_collector = None
        self.security_checker = None
        self.score_calculator = None
        self.pdf_generator = None
        self.json_uploader = None
        self.logger = None
        self.command_executor = None
        
        self.user_info = {}
        self.check_results = {}
        self.score_data = {}
        self.pdf_report_path = ""
        self.json_backup_path = ""
    
    def run(self):
        """보안 점검 실행"""
        try:
            # 1. 초기화 (0% ~ 5%)
            self.log_message.emit("=== macOS 보안 점검 시작 ===")
            self.progress_update.emit(5, "초기화 중...")
            
            self.user_data_collector = UserDataCollector()
            self.security_checker = SecurityChecker()
            self.score_calculator = ScoreCalculator()
            self.pdf_generator = PDFReportGenerator()
            self.json_uploader = JSONServerUploader()
            
            hostname = os.uname().nodename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            self.logger = SecurityLogger(log_dir=COMMON_SAVE_DIR, log_file_prefix="security_check")
            log_file_path = os.path.join(COMMON_SAVE_DIR, f"command_execution_log_{hostname}_{timestamp}.txt")
            self.command_executor = CommandExecutor(log_file_path=log_file_path)
            
            self.security_checker.command_executor = self.command_executor
            
            # 2. 사용자 정보 수집 (5% ~ 10%)
            self.log_message.emit("1단계: 사용자 정보 수집")
            self.progress_update.emit(10, "사용자 정보 수집 중...")
            self.user_info = self.user_data_collector.collect_all_user_info()
            self.logger.log_user_info(self.user_info)
            
            # 3. 보안 점검 실행 (10% ~ 80%)
            self.log_message.emit("2단계: 보안 점검 실행")
            self.progress_update.emit(10, "보안 점검 실행 중...")
            
            # 실시간 진행 상황을 위한 콜백 함수 설정
            def progress_callback(message):
                self.log_message.emit(message)
            
            # 보안 점검 진행률 업데이트를 위한 콜백 함수 설정
            def progress_update_callback(percentage, message):
                self.security_progress_update.emit(percentage, message)
            
            # SecurityChecker에 콜백 함수들 전달
            self.security_checker.progress_callback = progress_callback
            self.security_checker.progress_update_callback = progress_update_callback
            
            # 보안 점검 실행 (실시간 로그 출력됨)
            self.check_results = self.security_checker.run_all_security_checks()
            
            # 보안 점검 결과 로깅 (이미 실시간으로 출력되었으므로 중복 제거)
            for check_name, result in self.check_results.items():
                status, message = result
                self.logger.log_security_check(check_name, status, message)
            
            # 4. 점수 계산 (80% ~ 85%)
            self.log_message.emit("3단계: 점수 계산")
            self.progress_update.emit(85, "점수 계산 중...")
            self.score_data = self.score_calculator.calculate_security_score(self.check_results)
            self.logger.log_score_calculation(self.score_data)
            
            # 사용자 정보에 최종 점수 업데이트
            self.user_info['보안 평가 점수'] = self.score_data['final_score']
            
            # 5. PDF 보고서 생성 (85% ~ 90%)
            self.log_message.emit("4단계: PDF 보고서 생성")
            self.progress_update.emit(90, "PDF 보고서 생성 중...")
            self.pdf_report_path = os.path.join(COMMON_SAVE_DIR, f"security_check_report_{hostname}_{timestamp}.pdf")
            
            # PDF 생성 전 디렉토리 확인 / Check directory before PDF generation
            self.log_message.emit(f"PDF 저장 경로: {self.pdf_report_path}")
            if not os.path.exists(COMMON_SAVE_DIR):
                self.log_message.emit(f"디렉토리 생성 중: {COMMON_SAVE_DIR}")
                os.makedirs(COMMON_SAVE_DIR, exist_ok=True)
            
            pdf_success = self.pdf_generator.generate_pdf_report(
                self.user_info, self.check_results, self.score_data, self.pdf_report_path
            )
            self.logger.log_report_generation("PDF", self.pdf_report_path, pdf_success)
            # PDF 생성 결과 로그 출력 / Log PDF generation result
            if pdf_success:
                # 파일 존재 여부 재확인 / Re-verify file existence
                if os.path.exists(self.pdf_report_path):
                    file_size = os.path.getsize(self.pdf_report_path)
                    self.log_message.emit(f"PDF 보고서 생성 완료: {self.pdf_report_path} (크기: {file_size} bytes)")
                else:
                    self.log_message.emit(f"PDF 보고서 생성 실패: 파일이 존재하지 않습니다. {self.pdf_report_path}")
                    pdf_success = False
            else:
                self.log_message.emit(f"PDF 보고서 생성 실패: {self.pdf_report_path}")
                # 상세 오류 정보는 콘솔에 출력됨 / Detailed error information is printed to console
            
            # PDF 생성 실패 시 경로를 None으로 설정하여 버튼 비활성화 / Set path to None on failure to disable button
            if not pdf_success:
                self.pdf_report_path = None
            
            # 6. JSON 로그 저장 (90% ~ 95%)
            self.log_message.emit("5단계: JSON 로그 저장")
            self.progress_update.emit(95, "JSON 로그 저장 중...")
            
            # JSON 로그 저장 (이것이 메인 JSON 파일)
            self.json_backup_path = self.logger.json_log_file
            self.logger.save_json_log()
            
            # 7. 서버 업로드 시도 (95% ~ 100%)
            self.log_message.emit("6단계: 서버 업로드")
            self.progress_update.emit(98, "서버 업로드 중...")

            upload_result = self.json_uploader.upload_with_fallback(
                self.user_info, self.check_results, self.score_data, None  # 별도 백업 파일 생성하지 않음
            )
            # 상태 메시지 출력 (이미 json_server_uploader에서 sanitize됨)
            if upload_result.get("success", False):
                self.log_message.emit(f"서버 업로드 성공: {upload_result.get('message', '')}")
            else:
                self.log_message.emit(f"서버 업로드 실패: {upload_result.get('message', '')}")
            self.logger.log_server_upload(upload_result)
            
            # 사용자 정보에 서버 전송 여부 추가
            self.user_info['점검 결과 서버 전송 여부'] = upload_result.get("success", False)
            
            # 완료
            self.progress_update.emit(100, "완료!")
            self.log_message.emit("=== macOS 보안 점검 완료 ===")
            self.check_complete.emit(True, "보안 점검이 성공적으로 완료되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"오류 발생: {str(e)}")
            self.check_complete.emit(False, f"보안 점검 중 오류가 발생했습니다:\n{str(e)}")


class MainWindow(QMainWindow):
    """메인 GUI 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.security_thread = None
        self.init_ui()
        # 앱 실행 시 보안 점검 자동 시작 (윈도우가 완전히 생성된 뒤에 수행)
        # QTimer.singleShot(100, self.start_security_check)  # 100ms 후 자동 실행
        QTimer.singleShot(2000, self.start_security_check)  # 2초(2000ms) 뒤에 자동 실행
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("macOS 보안 점검 도구 v1.0")
        self.setGeometry(100, 100, 900, 700)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 로고 이미지 추가 (상단 중앙) - 중앙 정렬을 위한 컨테이너 위젯 사용
        logo_container = QWidget()
        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        
        # 좌측 여백을 위한 스페이서
        logo_layout.addStretch()
        
        # 로고 라벨
        logo_label = QLabel()
        logo_path = os.path.join(project_root, "assets", "NCSK_logo.png")
        if os.path.exists(logo_path):
            # 로고 이미지 로드 및 크기 조정 (253x50 픽셀)
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(253, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # 로고 파일이 없는 경우 대체 텍스트 표시
            logo_label.setText("NCSKorea")
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #dc3545;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedSize(253, 50)
        logo_layout.addWidget(logo_label)
        
        # 우측 여백을 위한 스페이서
        logo_layout.addStretch()
        
        logo_container.setLayout(logo_layout)
        main_layout.addWidget(logo_container)
        
        # 제목
        title_label = QLabel("macOS 보안 점검 애플리케이션")
        title_font = QFont("Arial", 20, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 버전 정보
        version_label = QLabel("Version 1.0 | NCSKorea")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(version_label)
        
        # 구분선
        main_layout.addSpacing(20)
        
        # 버튼 그룹
        button_group = QGroupBox("작업 선택")
        button_layout = QHBoxLayout()
        
        # self.start_btn = QPushButton("전체 보안 점검 시작")
        # self.start_btn.setMinimumHeight(50)
        # self.start_btn.clicked.connect(self.start_security_check)
        # button_layout.addWidget(self.start_btn)
        # "전체 보안 점검 시작" 버튼을 생성하지 않음 (표시 안함)

        self.open_pdf_btn = QPushButton("PDF 보고서 열기")
        self.open_pdf_btn.setMinimumHeight(50)
        self.open_pdf_btn.setEnabled(False)
        self.open_pdf_btn.clicked.connect(self.open_pdf_report)
        button_layout.addWidget(self.open_pdf_btn)
        
        self.open_json_btn = QPushButton("JSON 파일 열기")
        self.open_json_btn.setMinimumHeight(50)
        self.open_json_btn.setEnabled(False)
        self.open_json_btn.clicked.connect(self.open_json_file)
        button_layout.addWidget(self.open_json_btn)
        
        button_group.setLayout(button_layout)
        main_layout.addWidget(button_group)
        
        # 진행률 표시
        progress_group = QGroupBox("진행 상태")
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel("대기 중...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 로그 출력
        log_group = QGroupBox("실행 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(300)
        # 로그 텍스트 스타일 설정
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                font-family: 'Monaco', 'Menlo', 'SF Mono', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 결과 요약
        result_group = QGroupBox("점검 결과 요약")
        result_layout = QVBoxLayout()
        
        self.result_label = QLabel("앱이 시작되면 자동으로 보안 점검을 진행합니다.")
        self.result_label.setWordWrap(True)
        result_layout.addWidget(self.result_label)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
    
    def start_security_check(self):
        """보안 점검 시작"""
        # 버튼 비활성화 제거 (start_btn 없음)
        self.open_pdf_btn.setEnabled(False)
        self.open_json_btn.setEnabled(False)
        
        # 로그 초기화
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("시작 중...")
        
        # 스레드 시작
        self.security_thread = SecurityCheckThread()
        self.security_thread.progress_update.connect(self.update_progress)
        self.security_thread.check_complete.connect(self.on_check_complete)
        self.security_thread.log_message.connect(self.append_log)
        self.security_thread.security_progress_update.connect(self.update_security_progress)
        self.security_thread.start()
    
    def update_progress(self, value: int, message: str):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def update_security_progress(self, value: int, message: str):
        """보안 점검 진행률 업데이트"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def append_log(self, message: str):
        """로그 메시지 추가 (타임스탬프 포함)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        # 자동 스크롤
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def on_check_complete(self, success: bool, message: str):
        """점검 완료 처리"""
        # self.start_btn.setEnabled(True)  # start_btn 없음
        
        if success:
            # 결과 요약 표시
            score_data = self.security_thread.score_data
            result_text = f"""
점검 완료!

최종 점수: {score_data['final_score']:.1f}/{score_data['max_score']}점
등급: {score_data['grade']}
통과: {score_data['pass_count']}개
경고: {score_data['warning_count']}개
오류: {score_data['error_count']}개

PDF 보고서: {self.security_thread.pdf_report_path}
JSON 백업: {self.security_thread.json_backup_path}
            """
            self.result_label.setText(result_text.strip())
            
            # PDF, JSON 버튼 활성화 (파일이 존재하는 경우에만) / Enable PDF, JSON buttons (only if files exist)
            # PDF 보고서가 생성되었고 파일이 존재하는 경우에만 활성화 / Enable only if PDF report was created and file exists
            if self.security_thread.pdf_report_path and os.path.exists(self.security_thread.pdf_report_path):
                self.open_pdf_btn.setEnabled(True)
            else:
                self.open_pdf_btn.setEnabled(False)
            
            # JSON 파일이 존재하는 경우에만 활성화 / Enable only if JSON file exists
            if self.security_thread.json_backup_path and os.path.exists(self.security_thread.json_backup_path):
                self.open_json_btn.setEnabled(True)
            else:
                self.open_json_btn.setEnabled(False)
            
            # 완료 메시지 (아이콘 제거)
            # Complete message (icon removed)
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("완료")
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Icon.NoIcon)  # 아이콘 타입 제거 / Remove icon type
            # 빈 픽셀맵으로 아이콘 완전히 제거 / Completely remove icon with empty pixmap
            empty_pixmap = QPixmap()
            msg_box.setIconPixmap(empty_pixmap)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            # 스타일시트로 아이콘 완전히 숨김 / Completely hide icon with stylesheet
            # PyQt6 스타일시트는 CSS의 display와 visibility 속성을 지원하지 않으므로 제거
            # PyQt6 stylesheet does not support CSS display and visibility properties, so removed
            msg_box.setStyleSheet("""
                QLabel[objectName='qt_msgboxex_icon_label'] { 
                    width: 0px !important; 
                    height: 0px !important; 
                    max-width: 0px !important; 
                    max-height: 0px !important; 
                    padding: 0px !important; 
                    margin: 0px !important; 
                    border: none !important; 
                }
            """)
            # 아이콘 라벨을 찾아서 숨기는 함수 / Function to find and hide icon label
            def hide_icon_label():
                """아이콘 라벨 숨기기 / Hide icon label"""
                for widget in msg_box.findChildren(QLabel):
                    # 아이콘이 있는 라벨 찾기 / Find label with icon
                    pixmap = widget.pixmap()
                    if pixmap is not None and not pixmap.isNull():
                        widget.setVisible(False)
                        widget.setFixedSize(0, 0)
                        widget.hide()
            # 다이얼로그가 표시된 후 아이콘 숨김 (타이머 사용) / Hide icon after dialog is shown (using timer)
            QTimer.singleShot(0, lambda: hide_icon_label())
            QTimer.singleShot(50, lambda: hide_icon_label())  # 한 번 더 확인 (macOS 호환성) / Check once more (macOS compatibility)
            msg_box.exec()
        else:
            self.result_label.setText("점검 실패")
            QMessageBox.critical(self, "오류", message)
    
    def open_pdf_report(self):
        """PDF 보고서 열기 / Open PDF report"""
        if self.security_thread and self.security_thread.pdf_report_path:
            # 파일 존재 여부 확인 / Check if file exists
            if os.path.exists(self.security_thread.pdf_report_path):
                os.system(f'open "{self.security_thread.pdf_report_path}"')
            else:
                # 파일이 존재하지 않을 경우 에러 메시지 표시 / Show error message if file does not exist
                QMessageBox.warning(
                    self, 
                    "파일 없음", 
                    f"PDF 보고서 파일을 찾을 수 없습니다:\n{self.security_thread.pdf_report_path}\n\n파일이 생성되지 않았거나 삭제되었을 수 있습니다."
                )
    
    def open_json_file(self):
        """JSON 파일 열기 / Open JSON file"""
        if self.security_thread and self.security_thread.json_backup_path:
            # 파일 존재 여부 확인 / Check if file exists
            if os.path.exists(self.security_thread.json_backup_path):
                os.system(f'open "{self.security_thread.json_backup_path}"')
            else:
                # 파일이 존재하지 않을 경우 에러 메시지 표시 / Show error message if file does not exist
                QMessageBox.warning(
                    self, 
                    "파일 없음", 
                    f"JSON 파일을 찾을 수 없습니다:\n{self.security_thread.json_backup_path}\n\n파일이 생성되지 않았거나 삭제되었을 수 있습니다."
                )


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 스타일 설정
    app.setStyle('Fusion')
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


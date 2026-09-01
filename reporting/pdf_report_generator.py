# =========================
# PDF 보고서 생성 모듈
# =========================

import os
import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 프로젝트 루트 디렉토리를 Python 경로에 추가
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scoring.score_calculator import ScoreCalculator


class PDFReportGenerator:
    """PDF 보고서를 생성하는 클래스"""
    
    def __init__(self):
        """PDF 보고서 생성기 초기화"""
        self.korean_font = self._register_korean_font()
        self.styles = self._create_styles()
        self.logo_path = os.path.join(project_root, 'assets', 'NCSK_logo.png')
        
        # ScoreCalculator 인스턴스 생성 (평가 로직 통일)
        from scoring.score_calculator import ScoreCalculator
        self.score_calculator = ScoreCalculator()
    
    def _register_korean_font(self) -> str:
        """
        한글 폰트를 등록하는 함수
        Korean font registration function
        
        여러 한글 폰트를 시도하여 사용 가능한 첫 번째 폰트를 등록합니다.
        Try multiple Korean fonts and register the first available one.
        """
        # 시도할 한글 폰트 목록 (우선순위 순)
        # List of Korean fonts to try (in priority order)
        font_candidates = [
            # AppleGothic 계열 (macOS 기본 한글 폰트)
            ('/System/Library/Fonts/AppleSDGothicNeo.ttc', 'AppleGothic'),
            ('/System/Library/Fonts/Supplemental/AppleGothic.ttf', 'AppleGothic'),
            
            # NanumGothic 계열
            ('/System/Library/Fonts/Supplemental/NanumGothic.ttc', 'NanumGothic'),
            ('/System/Library/AssetsV2/com_apple_MobileAsset_Font8/7a0b5c0f3c1d41c4c52a33343496c9c65ad52c50.asset/AssetData/NanumGothic.ttc', 'NanumGothic'),
            
            # Arial Unicode (한글 지원)
            ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 'ArialUnicode'),
        ]
        
        for font_path, font_name in font_candidates:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
                    # print(f"✓ 한글 폰트 등록 성공: {font_name} ({font_path})")
                    return 'KoreanFont'
                except Exception as e:
                    # print(f"✗ 폰트 등록 실패: {font_name} - {str(e)}")
                    continue
        
        # 모든 폰트 등록 실패 시 Helvetica 사용 (한글 출력 안됨)
        # print("⚠ 경고: 한글 폰트를 찾을 수 없습니다. 기본 폰트(Helvetica)를 사용합니다.")
        return 'Helvetica'
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """PDF 스타일을 생성하는 함수"""
        styles = {}
        
        # 제목 스타일
        styles['title'] = ParagraphStyle(
            'ReportTitle',
            fontName=self.korean_font,
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # 섹션 헤딩 스타일
        styles['section'] = ParagraphStyle(
            'SectionHeading',
            fontName=self.korean_font,
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # 일반 텍스트 스타일
        styles['normal'] = ParagraphStyle(
            'Normal',
            fontName=self.korean_font,
            fontSize=10,
            spaceAfter=6
        )
        
        # 테이블 헤더 스타일
        styles['table_header'] = ParagraphStyle(
            'TableHeader',
            fontName=self.korean_font,
            fontSize=11,
            alignment=TA_CENTER,
            textColor=colors.white
        )
        
        # 테이블 데이터 스타일
        styles['table_data'] = ParagraphStyle(
            'TableData',
            fontName=self.korean_font,
            fontSize=9,
            alignment=TA_LEFT
        )
        
        return styles
    
    def create_user_info_table(self, user_info: Dict[str, Any]) -> Table:
        """사용자 정보 테이블을 생성하는 함수"""
        user_data = [
            ['항목', '내용'],
            ['점검 시각', user_info.get('점검 시작', 'N/A')],
            ['Hostname', user_info.get('Hostname', user_info.get('hostname', 'N/A'))],
            ['IP 주소', user_info.get('IP 주소', 'N/A')],
            ['사용자 이름', user_info.get('사용자 이름', 'N/A')],
            ['시리얼번호', user_info.get('시리얼번호', user_info.get('serial_number', 'N/A'))],
            ['OS 정보', user_info.get('OS 정보', 'N/A')],
            ['CrowdStrike Falcon 버전', user_info.get('CrowdStrike Falcon 버전', 'N/A')],
            ['Privacy-I 버전', user_info.get('Privacy-I 버전', 'N/A')],
            ['Genian NAC 버전', user_info.get('Genian NAC 버전', 'N/A')],
            ['보안 평가 점수', f"{user_info.get('보안 평가 점수', 0)}점"]
        ]
        
        table = Table(user_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        return table
    
    def _get_correct_status_text(self, check_name: str, result: tuple) -> str:
        """
        ScoreCalculator의 평가 로직을 사용하여 올바른 상태 텍스트를 반환하는 함수
        (점수 계산과 PDF 표시가 일치하도록 보장)
        Function to return correct status text using ScoreCalculator's evaluation logic
        (ensures consistency between score calculation and PDF display)
        
        Args:
            check_name: 점검 항목명 / Check item name
            result: (status, message) 튜플 / (status, message) tuple
            
        Returns:
            str: 올바른 상태 텍스트 (안전/취약/점검 불가) / Correct status text (Safe/Vulnerable/Unable to check)
        """
        # ScoreCalculator의 평가 로직 사용 / Use ScoreCalculator's evaluation logic
        # evaluate_check_result는 (evaluation, status_text) 2개의 값을 반환합니다
        # evaluate_check_result returns 2 values: (evaluation, status_text)
        evaluation, status_text = self.score_calculator.evaluate_check_result(check_name, result)
        return status_text
    
    def create_security_check_table(self, check_results: Dict[str, Any]) -> Table:
        """보안 점검 결과 테이블을 생성하는 함수"""
        check_data = [['번호', '점검 항목', '점검 결과']]
        
        item_number = 1
        for check_name, result in check_results.items():
            status, message = result
            
            # ScoreCalculator의 평가 로직을 사용하여 상태 텍스트 가져오기
            status_text = self._get_correct_status_text(check_name, result)
            
            # 결과 상태 결정 (색상 적용)
            if status_text == "안전":
                result_text = Paragraph(f"<font color='green'>{status_text}</font>", self.styles['table_data'])
            elif status_text == "취약":
                result_text = Paragraph(f"<font color='red'>{status_text}</font>", self.styles['table_data'])
            else:
                result_text = Paragraph(f"<font color='orange'>{status_text}</font>", self.styles['table_data'])
            
            check_data.append([
                f"ITEM_{item_number:03d}",
                check_name,
                result_text
            ])
            item_number += 1
        
        table = Table(check_data, colWidths=[1*inch, 3.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        return table
    
    def create_score_summary_table(self, score_data: Dict[str, Any]) -> Table:
        """점수 요약 테이블을 생성하는 함수"""
        score_data_table = [
            ['항목', '값'],
            ['최종 점수', f"{score_data.get('final_score', 0)}/{score_data.get('max_score', 100)}점"],
            ['등급', score_data.get('grade', 'N/A')],
            ['통과', f"{score_data.get('pass_count', 0)}개"],
            ['경고', f"{score_data.get('warning_count', 0)}개"],
            ['오류', f"{score_data.get('error_count', 0)}개"]
        ]
        
        table = Table(score_data_table, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        return table
    
    def generate_pdf_report(self, 
                           user_info: Dict[str, Any], 
                           check_results: Dict[str, Any], 
                           score_data: Dict[str, Any], 
                           output_path: str) -> bool:
        """PDF 보고서를 생성하는 함수 / Function to generate PDF report"""
        try:
            # 출력 디렉토리 확인 및 생성 / Check and create output directory
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"PDF 출력 디렉토리 생성: {output_dir}")
            
            # PDF 문서 생성 / Create PDF document
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=A4,
                rightMargin=50, 
                leftMargin=50,
                topMargin=50, 
                bottomMargin=50
            )
            
            # 문서 내용 구성
            story = []
            
            # 로고 이미지 추가 (좌측 상단)
            # print(f"로고 경로 확인: {self.logo_path}")
            # print(f"파일 존재 여부: {os.path.exists(self.logo_path)}")
            
            if os.path.exists(self.logo_path):
                try:
                    logo = Image(self.logo_path)
                    # 크기 고정: 가로 244px, 세로 50px
                    # PDF 단위로 변환 (72 DPI 기준: 1 inch = 72 points)
                    logo.drawWidth = 244 * 72 / 96  # 96 DPI 기준으로 변환 (약 183 points)
                    logo.drawHeight = 50 * 72 / 96  # 96 DPI 기준으로 변환 (약 37.5 points)
                    logo.hAlign = 'LEFT'
                    story.append(logo)
                    story.append(Spacer(1, 10))
                    # print(f"로고 이미지 추가 성공: {logo.drawWidth} x {logo.drawHeight} points")
                except Exception as e:
                    # print(f"로고 이미지 로드 실패: {str(e)}")
                    # import traceback
                    # traceback.print_exc()
                    pass
            else:
                # print(f"로고 파일이 존재하지 않습니다: {self.logo_path}")
                # 로고 없이 간격만 추가
                story.append(Spacer(1, 20))
            
            # 제목
            story.append(Paragraph("macOS 보안 점검 보고서", self.styles['title']))
            story.append(Spacer(1, 20))
            
            # 1. 사용자 정보 섹션
            story.append(Paragraph("1. 사용자 정보", self.styles['section']))
            story.append(self.create_user_info_table(user_info))
            story.append(Spacer(1, 20))
            
            # 2. 점검 결과 섹션
            story.append(Paragraph("2. 점검 결과", self.styles['section']))
            story.append(self.create_security_check_table(check_results))
            story.append(Spacer(1, 20))
            
            # 3. 점수 요약 섹션
            story.append(Paragraph("3. 점수 요약", self.styles['section']))
            story.append(self.create_score_summary_table(score_data))
            story.append(Spacer(1, 20))
            
            # 4. 상세 결과 섹션
            story.append(Paragraph("4. 상세 결과", self.styles['section']))
            
            item_number = 1
            for check_name, result in check_results.items():
                status, message = result
                
                # 항목 제목
                story.append(Paragraph(f"ITEM_{item_number:03d}. {check_name}", 
                                     ParagraphStyle('ItemTitle', fontName=self.korean_font, 
                                                  fontSize=12, textColor=colors.darkblue)))
                
                # ScoreCalculator의 평가 로직을 사용하여 상태 텍스트 가져오기
                status_text_raw = self._get_correct_status_text(check_name, result)
                
                # 결과 상태 (색상 적용)
                if status_text_raw == "안전":
                    status_text = f"<font color='green'>{status_text_raw}</font>"
                    comment = "정상 상태입니다."
                elif status_text_raw == "취약":
                    status_text = f"<font color='red'>{status_text_raw}</font>"
                    comment = "보안 설정을 확인하시기 바랍니다."
                else:
                    status_text = f"<font color='orange'>{status_text_raw}</font>"
                    comment = "관리자 권한이 필요할 수 있습니다."
                
                story.append(Paragraph(f"상태: {status_text}", 
                                     ParagraphStyle('ItemStatus', fontName=self.korean_font, 
                                                  fontSize=11)))
                story.append(Paragraph(f"메시지: {message}", 
                                     ParagraphStyle('ItemMessage', fontName=self.korean_font, 
                                                  fontSize=10, leftIndent=20)))
                story.append(Paragraph(f"권고사항: {comment}", 
                                     ParagraphStyle('ItemComment', fontName=self.korean_font, 
                                                  fontSize=10, leftIndent=20)))
                story.append(Spacer(1, 10))
                item_number += 1
            
            # 문서 빌드
            doc.build(story)
            # 파일이 실제로 생성되었는지 확인 / Verify that file was actually created
            if os.path.exists(output_path):
                return True
            else:
                # 파일이 생성되지 않았음 / File was not created
                import traceback
                error_msg = f"PDF 파일이 생성되지 않았습니다. 경로: {output_path}\n{traceback.format_exc()}"
                print(f"PDF 생성 실패: {error_msg}")
                return False
            
        except Exception as e:
            # 에러 상세 정보 출력 / Print detailed error information
            import traceback
            error_msg = f"PDF 보고서 생성 중 오류 발생: {str(e)}\n경로: {output_path}\n{traceback.format_exc()}"
            print(f"PDF 생성 오류: {error_msg}")
            return False


# 테스트 함수
def test_pdf_report_generator():
    """PDF 보고서 생성기 테스트 함수"""
    generator = PDFReportGenerator()
    
    # 테스트 데이터
    user_info = {
        '점검 시작': '2024-01-01 10:00:00',
        'IP 주소': '192.168.1.100',
        '사용자 이름': 'testuser',
        '사용자 부서': 'IT부서',
        'OS 정보': 'macOS 14.0',
        'CrowdStrike Falcon 버전': '6.0.0',
        'Privacy-I 버전': '미설치',
        'Genian NAC 버전': '미설치',
        '점검 결과 서버 전송 여부': True,
        '보안 평가 점수': 85
    }
    
    check_results = {
        'CrowdStrike Falcon 설치 여부': (True, '설치됨'),
        '방화벽 활성 여부': (True, '활성화됨'),
        '게스트 계정 활성 여부': (False, '비활성화됨')
    }
    
    score_data = {
        'final_score': 85,
        'max_score': 100,
        'penalty': 15,
        'pass_count': 2,
        'warning_count': 1,
        'error_count': 0,
        'total_checks': 3,
        'grade': '양호'
    }
    
    success = generator.generate_pdf_report(
        user_info, check_results, score_data, "/tmp/test_report.pdf"
    )
    
    if success:
        print("PDF 보고서가 성공적으로 생성되었습니다.")
    else:
        print("PDF 보고서 생성에 실패했습니다.")


if __name__ == "__main__":
    test_pdf_report_generator()

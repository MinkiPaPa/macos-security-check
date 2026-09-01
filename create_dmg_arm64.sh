#!/bin/bash

# =========================
# ARM64 전용 DMG 파일 생성 스크립트
# ARM64 Only DMG File Creation Script
# =========================

echo "=== ARM64 전용 DMG 파일 생성 시작 ==="
echo "=== ARM64 Only DMG File Creation Started ==="

# DMG 파일명 설정 (ARM64 명시)
# Set DMG filename (ARM64 specified)
DMG_NAME="macOS_Security_Check_ARM64_v1.0"
DMG_PATH="dist/${DMG_NAME}.dmg"

# 이전 DMG 파일 삭제
# Remove previous DMG file
if [ -f "$DMG_PATH" ]; then
    echo "이전 DMG 파일 삭제 중..."
    echo "Removing previous DMG file..."
    rm "$DMG_PATH"
fi

# 임시 DMG 생성
# Create temporary DMG
echo "임시 DMG 생성 중..."
echo "Creating temporary DMG..."
hdiutil create -srcfolder "dist/macOS Security Check.app" -volname "macOS Security Check (ARM64)" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size 100m temp_arm64.dmg

# DMG 마운트
# Mount DMG
echo "DMG 마운트 중..."
echo "Mounting DMG..."
MOUNT_DIR="/Volumes/macOS Security Check (ARM64)"
hdiutil attach temp_arm64.dmg -readwrite -noverify -noautoopen

# DMG 설정
# Configure DMG
echo "DMG 설정 중..."
echo "Configuring DMG..."

# 심볼릭 링크 생성 (Applications 폴더로 드래그 앤 드롭 가능)
# Create symbolic link (for drag and drop to Applications folder)
ln -s /Applications "$MOUNT_DIR/Applications"

# README 파일 생성 (ARM64 전용임을 명시)
# Create README file (specify ARM64 only)
cat > "$MOUNT_DIR/README.txt" << EOF
macOS Security Check (ARM64 전용)
================================

이 앱은 Apple Silicon (M1/M2/M3) 프로세서 전용으로 빌드되었습니다.
Intel Mac에서는 실행되지 않습니다.

This app is built specifically for Apple Silicon (M1/M2/M3) processors.
It will not run on Intel Macs.

시스템 요구사항:
- macOS 11.0 이상
- Apple Silicon (M1/M2/M3) 프로세서

System Requirements:
- macOS 11.0 or later
- Apple Silicon (M1/M2/M3) processor

설치 방법:
1. 이 앱을 Applications 폴더로 드래그하세요.
2. Applications 폴더에서 앱을 실행하세요.

Installation:
1. Drag this app to the Applications folder.
2. Run the app from the Applications folder.

버전: 1.0.0
Version: 1.0.0
EOF

# DMG 언마운트
# Unmount DMG
echo "DMG 언마운트 중..."
echo "Unmounting DMG..."
hdiutil detach "$MOUNT_DIR"

# 최종 DMG 생성 (압축)
# Create final DMG (compressed)
echo "최종 DMG 생성 중..."
echo "Creating final DMG..."
hdiutil convert temp_arm64.dmg -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"

# 임시 파일 정리
# Clean up temporary files
echo "임시 파일 정리 중..."
echo "Cleaning up temporary files..."
rm temp_arm64.dmg

echo "=== ARM64 전용 DMG 생성 완료 ==="
echo "=== ARM64 Only DMG Creation Complete ==="
echo "DMG 파일 위치: $DMG_PATH"
echo "DMG file location: $DMG_PATH"
echo "파일 크기:"
echo "File size:"
ls -lh "$DMG_PATH"

# 아키텍처 정보 확인
# Check architecture information
echo ""
echo "앱 아키텍처 확인:"
echo "App architecture check:"
file "dist/macOS Security Check.app/Contents/MacOS/macOS Security Check"

#!/bin/bash

# =========================
# DMG 파일 생성 스크립트
# DMG File Creation Script
# =========================

echo "=== DMG 파일 생성 시작 ==="
echo "=== DMG File Creation Started ==="

# DMG 파일명 설정
# Set DMG filename
DMG_NAME="macOS_Security_Check_v1.0"
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
hdiutil create -srcfolder "dist/macOS Security Check.app" -volname "macOS Security Check" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size 100m temp.dmg

# DMG 마운트
# Mount DMG
echo "DMG 마운트 중..."
echo "Mounting DMG..."
MOUNT_DIR="/Volumes/macOS Security Check"
hdiutil attach temp.dmg -readwrite -noverify -noautoopen

# DMG 설정
# Configure DMG
echo "DMG 설정 중..."
echo "Configuring DMG..."

# 배경 이미지 설정 (선택사항)
# Set background image (optional)
# cp background.png "$MOUNT_DIR/"

# 심볼릭 링크 생성 (Applications 폴더로 드래그 앤 드롭 가능)
# Create symbolic link (for drag and drop to Applications folder)
ln -s /Applications "$MOUNT_DIR/Applications"

# DMG 언마운트
# Unmount DMG
echo "DMG 언마운트 중..."
echo "Unmounting DMG..."
hdiutil detach "$MOUNT_DIR"

# 최종 DMG 생성 (압축)
# Create final DMG (compressed)
echo "최종 DMG 생성 중..."
echo "Creating final DMG..."
hdiutil convert temp.dmg -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"

# 임시 파일 정리
# Clean up temporary files
echo "임시 파일 정리 중..."
echo "Cleaning up temporary files..."
rm temp.dmg

echo "=== DMG 생성 완료 ==="
echo "=== DMG Creation Complete ==="
echo "DMG 파일 위치: $DMG_PATH"
echo "DMG file location: $DMG_PATH"
echo "파일 크기:"
echo "File size:"
ls -lh "$DMG_PATH"

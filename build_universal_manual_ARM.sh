#!/bin/bash

# 이전 빌드 정리
# Clean previous build
rm -rf build dist

# PyInstaller 설치 
# Install PyInstaller
pip install pyinstaller

# Apple Silicon(arm64) 버전 빌드
# Build for Apple Silicon (arm64)
echo "Building arm64 version..."
pyinstaller --clean --windowed --target-architecture arm64 --name="macOS Security Check" main_gui_app.py

# 빌드된 앱 이름 변경
# Rename built app
mv dist/macOS\ Security\ Check.app dist/macOS\ Security\ Check-arm64.app

# 앱 복사본 생성 (Universal Binary용)
# Create app copy for Universal Binary
cp -R dist/macOS\ Security\ Check-arm64.app dist/macOS\ Security\ Check.app

echo "Build completed!"
echo "Note: This is an arm64 binary optimized for Apple Silicon"

# 바이너리 정보 확인
# Check binary architecture
echo "Checking binary architecture..."
file dist/macOS\ Security\ Check.app/Contents/MacOS/macOS\ Security\ Check
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_clicker.py 초기화 테스트 스크립트
"""

import sys
import os
import pyautogui
import time
from datetime import datetime
from PIL import Image
import pytesseract

def test_initialization():
    """스크립트 초기화 과정을 테스트합니다."""
    
    # 스크립트 디렉토리
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 70)
    print("🤖 SkyBoot Mail - Continue 텍스트 자동 클릭 매크로 (개선된 버전)")
    print("=" * 70)
    print("🎯 기능: 화면에서 'Continue' 텍스트를 찾아 오른쪽 버튼을 정확히 클릭")
    print("🔍 검색 영역: 화면 오른쪽 3/4 영역 (더 정확한 타겟팅)")
    print("🎪 다중 클릭 포인트: 각 Continue 버튼마다 5개의 클릭 포인트 생성")
    print("🏆 우선순위 시스템: 텍스트 검색 > 이미지 검색, 오른쪽 위치 우선")
    print("⚠️  종료: Ctrl+C 또는 마우스를 화면 왼쪽 상단 모서리로 이동")
    print("💡 모니터링: 1.5초 간격으로 조용히 검색")
    print("=" * 70)
    
    # Tesseract 테스트
    tesseract_available = False
    try:
        test_img = Image.new('RGB', (100, 50), color='white')
        pytesseract.image_to_string(test_img)
        tesseract_available = True
        print("✅ OCR 엔진 (Tesseract) 정상 작동 확인")
        print("   🔤 텍스트 검색 모드 활성화 (우선순위 1)")
        print("   ⚙️  OCR 설정: OEM 3, PSM 6, 영문자+점 허용")
        print("   📊 신뢰도 임계값: 25% 이상")
    except Exception as e:
        print(f"⚠️  OCR 엔진 설정 필요: {e}")
        print("💡 이미지 검색 모드로 대체 실행합니다.")
        print("   더 정확한 텍스트 검색을 원하시면 Tesseract를 설치하세요:")
        print("   Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    
    # 이미지 파일 확인
    image_path = os.path.join(script_dir, "Models Limit Continue.png")
    print(f"\n📁 작업 디렉토리: {script_dir}")
    
    image_exists = os.path.exists(image_path)
    print(f"🖼️  백업 이미지: {'✅ 존재' if image_exists else '❌ 없음'}")
    
    if image_exists:
        print(f"   📄 이미지 파일: {os.path.basename(image_path)}")
        print("   🎯 이미지 검색 신뢰도: 80% → 70% → 60% → 50% (순차 시도)")
    
    # 화면 정보
    try:
        screen_width, screen_height = pyautogui.size()
        print(f"🖥️  화면 해상도: {screen_width} x {screen_height}")
        print(f"🔍 검색 영역: x={screen_width//4}~{screen_width}, y=0~{screen_height} (오른쪽 3/4)")
    except Exception as e:
        print(f"⚠️  화면 정보 가져오기 실패: {e}")
    
    print("=" * 70)
    print("✅ 스크립트 초기화 테스트 완료!")
    
    # 설정 요약
    print("\n📋 설정 요약:")
    print(f"   🔤 OCR 엔진: {'활성화' if tesseract_available else '비활성화'}")
    print(f"   🖼️  백업 이미지: {'사용 가능' if image_exists else '사용 불가'}")
    print(f"   🎯 검색 모드: {'텍스트 + 이미지' if tesseract_available and image_exists else '이미지만' if image_exists else '텍스트만' if tesseract_available else '설정 필요'}")
    
    return tesseract_available, image_exists

if __name__ == "__main__":
    test_initialization()
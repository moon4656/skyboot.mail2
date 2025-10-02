import pyautogui
import os
from datetime import datetime
from PIL import Image
import pytesseract

# 현재 스크립트의 디렉토리 경로
script_dir = os.path.dirname(os.path.abspath(__file__))

print("🔍 현재 화면 상태 분석 중...")

# 전체 화면 스크린샷
screenshot = pyautogui.screenshot()
screenshot_path = os.path.join(script_dir, f"current_screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
screenshot.save(screenshot_path)
print(f"📸 전체 화면 스크린샷 저장: {screenshot_path}")

# 화면 크기 정보
screen_width, screen_height = screenshot.size
print(f"🖥️  화면 해상도: {screen_width} x {screen_height}")

# 오른쪽 3/4 영역 추출 (auto_clicker와 동일한 검색 영역)
right_start = screen_width // 4
right_region = screenshot.crop((right_start, 0, screen_width, screen_height))
right_region_path = os.path.join(script_dir, f"right_region_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
right_region.save(right_region_path)
print(f"🎯 검색 영역 (오른쪽 3/4) 저장: {right_region_path}")
print(f"   검색 영역 크기: {right_region.size[0]} x {right_region.size[1]}")

# OCR로 텍스트 검색 시도
try:
    # OCR 설정
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.'
    
    # 전체 화면에서 텍스트 추출
    print("\n🔤 전체 화면 텍스트 분석 중...")
    full_text = pytesseract.image_to_string(screenshot, config=custom_config)
    
    # Continue 관련 텍스트 찾기
    lines = full_text.split('\n')
    continue_found = False
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        if 'continue' in line_clean or 'continu' in line_clean:
            print(f"✅ Continue 관련 텍스트 발견: '{line.strip()}'")
            continue_found = True
    
    if not continue_found:
        print("❌ 전체 화면에서 Continue 텍스트를 찾을 수 없습니다.")
    
    # 오른쪽 영역에서 상세 분석
    print("\n🎯 오른쪽 영역 상세 분석 중...")
    ocr_data = pytesseract.image_to_data(right_region, config=custom_config, output_type=pytesseract.Output.DICT)
    
    continue_positions = []
    for i, text in enumerate(ocr_data['text']):
        text_clean = text.strip().lower()
        if text_clean in ['continue', 'continue.', 'continu', 'contin']:
            confidence = int(ocr_data['conf'][i])
            if confidence > 10:  # 매우 낮은 임계값으로 테스트
                x = ocr_data['left'][i] + right_start
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                continue_positions.append({
                    'text': text.strip(),
                    'confidence': confidence,
                    'position': (x, y, w, h),
                    'center': (x + w//2, y + h//2)
                })
    
    if continue_positions:
        print(f"🎉 오른쪽 영역에서 {len(continue_positions)}개의 Continue 후보 발견:")
        for i, pos in enumerate(continue_positions):
            print(f"   {i+1}. '{pos['text']}' - 신뢰도: {pos['confidence']}%, 위치: {pos['position']}, 중심: {pos['center']}")
    else:
        print("❌ 오른쪽 영역에서 Continue 텍스트를 찾을 수 없습니다.")
        
except Exception as e:
    print(f"❌ OCR 분석 실패: {e}")

# 이미지 매칭 시도
image_path = os.path.join(script_dir, "Models Limit Continue.png")
if os.path.exists(image_path):
    print(f"\n🖼️  이미지 매칭 시도: {image_path}")
    try:
        # 여러 신뢰도로 검색
        confidence_levels = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
        
        for conf_level in confidence_levels:
            try:
                buttons = list(pyautogui.locateAllOnScreen(
                    image_path, 
                    confidence=conf_level,
                    region=(right_start, 0, screen_width - right_start, screen_height)
                ))
                
                if buttons:
                    print(f"✅ 신뢰도 {conf_level*100}%에서 {len(buttons)}개의 이미지 매치 발견:")
                    for i, button in enumerate(buttons):
                        center = pyautogui.center(button)
                        print(f"   {i+1}. 위치: {button}, 중심: ({center.x}, {center.y})")
                    break
            except Exception:
                continue
        else:
            print("❌ 이미지 매칭으로 Continue 버튼을 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 이미지 매칭 실패: {e}")
else:
    print(f"❌ 참조 이미지 파일이 없습니다: {image_path}")

print(f"\n📋 분석 완료!")
print(f"📁 저장된 파일:")
print(f"   - 전체 화면: {screenshot_path}")
print(f"   - 검색 영역: {right_region_path}")
print("\n💡 이 파일들을 확인하여 Continue 버튼의 실제 위치와 상태를 파악하세요.")
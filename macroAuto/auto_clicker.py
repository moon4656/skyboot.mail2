import pyautogui
import time
import os
import re
from datetime import datetime
from PIL import Image
import pytesseract

# 안전 설정: 마우스를 화면 모서리로 이동하면 프로그램 중단
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5  # 각 pyautogui 함수 호출 사이에 0.5초 대기

# 현재 스크립트의 디렉토리 경로를 가져옵니다
script_dir = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("🤖 SkyBoot Mail - Continue 텍스트 자동 클릭 매크로 (대기 모드)")
print("=" * 60)
print("🔍 화면에서 'Continue' 텍스트를 찾아 오른쪽 밑줄친 버튼을 클릭합니다...")
print("⚠️  종료하려면 Ctrl+C를 누르거나 마우스를 화면 왼쪽 상단 모서리로 이동하세요.")
print("💡 텍스트가 가끔 나타나므로 오류 메시지 없이 조용히 모니터링합니다.")
print("=" * 60)

# Tesseract 설정 및 가용성 확인
TESSERACT_AVAILABLE = False
try:
    # Tesseract 테스트
    test_img = Image.new('RGB', (100, 50), color='white')
    pytesseract.image_to_string(test_img)
    TESSERACT_AVAILABLE = True
    print("✅ OCR 엔진 (Tesseract) 정상 작동 확인 - 텍스트 검색 모드")
except Exception as e:
    print(f"⚠️  OCR 엔진 설정 필요: {e}")
    print("💡 이미지 검색 모드로 대체 실행합니다.")
    print("   더 정확한 텍스트 검색을 원하시면 Tesseract를 설치하세요:")
    print("   Windows: https://github.com/UB-Mannheim/tesseract/wiki")

# 이미지 파일 경로 (백업용)
image_path = os.path.join(script_dir, "Models Limit Continue.png")

def find_continue_on_screen():
    """화면에서 'Continue' 텍스트 또는 이미지를 찾아 위치를 반환합니다."""
    continue_positions = []
    
    # 1. Tesseract가 사용 가능하면 텍스트 검색 시도
    if TESSERACT_AVAILABLE:
        try:
            # 화면 스크린샷 촬영
            screenshot = pyautogui.screenshot()
            
            # 화면 크기 가져오기
            screen_width, screen_height = screenshot.size
            
            # 오른쪽 절반만 검색 (오른쪽 Continue 버튼 우선)
            right_half = screenshot.crop((screen_width // 2, 0, screen_width, screen_height))
            
            # OCR로 텍스트 추출 (위치 정보 포함)
            ocr_data = pytesseract.image_to_data(right_half, output_type=pytesseract.Output.DICT)
            
            # 'Continue' 텍스트 찾기
            for i, text in enumerate(ocr_data['text']):
                if text.strip().lower() in ['continue', 'continue.']:
                    confidence = int(ocr_data['conf'][i])
                    if confidence > 30:  # 신뢰도 30% 이상
                        x = ocr_data['left'][i] + screen_width // 2  # 오른쪽 절반 오프셋 추가
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]
                        
                        # 텍스트 중앙 좌표 계산
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        continue_positions.append({
                            'x': center_x,
                            'y': center_y,
                            'confidence': confidence,
                            'text': text.strip(),
                            'bbox': (x, y, w, h),
                            'method': 'text'
                        })
            
            if continue_positions:
                return continue_positions
                
        except Exception:
            # 텍스트 검색 실패 시 이미지 검색으로 대체
            pass
    
    # 2. 이미지 검색 (백업 방법 또는 Tesseract 없을 때)
    try:
        if os.path.exists(image_path):
            # 화면 크기 가져오기
            screen_width, screen_height = pyautogui.size()
            
            # 오른쪽 절반에서 이미지 검색
            buttons = list(pyautogui.locateAllOnScreen(
                image_path, 
                confidence=0.6,
                region=(screen_width // 2, 0, screen_width // 2, screen_height)
            ))
            
            for button in buttons:
                center = pyautogui.center(button)
                continue_positions.append({
                    'x': center.x,
                    'y': center.y,
                    'confidence': 60,  # 기본 신뢰도
                    'text': 'Continue (이미지)',
                    'bbox': (button.left, button.top, button.width, button.height),
                    'method': 'image'
                })
                
    except Exception:
        # 조용한 모드 - 오류 메시지 출력하지 않음
        pass
    
    return continue_positions

click_count = 0
start_time = datetime.now()

while True:
    try:
        
        # 더 긴 간격으로 체크 (2초) - 가끔 나타나는 텍스트이므로
        time.sleep(2)
        
        # Continue 검색 - 조용한 모드로 검색 (텍스트 우선, 이미지 백업)
        btn = None
        continue_positions = find_continue_on_screen()
        
        if continue_positions:
            search_method = continue_positions[0]['method']
            method_text = "텍스트" if search_method == "text" else "이미지"
            print(f"🎉 Continue {method_text} 발견! (총 {len(continue_positions)}개)")
            
            # 각 항목의 위치와 신뢰도 출력
            for i, pos in enumerate(continue_positions):
                print(f"   {method_text} {i+1}: '{pos['text']}' 위치 ({pos['x']}, {pos['y']}) 신뢰도: {pos['confidence']}%")
                print(f"      바운딩 박스: {pos['bbox']} (방법: {pos['method']})")
            
            # 가장 오른쪽에 있는 항목 선택 (x 좌표가 가장 큰 것)
            rightmost_item = max(continue_positions, key=lambda pos: pos['x'])
            btn = (rightmost_item['x'], rightmost_item['y'])
            
            print(f"🎯 선택된 오른쪽 Continue {method_text}: 위치 ({btn[0]}, {btn[1]})")
            print(f"   바운딩 박스: {rightmost_item['bbox']}, 신뢰도: {rightmost_item['confidence']}%")
            print(f"   검색 방법: {rightmost_item['method']}")
            
            # 디버깅을 위한 스크린샷 저장 (첫 번째 클릭 시에만)
            if click_count == 0:
                screenshot = pyautogui.screenshot()
                screenshot_path = os.path.join(script_dir, f"debug_{search_method}_screenshot_{datetime.now().strftime('%H%M%S')}.png")
                screenshot.save(screenshot_path)
                print(f"📸 디버깅용 스크린샷 저장: {screenshot_path}")
        
        if btn:
            # 텍스트 위치 클릭
            pyautogui.click(btn[0], btn[1])
            click_count += 1
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            
            # 검색 방법 확인
            search_method = "텍스트" if rightmost_item['method'] == "text" else "이미지"
            print(f"✅ [{current_time.strftime('%H:%M:%S')}] Continue {search_method}를 클릭했습니다! (총 {click_count}회)")
            print(f"   📍 위치: ({btn[0]}, {btn[1]})")
            print(f"   🔍 검색 방법: {rightmost_item['method']}")
            print(f"   ⏱️  실행 시간: {elapsed_time}")
            
            # 클릭 후 잠시 대기
            time.sleep(1.5)
        else:
            # 30초마다 상태 출력 (너무 자주 출력하지 않도록)
            if int(time.time()) % 30 == 0:
                current_time = datetime.now()
                elapsed_time = current_time - start_time
                print(f"⏰ [{current_time.strftime('%H:%M:%S')}] 대기 중... (클릭 완료: {click_count}회, 실행 시간: {elapsed_time})")
                time.sleep(1)  # 중복 출력 방지
    except pyautogui.FailSafeException:
        print("\n🛑 안전 모드 활성화: 마우스가 화면 모서리로 이동했습니다.")
        print("프로그램을 종료합니다.")
        break
    except KeyboardInterrupt:
        print(f"\n🛑 사용자가 프로그램을 종료했습니다.")
        print(f"📊 총 {click_count}회 클릭했습니다.")
        elapsed_time = datetime.now() - start_time
        print(f"⏱️  총 실행 시간: {elapsed_time}")
        break
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        print("프로그램을 계속 실행합니다...")
        time.sleep(2)
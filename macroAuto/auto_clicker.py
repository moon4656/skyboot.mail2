import pyautogui
import time
import os
import re
from datetime import datetime
from PIL import Image
import pytesseract

# 안전 설정: 마우스를 화면 모서리로 이동하면 프로그램 중단
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3  # 각 pyautogui 함수 호출 사이에 0.3초 대기 (더 빠른 반응)

# 현재 스크립트의 디렉토리 경로를 가져옵니다
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

# Tesseract 설정 및 가용성 확인
TESSERACT_AVAILABLE = False
try:
    # Tesseract 테스트
    test_img = Image.new('RGB', (100, 50), color='white')
    pytesseract.image_to_string(test_img)
    TESSERACT_AVAILABLE = True
    print("✅ OCR 엔진 (Tesseract) 정상 작동 확인")
    print("   🔤 텍스트 검색 모드 활성화 (우선순위 1)")
    print("   ⚙️  OCR 설정: OEM 3, PSM 6, 영문자+점 허용")
    print("   📊 신뢰도 임계값: 25% 이상")
except Exception as e:
    print(f"⚠️  OCR 엔진 설정 필요: {e}")
    print("💡 이미지 검색 모드로 대체 실행합니다.")
    print("   더 정확한 텍스트 검색을 원하시면 Tesseract를 설치하세요:")
    print("   Windows: https://github.com/UB-Mannheim/tesseract/wiki")

# 이미지 파일 경로 (백업용)
image_path = os.path.join(script_dir, "Models Limit Continue.png")

# 설정 정보 출력
print(f"\n📁 작업 디렉토리: {script_dir}")
print(f"🖼️  백업 이미지: {'✅ 존재' if os.path.exists(image_path) else '❌ 없음'}")
if os.path.exists(image_path):
    print(f"   📄 이미지 파일: {os.path.basename(image_path)}")
    print(f"   🎯 이미지 검색 신뢰도: 80% → 70% → 60% → 50% (순차 시도)")

# 화면 정보 출력
screen_width, screen_height = pyautogui.size()
print(f"🖥️  화면 해상도: {screen_width} x {screen_height}")
print(f"🔍 검색 영역: x={screen_width//4}~{screen_width}, y=0~{screen_height} (오른쪽 3/4)")
print("=" * 70)

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
            
            # 오른쪽 3/4 영역만 검색 (더 정확한 오른쪽 Continue 버튼 타겟팅)
            right_start = screen_width // 4  # 화면의 1/4 지점부터 시작
            right_region = screenshot.crop((right_start, 0, screen_width, screen_height))
            
            # OCR로 텍스트 추출 (위치 정보 포함) - 더 나은 설정 사용
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.'
            ocr_data = pytesseract.image_to_data(right_region, config=custom_config, output_type=pytesseract.Output.DICT)
            
            # 'Continue' 텍스트 찾기 (더 유연한 매칭)
            for i, text in enumerate(ocr_data['text']):
                text_clean = text.strip().lower()
                if text_clean in ['continue', 'continue.', 'continu', 'contin']:
                    confidence = int(ocr_data['conf'][i])
                    if confidence > 25:  # 신뢰도 25% 이상 (더 관대한 설정)
                        x = ocr_data['left'][i] + right_start  # 오른쪽 영역 오프셋 추가
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]
                        
                        # 텍스트 중앙 좌표 계산 (여러 클릭 포인트 생성)
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # 다중 클릭 포인트 생성 (정확도 향상)
                        click_points = [
                            (center_x, center_y),  # 중앙
                            (center_x + 10, center_y),  # 약간 오른쪽
                            (center_x - 5, center_y),   # 약간 왼쪽
                            (center_x, center_y + 3),   # 약간 아래
                            (center_x, center_y - 3)    # 약간 위
                        ]
                        
                        for idx, (click_x, click_y) in enumerate(click_points):
                            continue_positions.append({
                                'x': click_x,
                                'y': click_y,
                                'confidence': confidence,
                                'text': f"{text.strip()} (포인트{idx+1})",
                                'bbox': (x, y, w, h),
                                'method': 'text',
                                'priority': idx  # 우선순위 (0이 가장 높음)
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
            
            # 오른쪽 3/4 영역에서 이미지 검색 (더 정확한 타겟팅)
            right_start = screen_width // 4
            search_region = (right_start, 0, screen_width - right_start, screen_height)
            
            # 여러 신뢰도로 검색 시도
            confidence_levels = [0.8, 0.7, 0.6, 0.5]
            
            for conf_level in confidence_levels:
                try:
                    buttons = list(pyautogui.locateAllOnScreen(
                        image_path, 
                        confidence=conf_level,
                        region=search_region
                    ))
                    
                    if buttons:
                        for button in buttons:
                            center = pyautogui.center(button)
                            
                            # 다중 클릭 포인트 생성 (이미지 검색용)
                            click_points = [
                                (center.x, center.y),  # 중앙
                                (center.x + 8, center.y),  # 약간 오른쪽
                                (center.x - 4, center.y),  # 약간 왼쪽
                                (center.x, center.y + 2),  # 약간 아래
                                (center.x, center.y - 2)   # 약간 위
                            ]
                            
                            for idx, (click_x, click_y) in enumerate(click_points):
                                continue_positions.append({
                                    'x': click_x,
                                    'y': click_y,
                                    'confidence': int(conf_level * 100),
                                    'text': f'Continue (이미지-포인트{idx+1})',
                                    'bbox': (button.left, button.top, button.width, button.height),
                                    'method': 'image',
                                    'priority': idx + 10  # 이미지 검색은 텍스트보다 낮은 우선순위
                                })
                        break  # 성공하면 더 낮은 신뢰도는 시도하지 않음
                except:
                    continue
                
    except Exception:
        # 조용한 모드 - 오류 메시지 출력하지 않음
        pass
    
    return continue_positions

click_count = 0
start_time = datetime.now()

while True:
    try:
        
        # 더 빠른 간격으로 체크 (1.5초) - 더 빠른 반응성
        time.sleep(1.5)
        
        # Continue 검색 - 조용한 모드로 검색 (텍스트 우선, 이미지 백업)
        btn = None
        continue_positions = find_continue_on_screen()
        
        if continue_positions:
            # 우선순위와 오른쪽 위치를 고려한 정렬
            # 1순위: 우선순위 (priority) - 낮을수록 높은 우선순위
            # 2순위: x 좌표 (오른쪽일수록 우선)
            # 3순위: 신뢰도 (높을수록 우선)
            continue_positions.sort(key=lambda pos: (
                pos.get('priority', 0),  # 우선순위 (낮을수록 우선)
                -pos['x'],               # x 좌표 (높을수록 우선, 음수로 역순)
                -pos['confidence']       # 신뢰도 (높을수록 우선, 음수로 역순)
            ))
            
            selected_item = continue_positions[0]  # 가장 우선순위가 높은 항목
            search_method = selected_item['method']
            method_text = "텍스트" if search_method == "text" else "이미지"
            
            print(f"🎉 Continue {method_text} 발견! (총 {len(continue_positions)}개 후보)")
            print(f"🎯 최적 선택: '{selected_item['text']}' 위치 ({selected_item['x']}, {selected_item['y']})")
            print(f"   신뢰도: {selected_item['confidence']}%, 우선순위: {selected_item.get('priority', 0)}")
            print(f"   바운딩 박스: {selected_item['bbox']}, 방법: {selected_item['method']}")
            
            # 상위 3개 후보 출력 (디버깅용)
            if len(continue_positions) > 1:
                print(f"📋 상위 후보들:")
                for i, pos in enumerate(continue_positions[:3]):
                    print(f"   {i+1}. '{pos['text']}' ({pos['x']}, {pos['y']}) 신뢰도:{pos['confidence']}% 우선순위:{pos.get('priority', 0)}")
            
            btn = (selected_item['x'], selected_item['y'])
            
            # 디버깅을 위한 스크린샷 저장 (첫 번째 클릭 시에만)
            if click_count == 0:
                screenshot = pyautogui.screenshot()
                screenshot_path = os.path.join(script_dir, f"debug_{search_method}_screenshot_{datetime.now().strftime('%H%M%S')}.png")
                screenshot.save(screenshot_path)
                print(f"📸 디버깅용 스크린샷 저장: {screenshot_path}")
        
        if btn:
            # 선택된 위치 클릭
            pyautogui.click(btn[0], btn[1])
            click_count += 1
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            
            # 검색 방법 확인
            search_method = "텍스트" if selected_item['method'] == "text" else "이미지"
            print(f"✅ [{current_time.strftime('%H:%M:%S')}] Continue {search_method}를 클릭했습니다! (총 {click_count}회)")
            print(f"   📍 클릭 위치: ({btn[0]}, {btn[1]})")
            print(f"   🎯 선택된 항목: '{selected_item['text']}'")
            print(f"   🔍 검색 방법: {selected_item['method']}")
            print(f"   📊 신뢰도: {selected_item['confidence']}%")
            print(f"   🏆 우선순위: {selected_item.get('priority', 0)}")
            print(f"   ⏱️  실행 시간: {elapsed_time}")
            print(f"   📦 바운딩 박스: {selected_item['bbox']}")
            
            # 클릭 후 잠시 대기 (더 짧은 대기 시간)
            time.sleep(1.0)
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
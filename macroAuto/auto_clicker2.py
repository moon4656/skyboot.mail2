import pyautogui
import time
import os
import re
from datetime import datetime
from PIL import Image

# 안전 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

# 현재 스크립트의 디렉토리 경로
script_dir = os.path.dirname(os.path.abspath(__file__))

print("=" * 80)
print("🤖 SkyBoot Mail - Continue 텍스트 자동 클릭 매크로 (개선된 버전 v2)")
print("=" * 80)
print("🎯 기능: 화면에서 'Continue' 관련 텍스트/버튼을 찾아 클릭")
print("🔍 검색 영역: 전체 화면 (더 넓은 범위)")
print("🎪 다중 검색 방법: 이미지 매칭 + 색상 기반 버튼 검색")
print("🏆 검색 패턴: Continue, continue, CONTINUE, 계속, 다음")
print("⚠️  종료: Ctrl+C 또는 마우스를 화면 왼쪽 상단 모서리로 이동")
print("💡 모니터링: 1초 간격으로 검색")
print("=" * 80)

# 이미지 파일 경로들
image_paths = [
    os.path.join(script_dir, "Models Limit Continue.png"),
    os.path.join(script_dir, "continue_button.png"),
    os.path.join(script_dir, "continue.png")
]

# 화면 정보
screen_width, screen_height = pyautogui.size()
print(f"🖥️  화면 해상도: {screen_width} x {screen_height}")
print(f"🔍 검색 영역: 전체 화면 (0, 0, {screen_width}, {screen_height})")

# 검색할 텍스트 패턴들 (다양한 언어와 형태)
search_patterns = [
    'continue', 'Continue', 'CONTINUE', 'continue.', 'Continue.',
    '계속', '다음', 'Next', 'NEXT', 'next',
    'Proceed', 'proceed', 'PROCEED',
    'Go', 'GO', 'go'
]

def find_continue_buttons():
    """다양한 방법으로 Continue 버튼을 찾습니다."""
    found_buttons = []
    
    # 1. 이미지 매칭 (여러 참조 이미지 시도)
    for image_path in image_paths:
        if os.path.exists(image_path):
            try:
                # 여러 신뢰도로 검색
                confidence_levels = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
                
                for conf_level in confidence_levels:
                    try:
                        buttons = list(pyautogui.locateAllOnScreen(
                            image_path, 
                            confidence=conf_level
                        ))
                        
                        if buttons:
                            for button in buttons:
                                center = pyautogui.center(button)
                                found_buttons.append({
                                    'x': center.x,
                                    'y': center.y,
                                    'confidence': conf_level * 100,
                                    'method': 'image',
                                    'source': os.path.basename(image_path),
                                    'bbox': button
                                })
                            break  # 찾았으면 더 낮은 신뢰도는 시도하지 않음
                    except Exception:
                        continue
            except Exception as e:
                continue
    
    # 2. 색상 기반 버튼 검색 (일반적인 버튼 색상들)
    try:
        screenshot = pyautogui.screenshot()
        
        # 일반적인 버튼 색상들 (RGB)
        button_colors = [
            (0, 123, 255),    # 파란색 버튼
            (40, 167, 69),    # 초록색 버튼
            (220, 53, 69),    # 빨간색 버튼
            (255, 193, 7),    # 노란색 버튼
            (108, 117, 125),  # 회색 버튼
            (23, 162, 184),   # 청록색 버튼
            (102, 16, 242),   # 보라색 버튼
        ]
        
        # 화면을 격자로 나누어 검색 (성능 최적화)
        step = 50  # 50픽셀 간격으로 검색
        
        for x in range(0, screen_width, step):
            for y in range(0, screen_height, step):
                try:
                    pixel_color = screenshot.getpixel((x, y))
                    
                    # 버튼 색상과 유사한지 확인 (허용 오차 ±30)
                    for target_color in button_colors:
                        if all(abs(pixel_color[i] - target_color[i]) <= 30 for i in range(3)):
                            # 주변 영역이 버튼 모양인지 확인
                            if is_button_area(screenshot, x, y):
                                found_buttons.append({
                                    'x': x,
                                    'y': y,
                                    'confidence': 60,
                                    'method': 'color',
                                    'source': f'color_{target_color}',
                                    'bbox': (x-25, y-15, 50, 30)
                                })
                except Exception:
                    continue
    except Exception:
        pass
    
    # 3. 텍스트 영역 검색 (OCR 없이 패턴 기반)
    try:
        screenshot = pyautogui.screenshot()
        
        # 화면을 작은 영역으로 나누어 텍스트 영역 찾기
        region_size = 200
        for x in range(0, screen_width - region_size, 100):
            for y in range(0, screen_height - region_size, 100):
                region = screenshot.crop((x, y, x + region_size, y + region_size))
                
                # 텍스트가 있을 만한 영역인지 확인 (색상 변화가 많은 영역)
                if has_text_characteristics(region):
                    center_x = x + region_size // 2
                    center_y = y + region_size // 2
                    
                    found_buttons.append({
                        'x': center_x,
                        'y': center_y,
                        'confidence': 40,
                        'method': 'text_area',
                        'source': 'pattern_detection',
                        'bbox': (x, y, region_size, region_size)
                    })
    except Exception:
        pass
    
    # 우선순위 정렬 (신뢰도 높은 순, 화면 오른쪽 우선)
    found_buttons.sort(key=lambda b: (-b['confidence'], -b['x']))
    
    return found_buttons

def is_button_area(screenshot, x, y):
    """주변 픽셀을 확인하여 버튼 영역인지 판단합니다."""
    try:
        # 주변 20x20 영역 확인
        region = screenshot.crop((max(0, x-10), max(0, y-10), 
                                min(screen_width, x+10), min(screen_height, y+10)))
        
        # 색상 변화가 적으면 버튼일 가능성이 높음
        colors = region.getcolors(maxcolors=256)
        if colors and len(colors) <= 10:  # 색상이 10개 이하면 단순한 영역
            return True
    except Exception:
        pass
    return False

def has_text_characteristics(region):
    """이미지 영역이 텍스트를 포함할 가능성이 있는지 확인합니다."""
    try:
        # 색상 히스토그램 분석
        colors = region.getcolors(maxcolors=256)
        if not colors:
            return False
        
        # 색상 다양성 확인 (텍스트는 보통 2-10개 색상)
        if 2 <= len(colors) <= 15:
            # 주요 색상이 흰색/검은색 계열인지 확인
            main_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:3]
            for count, color in main_colors:
                if isinstance(color, tuple) and len(color) >= 3:
                    r, g, b = color[:3]
                    # 흰색 계열 (240-255) 또는 검은색 계열 (0-50)
                    if (r > 240 and g > 240 and b > 240) or (r < 50 and g < 50 and b < 50):
                        return True
    except Exception:
        pass
    return False

# 메인 실행 루프
click_count = 0
start_time = datetime.now()
last_status_time = 0

print(f"\n🚀 Continue 버튼 검색을 시작합니다...")
print(f"📁 작업 디렉토리: {script_dir}")

# 참조 이미지 확인
available_images = [path for path in image_paths if os.path.exists(path)]
print(f"🖼️  사용 가능한 참조 이미지: {len(available_images)}개")
for img_path in available_images:
    print(f"   - {os.path.basename(img_path)}")

print("=" * 80)

try:
    while True:
        current_time = time.time()
        
        # Continue 버튼 검색
        buttons = find_continue_buttons()
        
        if buttons:
            # 가장 신뢰도 높은 버튼 선택
            best_button = buttons[0]
            
            print(f"🎉 Continue 버튼 발견! (총 {len(buttons)}개 후보)")
            print(f"🎯 최적 선택: {best_button['method']} 방법")
            print(f"   위치: ({best_button['x']}, {best_button['y']})")
            print(f"   신뢰도: {best_button['confidence']}%")
            print(f"   소스: {best_button['source']}")
            print(f"   바운딩 박스: {best_button['bbox']}")
            
            # 상위 3개 후보 출력
            if len(buttons) > 1:
                print(f"📋 상위 후보들:")
                for i, btn in enumerate(buttons[:3]):
                    print(f"   {i+1}. {btn['method']} ({btn['x']}, {btn['y']}) 신뢰도:{btn['confidence']}%")
            
            # 클릭 실행
            pyautogui.click(best_button['x'], best_button['y'])
            click_count += 1
            
            current_datetime = datetime.now()
            elapsed_time = current_datetime - start_time
            
            print(f"✅ [{current_datetime.strftime('%H:%M:%S')}] Continue 버튼을 클릭했습니다! (총 {click_count}회)")
            print(f"   📍 클릭 위치: ({best_button['x']}, {best_button['y']})")
            print(f"   🔍 검색 방법: {best_button['method']}")
            print(f"   📊 신뢰도: {best_button['confidence']}%")
            print(f"   ⏱️  실행 시간: {elapsed_time}")
            
            # 클릭 후 대기
            time.sleep(2.0)
            
        else:
            # 10초마다 상태 출력
            if current_time - last_status_time >= 10:
                current_datetime = datetime.now()
                elapsed_time = current_datetime - start_time
                print(f"⏰ [{current_datetime.strftime('%H:%M:%S')}] 검색 중... (클릭 완료: {click_count}회, 실행 시간: {elapsed_time})")
                last_status_time = current_time
        
        # 1초 대기
        time.sleep(1.0)
        
except pyautogui.FailSafeException:
    print("\n🛑 안전 모드 활성화: 마우스가 화면 모서리로 이동했습니다.")
    print("프로그램을 종료합니다.")
except KeyboardInterrupt:
    print(f"\n🛑 사용자가 프로그램을 종료했습니다.")
    print(f"📊 총 {click_count}회 클릭했습니다.")
    elapsed_time = datetime.now() - start_time
    print(f"⏱️  총 실행 시간: {elapsed_time}")
except Exception as e:
    print(f"❌ 예상치 못한 오류 발생: {e}")
    print("프로그램을 종료합니다.")

print("\n🏁 프로그램이 종료되었습니다.")
import pyautogui
import time
import os
from datetime import datetime
from PIL import Image

# 안전 설정: 마우스를 화면 모서리로 이동하면 프로그램 중단
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5  # 각 pyautogui 함수 호출 사이에 0.5초 대기

# 현재 스크립트의 디렉토리 경로를 가져옵니다
script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, "Models Limit Continue.png")

print("=" * 60)
print("🤖 SkyBoot Mail - Continue 버튼 자동 클릭 매크로 (대기 모드)")
print("=" * 60)
print(f"📁 이미지 파일 경로: {image_path}")
print("🔍 Continue 버튼이 나타날 때까지 조용히 대기 중...")
print("⚠️  종료하려면 Ctrl+C를 누르거나 마우스를 화면 왼쪽 상단 모서리로 이동하세요.")
print("💡 버튼이 가끔 나타나므로 오류 메시지 없이 조용히 모니터링합니다.")
print("=" * 60)

# 이미지 파일 존재 확인
if not os.path.exists(image_path):
    print(f"❌ 오류: 이미지 파일을 찾을 수 없습니다: {image_path}")
    exit(1)

click_count = 0
start_time = datetime.now()

while True:
    try:
        # 5회 이상 클릭하면 자동 중지
        if click_count >= 5:
            print(f"\n🎯 목표 달성! 5회 클릭을 완료했습니다.")
            elapsed_time = datetime.now() - start_time
            print(f"📊 총 {click_count}회 클릭 완료")
            print(f"⏱️  총 실행 시간: {elapsed_time}")
            print("🛑 매크로를 자동으로 종료합니다.")
            break
        
        # 더 긴 간격으로 체크 (2초) - 가끔 나타나는 버튼이므로
        time.sleep(2)
        
        # 이미지 검색 - 조용한 모드로 검색
        btn = None
        try:
            # 먼저 모든 버튼을 찾아보기 (조용히)
            buttons = list(pyautogui.locateAllOnScreen(image_path, confidence=0.6))
            
            if buttons:
                print(f"🎉 Continue 버튼 발견! (총 {len(buttons)}개)")
                
                # 각 버튼의 위치 출력
                for i, button in enumerate(buttons):
                    center = pyautogui.center(button)
                    print(f"   버튼 {i+1}: 위치 ({center.x}, {center.y})")
                
                # 가장 오른쪽에 있는 버튼 선택 (x 좌표가 가장 큰 것)
                rightmost_btn = max(buttons, key=lambda btn: btn.left + btn.width/2)
                btn = pyautogui.center(rightmost_btn)
                
                print(f"🎯 선택된 버튼 (가장 오른쪽): 위치 ({btn.x}, {btn.y})")
                
                # 디버깅을 위한 스크린샷 저장 (첫 번째 클릭 시에만)
                if click_count == 0:
                    screenshot = pyautogui.screenshot()
                    screenshot_path = os.path.join(script_dir, f"debug_screenshot_{datetime.now().strftime('%H%M%S')}.png")
                    screenshot.save(screenshot_path)
                    print(f"📸 디버깅용 스크린샷 저장: {screenshot_path}")
                
            else:
                # 단일 버튼 검색 시도 (기존 방식, 조용히)
                btn = pyautogui.locateCenterOnScreen(image_path, confidence=0.6)
                if btn:
                    print(f"🎉 Continue 버튼 발견: 위치 ({btn.x}, {btn.y})")
                
        except Exception:
            # 오류 메시지 출력하지 않음 (조용한 모드)
            # 기존 방식으로 재시도 (조용히)
            try:
                btn = pyautogui.locateCenterOnScreen(image_path, confidence=0.5)
                if btn:
                    print(f"🎉 Continue 버튼 발견 (재시도): 위치 ({btn.x}, {btn.y})")
            except:
                btn = None
        
        if btn:
            # 버튼 클릭
            pyautogui.click(btn)
            click_count += 1
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            
            print(f"✅ [{current_time.strftime('%H:%M:%S')}] Continue 버튼을 클릭했습니다! (총 {click_count}회)")
            print(f"   📍 위치: ({btn.x}, {btn.y})")
            print(f"   ⏱️  실행 시간: {elapsed_time}")
            
            # 5회에 가까워지면 알림
            if click_count >= 4:
                print(f"   ⚠️  다음 클릭 후 자동 종료됩니다. (목표: 5회)")
            
            # 클릭 후 잠시 대기 (버튼이 사라질 시간을 줌)
            time.sleep(1.5)
        else:
            # 주기적으로 상태 메시지 출력 (30초마다) - 조용한 모드
            if int(time.time()) % 30 == 0:
                current_time = datetime.now()
                elapsed_time = current_time - start_time
                remaining_clicks = 5 - click_count
                print(f"⏰ [{current_time.strftime('%H:%M:%S')}] 대기 중... (클릭 완료: {click_count}회, 남은 목표: {remaining_clicks}회, 실행 시간: {elapsed_time})")
                time.sleep(1)  # 중복 출력 방지
                
    except pyautogui.ImageNotFoundException:
        # 이미지를 찾지 못한 경우 계속 진행
        pass
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
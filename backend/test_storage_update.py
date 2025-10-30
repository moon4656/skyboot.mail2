#!/usr/bin/env python3
"""
저장 용량 업데이트 메서드 테스트 스크립트
"""

import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.service.mail_service import MailService
import inspect

async def test_storage_update():
    """저장 용량 업데이트 메서드 테스트"""
    print("📊 저장 용량 업데이트 메서드 테스트 시작...")
    
    try:
        # 데이터베이스 세션 생성
        db = next(get_db())
        
        # MailService 인스턴스 생성
        mail_service = MailService(db=db)
        
        # _update_user_storage_usage 메서드 시그니처 확인
        method = getattr(mail_service, '_update_user_storage_usage')
        sig = inspect.signature(method)
        print(f"🔍 메서드 시그니처: {sig}")
        
        # 파라미터 목록 출력
        for param_name, param in sig.parameters.items():
            print(f"  - {param_name}: {param.annotation} = {param.default}")
        
        # 테스트 호출 (실제로는 실행하지 않음)
        print("\n✅ 메서드 시그니처 확인 완료")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(test_storage_update())
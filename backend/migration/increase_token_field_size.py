"""
refresh_tokens 테이블의 token 필드 크기 증가 마이그레이션
JWT 토큰이 255자를 초과할 수 있으므로 TEXT 타입으로 변경
"""

from app.database import engine
from sqlalchemy import text

def upgrade_token_field():
    """token 필드를 VARCHAR(255)에서 TEXT로 변경"""
    with engine.connect() as conn:
        try:
            print('refresh_tokens 테이블의 token 필드 크기를 증가시키는 중...')
            
            # 현재 token 필드 상태 확인
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'refresh_tokens' AND column_name = 'token'
            """))
            current_info = result.fetchone()
            
            if current_info:
                print(f'현재 token 필드: {current_info[1]}({current_info[2]})')
            
            # token 필드를 TEXT 타입으로 변경
            conn.execute(text("""
                ALTER TABLE refresh_tokens 
                ALTER COLUMN token TYPE TEXT
            """))
            conn.commit()
            
            # 변경 후 상태 확인
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'refresh_tokens' AND column_name = 'token'
            """))
            new_info = result.fetchone()
            
            if new_info:
                print(f'변경된 token 필드: {new_info[1]}({new_info[2]})')
            
            print('✅ refresh_tokens 테이블의 token 필드가 TEXT 타입으로 성공적으로 변경되었습니다!')
            
        except Exception as e:
            print(f'❌ 마이그레이션 오류 발생: {e}')
            conn.rollback()
            raise

def downgrade_token_field():
    """token 필드를 TEXT에서 VARCHAR(255)로 되돌리기 (롤백용)"""
    with engine.connect() as conn:
        try:
            print('refresh_tokens 테이블의 token 필드를 VARCHAR(255)로 되돌리는 중...')
            
            # 현재 저장된 토큰들의 길이 확인
            result = conn.execute(text("""
                SELECT MAX(LENGTH(token)) as max_length 
                FROM refresh_tokens 
                WHERE token IS NOT NULL
            """))
            max_length = result.fetchone()
            
            if max_length and max_length[0] and max_length[0] > 255:
                print(f'⚠️  경고: 현재 저장된 토큰 중 최대 길이가 {max_length[0]}자입니다.')
                print('VARCHAR(255)로 되돌리면 데이터 손실이 발생할 수 있습니다.')
                return False
            
            # token 필드를 VARCHAR(255)로 변경
            conn.execute(text("""
                ALTER TABLE refresh_tokens 
                ALTER COLUMN token TYPE VARCHAR(255)
            """))
            conn.commit()
            
            print('✅ refresh_tokens 테이블의 token 필드가 VARCHAR(255)로 성공적으로 되돌려졌습니다!')
            return True
            
        except Exception as e:
            print(f'❌ 롤백 오류 발생: {e}')
            conn.rollback()
            raise

if __name__ == "__main__":
    # 마이그레이션 실행
    upgrade_token_field()
    
    # 변경 결과 확인
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'refresh_tokens' AND column_name = 'token'
        """))
        info = result.fetchone()
        print(f'\n최종 확인 - token 필드: {info[1]}({info[2]})')
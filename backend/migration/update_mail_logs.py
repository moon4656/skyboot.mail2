from app.database import engine
from sqlalchemy import text

# mail_logs 테이블의 user_id를 UUID로 업데이트
with engine.connect() as conn:
    try:
        print('mail_logs 테이블의 user_id를 UUID로 업데이트 중...')
        
        # 먼저 현재 mail_logs 데이터 확인
        result = conn.execute(text('SELECT COUNT(*) FROM mail_logs;'))
        count = result.scalar()
        print(f'mail_logs 테이블의 레코드 수: {count}')
        
        if count > 0:
            # 1. 임시 컬럼 생성
            conn.execute(text('ALTER TABLE mail_logs ADD COLUMN temp_user_id VARCHAR(36);'))
            conn.commit()
            
            # 2. 기존 정수 user_id를 기반으로 해당 사용자의 UUID를 temp_user_id에 복사
            result = conn.execute(text('SELECT id, user_id FROM mail_logs;'))
            mail_logs = result.fetchall()
            
            print(f'업데이트할 mail_log 수: {len(mail_logs)}')
            
            # 각 mail_log의 user_id를 UUID로 매핑
            user_mapping = {
                1: '00bfa008-6998-454e-b51c-eaa1be90ff67',
                2: '9b95bfc4-8d6d-43af-884e-92999766e1f3', 
                3: 'a7da04c6-cd3c-42e5-9b2a-60e4669c83a5',
                4: 'c58fac92-0d48-41e1-8a23-95ac330de7ed',
                5: '144866c6-8b62-4ed0-b434-d7ed7442dcd9',
                6: '4fe09109-7c32-4406-bf15-c6e2a9b26479',
                7: 'd8b8fe27-fdf0-48b1-904a-2b1b1fdcf6c9',
                8: '5c055e59-6419-49d2-8fb7-be9318c4ae91'
            }
            
            for log_id, old_user_id in mail_logs:
                if old_user_id in user_mapping:
                    new_user_uuid = user_mapping[old_user_id]
                    conn.execute(text(
                        'UPDATE mail_logs SET temp_user_id = :uuid WHERE id = :log_id'
                    ), {'uuid': new_user_uuid, 'log_id': log_id})
                    print(f'Log ID {log_id}: user_id {old_user_id} -> {new_user_uuid}')
            
            conn.commit()
            
            # 3. 기존 user_id 컬럼 삭제
            conn.execute(text('ALTER TABLE mail_logs DROP COLUMN user_id;'))
            conn.commit()
            
            # 4. temp_user_id를 user_id로 이름 변경
            conn.execute(text('ALTER TABLE mail_logs RENAME COLUMN temp_user_id TO user_id;'))
            conn.commit()
            
            print('✅ mail_logs 테이블의 user_id가 UUID로 성공적으로 변경되었습니다!')
        else:
            print('mail_logs 테이블에 데이터가 없습니다. 스키마만 변경합니다.')
            
            # 데이터가 없는 경우 컬럼 타입만 변경
            conn.execute(text('ALTER TABLE mail_logs ALTER COLUMN user_id TYPE VARCHAR(36);'))
            conn.commit()
            print('✅ mail_logs 테이블의 user_id 컬럼 타입이 VARCHAR(36)으로 변경되었습니다!')
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        conn.rollback()

# 변경 결과 확인
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM mail_logs;'))
    count = result.scalar()
    print(f'\n변경 결과 확인: mail_logs 테이블 레코드 수: {count}')
    
    if count > 0:
        result = conn.execute(text('SELECT id, user_id, recipient, subject FROM mail_logs LIMIT 5;'))
        logs = result.fetchall()
        for log_id, user_id, recipient, subject in logs:
            print(f'Log ID: {log_id}, User ID(UUID): {user_id}, Recipient: {recipient}, Subject: {subject}')
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최소한의 이메일 첨부파일 처리 테스트
Python email 라이브러리의 동작을 직접 확인하여 bytes/str 오류 원인 파악
"""

import os
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import urllib.parse

def test_email_creation():
    """이메일 생성 및 첨부파일 처리 테스트"""
    print("🧪 최소한의 이메일 첨부파일 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. 테스트 파일 생성
        print("📄 테스트 파일 생성 중...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("이것은 테스트 첨부파일입니다.\nThis is a test attachment file.\n한글 파일명 테스트")
            test_file_path = f.name
        
        print(f"✅ 테스트 파일 생성 완료: {test_file_path}")
        
        # 2. MIMEMultipart 메시지 생성
        print("📧 MIMEMultipart 메시지 생성 중...")
        msg = MIMEMultipart()
        msg['From'] = "test@example.com"
        msg['To'] = "recipient@example.com"
        msg['Subject'] = "테스트 메일 - 첨부파일 포함"
        
        # 3. 텍스트 본문 추가
        print("📝 텍스트 본문 추가 중...")
        body = "이것은 첨부파일이 포함된 테스트 메일입니다."
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 4. 첨부파일 처리
        print("📎 첨부파일 처리 시작...")
        filename = "테스트_첨부파일.txt"  # 한글 파일명으로 테스트
        
        print(f"📎 파일 읽기: {test_file_path}")
        with open(test_file_path, "rb") as f:
            file_content = f.read()
            print(f"📎 파일 내용 읽기 완료 - 크기: {len(file_content)} bytes")
            print(f"📎 파일 내용 타입: {type(file_content)}")
        
        # MIMEBase 객체 생성
        print("📎 MIMEBase 객체 생성...")
        part = MIMEBase('application', 'octet-stream')
        print(f"📎 MIMEBase 객체 타입: {type(part)}")
        
        # 페이로드 설정
        print("📎 페이로드 설정...")
        part.set_payload(file_content)
        print("📎 페이로드 설정 완료")
        
        # Base64 인코딩
        print("📎 Base64 인코딩...")
        encoders.encode_base64(part)
        print("📎 Base64 인코딩 완료")
        
        # 파일명 헤더 설정 테스트
        print("📎 파일명 헤더 설정 테스트...")
        print(f"📎 원본 파일명: {filename}")
        print(f"📎 파일명 타입: {type(filename)}")
        
        try:
            # ASCII 인코딩 테스트
            filename.encode('ascii')
            print("📎 ASCII 인코딩 가능")
            header_value = f'attachment; filename="{filename}"'
            print(f"📎 ASCII 헤더 값: {header_value}")
            part.add_header('Content-Disposition', header_value)
            print("📎 ASCII 헤더 추가 완료")
        except UnicodeEncodeError:
            print("📎 ASCII 인코딩 불가능 - RFC 2231 사용")
            encoded_filename = urllib.parse.quote(filename, safe='')
            print(f"📎 URL 인코딩된 파일명: {encoded_filename}")
            print(f"📎 인코딩된 파일명 타입: {type(encoded_filename)}")
            header_value = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
            print(f"📎 RFC 2231 헤더 값: {header_value}")
            print(f"📎 헤더 값 타입: {type(header_value)}")
            part.add_header('Content-Disposition', header_value)
            print("📎 RFC 2231 헤더 추가 완료")
        
        # 메시지에 첨부파일 추가
        print("📎 메시지에 첨부파일 추가...")
        msg.attach(part)
        print("📎 첨부파일 추가 완료")
        
        # 5. 메시지 문자열 변환 테스트
        print("📧 메시지 문자열 변환 테스트...")
        try:
            msg_str = msg.as_string()
            print(f"✅ 메시지 문자열 변환 성공 - 길이: {len(msg_str)}")
            print(f"📧 메시지 문자열 타입: {type(msg_str)}")
            
            # 바이트 변환 테스트
            print("📧 메시지 바이트 변환 테스트...")
            msg_bytes = msg_str.encode('utf-8')
            print(f"✅ 메시지 바이트 변환 성공 - 길이: {len(msg_bytes)}")
            print(f"📧 메시지 바이트 타입: {type(msg_bytes)}")
            
        except Exception as convert_error:
            print(f"❌ 메시지 변환 실패: {str(convert_error)}")
            print(f"❌ 오류 타입: {type(convert_error).__name__}")
            import traceback
            print(f"❌ 스택 트레이스: {traceback.format_exc()}")
            raise
        
        print("✅ 모든 테스트 완료 - 문제 없음")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        print(f"❌ 오류 타입: {type(e).__name__}")
        import traceback
        print(f"❌ 상세 스택 트레이스: {traceback.format_exc()}")
    
    finally:
        # 테스트 파일 정리
        if 'test_file_path' in locals() and os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print(f"🗑️ 테스트 파일 삭제: {test_file_path}")

if __name__ == "__main__":
    test_email_creation()
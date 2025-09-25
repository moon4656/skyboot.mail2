#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한글 메일 디코더 스크립트
quoted-printable 및 base64로 인코딩된 한글 메일을 올바르게 디코딩합니다.
"""

import quopri
import base64
import re
import email
from email.header import decode_header
import subprocess
import sys

def decode_quoted_printable(text):
    """
    quoted-printable 인코딩된 텍스트를 디코딩합니다.
    
    Args:
        text: quoted-printable 인코딩된 텍스트
    
    Returns:
        디코딩된 UTF-8 텍스트
    """
    try:
        # quoted-printable 디코딩
        decoded_bytes = quopri.decodestring(text.encode('ascii'))
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        print(f"❌ quoted-printable 디코딩 오류: {e}")
        return text

def decode_mail_subject(subject):
    """
    메일 제목의 인코딩을 디코딩합니다.
    
    Args:
        subject: 인코딩된 메일 제목
    
    Returns:
        디코딩된 제목
    """
    try:
        decoded_parts = decode_header(subject)
        decoded_subject = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_subject += part.decode(encoding)
                else:
                    decoded_subject += part.decode('utf-8')
            else:
                decoded_subject += part
        
        return decoded_subject
    except Exception as e:
        print(f"❌ 제목 디코딩 오류: {e}")
        return subject

def read_and_decode_mail(mailbox_path):
    """
    메일박스 파일을 읽고 한글 내용을 디코딩합니다.
    
    Args:
        mailbox_path: 메일박스 파일 경로
    """
    try:
        # WSL을 통해 메일박스 파일 읽기
        result = subprocess.run(
            ['wsl', 'cat', mailbox_path],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            print(f"❌ 메일박스 읽기 실패: {result.stderr}")
            return
        
        mail_content = result.stdout
        
        # 메일을 개별적으로 분리
        mails = mail_content.split('\nFrom ')
        
        print(f"📧 총 {len(mails)}개의 메일을 발견했습니다.\n")
        
        for i, mail_text in enumerate(mails):
            if i > 0:  # 첫 번째가 아닌 경우 'From ' 다시 추가
                mail_text = 'From ' + mail_text
            
            if not mail_text.strip():
                continue
                
            print(f"{'='*60}")
            print(f"📬 메일 #{i+1}")
            print(f"{'='*60}")
            
            try:
                # 이메일 파싱
                msg = email.message_from_string(mail_text)
                
                # 헤더 정보 출력
                print(f"📤 발송자: {msg.get('From', 'Unknown')}")
                print(f"📥 수신자: {msg.get('To', 'Unknown')}")
                print(f"📅 날짜: {msg.get('Date', 'Unknown')}")
                
                # 제목 디코딩
                subject = msg.get('Subject', 'No Subject')
                decoded_subject = decode_mail_subject(subject)
                print(f"📋 제목: {decoded_subject}")
                
                print(f"🔧 Content-Type: {msg.get('Content-Type', 'Unknown')}")
                print(f"🔧 Content-Transfer-Encoding: {msg.get('Content-Transfer-Encoding', 'Unknown')}")
                
                # 메일 본문 처리
                if msg.is_multipart():
                    print("\n📄 메일 본문 (멀티파트):")
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload()
                            if part.get('Content-Transfer-Encoding') == 'quoted-printable':
                                decoded_content = decode_quoted_printable(payload)
                                print(f"✅ 디코딩된 내용:\n{decoded_content}")
                            else:
                                print(f"📝 원본 내용:\n{payload}")
                else:
                    print("\n📄 메일 본문:")
                    payload = msg.get_payload()
                    encoding = msg.get('Content-Transfer-Encoding', '')
                    
                    if encoding == 'quoted-printable':
                        decoded_content = decode_quoted_printable(payload)
                        print(f"✅ 디코딩된 내용:\n{decoded_content}")
                    elif encoding == 'base64':
                        try:
                            decoded_bytes = base64.b64decode(payload)
                            decoded_content = decoded_bytes.decode('utf-8')
                            print(f"✅ 디코딩된 내용:\n{decoded_content}")
                        except Exception as e:
                            print(f"❌ base64 디코딩 오류: {e}")
                            print(f"📝 원본 내용:\n{payload}")
                    else:
                        print(f"📝 원본 내용:\n{payload}")
                
                print("\n")
                
            except Exception as e:
                print(f"❌ 메일 파싱 오류: {e}")
                print(f"📝 원본 텍스트:\n{mail_text[:500]}...")
                print("\n")
        
    except Exception as e:
        print(f"❌ 전체 처리 오류: {e}")

def main():
    """메인 함수"""
    print("🔍 한글 메일 디코더 시작")
    print("=" * 50)
    
    # testuser 메일박스 경로
    mailbox_path = "/var/spool/mail/testuser"
    
    print(f"📂 메일박스 경로: {mailbox_path}")
    print(f"🔄 메일 디코딩 시작...\n")
    
    read_and_decode_mail(mailbox_path)
    
    print("✅ 메일 디코딩 완료!")

if __name__ == "__main__":
    main()
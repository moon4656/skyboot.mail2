# WSL 메일 발송 설정 가이드

## 📋 개요
이 문서는 SkyBoot Mail SaaS 시스템에서 WSL(Windows Subsystem for Linux) 환경의 Postfix SMTP 서버를 통한 메일 발송 설정 및 테스트 방법을 설명합니다.

## 🏗️ 아키텍처 구성

### 시스템 구조
```
Windows 환경
├── SkyBoot Mail Backend (FastAPI)
│   ├── Gmail SMTP (개발용)
│   └── WSL Postfix SMTP (프로덕션용)
└── WSL Ubuntu
    ├── Postfix (SMTP 서버)
    ├── Dovecot (IMAP/POP3 서버)
    └── PostgreSQL (메일 데이터베이스)
```

### 네트워크 설정
- **WSL IP**: `172.18.0.233`
- **SMTP 포트**: `25`
- **IMAP 포트**: `143`
- **POP3 포트**: `110`

## 🔧 WSL Postfix 설정

### 1. Postfix 설치 및 기본 설정
```bash
# WSL Ubuntu에서 실행
sudo apt update
sudo apt install postfix postfix-pgsql

# Postfix 설정 파일 편집
sudo nano /etc/postfix/main.cf
```

### 2. 주요 설정 파라미터
```conf
# /etc/postfix/main.cf
myhostname = mail.skyboot.local
mydomain = skyboot.local
myorigin = $mydomain
inet_interfaces = all
inet_protocols = ipv4
mydestination = $myhostname, localhost.$mydomain, localhost, $mydomain

# 가상 도메인 설정
virtual_mailbox_domains = pgsql:/etc/postfix/pgsql-virtual-mailbox-domains.cf
virtual_mailbox_maps = pgsql:/etc/postfix/pgsql-virtual-mailbox-maps.cf
virtual_alias_maps = pgsql:/etc/postfix/pgsql-virtual-alias-maps.cf

# 메일박스 설정
virtual_mailbox_base = /var/mail/vhosts
virtual_minimum_uid = 100
virtual_uid_maps = static:5000
virtual_gid_maps = static:5000

# SMTP 인증 설정
smtpd_sasl_auth_enable = yes
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
```

### 3. PostgreSQL 연동 설정
```conf
# /etc/postfix/pgsql-virtual-mailbox-domains.cf
user = postfix
password = your_password
hosts = localhost
dbname = skyboot_mail
query = SELECT 1 FROM virtual_domains WHERE name='%s' AND is_active=true

# /etc/postfix/pgsql-virtual-mailbox-maps.cf
user = postfix
password = your_password
hosts = localhost
dbname = skyboot_mail
query = SELECT 1 FROM users WHERE email='%s' AND is_active=true

# /etc/postfix/pgsql-virtual-alias-maps.cf
user = postfix
password = your_password
hosts = localhost
dbname = skyboot_mail
query = SELECT destination FROM virtual_aliases WHERE source='%s' AND is_active=true
```

## 🧪 WSL SMTP 연결 테스트

### 테스트 스크립트 실행
```bash
# Windows PowerShell에서 실행
cd C:\Users\eldorado\skyboot.mail2\backend
python test_smtp_wsl.py
```

### 테스트 과정
1. **소켓 연결 테스트**: WSL IP와 포트 25 연결 확인
2. **SMTP 프로토콜 테스트**: EHLO 명령어 실행
3. **메일 발송 테스트**: 테스트 메일 발송 및 응답 확인

### 예상 출력
```
🚀 SkyBoot Mail WSL Postfix SMTP 테스트
============================================================
🔍 SMTP 서버 연결 테스트 시작
📍 서버: 172.18.0.233:25
--------------------------------------------------
1️⃣ 소켓 연결 테스트...
✅ 소켓 연결 성공: 172.18.0.233:25
2️⃣ SMTP 프로토콜 연결 테스트...
📡 SMTP 서버 연결 중: 172.18.0.233:25
👋 SMTP 서버 인사...
✅ SMTP 연결 성공!
3️⃣ 테스트 메일 발송...
✅ 테스트 메일 발송 성공!
🎉 모든 테스트 완료!

🎊 테스트 성공! WSL Postfix SMTP 서버가 정상 작동합니다.
```

## 📧 메일 발송 구현

### Python 코드 예시
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_mail_via_wsl(sender, recipient, subject, content):
    """WSL Postfix를 통한 메일 발송"""
    
    # WSL SMTP 서버 설정
    smtp_host = "172.18.0.233"
    smtp_port = 25
    
    try:
        # SMTP 서버 연결
        server = smtplib.SMTP(smtp_host, smtp_port)
        
        # 메일 구성
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # 본문 추가
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        # 메일 발송
        text = msg.as_string()
        server.sendmail(sender, [recipient], text)
        server.quit()
        
        return {"success": True, "message": "메일 발송 성공"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### FastAPI 통합
```python
# app/service/mail_service.py
class MailService:
    def __init__(self):
        self.wsl_smtp_host = "172.18.0.233"
        self.wsl_smtp_port = 25
        
    async def send_mail_wsl(self, mail_data: MailSendRequest):
        """WSL Postfix를 통한 메일 발송"""
        
        try:
            # SMTP 연결 및 발송
            server = smtplib.SMTP(self.wsl_smtp_host, self.wsl_smtp_port)
            
            # 메일 구성 및 발송
            # ... 메일 발송 로직
            
            return MailSendResponse(
                success=True,
                message="WSL Postfix를 통한 메일 발송 성공",
                mail_id=mail_id
            )
            
        except Exception as e:
            logger.error(f"WSL 메일 발송 실패: {e}")
            return MailSendResponse(
                success=False,
                error=str(e)
            )
```

## 🔧 환경 설정

### .env 파일 설정
```env
# WSL SMTP 설정 (프로덕션용)
WSL_SMTP_HOST=172.18.0.233
WSL_SMTP_PORT=25
WSL_SMTP_USE_TLS=false
WSL_SMTP_USE_SSL=false

# Gmail SMTP 설정 (개발용)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=moon4656@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
```

### 설정 분기 처리
```python
# app/config.py
import os

class Settings:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        if self.environment == "production":
            # WSL Postfix 설정
            self.smtp_host = os.getenv("WSL_SMTP_HOST", "172.18.0.233")
            self.smtp_port = int(os.getenv("WSL_SMTP_PORT", "25"))
            self.smtp_use_tls = False
            self.smtp_use_ssl = False
        else:
            # Gmail SMTP 설정 (개발용)
            self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            self.smtp_use_tls = True
            self.smtp_use_ssl = False
```

## 🚨 문제 해결

### 일반적인 오류 및 해결책

#### 1. 연결 거부 오류
```
❌ 연결 거부: 172.18.0.233:25
```
**해결책**:
- WSL에서 Postfix 서비스 상태 확인: `sudo systemctl status postfix`
- Postfix 재시작: `sudo systemctl restart postfix`
- 방화벽 설정 확인: `sudo ufw status`

#### 2. 타임아웃 오류
```
❌ 연결 타임아웃: 172.18.0.233:25
```
**해결책**:
- WSL IP 주소 확인: `ip addr show eth0`
- Windows 방화벽 설정 확인
- WSL 네트워크 재시작: `wsl --shutdown` 후 재시작

#### 3. SMTP 인증 오류
```
❌ SMTP 오류: (535, '5.7.8 Error: authentication failed')
```
**해결책**:
- Dovecot SASL 설정 확인
- 사용자 인증 정보 확인
- PostgreSQL 연동 설정 점검

### 로그 확인
```bash
# Postfix 로그 확인
sudo tail -f /var/log/mail.log

# Dovecot 로그 확인
sudo tail -f /var/log/dovecot.log

# PostgreSQL 로그 확인
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## 📊 성능 모니터링

### 메일 발송 성능 측정
```python
import time
import asyncio

async def benchmark_wsl_smtp():
    """WSL SMTP 성능 벤치마크"""
    
    start_time = time.time()
    
    # 100개 메일 발송 테스트
    tasks = []
    for i in range(100):
        task = send_mail_via_wsl(
            sender="test@skyboot.mail",
            recipient="admin@skyboot.mail",
            subject=f"성능 테스트 {i+1}",
            content="WSL SMTP 성능 테스트 메일입니다."
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    success_count = sum(1 for r in results if r["success"])
    
    print(f"📊 성능 테스트 결과:")
    print(f"   총 메일 수: 100개")
    print(f"   성공: {success_count}개")
    print(f"   실패: {100 - success_count}개")
    print(f"   총 소요 시간: {duration:.2f}초")
    print(f"   평균 처리 시간: {duration/100:.3f}초/메일")
```

## 🔐 보안 고려사항

### 1. 네트워크 보안
- WSL과 Windows 간 통신 암호화
- 방화벽 규칙 최소 권한 원칙
- 포트 접근 제한

### 2. 인증 보안
- SASL 인증 강화
- 패스워드 정책 적용
- 접속 로그 모니터링

### 3. 메일 보안
- SPF, DKIM, DMARC 설정
- 스팸 필터링 강화
- 첨부파일 검사

## 📚 참고 자료

- [Postfix 공식 문서](http://www.postfix.org/documentation.html)
- [Dovecot 설정 가이드](https://doc.dovecot.org/)
- [WSL 네트워킹 가이드](https://docs.microsoft.com/en-us/windows/wsl/networking)
- [SkyBoot Mail 프로젝트 규칙](../.trae/rules/project_rules.md)

---

**작성일**: 2025년 1월 15일  
**버전**: 1.0  
**작성자**: SkyBoot Mail 개발팀
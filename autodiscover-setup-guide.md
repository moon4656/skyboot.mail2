# 📧 SkyBoot Mail - Outlook Autodiscover 설정 가이드

## 🎯 개요
Microsoft Outlook의 Autodiscover 기능을 통해 사용자가 이메일 주소와 비밀번호만 입력하면 자동으로 메일 서버 설정이 구성되도록 하는 방법을 설명합니다.

## 🔧 1. DNS 설정

### 1-1. Autodiscover CNAME 레코드 추가
```dns
autodiscover.yourdomain.com.    IN    CNAME    mail.yourdomain.com.
```

### 1-2. SRV 레코드 추가 (선택사항)
```dns
_autodiscover._tcp.yourdomain.com.    IN    SRV    0 0 443 autodiscover.yourdomain.com.
```

## 🌐 2. 웹서버 설정 (Nginx)

### 2-1. Autodiscover 가상 호스트 설정
```nginx
# /etc/nginx/sites-available/autodiscover
server {
    listen 80;
    listen 443 ssl http2;
    server_name autodiscover.yourdomain.com;

    # SSL 인증서 설정
    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;

    # Autodiscover 경로 설정
    location /autodiscover/autodiscover.xml {
        proxy_pass http://127.0.0.1:8000/autodiscover/autodiscover.xml;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Outlook 호환성을 위한 헤더
        proxy_set_header Content-Type "text/xml; charset=utf-8";
    }

    # Microsoft-Server-ActiveSync 경로 (선택사항)
    location /Microsoft-Server-ActiveSync {
        return 501 "ActiveSync not implemented";
    }

    # 기본 경로
    location / {
        return 301 https://mail.yourdomain.com;
    }
}
```

### 2-2. 메인 도메인에 Autodiscover 경로 추가
```nginx
# 기존 mail.yourdomain.com 설정에 추가
location /autodiscover/autodiscover.xml {
    proxy_pass http://127.0.0.1:8000/autodiscover/autodiscover.xml;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 🔗 3. FastAPI 라우터 등록

### 3-1. main.py에 Autodiscover 라우터 추가
```python
# backend/main.py
from app.router import autodiscover_router

# 라우터 등록
app.include_router(autodiscover_router.router, prefix="/api/v1")
```

## 🧪 4. 테스트 방법

### 4-1. curl을 이용한 테스트
```bash
# Autodiscover 요청 테스트
curl -X POST https://autodiscover.yourdomain.com/autodiscover/autodiscover.xml \
  -H "Content-Type: text/xml; charset=utf-8" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/outlook/requestschema/2006">
  <Request>
    <EMailAddress>user@yourdomain.com</EMailAddress>
    <AcceptableResponseSchema>http://schemas.microsoft.com/exchange/autodiscover/outlook/responseschema/2006a</AcceptableResponseSchema>
  </Request>
</Autodiscover>'
```

### 4-2. Outlook에서 테스트
1. Outlook 실행
2. 파일 → 계정 추가
3. 이메일 주소 입력: `user@yourdomain.com`
4. 비밀번호 입력
5. "계정 설정 자동 검색" 체크
6. 연결 버튼 클릭

## 🔍 5. 문제 해결

### 5-1. Autodiscover 로그 확인
```bash
# FastAPI 로그 확인
tail -f /var/log/skyboot-mail/autodiscover.log

# Nginx 로그 확인
tail -f /var/log/nginx/autodiscover.access.log
tail -f /var/log/nginx/autodiscover.error.log
```

### 5-2. 일반적인 문제들

#### DNS 설정 문제
```bash
# DNS 확인
nslookup autodiscover.yourdomain.com
dig autodiscover.yourdomain.com
```

#### SSL 인증서 문제
```bash
# SSL 인증서 확인
openssl s_client -connect autodiscover.yourdomain.com:443 -servername autodiscover.yourdomain.com
```

#### Outlook 연결 문제
- Outlook 버전 확인 (2013 이상 권장)
- 방화벽 설정 확인
- 프록시 설정 확인

## 📋 6. Autodiscover 응답 예시

```xml
<?xml version="1.0" encoding="utf-8"?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/responseschema/2006">
  <Response xmlns="http://schemas.microsoft.com/exchange/autodiscover/outlook/responseschema/2006a">
    <User>
      <DisplayName>사용자 이름</DisplayName>
      <LegacyDN>/o=Organization/ou=Exchange Administrative Group (FYDIBOHF23SPDLT)/cn=Recipients/cn=user@yourdomain.com</LegacyDN>
      <AutoDiscoverSMTPAddress>user@yourdomain.com</AutoDiscoverSMTPAddress>
      <DeploymentId>org-uuid-here</DeploymentId>
    </User>
    <Account>
      <AccountType>email</AccountType>
      <Action>settings</Action>
      <MicrosoftOnline>False</MicrosoftOnline>
      <Protocol>
        <Type>IMAP</Type>
        <Server>mail.yourdomain.com</Server>
        <Port>993</Port>
        <DomainRequired>false</DomainRequired>
        <LoginName>user@yourdomain.com</LoginName>
        <SPA>false</SPA>
        <SSL>on</SSL>
        <AuthRequired>on</AuthRequired>
      </Protocol>
      <Protocol>
        <Type>SMTP</Type>
        <Server>mail.yourdomain.com</Server>
        <Port>587</Port>
        <DomainRequired>false</DomainRequired>
        <LoginName>user@yourdomain.com</LoginName>
        <SPA>false</SPA>
        <Encryption>TLS</Encryption>
        <AuthRequired>on</AuthRequired>
        <UsePOPAuth>on</UsePOPAuth>
        <SMTPLast>off</SMTPLast>
      </Protocol>
    </Account>
  </Response>
</Autodiscover>
```

## ✅ 7. 설정 완료 체크리스트

- [ ] DNS CNAME 레코드 설정
- [ ] SSL 인증서 설치
- [ ] Nginx 가상 호스트 설정
- [ ] FastAPI 라우터 등록
- [ ] Autodiscover 엔드포인트 테스트
- [ ] Outlook 클라이언트 테스트
- [ ] 로그 모니터링 설정

## 🚀 8. 고급 설정

### 8-1. 조직별 Autodiscover 설정
```python
# 조직별 서버 설정 커스터마이징
def get_organization_mail_settings(organization):
    return {
        "imap_server": f"imap.{organization.domain}",
        "smtp_server": f"smtp.{organization.domain}",
        "imap_port": 993,
        "smtp_port": 587
    }
```

### 8-2. 캐싱 설정
```python
# Redis를 이용한 Autodiscover 응답 캐싱
@cache(expire=3600)  # 1시간 캐시
async def get_autodiscover_response(email_address):
    # Autodiscover 응답 생성 로직
    pass
```

이 가이드를 따라 설정하면 Outlook 사용자들이 이메일 주소와 비밀번호만으로 쉽게 메일 계정을 설정할 수 있습니다.
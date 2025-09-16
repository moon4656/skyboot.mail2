# WSL Ubuntu에 Postfix와 Dovecot을 이용한 메일 서버 구축 안내서

이 문서는 Windows Subsystem for Linux (WSL) Ubuntu 환경에 Postfix와 Dovecot을 설치하고 설정하여 기본적인 메일 서버를 구축하는 과정을 안내합니다.

## 1. 사전 준비

- WSL2와 Ubuntu가 설치된 환경
- `root` 또는 `sudo` 권한

## 2. Postfix 설치 및 설정

Postfix는 메일 발송을 담당하는 MTA(Mail Transfer Agent)입니다.

### 2.1. Postfix 설치

```bash
sudo apt-get update
sudo apt-get install postfix -y
```

설치 중 설정 화면이 나타나면 'Internet Site'를 선택합니다.

### 2.2. Postfix 설정 (`/etc/postfix/main.cf`)

`main.cf` 파일을 열어 아래와 같이 수정하거나 추가합니다.

```bash
sudo nano /etc/postfix/main.cf
```

```ini
# 도메인 및 호스트 이름 설정
myhostname = skyboot.local
mydomain = skyboot.local
myorigin = $mydomain

# 모든 네트워크 인터페이스에서 수신
inet_interfaces = all
inet_protocols = ipv4

# 메일 수신 대상 도메인
mydestination = $myhostname, localhost.$mydomain, localhost, $mydomain

# 로컬 네트워크 및 외부 접근 허용 (WSL IP 추가)
# WSL IP는 `hostname -I` 명령으로 확인하여 추가합니다.
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128 <YOUR_WSL_IP>

# 메일박스 형식
home_mailbox = Maildir/
```

### 2.3. Postfix 설정 (`/etc/postfix/master.cf`)

SMTP 인증(SMTP-AUTH)을 위해 `master.cf` 파일의 주석을 해제합니다.

```bash
sudo nano /etc/postfix/master.cf
```

아래 라인의 주석을 제거합니다.

```
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING

smtps     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING
```

## 3. Dovecot 설치 및 설정

Dovecot은 IMAP과 POP3를 지원하는 MDA(Mail Delivery Agent)로, 사용자가 메일을 수신하고 읽을 수 있게 해줍니다.

### 3.1. Dovecot 설치

```bash
sudo apt-get install dovecot-core dovecot-imapd dovecot-pop3d -y
```

### 3.2. Dovecot 설정

#### 3.2.1. 메일 위치 설정 (`/etc/dovecot/conf.d/10-mail.conf`)

```bash
sudo nano /etc/dovecot/conf.d/10-mail.conf
```

```
mail_location = maildir:~/Maildir
```

#### 3.2.2. 인증 방식 설정 (`/etc/dovecot/conf.d/10-auth.conf`)

```bash
sudo nano /etc/dovecot/conf.d/10-auth.conf
```

```
disable_plaintext_auth = no
auth_mechanisms = plain login
```

#### 3.2.3. 서비스 리스너 설정 (`/etc/dovecot/conf.d/10-master.conf`)

Postfix와 연동을 위해 `service auth` 부분을 수정합니다.

```bash
sudo nano /etc/dovecot/conf.d/10-master.conf
```

```
service auth {
  unix_listener /var/spool/postfix/private/auth {
    mode = 0666
    user = postfix
    group = postfix
  }
}
```

#### 3.2.4. SSL 설정 (`/etc/dovecot/conf.d/10-ssl.conf`)

기본적인 SSL 설정을 사용합니다. (필요시 자체 인증서로 교체)

```bash
sudo nano /etc/dovecot/conf.d/10-ssl.conf
```

```
ssl = yes
ssl_cert = </etc/dovecot/private/dovecot.pem
ssl_key = </etc/dovecot/private/dovecot.key
```
*기존에 `ssl = required` 였다면 `ssl = yes`로 변경합니다.*

## 4. 사용자 계정 및 테스트

### 4.1. 테스트 사용자 생성

```bash
# 사용자 추가
sudo adduser testuser

# 비밀번호 설정
echo 'testuser:password123' | sudo chpasswd

# Maildir 생성
sudo -u testuser mkdir -p /home/testuser/Maildir/{cur,new,tmp}
```

### 4.2. 서비스 재시작 및 상태 확인

```bash
sudo systemctl restart postfix
sudo systemctl restart dovecot
sudo systemctl status postfix dovecot
```

### 4.3. 메일 발송 테스트

`mailutils`를 설치하여 메일을 발송합니다.

```bash
sudo apt-get install mailutils -y
echo 'Test email body' | mail -s 'Test Subject' testuser@skyboot.local
```

### 4.4. 메일 수신 확인

```bash
sudo ls -la /home/testuser/Maildir/new/
```

위 명령 실행 시 새로운 메일 파일이 보이면 성공입니다.

## 5. 외부 애플리케이션 연동

Python 애플리케이션 등 외부에서 메일 서버를 사용하려면 `mynetworks` 설정에 해당 애플리케이션이 실행되는 기기의 IP를 추가해야 합니다. 또한, SSL/TLS 연결 시 인증서 검증을 비활성화해야 할 수 있습니다.

---
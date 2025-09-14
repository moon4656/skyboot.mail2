# 📌 Postfix + Dovecot 학습 체크리스트

## 1️⃣ 환경 준비
- [ ] Ubuntu 22.04 서버 준비 (WSL2, VM, 실제 서버)
- [ ] `apt update && apt upgrade`
- [ ] DNS 기본 이해 (A, MX, SPF/DKIM/DMARC)
✅ 확인: `hostname -f`, `dig yourdomain.com MX`

---

## 2️⃣ Postfix 설치 & 설정
- [ ] `apt install postfix`
- [ ] 설치 중 Internet Site 선택
- [ ] `/etc/postfix/main.cf` 수정  
  → `home_mailbox = Maildir/` 추가
✅ 확인: `systemctl status postfix` → Active 상태

---

## 3️⃣ Dovecot 설치 & 설정
- [ ] `apt install dovecot-imapd dovecot-pop3d`
- [ ] `/etc/dovecot/dovecot.conf` 편집  
  → `protocols = imap pop3`  
  → `mail_location = maildir:~/Maildir`
✅ 확인: `systemctl status dovecot` → Active 상태

---

## 4️⃣ 사용자 계정 생성
- [ ] `adduser testuser`
- [ ] `maildirmake.dovecot /home/testuser/Maildir`
✅ 확인: `ls -l /home/testuser/Maildir` → 폴더 구조 확인

---

## 5️⃣ 로컬 송수신 테스트
- [ ] `telnet localhost 25` → 메일 송신
- [ ] `openssl s_client -connect localhost:143` → IMAP 접속
- [ ] 로그 확인: `/var/log/mail.log`
✅ 확인: 메일 송/수신 시 로그에 정상 기록됨

---

## 6️⃣ 클라이언트 연동
- [ ] Thunderbird/Outlook에서 testuser 계정 등록
- [ ] 선택적으로 Roundcube 설치
✅ 확인: 클라이언트에서 로그인 & 메일 송수신 가능

---

## 7️⃣ 보안 강화
- [ ] TLS 인증서 발급 (Let’s Encrypt)
- [ ] Postfix TLS 적용: `/etc/postfix/main.cf` → `smtpd_tls_cert_file`, `smtpd_tls_key_file`
- [ ] Dovecot TLS 적용: `/etc/dovecot/conf.d/10-ssl.conf`
✅ 확인: `openssl s_client -connect localhost:465` → 인증서 정보 출력

---

## 8️⃣ 외부 메일 연동
- [ ] Gmail, Naver 같은 외부 메일 계정과 송수신 테스트
- [ ] SPF 레코드: `v=spf1 mx ~all`
- [ ] DKIM 설정: opendkim 설치 및 key 등록
- [ ] DMARC 설정: `v=DMARC1; p=quarantine; rua=mailto:...`
✅ 확인: [mail-tester.com](https://www.mail-tester.com) 점수 확인

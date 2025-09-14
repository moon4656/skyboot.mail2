
# 📌 Postfix + Dovecot + PostgreSQL (Virtual User 기반) 학습 리포트

## 1️⃣ 학습 개요
일반적인 메일 서버는 OS 사용자 계정을 기반으로 메일을 관리하지만, 대규모 환경에서는 관리가 어렵고 보안상 제약이 있습니다.  
따라서 **Postfix + Dovecot + PostgreSQL** 조합을 통해 **가상 사용자(Virtual User)** 를 관리하면 확장성과 보안성을 높일 수 있습니다.

## 2️⃣ 가상 사용자 방식 개념
- **기본 사용자 방식**
  - OS 계정(`/etc/passwd`) 사용
  - 소규모 환경에서는 간단하지만, 수백~수천 명 관리에는 비효율적
- **가상 사용자 방식**
  - DB(PostgreSQL)에 사용자/도메인/별칭 관리
  - OS 계정과 분리 → 보안 강화
  - 확장성 및 중앙 집중 관리 가능

---

## 3️⃣ PostgreSQL 테이블 구조 예시
```sql
-- 도메인 관리
CREATE TABLE virtual_domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

-- 사용자 관리
CREATE TABLE virtual_users (
    id SERIAL PRIMARY KEY,
    domain_id INT NOT NULL,
    password VARCHAR(106) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
);

-- 별칭(Forwarding) 관리
CREATE TABLE virtual_aliases (
    id SERIAL PRIMARY KEY,
    domain_id INT NOT NULL,
    source VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
);
````

---

## 4️⃣ Postfix 설정

📄 `/etc/postfix/main.cf`

```ini
virtual_mailbox_domains = pgsql:/etc/postfix/pgsql-domains.cf
virtual_mailbox_maps = pgsql:/etc/postfix/pgsql-users.cf
virtual_alias_maps = pgsql:/etc/postfix/pgsql-aliases.cf
virtual_transport = lmtp:unix:private/dovecot-lmtp
```

📄 `/etc/postfix/pgsql-users.cf`

```ini
user = mailuser
password = strongpassword
hosts = 127.0.0.1
dbname = mailserver
query = SELECT email FROM virtual_users WHERE email='%s';
```

---

## 5️⃣ Dovecot 설정

📄 `/etc/dovecot/conf.d/10-mail.conf`

```ini
mail_location = maildir:/var/mail/vhosts/%d/%n
```

📄 `/etc/dovecot/conf.d/10-auth.conf`

```ini
disable_plaintext_auth = yes
auth_mechanisms = plain login
!include auth-sql.conf.ext
```

📄 `/etc/dovecot/conf.d/auth-sql.conf.ext`

```ini
passdb {
  driver = sql
  args = /etc/dovecot/dovecot-sql.conf.ext
}
userdb {
  driver = static
  args = uid=vmail gid=vmail home=/var/mail/vhosts/%d/%n
}
```

📄 `/etc/dovecot/dovecot-sql.conf.ext`

```ini
driver = pgsql
connect = host=127.0.0.1 dbname=mailserver user=mailuser password=strongpassword
default_pass_scheme = SHA512-CRYPT
password_query = SELECT email as user, password FROM virtual_users WHERE email='%u';
```

---

## 6️⃣ 가상 사용자 메일 저장소 준비

```bash
groupadd -g 5000 vmail
useradd -g vmail -u 5000 vmail -d /var/mail
mkdir -p /var/mail/vhosts
chown -R vmail:vmail /var/mail/vhosts
```

---

## 7️⃣ 학습/운용 시나리오

1. PostgreSQL에 `virtual_domains`, `virtual_users`, `virtual_aliases` 데이터 등록
2. Postfix가 DB를 조회하여 수신 메일 라우팅
3. Dovecot이 DB 인증을 거쳐 IMAP/POP3 서비스 제공
4. 메일 저장 경로: `/var/mail/vhosts/domain/user/`
5. 클라이언트(Outlook, Thunderbird, Roundcube) 연동 및 테스트

---

## 8️⃣ 결론

* **Postfix + Dovecot + PostgreSQL** 구조는 대규모 메일 서버에 적합
* OS 사용자에 의존하지 않고, **DB 기반의 중앙 관리** 가능
* 확장성, 보안성, 관리 효율성이 크게 향상됨
* 실제 기업 환경에서 표준적으로 사용되는 구조이므로 학습 가치가 높음

```

---

👉 이 문서를 **과제 제출용**으로 다듬으려면, 제가 **A3 리포트 PDF (가상 사용자 버전)** 으로 확장해드릴 수도 있습니다.  
문수씨, PDF 형식으로 다시 제작해드릴까요?
```


# post fix manual
cd /etc/postfix/main.cf
nano main.cf

# postfix restart
sudo systemctl restart postfix

# postfix status
sudo systemctl status postfix


# postfix start
sudo service postfix start

# postfix send mail
apk add s-nail
sendmail -v -t

# postfix add user
adduser user01

# testuser 메일박스 확인
sudo cat /var/spool/mail/testuser


# 1. WSL에 testuser 시스템 사용자 생성
wsl sudo useradd -m testuser
wsl sudo passwd testuser
wsl -u root adduser -D testuser

# 2. testuser에게 메일 발송
wsl -e sh -c "echo '테스트 메일' | mail -s '제목' testuser@localhost"
wsl -e sh -c "echo 'testuser님 안녕하세요! 메일박스 생성을 위한 테스트 메일입니다.' | mail -s 'testuser 메일박스 생성 테스트2' testuser"

# 2. testuser 메일박스 확인
wsl ls -la /var/spool/mail/

# 3. testuser 메일박스 읽기
wsl cat /var/spool/mail/testuser

# 메일 목록 확인
wsl -e sh -c "echo 'q' | mail -u testuser"

# 최신 메일 읽기 (보통 마지막 번호)
wsl -e sh -c "echo -e 'p 2\nq' | mail -u testuser"

# 또는 Python 디코더로 모든 메일 한번에 보기
python backend/korean_mail_decoder.py

# 사용자 접속
wsl -u user01

# 다른 사용자로 전환 (패스워드 필요)
su username

# root 사용자로 전환
su -

# 사용자 환경까지 완전히 전환
su - username



# Git 저장소 생성 및 첫 푸시 가이드

Git 저장소를 만들고 첫 푸시를 하기까지의 일반적인 단계는 다음과 같습니다.

## 1단계: Git 저장소 초기화

먼저, 프로젝트 폴더에서 Git 저장소를 생성합니다. `main` 브랜치를 기본으로 사용하도록 `-b main` 옵션을 추가하는 것이 좋습니다.

```bash
git init -b main
```

## 2단계: 변경 내용 스테이징

작업한 파일들을 Git이 추적하도록 추가합니다. 모든 파일을 추가하려면 `.`을 사용합니다.

```bash
git add .
```

특정 파일만 추가하려면 파일 이름을 직접 입력합니다.

```bash
git add <file_name>
```

## 3단계: 변경 내용 커밋

스테이징된 파일들을 로컬 저장소에 기록(커밋)합니다. `-m` 옵션으로 커밋 메시지를 함께 기록합니다.

```bash
git commit -m "첫 커밋 메시지"
```

## 4단계: 원격 저장소 연결

GitHub, GitLab 등 원격 저장소의 주소를 로컬 저장소에 추가합니다. `origin`은 보통 원격 저장소의 기본 이름으로 사용됩니다.

```bash
git remote add origin <원격_저장소_URL>
```

## 5단계: 원격 저장소로 푸시

로컬 저장소의 커밋을 원격 저장소로 업로드(푸시)합니다. `-u` 옵션은 로컬 `main` 브랜치와 원격 `origin/main` 브랜치를 연결하여 앞으로 `git push` 명령만으로 푸시할 수 있게 해줍니다.

```bash
git push -u origin main
```

이 5단계를 거치면 로컬 프로젝트가 원격 Git 저장소에 성공적으로 업로드됩니다.


## GITHUB   

- git init
- git status
- git remote -v
- git config --list

# git 사용자정보 설정
# 전역 설정 (모든 저장소에 적용)
- git config --global user.name "사용자명"
- git config --global user.email "이메일@example.com"

# 로컬 설정 (현재 저장소에만 적용)
- git config user.name "사용자명"
- git config user.email "이메일@example.com"

# 프로젝트 루트 디렉토리에서
- git init
- git add .
- git commit -m "Initial commit: STT project with FastAPI, Vue3, PostgreSQL"
- git branch -M main
- git remote add origin https://github.com/moon4656/stt_service.git
- git push -u origin main

- git remote add origin 
- git push -u origin main

- git init
- git add README.md
- git commit -m "first commit"
- git branch -M main
- git remote add origin https://github.com/moon4656/skyboot.core.git
- git push -u origin main

# 향후 변경사항 푸시:
- git add .
- git commit -m "커밋 메시지"
- git push

# 브랜치 확인:
- git branch
- git branch -a

# 브랜치 생성:
- git branch <브랜치명>

# 브랜치 변경:
- git checkout <브랜치명>

# 브랜치 병합:
- git checkout <병합할 브랜치>
- git merge <병합할 브랜치>
- git branch -d <병합된 브랜치>

# 원격 브랜치 삭제:
- git branch -r -d origin/<브랜치명>
- git push origin --delete <브랜치명>

# 서버 8001 포트 확인
- netstat -an | findstr :8001

# 서버 8001 포트 종료
- taskkill /f /pid <PID>

# uvicorn 서버 실행
- uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# 1단계: Git 상태 확인
- git status

# 2단계: 변경 사항 확인
- git diff

# 3단계: 변경 사항 스테이징
- git add .

# 4단계: 커밋
- git commit -m "Add new feature"

# 5단계: 원격 저장소에 푸시
- git push origin main

# 6단계: 원격 저장소 설정
- git remote add origin https://github.com/moonsoo-dx/skyboot.mail2.git

# Personal Access Token 사용 
- git remote set-url origin https://[moonsoo-dx]:[TOKEN]@github.com/moonsoo-dx/skyboot.mainl2.git


# GitHub에서 Personal Access Token 생성
# Settings → Developer settings → Personal access tokens → Generate new token
# repo 권한 체크 후 토큰 생성

# push 시 사용자명: GitHub 사용자명, 비밀번호: 생성한 토큰

# Windows Credential Manager 사용
- git config --global credential.helper manager-core

# 또는 토큰을 URL에 직접 포함
- git remote set-url origin https://[토큰]@github.com/moon4656/skyboot.core.git


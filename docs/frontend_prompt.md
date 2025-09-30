
# 프로젝트 개요
FastAPI 백엔드 + Vite + TypeScript + Vuestic(Vue3) 프론트엔드 + Postfix 메일 발송 기능을 포함한 MVP 웹서버를 만들어줘.

요구사항:
1. 프로젝트 구조
   - backend/ → FastAPI (Python)
   - frontend/ → Vuestic (Vue3, Vite 기반)
   - README.md → 설치 및 실행 가이드 작성

2. 백엔드 (FastAPI)
   - JWT 기반 인증 (access, refresh token)
   - 엔드포인트
     - POST /auth/register : 회원가입
     - POST /auth/login : 로그인
     - POST /auth/refresh : 토큰 재발급
     - POST /mail/send : Postfix SMTP 이용 메일 발송
   - DB: Postgresql (User, Token 테이블)
   - 메일 발송 시 로컬 Postfix 서버 사용 (host: localhost, port: 25)

3. 프론트엔드 (Vuestic + Vue3 + Vite + TypeScript)
   - Vuestic UI로 로그인/회원가입 페이지 작성
   - Axios 인터셉터 적용 → access token 자동 헤더 설정, refresh token으로 갱신
   - 메일 발송 테스트 페이지(/send-mail) 작성 (제목, 수신자, 본문 입력 → API 호출)

4. Postfix
   - 시스템에 설치된 Postfix 서버 사용
   - 외부 메일 발송은 불필요, 로컬 로그 확인 가능하도록 최소 설정

5. 실행
   - backend는 `uvicorn main:app --reload` 로 실행
   - frontend는 `pnpm dev` 또는 `npm run dev` 로 실행
   - README.md에 전체 실행 과정 포함

추가 조건:
- Git 저장소 초기화 (README 포함)
- 전체 소스는 바로 실행 가능해야 함

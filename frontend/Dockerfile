# 프론트엔드 Dockerfile
# Node.js 18 Alpine 이미지 사용
FROM node:18-alpine as build-stage

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci --only=production

# 소스 코드 복사
COPY . .

# 프로덕션 빌드
RUN npm run build

# Nginx를 사용한 프로덕션 스테이지
FROM nginx:alpine as production-stage

# 빌드된 파일을 Nginx 웹 루트로 복사
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/nginx.conf

# 포트 80 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.auth_router import router as auth_router
from app.router.mail_router import router as mail_router
from app.database.base import engine
from app.model.base_model import Base
from app.logging_config import setup_logging, get_logger
import logging

# 로깅 시스템 초기화
setup_logging()
logger = get_logger(__name__)

# 데이터베이스 테이블 생성
logger.info("🗄️ 데이터베이스 테이블 생성 시작")
Base.metadata.create_all(bind=engine)
logger.info("✅ 데이터베이스 테이블 생성 완료")

app = FastAPI(
    title="SkyBoot Mail API",
    description="FastAPI + Postfix 메일 발송 시스템",
    version="1.0.0"
)

logger.info("🚀 FastAPI 애플리케이션 초기화 완료")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("🌐 CORS 미들웨어 설정 완료")

# 라우터 등록
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(mail_router, prefix="/mail", tags=["mail"])
logger.info("📡 API 라우터 등록 완료")

@app.get("/")
async def root():
    """루트 엔드포인트 - API 상태 확인"""
    logger.info("📍 루트 엔드포인트 접근")
    return {"message": "SkyBoot Mail API is running"}

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    from datetime import datetime, timezone
    logger.info("💚 헬스체크 엔드포인트 접근")
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

if __name__ == "__main__":
    """메인 실행 블록 - 개발용 서버 시작"""
    import uvicorn
    logger.info("🔥 FastAPI 서버 시작 - 호스트: 127.0.0.1, 포트: 8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
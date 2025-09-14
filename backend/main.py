from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, mail
from app.database import engine
from app.models import Base

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkyBoot Mail API",
    description="FastAPI + Postfix 메일 발송 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(mail.router, prefix="/mail", tags=["mail"])

@app.get("/")
async def root():
    """루트 엔드포인트 - API 상태 확인"""
    return {"message": "SkyBoot Mail API is running"}

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    from datetime import datetime, timezone
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

if __name__ == "__main__":
    """메인 실행 블록 - 개발용 서버 시작"""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)
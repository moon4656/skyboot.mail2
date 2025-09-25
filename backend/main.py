from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

# 라우터 임포트
from app.router.auth_router import router as auth_router
from app.router.mail_core_router import router as mail_core_router
from app.router.mail_convenience_router import router as mail_convenience_router
from app.router.mail_advanced_router import router as mail_advanced_router
from app.router.mail_setup_router import router as mail_setup_router
from app.router.organization_router import router as organization_router
from app.router.user_router import router as user_router

# 데이터베이스 및 설정
from app.database.base import engine, Base
from app.config import settings
from app.logging_config import setup_logging, get_logger

# 미들웨어
from app.middleware.tenant import TenantMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 SkyBoot Mail SaaS 애플리케이션 시작")
    
    # 데이터베이스 테이블 생성 (필요시 수동으로 실행)
    # logger.info("🗄️ 데이터베이스 테이블 생성 시작")
    # Base.metadata.create_all(bind=engine)
    # logger.info("✅ 데이터베이스 테이블 생성 완료")
    logger.info("🗄️ 데이터베이스 테이블 생성은 필요시 수동으로 실행하세요")
    
    # 기본 조직 및 관리자 계정 생성 (개발 환경에서만)
    if settings.is_development():
        from app.service.organization_service import OrganizationService
        from app.service.auth_service import AuthService
        
        try:
            # 기본 조직 생성
            org_service = OrganizationService
            auth_service = AuthService
            
            # 시스템 관리자 조직 확인/생성
            # 개발 모드에서만 수행하며, 필요한 경우 서비스 내부에서 처리되도록 유지
            # (db 세션 주입은 실제 사용 시점에 수행)
            logger.info("✅ 개발 환경 초기 설정 확인")
            
        except Exception as e:
            logger.error(f"❌ 초기 설정 중 오류: {str(e)}")
    
    yield
    
    # 종료 시 실행
    logger.info("🛑 SkyBoot Mail SaaS 애플리케이션 종료")

# 로깅 시스템 초기화
setup_logging()
logger = get_logger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="SaaS 기반 기업용 메일 서버 시스템 - 다중 조직 지원",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.is_development() else None,
    redoc_url="/redoc" if settings.is_development() else None,
    lifespan=lifespan
)

logger.info("🚀 FastAPI 애플리케이션 초기화 완료")

# 보안 미들웨어 추가
if settings.is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    logger.info("🔒 TrustedHost 미들웨어 설정 완료")

# CORS 설정 (SaaS 환경에 맞게 확장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Organization-Id"]
)
logger.info("🌐 CORS 미들웨어 설정 완료")

# 테넌트(조직) 미들웨어 추가
app.add_middleware(TenantMiddleware)
logger.info("🏢 테넌트 미들웨어 설정 완료")

# 속도 제한 미들웨어 추가 (함수형)
from app.middleware.rate_limit_middleware import rate_limit_middleware

@app.middleware("http")
async def rate_limit_middleware_wrapper(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)

logger.info("🚦 속도 제한 미들웨어 활성화 완료")

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """요청 로깅 미들웨어"""
    start_time = time.time()
    
    # 요청 정보 로깅
    logger.info(f"📥 {request.method} {request.url.path} - IP: {request.client.host}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 응답 정보 로깅
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise

# 전역 예외 처리기
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리기"""
    logger.error(f"❌ HTTP 예외 발생: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": exc.status_code,
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리기"""
    logger.error(f"❌ 예상치 못한 오류 발생: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "내부 서버 오류가 발생했습니다.",
            "error_code": 500,
            "timestamp": time.time()
        }
    )

# API 라우터 등록 (v1 API)
api_prefix = settings.API_V1_PREFIX

app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["인증"]) 
app.include_router(organization_router, prefix=f"{api_prefix}/organizations", tags=["조직 관리"]) 
app.include_router(user_router, prefix=f"{api_prefix}/users", tags=["사용자 관리"]) 
app.include_router(mail_core_router, prefix=f"{api_prefix}/mail", tags=["메일 핵심"]) 
app.include_router(mail_convenience_router, prefix=f"{api_prefix}/mail", tags=["메일 편의"]) 
app.include_router(mail_advanced_router, prefix=f"{api_prefix}/mail", tags=["메일 고급"]) 
app.include_router(mail_setup_router, prefix=f"{api_prefix}/mail", tags=["메일 설정"]) 
logger.info("📡 API 라우터 등록 완료")

@app.get("/", summary="API 루트", description="SkyBoot Mail SaaS API 기본 정보")
async def root():
    """루트 엔드포인트 - API 상태 및 기본 정보 확인"""
    logger.info("📍 루트 엔드포인트 접근")
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "SaaS 기반 기업용 메일 서버 시스템",
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "features": [
            "다중 조직 지원",
            "메일 발송/수신",
            "폴더 관리",
            "백업/복원",
            "분석 및 통계",
            "조직별 데이터 격리"
        ],
        "api_docs": "/docs" if settings.is_development() else "문서는 개발 환경에서만 제공됩니다",
        "contact": {
            "name": "SkyBoot Mail 개발팀",
            "email": "support@skyboot.mail"
        }
    }

@app.get("/health", summary="헬스체크", description="시스템 상태 및 의존성 확인")
async def health_check():
    """헬스체크 엔드포인트 - 시스템 상태 및 의존성 확인"""
    from datetime import datetime, timezone
    from sqlalchemy import text
    
    logger.info("💚 헬스체크 엔드포인트 접근")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "checks": {}
    }
    
    # 데이터베이스 연결 확인
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "데이터베이스 연결 정상"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"데이터베이스 연결 실패: {str(e)}"
        }

    return health_status

@app.get("/info", summary="시스템 정보", description="시스템 설정 및 환경 정보")
async def system_info():
    """시스템 정보 엔드포인트 - 설정 및 환경 정보 제공"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_prefix": settings.API_V1_PREFIX,
        "cors_origins": settings.CORS_ORIGINS,
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🔥 FastAPI 서버 시작 - 호스트: 0.0.0.0, 포트: 8000")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=settings.is_development(),
        log_level="info" if settings.is_production() else "debug"
    )
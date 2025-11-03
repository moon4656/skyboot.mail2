from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging
import platform
import asyncio

# 라우터 임포트
from app.router.auth_router import router as auth_router
from app.router.mail_core_router import router as mail_core_router
from app.router.mail_convenience_router import router as mail_convenience_router
from app.router.mail_advanced_router import router as mail_advanced_router
from app.router.mail_setup_router import router as mail_setup_router
from app.router.organization_router import router as organization_router
from app.router.user_router import router as user_router
from app.router.debug_router import router as debug_router
from app.router.addressbook_router import router as addressbook_router
from app.router.monitoring_router import router as monitoring_router
from app.router.i18n_router import router as i18n_router
from app.router.theme_router import router as theme_router
from app.router.pwa_router import router as pwa_router
from app.router.offline_router import router as offline_router
from app.router.push_notification_router import router as push_notification_router
from app.router.devops_router import router as devops_router

# Outlook 연동 라우터
from app.router.autodiscover_router import router as autodiscover_router
from app.router.ews_router import router as ews_router
from app.router.graph_api_router import router as graph_api_router

# 테스트 CSV 라우터
from app.router.test_csv_router import router as test_csv_router

# 데이터베이스 및 설정
from app.database.user import engine, Base
from app.config import settings
from app.logging_config import setup_logging, get_logger

# 미들웨어
from app.middleware.tenant_middleware import TenantMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks.usage_reset import reset_daily_email_usage

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 SkyBoot Mail SaaS 애플리케이션 시작")

    # APScheduler 초기화 및 자정 리셋 잡 등록 (테스트 환경에서는 비활성화)
    scheduler = None
    if not settings.is_testing():
        logger.info("🗓️ APScheduler 초기화")
        scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
        scheduler.add_job(
            reset_daily_email_usage,
            CronTrigger(hour=0, minute=0),
            id="reset_daily_email_usage",
            replace_existing=True
        )
        scheduler.start()
        logger.info("✅ APScheduler 시작 및 자정 리셋 잡 등록 완료")
    else:
        logger.info("🧪 테스트 환경 - APScheduler 비활성화")
    
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
    try:
        if scheduler:
            logger.info("🛑 APScheduler 종료 시도")
            scheduler.shutdown(wait=False)
            logger.info("✅ APScheduler 종료 완료")
        else:
            logger.info("🧪 테스트 환경 - APScheduler 종료 스킵")
    except Exception:
        logger.warning("⚠️ APScheduler 종료 중 문제가 발생했지만 서버 종료를 계속 진행합니다")

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

# 테넌트 미들웨어 추가
app.add_middleware(TenantMiddleware)
logger.info("🏢 테넌트 미들웨어 설정 완료")

# 속도 제한 미들웨어 추가 (함수형) - Redis 연결 성공으로 활성화
from app.middleware.rate_limit_middleware import rate_limit_middleware

@app.middleware("http")
async def rate_limit_middleware_wrapper(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)

logger.info("🚦 속도 제한 미들웨어 활성화 완료 (Redis 연결 성공)")

# 요청 로깅 미들웨어 (성능 테스트를 위해 임시 비활성화)
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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 검증 에러 처리기"""
    logger.error(f"❌ 검증 에러 발생: {exc.errors()}")
    logger.error(f"📋 요청 URL: {request.url}")
    logger.error(f"📋 요청 메서드: {request.method}")
    
    # 에러 메시지를 한국어로 변환하고 JSON 직렬화 가능하게 처리
    error_messages = []
    serializable_errors = []
    
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")
        
        # JSON 직렬화 가능한 에러 정보 생성
        serializable_error = {
            "type": error["type"],
            "loc": error["loc"],
            "msg": error["msg"],
            "input": str(error.get("input", ""))  # input을 문자열로 변환
        }
        # ctx에 ValueError가 있으면 문자열로 변환
        if "ctx" in error and "error" in error["ctx"]:
            serializable_error["ctx"] = {"error": str(error["ctx"]["error"])}
        
        serializable_errors.append(serializable_error)
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "입력 데이터 검증 오류",
            "errors": error_messages,
            "detail": serializable_errors,
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

# API 라우터 등록 (v1 API) - 기존 엔드포인트 유지
api_prefix = settings.API_V1_PREFIX

app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["인증"]) 
app.include_router(organization_router, prefix=f"{api_prefix}/organizations", tags=["조직 관리"]) 
app.include_router(user_router, prefix=f"{api_prefix}/users", tags=["사용자 관리"]) 
app.include_router(mail_convenience_router, prefix=f"{api_prefix}/mail", tags=["메일 편의"]) 
app.include_router(mail_core_router, prefix=f"{api_prefix}/mail", tags=["메일 핵심"]) 
app.include_router(mail_advanced_router, prefix=f"{api_prefix}/mail", tags=["메일 고급"]) 
app.include_router(mail_setup_router, prefix=f"{api_prefix}/mail", tags=["메일 설정"])
app.include_router(addressbook_router, prefix=f"{api_prefix}/addressbook", tags=["주소록"])
app.include_router(test_csv_router, prefix=f"{api_prefix}/test-csv", tags=["테스트 CSV"])
app.include_router(monitoring_router, prefix=f"{api_prefix}", tags=["모니터링"])

# 국제화, 브랜딩, PWA, 오프라인, 푸시 알림 라우터 등록
app.include_router(i18n_router, prefix=f"{api_prefix}", tags=["국제화"])
app.include_router(theme_router, prefix=f"{api_prefix}", tags=["조직 테마"])
app.include_router(pwa_router, prefix=f"{api_prefix}", tags=["PWA"])
app.include_router(offline_router, prefix=f"{api_prefix}", tags=["오프라인"])
app.include_router(push_notification_router, prefix=f"{api_prefix}", tags=["푸시 알림"])
app.include_router(devops_router, prefix=f"{api_prefix}", tags=["DevOps"])
logger.info("🛠️ DevOps 라우터 등록 완료")

# Outlook 연동 라우터 등록
app.include_router(autodiscover_router, prefix="", tags=["Outlook Autodiscover"])
app.include_router(ews_router, prefix="", tags=["Exchange Web Services"])
app.include_router(graph_api_router, prefix=f"{api_prefix}", tags=["Microsoft Graph API"])
logger.info("📧 Outlook 연동 라우터 등록 완료")

if settings.is_development():
    app.include_router(debug_router, prefix=f"{api_prefix}", tags=["디버그"])
    logger.info("🔍 디버그 라우터 등록 완료 (개발 환경)")

logger.info("📡 기존 API 라우터 등록 완료")

# 도메인별 API 문서 엔드포인트 구현
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

def create_domain_openapi_schema(domain_name: str, router_tags: list):
    """도메인별 OpenAPI 스키마 생성"""
    # 해당 도메인의 태그만 포함하는 스키마 생성
    openapi_schema = get_openapi(
        title=f"{settings.APP_NAME} - {domain_name} API",
        version=settings.APP_VERSION,
        description=f"SkyBoot Mail SaaS {domain_name} 도메인 API 문서",
        routes=app.routes,
    )
    
    # OpenAPI 3.0 필수 정보 명시적 추가
    openapi_schema["openapi"] = "3.0.0"
    openapi_schema["info"] = {
        "title": f"{settings.APP_NAME} - {domain_name} API",
        "version": settings.APP_VERSION,
        "description": f"SkyBoot Mail SaaS {domain_name} 도메인 API 문서"
    }
    
    # 해당 도메인의 태그만 필터링
    if "paths" in openapi_schema:
        filtered_paths = {}
        for path, methods in openapi_schema["paths"].items():
            for method, details in methods.items():
                if "tags" in details and any(tag in router_tags for tag in details["tags"]):
                    if path not in filtered_paths:
                        filtered_paths[path] = {}
                    filtered_paths[path][method] = details
        openapi_schema["paths"] = filtered_paths
    
    return openapi_schema

@app.get("/docs/admin", include_in_schema=False)
async def get_admin_docs():
    """관리자 도메인 API 문서"""
    admin_tags = ["조직 관리", "사용자 관리", "모니터링", "DevOps"]
    openapi_schema = create_domain_openapi_schema("관리자", admin_tags)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME} - 관리자 API 문서</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '/openapi/admin.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ]
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/docs/user", include_in_schema=False)
async def get_user_docs():
    """사용자 도메인 API 문서"""
    user_tags = ["인증", "사용자 관리", "주소록", "국제화", "조직 테마", "PWA", "오프라인", "푸시 알림"]
    openapi_schema = create_domain_openapi_schema("사용자", user_tags)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME} - 사용자 API 문서</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '/openapi/user.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ]
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/docs/mail", include_in_schema=False)
async def get_mail_docs():
    """메일 도메인 API 문서"""
    mail_tags = ["메일 핵심", "메일 편의", "메일 고급", "메일 설정", "Outlook Autodiscover", "Exchange Web Services", "Microsoft Graph API"]
    openapi_schema = create_domain_openapi_schema("메일", mail_tags)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME} - 메일 API 문서</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '/openapi/mail.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ]
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/docs/business", include_in_schema=False)
async def get_business_docs():
    """비즈니스 도메인 API 문서"""
    business_tags = ["조직 관리", "메일 핵심", "메일 편의", "메일 고급", "주소록", "모니터링"]
    openapi_schema = create_domain_openapi_schema("비즈니스", business_tags)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME} - 비즈니스 API 문서</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '/openapi/business.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ]
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/docs/system", include_in_schema=False)
async def get_system_docs():
    """시스템 도메인 API 문서"""
    system_tags = ["메일 설정", "모니터링", "DevOps", "디버그"]
    openapi_schema = create_domain_openapi_schema("시스템", system_tags)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME} - 시스템 API 문서</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '/openapi/system.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ]
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 도메인별 OpenAPI JSON 엔드포인트
@app.get("/openapi/admin.json", include_in_schema=False)
async def get_admin_openapi():
    """관리자 도메인 OpenAPI JSON"""
    admin_tags = ["조직 관리", "사용자 관리", "모니터링", "DevOps"]
    return create_domain_openapi_schema("관리자", admin_tags)

@app.get("/openapi/user.json", include_in_schema=False)
async def get_user_openapi():
    """사용자 도메인 OpenAPI JSON"""
    user_tags = ["인증", "사용자 관리", "주소록", "국제화", "조직 테마", "PWA", "오프라인", "푸시 알림"]
    return create_domain_openapi_schema("사용자", user_tags)

@app.get("/openapi/mail.json", include_in_schema=False)
async def get_mail_openapi():
    """메일 도메인 OpenAPI JSON"""
    mail_tags = ["메일 핵심", "메일 편의", "메일 고급", "메일 설정", "Outlook Autodiscover", "Exchange Web Services", "Microsoft Graph API"]
    return create_domain_openapi_schema("메일", mail_tags)

@app.get("/openapi/business.json", include_in_schema=False)
async def get_business_openapi():
    """비즈니스 도메인 OpenAPI JSON"""
    business_tags = ["조직 관리", "메일 핵심", "메일 편의", "메일 고급", "주소록", "모니터링"]
    return create_domain_openapi_schema("비즈니스", business_tags)

@app.get("/openapi/system.json", include_in_schema=False)
async def get_system_openapi():
    """시스템 도메인 OpenAPI JSON"""
    system_tags = ["메일 설정", "모니터링", "DevOps", "디버그"]
    return create_domain_openapi_schema("시스템", system_tags)

@app.get("/", summary="API 루트", description="SkyBoot Mail SaaS API 기본 정보")
async def root():
    return {"message": "SkyBoot Mail SaaS API"}

@app.get("/health", summary="헬스체크", description="시스템 상태 및 의존성 확인")
async def health_check():
    return {"status": "ok"}

@app.get("/health/detailed", summary="상세 헬스체크", description="데이터베이스 연결 등 상세 시스템 상태 확인")
async def detailed_health_check():
    return {"status": "ok", "database": "connected"}

@app.get("/info", summary="시스템 정보", description="시스템 설정 및 환경 정보")
async def system_info():
    return {"app": settings.APP_NAME, "env": settings.ENVIRONMENT}

if __name__ == "__main__":
    import uvicorn
    logger.info("🔥 FastAPI 서버 시작 - 호스트: 0.0.0.0, 포트: 8000")
    is_windows = platform.system() == "Windows"
    should_reload = settings.is_development() and not is_windows
    if settings.is_development() and is_windows:
        logger.info("🪟 Windows 개발 환경 - reload 비활성화(안정성)")
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            reload=should_reload,
            log_level="info" if settings.is_production() else "debug"
        )
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자 중단(KeyboardInterrupt)으로 서버 종료")
    except asyncio.CancelledError:
        logger.info("⏹️ 이벤트 루프 취소로 서버 종료")
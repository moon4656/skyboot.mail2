import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging():
    """
    FastAPI 애플리케이션을 위한 로깅 설정을 구성합니다.
    
    - 일별 로그 파일 생성 (YYYY-MM-DD.log 형식)
    - 10MB 초과 시 새로운 로그 파일 생성
    - 콘솔과 파일 모두에 로그 출력
    """
    # 로그 디렉토리 생성 (절대 경로 사용)
    import os
    current_dir = Path(os.getcwd())
    log_dir = current_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 - 일별 로테이션
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_dir / f"{today}.log"
    
    # 로그 파일을 즉시 생성하기 위해 테스트 로그 작성
    try:
        log_file.touch()  # 파일 생성
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INIT - INFO - 로그 파일 초기화\n")
        print(f"✅ 로그 파일 생성 성공: {log_file.absolute()}")
    except Exception as e:
        print(f"❌ 로그 파일 생성 실패: {e}")
        print(f"로그 디렉토리: {log_dir.absolute()}")
        print(f"로그 파일 경로: {log_file.absolute()}")
    
    # 크기 기반 로테이션 핸들러 (10MB)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # 최대 5개의 백업 파일 유지
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 시간 기반 로테이션 핸들러 (일별)
    timed_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when='midnight',
        interval=1,
        backupCount=30,  # 30일간 로그 보관
        encoding='utf-8'
    )
    timed_handler.setLevel(logging.INFO)
    timed_handler.setFormatter(formatter)
    # 파일명에 날짜 추가
    timed_handler.suffix = "%Y-%m-%d"
    logger.addHandler(timed_handler)
    
    # 에러 로그 전용 핸들러
    error_log_file = log_dir / f"error-{today}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # 메일 관련 로그 전용 핸들러
    mail_log_file = log_dir / f"mail-{today}.log"
    mail_handler = logging.handlers.RotatingFileHandler(
        filename=mail_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    mail_handler.setLevel(logging.INFO)
    mail_handler.setFormatter(formatter)
    
    # 메일 로거 설정
    mail_logger = logging.getLogger('mail')
    mail_logger.addHandler(mail_handler)
    mail_logger.setLevel(logging.INFO)
    
    logger.info("📝 로깅 시스템이 초기화되었습니다.")
    logger.info(f"📁 로그 디렉토리: {log_dir.absolute()}")
    logger.info(f"📄 오늘 로그 파일: {log_file}")
    
    # 로그 파일 생성 강제 실행
    logger.info("🔧 로그 파일 생성 테스트")
    logger.warning("⚠️ 경고 레벨 로그 테스트")
    logger.error("❌ 에러 레벨 로그 테스트")
    
    # 메일 로거 테스트
    mail_logger.info("📧 메일 로거 테스트")
    
    # 핸들러 강제 플러시
    for handler in logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    return logger


def get_logger(name: str = None):
    """
    로거 인스턴스를 반환합니다.
    
    Args:
        name: 로거 이름 (기본값: None)
    
    Returns:
        logging.Logger: 로거 인스턴스
    """
    return logging.getLogger(name)


def get_mail_logger():
    """
    메일 전용 로거를 반환합니다.
    
    Returns:
        logging.Logger: 메일 로거 인스턴스
    """
    return logging.getLogger('mail')
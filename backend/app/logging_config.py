import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging():
    """
    FastAPI 애플리케이션을 위한 간소화된 로깅 설정을 구성합니다.
    성능 최적화를 위해 핸들러 수를 최소화했습니다.
    """
    # 로그 디렉토리 생성 (절대 경로 사용)
    current_dir = Path(os.getcwd())
    log_dir = current_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
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
    
    # 파일 핸들러 추가 (일별 로테이션)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_dir / f"app.log.{today}"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 로그 초기화 메시지
    logger.info("📝 로깅 시스템이 초기화되었습니다.")
    logger.info(f"📁 로그 파일: {log_file}")
    
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
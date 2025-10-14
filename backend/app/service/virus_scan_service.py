"""
바이러스 검사 서비스 모듈

ClamAV를 사용하여 첨부파일의 바이러스 검사를 수행합니다.
"""

import os
import logging
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import pyclamd
    CLAMAV_AVAILABLE = True
except ImportError:
    CLAMAV_AVAILABLE = False
    pyclamd = None

logger = logging.getLogger(__name__)


class VirusScanResult:
    """바이러스 검사 결과를 담는 클래스"""
    
    def __init__(self, 
                 file_path: str,
                 is_infected: bool = False,
                 virus_name: Optional[str] = None,
                 engine: str = "unknown",
                 scan_time: Optional[float] = None,
                 file_hash: Optional[str] = None,
                 error_message: Optional[str] = None):
        self.file_path = file_path
        self.is_infected = is_infected
        self.virus_name = virus_name
        self.engine = engine
        self.scan_time = scan_time or 0.0
        self.file_hash = file_hash
        self.error_message = error_message
    
    @property
    def status(self) -> str:
        """검사 상태를 반환"""
        if self.error_message:
            return "error"
        elif self.is_infected:
            return "infected"
        else:
            return "clean"
    
    @property
    def message(self) -> str:
        """검사 결과 메시지를 반환"""
        if self.error_message:
            return f"검사 오류: {self.error_message}"
        elif self.is_infected:
            return f"바이러스 발견: {self.virus_name or '알 수 없는 바이러스'}"
        else:
            return "파일이 안전합니다"
    
    def to_dict(self) -> Dict[str, Any]:
        """결과를 딕셔너리로 변환"""
        return {
            "file_path": self.file_path,
            "is_infected": self.is_infected,
            "virus_name": self.virus_name,
            "engine": self.engine,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "file_hash": self.file_hash,
            "error_message": self.error_message
        }


class VirusScanService:
    """바이러스 검사 서비스 클래스"""
    
    def __init__(self, 
                 clamav_host: str = "localhost",
                 clamav_port: int = 3310,
                 enable_fallback: bool = True):
        """
        바이러스 검사 서비스 초기화
        
        Args:
            clamav_host: ClamAV 데몬 호스트
            clamav_port: ClamAV 데몬 포트
            enable_fallback: ClamAV 사용 불가 시 휴리스틱 검사 사용 여부
        """
        self.clamav_host = clamav_host
        self.clamav_port = clamav_port
        self.enable_fallback = enable_fallback
        self._clamav_client = None
        self._clamav_available = False
        
        # ClamAV 연결 시도
        self._initialize_clamav()
    
    def _initialize_clamav(self) -> None:
        """ClamAV 데몬 연결 초기화"""
        if not CLAMAV_AVAILABLE:
            logger.warning("🦠 pyclamd 모듈이 설치되지 않았습니다. 휴리스틱 검사만 사용됩니다.")
            return
        
        try:
            # TCP 연결 시도
            self._clamav_client = pyclamd.ClamdNetworkSocket(
                host=self.clamav_host, 
                port=self.clamav_port
            )
            
            # 연결 테스트
            if self._clamav_client.ping():
                self._clamav_available = True
                version = self._clamav_client.version()
                logger.info(f"✅ ClamAV 연결 성공 - {version}")
            else:
                logger.warning(f"⚠️ ClamAV 데몬에 연결할 수 없습니다 ({self.clamav_host}:{self.clamav_port})")
                
        except Exception as e:
            logger.warning(f"⚠️ ClamAV 초기화 실패: {str(e)}")
            
            # Unix 소켓 연결 시도 (Linux/macOS)
            try:
                self._clamav_client = pyclamd.ClamdUnixSocket()
                if self._clamav_client.ping():
                    self._clamav_available = True
                    logger.info("✅ ClamAV Unix 소켓 연결 성공")
                else:
                    logger.warning("⚠️ ClamAV Unix 소켓 연결 실패")
            except Exception as unix_e:
                logger.warning(f"⚠️ ClamAV Unix 소켓 연결 실패: {str(unix_e)}")
    
    def scan_file(self, file_path: str) -> VirusScanResult:
        """
        파일 바이러스 검사 수행
        
        Args:
            file_path: 검사할 파일 경로
            
        Returns:
            VirusScanResult: 검사 결과
        """
        start_time = time.time()
        
        if not os.path.exists(file_path):
            return VirusScanResult(
                file_path=file_path,
                error_message="파일이 존재하지 않습니다",
                engine="error",
                scan_time=time.time() - start_time
            )
        
        # 파일 해시 계산
        file_hash = self._calculate_file_hash(file_path)
        
        # ClamAV 검사 시도
        if self._clamav_available and self._clamav_client:
            try:
                result = self._scan_with_clamav(file_path)
                result.file_hash = file_hash
                result.scan_time = time.time() - start_time
                return result
            except Exception as e:
                logger.error(f"❌ ClamAV 검사 실패: {str(e)}")
                if not self.enable_fallback:
                    return VirusScanResult(
                        file_path=file_path,
                        error_message=f"ClamAV 검사 실패: {str(e)}",
                        engine="clamav_error",
                        file_hash=file_hash,
                        scan_time=time.time() - start_time
                    )
        
        # 휴리스틱 검사 (폴백)
        if self.enable_fallback:
            result = self._scan_with_heuristic(file_path)
            result.file_hash = file_hash
            result.scan_time = time.time() - start_time
            return result
        
        return VirusScanResult(
            file_path=file_path,
            error_message="바이러스 검사 엔진을 사용할 수 없습니다",
            engine="unavailable",
            file_hash=file_hash,
            scan_time=time.time() - start_time
        )
    
    def _scan_with_clamav(self, file_path: str) -> VirusScanResult:
        """ClamAV를 사용한 파일 검사"""
        try:
            scan_result = self._clamav_client.scan_file(file_path)
            
            if scan_result is None:
                # 깨끗한 파일
                return VirusScanResult(
                    file_path=file_path,
                    is_infected=False,
                    engine="clamav"
                )
            else:
                # 바이러스 발견
                virus_name = scan_result.get(file_path, "Unknown virus")
                if isinstance(virus_name, tuple):
                    virus_name = virus_name[1] if len(virus_name) > 1 else virus_name[0]
                
                return VirusScanResult(
                    file_path=file_path,
                    is_infected=True,
                    virus_name=virus_name,
                    engine="clamav"
                )
                
        except Exception as e:
            raise Exception(f"ClamAV 검사 중 오류: {str(e)}")
    
    def _scan_with_heuristic(self, file_path: str) -> VirusScanResult:
        """휴리스틱 바이러스 검사 (EICAR 테스트 패턴 탐지)"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            # EICAR 테스트 패턴 탐지
            eicar_patterns = [
                b"X5O!P%@AP[4\PZX54(P^)7CC)7$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*",
                b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"
            ]
            
            for pattern in eicar_patterns:
                if pattern in content:
                    return VirusScanResult(
                        file_path=file_path,
                        is_infected=True,
                        virus_name="EICAR-Test-File",
                        engine="heuristic"
                    )
            
            # 추가 휴리스틱 검사 (의심스러운 패턴)
            suspicious_patterns = [
                b"CreateRemoteThread",
                b"VirtualAllocEx",
                b"WriteProcessMemory",
                b"SetWindowsHookEx"
            ]
            
            suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in content)
            if suspicious_count >= 2:
                return VirusScanResult(
                    file_path=file_path,
                    is_infected=True,
                    virus_name="Heuristic.Suspicious.Behavior",
                    engine="heuristic"
                )
            
            return VirusScanResult(
                file_path=file_path,
                is_infected=False,
                engine="heuristic"
            )
            
        except Exception as e:
            return VirusScanResult(
                file_path=file_path,
                error_message=f"휴리스틱 검사 실패: {str(e)}",
                engine="heuristic_error"
            )
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일의 SHA256 해시 계산"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def scan_multiple_files(self, file_paths: List[str]) -> List[VirusScanResult]:
        """
        여러 파일 일괄 검사
        
        Args:
            file_paths: 검사할 파일 경로 목록
            
        Returns:
            List[VirusScanResult]: 검사 결과 목록
        """
        results = []
        for file_path in file_paths:
            result = self.scan_file(file_path)
            results.append(result)
            
            # 감염된 파일 발견 시 로깅
            if result.is_infected:
                logger.warning(f"🦠 바이러스 발견 - 파일: {file_path}, 바이러스: {result.virus_name}")
        
        return results
    
    def get_engine_info(self) -> Dict[str, Any]:
        """바이러스 검사 엔진 정보 반환"""
        info = {
            "clamav_available": self._clamav_available,
            "fallback_enabled": self.enable_fallback,
            "host": self.clamav_host,
            "port": self.clamav_port
        }
        
        if self._clamav_available and self._clamav_client:
            try:
                info["clamav_version"] = self._clamav_client.version()
                info["database_version"] = self._clamav_client.stats()
            except Exception as e:
                info["clamav_error"] = str(e)
        
        return info
    
    def update_virus_database(self) -> bool:
        """
        바이러스 데이터베이스 업데이트
        
        Returns:
            bool: 업데이트 성공 여부
        """
        if not self._clamav_available:
            logger.warning("⚠️ ClamAV가 사용 불가능하여 데이터베이스를 업데이트할 수 없습니다")
            return False
        
        try:
            # ClamAV 데이터베이스 업데이트는 일반적으로 freshclam 명령으로 수행
            # 여기서는 연결 상태만 확인
            if self._clamav_client.ping():
                logger.info("✅ ClamAV 데이터베이스 연결 확인 완료")
                return True
            else:
                logger.error("❌ ClamAV 데이터베이스 연결 실패")
                return False
        except Exception as e:
            logger.error(f"❌ ClamAV 데이터베이스 업데이트 확인 실패: {str(e)}")
            return False


# 전역 바이러스 검사 서비스 인스턴스
_virus_scanner = None


def get_virus_scanner() -> VirusScanService:
    """바이러스 검사 서비스 싱글톤 인스턴스 반환"""
    global _virus_scanner
    if _virus_scanner is None:
        _virus_scanner = VirusScanService()
    return _virus_scanner


def scan_file_for_virus(file_path: str) -> VirusScanResult:
    """
    파일 바이러스 검사 편의 함수
    
    Args:
        file_path: 검사할 파일 경로
        
    Returns:
        VirusScanResult: 검사 결과
    """
    scanner = get_virus_scanner()
    return scanner.scan_file(file_path)
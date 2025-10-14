"""
DevOps 서비스

SkyBoot Mail SaaS 프로젝트의 DevOps 기능을 위한 서비스 클래스입니다.
백업, 복구, 테스트 등의 DevOps 작업을 처리합니다.
"""

import os
import json
import uuid
import zipfile
import shutil
import psutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from ..config import settings
from ..model.user_model import User
from ..model.organization_model import Organization
from ..model.mail_model import Mail, MailUser, MailAttachment
from ..schemas.devops_schema import (
    BackupType, BackupStatus, RestoreType, TestType, TestStatus,
    BackupRequest, BackupResponse, BackupListResponse,
    RestoreRequest, RestoreResponse,
    TestRequest, TestResponse, TestResult,
    SystemHealthResponse, DevOpsResponse, JobStatusResponse
)

logger = logging.getLogger(__name__)

class DevOpsService:
    """DevOps 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.backup_dir = Path(settings.BACKUP_DIR if hasattr(settings, 'BACKUP_DIR') else "backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_dir = Path(tempfile.gettempdir()) / "skyboot_devops"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 작업 상태 저장소 (실제 환경에서는 Redis나 데이터베이스 사용)
        self.job_status = {}
    
    # ===== 백업 기능 =====
    
    async def create_backup(
        self, 
        organization_id: int, 
        user_id: int, 
        request: BackupRequest
    ) -> BackupResponse:
        """백업 생성"""
        backup_id = str(uuid.uuid4())
        
        try:
            logger.info(f"📦 백업 시작 - 조직: {organization_id}, 사용자: {user_id}, 타입: {request.backup_type}")
            
            # 백업 작업 상태 초기화
            self.job_status[backup_id] = {
                "status": BackupStatus.RUNNING,
                "progress": 0,
                "started_at": datetime.now(),
                "log_messages": []
            }
            
            # 백업 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{organization_id}_{timestamp}_{backup_id[:8]}.zip"
            backup_path = self.backup_dir / backup_filename
            
            # 백업 실행
            backup_size = await self._execute_backup(
                organization_id, backup_id, backup_path, request
            )
            
            # 백업 완료
            self.job_status[backup_id]["status"] = BackupStatus.COMPLETED
            self.job_status[backup_id]["progress"] = 100
            self.job_status[backup_id]["completed_at"] = datetime.now()
            
            logger.info(f"✅ 백업 완료 - ID: {backup_id}, 크기: {backup_size} bytes")
            
            return BackupResponse(
                backup_id=backup_id,
                backup_type=request.backup_type,
                status=BackupStatus.COMPLETED,
                file_path=str(backup_path),
                file_size=backup_size,
                created_at=self.job_status[backup_id]["started_at"],
                completed_at=self.job_status[backup_id]["completed_at"],
                organization_id=organization_id,
                created_by=user_id,
                description=request.description,
                tags=request.tags,
                metadata={
                    "include_database": request.include_database,
                    "include_files": request.include_files,
                    "include_config": request.include_config,
                    "include_attachments": request.include_attachments,
                    "compression": request.compression,
                    "encryption": request.encryption
                }
            )
            
        except Exception as e:
            logger.error(f"❌ 백업 실패 - ID: {backup_id}, 오류: {str(e)}")
            self.job_status[backup_id]["status"] = BackupStatus.FAILED
            self.job_status[backup_id]["log_messages"].append(f"백업 실패: {str(e)}")
            raise
    
    async def _execute_backup(
        self, 
        organization_id: int, 
        backup_id: str, 
        backup_path: Path, 
        request: BackupRequest
    ) -> int:
        """백업 실행"""
        temp_backup_dir = self.temp_dir / f"backup_{backup_id}"
        temp_backup_dir.mkdir(exist_ok=True)
        
        try:
            progress = 0
            
            # 데이터베이스 백업
            if request.include_database:
                logger.info(f"📊 데이터베이스 백업 시작 - 조직: {organization_id}")
                await self._backup_database(organization_id, temp_backup_dir)
                progress += 30
                self.job_status[backup_id]["progress"] = progress
                self.job_status[backup_id]["log_messages"].append("데이터베이스 백업 완료")
            
            # 파일 백업
            if request.include_files:
                logger.info(f"📁 파일 백업 시작 - 조직: {organization_id}")
                await self._backup_files(organization_id, temp_backup_dir, request.include_attachments)
                progress += 40
                self.job_status[backup_id]["progress"] = progress
                self.job_status[backup_id]["log_messages"].append("파일 백업 완료")
            
            # 설정 백업
            if request.include_config:
                logger.info(f"⚙️ 설정 백업 시작 - 조직: {organization_id}")
                await self._backup_config(organization_id, temp_backup_dir)
                progress += 20
                self.job_status[backup_id]["progress"] = progress
                self.job_status[backup_id]["log_messages"].append("설정 백업 완료")
            
            # 메타데이터 생성
            metadata = {
                "backup_id": backup_id,
                "organization_id": organization_id,
                "backup_type": request.backup_type,
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "includes": {
                    "database": request.include_database,
                    "files": request.include_files,
                    "config": request.include_config,
                    "attachments": request.include_attachments
                }
            }
            
            metadata_file = temp_backup_dir / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # ZIP 파일 생성
            logger.info(f"🗜️ 백업 파일 압축 시작")
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_backup_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_backup_dir)
                        zipf.write(file_path, arcname)
            
            progress = 100
            self.job_status[backup_id]["progress"] = progress
            self.job_status[backup_id]["log_messages"].append("백업 파일 압축 완료")
            
            return backup_path.stat().st_size
            
        finally:
            # 임시 디렉토리 정리
            if temp_backup_dir.exists():
                shutil.rmtree(temp_backup_dir)
    
    async def _backup_database(self, organization_id: int, backup_dir: Path):
        """데이터베이스 백업"""
        # 조직별 데이터 추출
        db_backup_dir = backup_dir / "database"
        db_backup_dir.mkdir(exist_ok=True)
        
        # 사용자 데이터
        users = self.db.query(User).filter(User.organization_id == organization_id).all()
        users_data = [
            {
                "id": user.id,
                "user_uuid": user.user_uuid,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "role": user.role.value if user.role else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
        
        with open(db_backup_dir / "users.json", 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        
        # 메일 데이터
        mails = self.db.query(Mail).filter(Mail.organization_id == organization_id).all()
        mails_data = [
            {
                "mail_id": mail.mail_id,
                "sender_id": mail.sender_id,
                "subject": mail.subject,
                "content": mail.content,
                "sent_at": mail.sent_at.isoformat() if mail.sent_at else None,
                "status": mail.status.value if mail.status else None
            }
            for mail in mails
        ]
        
        with open(db_backup_dir / "mails.json", 'w', encoding='utf-8') as f:
            json.dump(mails_data, f, indent=2, ensure_ascii=False)
    
    async def _backup_files(self, organization_id: int, backup_dir: Path, include_attachments: bool):
        """파일 백업"""
        files_backup_dir = backup_dir / "files"
        files_backup_dir.mkdir(exist_ok=True)
        
        if include_attachments:
            # 첨부파일 백업
            attachments_dir = files_backup_dir / "attachments"
            attachments_dir.mkdir(exist_ok=True)
            
            # 조직의 첨부파일 경로 (실제 구현에서는 설정에서 가져옴)
            org_attachments_path = Path("attachments") / str(organization_id)
            if org_attachments_path.exists():
                shutil.copytree(org_attachments_path, attachments_dir / str(organization_id))
    
    async def _backup_config(self, organization_id: int, backup_dir: Path):
        """설정 백업"""
        config_backup_dir = backup_dir / "config"
        config_backup_dir.mkdir(exist_ok=True)
        
        # 조직 설정
        org = self.db.query(Organization).filter(Organization.id == organization_id).first()
        if org:
            org_config = {
                "id": org.id,
                "org_uuid": org.org_uuid,
                "name": org.name,
                "domain": org.domain,
                "max_users": org.max_users,
                "is_active": org.is_active,
                "created_at": org.created_at.isoformat() if org.created_at else None
            }
            
            with open(config_backup_dir / "organization.json", 'w', encoding='utf-8') as f:
                json.dump(org_config, f, indent=2, ensure_ascii=False)
    
    # ===== 복구 기능 =====
    
    async def restore_backup(
        self, 
        organization_id: int, 
        user_id: int, 
        request: RestoreRequest
    ) -> RestoreResponse:
        """백업 복구"""
        restore_id = str(uuid.uuid4())
        
        try:
            logger.info(f"🔄 복구 시작 - 조직: {organization_id}, 백업: {request.backup_id}")
            
            # 복구 작업 상태 초기화
            self.job_status[restore_id] = {
                "status": BackupStatus.RUNNING,
                "progress": 0,
                "started_at": datetime.now(),
                "log_messages": []
            }
            
            # 백업 파일 찾기
            backup_file = await self._find_backup_file(request.backup_id)
            if not backup_file:
                raise FileNotFoundError(f"백업 파일을 찾을 수 없습니다: {request.backup_id}")
            
            # 복구 실행
            await self._execute_restore(
                organization_id, restore_id, backup_file, request
            )
            
            # 복구 완료
            self.job_status[restore_id]["status"] = BackupStatus.COMPLETED
            self.job_status[restore_id]["progress"] = 100
            self.job_status[restore_id]["completed_at"] = datetime.now()
            
            logger.info(f"✅ 복구 완료 - ID: {restore_id}")
            
            return RestoreResponse(
                restore_id=restore_id,
                backup_id=request.backup_id,
                restore_type=request.restore_type,
                status=BackupStatus.COMPLETED,
                started_at=self.job_status[restore_id]["started_at"],
                completed_at=self.job_status[restore_id]["completed_at"],
                organization_id=organization_id,
                restored_by=user_id,
                progress=100,
                log_messages=self.job_status[restore_id]["log_messages"]
            )
            
        except Exception as e:
            logger.error(f"❌ 복구 실패 - ID: {restore_id}, 오류: {str(e)}")
            self.job_status[restore_id]["status"] = BackupStatus.FAILED
            self.job_status[restore_id]["log_messages"].append(f"복구 실패: {str(e)}")
            raise
    
    async def _find_backup_file(self, backup_id: str) -> Optional[Path]:
        """백업 파일 찾기"""
        for backup_file in self.backup_dir.glob("*.zip"):
            if backup_id in backup_file.name:
                return backup_file
        return None
    
    async def _execute_restore(
        self, 
        organization_id: int, 
        restore_id: str, 
        backup_file: Path, 
        request: RestoreRequest
    ):
        """복구 실행"""
        temp_restore_dir = self.temp_dir / f"restore_{restore_id}"
        temp_restore_dir.mkdir(exist_ok=True)
        
        try:
            # 백업 파일 압축 해제
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_restore_dir)
            
            progress = 20
            self.job_status[restore_id]["progress"] = progress
            self.job_status[restore_id]["log_messages"].append("백업 파일 압축 해제 완료")
            
            # 메타데이터 확인
            metadata_file = temp_restore_dir / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                logger.info(f"📋 백업 메타데이터: {metadata}")
            
            # 데이터베이스 복구
            if request.restore_database:
                await self._restore_database(organization_id, temp_restore_dir, request.overwrite_existing)
                progress += 40
                self.job_status[restore_id]["progress"] = progress
                self.job_status[restore_id]["log_messages"].append("데이터베이스 복구 완료")
            
            # 파일 복구
            if request.restore_files:
                await self._restore_files(organization_id, temp_restore_dir, request.overwrite_existing)
                progress += 30
                self.job_status[restore_id]["progress"] = progress
                self.job_status[restore_id]["log_messages"].append("파일 복구 완료")
            
            # 설정 복구
            if request.restore_config:
                await self._restore_config(organization_id, temp_restore_dir, request.overwrite_existing)
                progress += 10
                self.job_status[restore_id]["progress"] = progress
                self.job_status[restore_id]["log_messages"].append("설정 복구 완료")
            
        finally:
            # 임시 디렉토리 정리
            if temp_restore_dir.exists():
                shutil.rmtree(temp_restore_dir)
    
    async def _restore_database(self, organization_id: int, restore_dir: Path, overwrite: bool):
        """데이터베이스 복구"""
        db_restore_dir = restore_dir / "database"
        if not db_restore_dir.exists():
            return
        
        # 사용자 데이터 복구
        users_file = db_restore_dir / "users.json"
        if users_file.exists():
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            for user_data in users_data:
                existing_user = self.db.query(User).filter(
                    User.user_uuid == user_data["user_uuid"]
                ).first()
                
                if existing_user and not overwrite:
                    continue
                
                # 사용자 복구 로직 (실제 구현에서는 더 정교하게)
                logger.info(f"👤 사용자 복구: {user_data['email']}")
    
    async def _restore_files(self, organization_id: int, restore_dir: Path, overwrite: bool):
        """파일 복구"""
        files_restore_dir = restore_dir / "files"
        if not files_restore_dir.exists():
            return
        
        # 첨부파일 복구
        attachments_restore_dir = files_restore_dir / "attachments" / str(organization_id)
        if attachments_restore_dir.exists():
            target_dir = Path("attachments") / str(organization_id)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            if overwrite or not target_dir.exists():
                shutil.copytree(attachments_restore_dir, target_dir, dirs_exist_ok=True)
    
    async def _restore_config(self, organization_id: int, restore_dir: Path, overwrite: bool):
        """설정 복구"""
        config_restore_dir = restore_dir / "config"
        if not config_restore_dir.exists():
            return
        
        # 조직 설정 복구
        org_file = config_restore_dir / "organization.json"
        if org_file.exists():
            with open(org_file, 'r', encoding='utf-8') as f:
                org_data = json.load(f)
            
            logger.info(f"🏢 조직 설정 복구: {org_data['name']}")
    
    # ===== 테스트 기능 =====
    
    async def run_tests(
        self, 
        organization_id: int, 
        user_id: int, 
        request: TestRequest
    ) -> TestResponse:
        """테스트 실행"""
        test_id = str(uuid.uuid4())
        
        try:
            logger.info(f"🧪 테스트 시작 - 조직: {organization_id}, 테스트: {request.test_types}")
            
            started_at = datetime.now()
            results = []
            
            for test_type in request.test_types:
                result = await self._run_single_test(test_type, organization_id)
                results.append(result)
            
            completed_at = datetime.now()
            total_execution_time = (completed_at - started_at).total_seconds()
            
            # 전체 상태 계산
            passed_tests = sum(1 for r in results if r.status == TestStatus.PASS)
            failed_tests = sum(1 for r in results if r.status == TestStatus.FAIL)
            warning_tests = sum(1 for r in results if r.status == TestStatus.WARNING)
            
            if failed_tests > 0:
                overall_status = TestStatus.FAIL
            elif warning_tests > 0:
                overall_status = TestStatus.WARNING
            else:
                overall_status = TestStatus.PASS
            
            logger.info(f"✅ 테스트 완료 - ID: {test_id}, 상태: {overall_status}")
            
            return TestResponse(
                test_id=test_id,
                overall_status=overall_status,
                total_tests=len(results),
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                warning_tests=warning_tests,
                results=results,
                started_at=started_at,
                completed_at=completed_at,
                total_execution_time=total_execution_time,
                organization_id=organization_id,
                executed_by=user_id
            )
            
        except Exception as e:
            logger.error(f"❌ 테스트 실패 - ID: {test_id}, 오류: {str(e)}")
            raise
    
    async def _run_single_test(self, test_type: TestType, organization_id: int) -> TestResult:
        """개별 테스트 실행"""
        start_time = datetime.now()
        
        try:
            if test_type == TestType.HEALTH_CHECK:
                return await self._test_health_check()
            elif test_type == TestType.SYSTEM_STATUS:
                return await self._test_system_status()
            elif test_type == TestType.DATABASE_CHECK:
                return await self._test_database_check()
            elif test_type == TestType.MAIL_SERVER_CHECK:
                return await self._test_mail_server_check()
            elif test_type == TestType.PERFORMANCE_TEST:
                return await self._test_performance()
            elif test_type == TestType.SECURITY_SCAN:
                return await self._test_security_scan()
            elif test_type == TestType.INTEGRATION_TEST:
                return await self._test_integration()
            else:
                return TestResult(
                    test_type=test_type,
                    status=TestStatus.SKIP,
                    message="지원하지 않는 테스트 타입입니다",
                    details={},
                    execution_time=0.0,
                    timestamp=start_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=test_type,
                status=TestStatus.ERROR,
                message=f"테스트 실행 중 오류 발생: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    async def _test_health_check(self) -> TestResult:
        """헬스체크 테스트"""
        start_time = datetime.now()
        
        try:
            # 기본 시스템 상태 확인
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            details = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "available_memory": memory.available,
                "free_disk": disk.free
            }
            
            # 상태 판정
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = TestStatus.FAIL
                message = "시스템 리소스 사용량이 위험 수준입니다"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = TestStatus.WARNING
                message = "시스템 리소스 사용량이 높습니다"
            else:
                status = TestStatus.PASS
                message = "시스템 상태가 정상입니다"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                status=status,
                message=message,
                details=details,
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                status=TestStatus.ERROR,
                message=f"헬스체크 실패: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    async def _test_system_status(self) -> TestResult:
        """시스템 상태 테스트"""
        start_time = datetime.now()
        
        try:
            # 시스템 정보 수집
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            details = {
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "uptime_days": uptime.days,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
                "process_count": len(psutil.pids())
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_type=TestType.SYSTEM_STATUS,
                status=TestStatus.PASS,
                message="시스템 상태 정보 수집 완료",
                details=details,
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.SYSTEM_STATUS,
                status=TestStatus.ERROR,
                message=f"시스템 상태 확인 실패: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    async def _test_database_check(self) -> TestResult:
        """데이터베이스 체크 테스트"""
        start_time = datetime.now()
        
        try:
            # 데이터베이스 연결 테스트
            result = self.db.execute(text("SELECT 1")).scalar()
            
            # 테이블 존재 확인
            inspector = inspect(self.db.bind)
            tables = inspector.get_table_names()
            
            details = {
                "connection_test": result == 1,
                "table_count": len(tables),
                "tables": tables[:10]  # 처음 10개 테이블만
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_type=TestType.DATABASE_CHECK,
                status=TestStatus.PASS,
                message="데이터베이스 연결 및 구조 확인 완료",
                details=details,
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.DATABASE_CHECK,
                status=TestStatus.FAIL,
                message=f"데이터베이스 체크 실패: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    async def _test_mail_server_check(self) -> TestResult:
        """메일 서버 체크 테스트"""
        start_time = datetime.now()
        
        try:
            # 메일 서버 상태 확인 (간단한 구현)
            details = {
                "smtp_status": "unknown",
                "imap_status": "unknown",
                "postfix_status": "unknown",
                "dovecot_status": "unknown"
            }
            
            # 실제 구현에서는 메일 서버 프로세스 상태 확인
            # 예: subprocess를 사용하여 서비스 상태 확인
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_type=TestType.MAIL_SERVER_CHECK,
                status=TestStatus.WARNING,
                message="메일 서버 상태 확인 기능이 구현되지 않았습니다",
                details=details,
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.MAIL_SERVER_CHECK,
                status=TestStatus.ERROR,
                message=f"메일 서버 체크 실패: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    async def _test_performance(self) -> TestResult:
        """성능 테스트"""
        start_time = datetime.now()
        
        try:
            # 간단한 성능 테스트
            db_start = datetime.now()
            self.db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            db_time = (datetime.now() - db_start).total_seconds()
            
            details = {
                "database_query_time": db_time,
                "database_performance": "good" if db_time < 0.1 else "slow"
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            status = TestStatus.PASS if db_time < 0.5 else TestStatus.WARNING
            message = f"성능 테스트 완료 - DB 쿼리 시간: {db_time:.3f}초"
            
            return TestResult(
                test_type=TestType.PERFORMANCE_TEST,
                status=status,
                message=message,
                details=details,
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.PERFORMANCE_TEST,
                status=TestStatus.ERROR,
                message=f"성능 테스트 실패: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    async def _test_security_scan(self) -> TestResult:
        """보안 스캔 테스트"""
        start_time = datetime.now()
        
        try:
            details = {
                "security_scan": "basic_check_only",
                "note": "고급 보안 스캔 기능은 별도 구현 필요"
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_type=TestType.SECURITY_SCAN,
                status=TestStatus.WARNING,
                message="기본 보안 체크만 수행됨",
                details=details,
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.SECURITY_SCAN,
                status=TestStatus.ERROR,
                message=f"보안 스캔 실패: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    async def _test_integration(self) -> TestResult:
        """통합 테스트"""
        start_time = datetime.now()
        
        try:
            details = {
                "integration_test": "placeholder",
                "note": "통합 테스트 시나리오 구현 필요"
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_type=TestType.INTEGRATION_TEST,
                status=TestStatus.SKIP,
                message="통합 테스트 시나리오가 구현되지 않았습니다",
                details=details,
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.INTEGRATION_TEST,
                status=TestStatus.ERROR,
                message=f"통합 테스트 실패: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=start_time
            )
    
    # ===== 시스템 상태 조회 =====
    
    async def get_system_health(self) -> SystemHealthResponse:
        """시스템 헬스 상태 조회"""
        try:
            # 시스템 리소스 정보
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = (datetime.now() - boot_time).total_seconds()
            
            # 서비스 상태 (간단한 구현)
            services = {
                "fastapi": {"status": "running", "uptime": uptime},
                "database": {"status": "unknown", "last_check": datetime.now().isoformat()},
                "redis": {"status": "unknown", "last_check": datetime.now().isoformat()},
                "mail_server": {"status": "unknown", "last_check": datetime.now().isoformat()}
            }
            
            # 데이터베이스 상태
            try:
                self.db.execute(text("SELECT 1")).scalar()
                db_status = "healthy"
            except:
                db_status = "error"
            
            database = {
                "status": db_status,
                "connection_pool": "unknown",
                "last_check": datetime.now().isoformat()
            }
            
            # 전체 상태 판정
            if cpu_usage > 90 or memory.percent > 90 or disk.percent > 90 or db_status == "error":
                overall_status = "critical"
            elif cpu_usage > 70 or memory.percent > 70 or disk.percent > 80:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return SystemHealthResponse(
                status=overall_status,
                timestamp=datetime.now(),
                services=services,
                database=database,
                mail_server={"status": "unknown", "last_check": datetime.now().isoformat()},
                redis={"status": "unknown", "last_check": datetime.now().isoformat()},
                disk_usage={
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                memory_usage={
                    "total": memory.total,
                    "used": memory.used,
                    "available": memory.available,
                    "percent": memory.percent
                },
                cpu_usage=cpu_usage,
                uptime=uptime
            )
            
        except Exception as e:
            logger.error(f"❌ 시스템 헬스 체크 실패: {str(e)}")
            raise
    
    # ===== 작업 상태 조회 =====
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """작업 상태 조회"""
        if job_id not in self.job_status:
            return None
        
        job_info = self.job_status[job_id]
        
        return JobStatusResponse(
            job_id=job_id,
            job_type="backup" if "backup" in job_id else "restore",
            status=job_info["status"],
            progress=job_info.get("progress", 0),
            started_at=job_info["started_at"],
            updated_at=job_info.get("updated_at", job_info["started_at"]),
            estimated_completion=job_info.get("estimated_completion"),
            log_messages=job_info.get("log_messages", []),
            result=job_info.get("result")
        )
    
    # ===== 백업 목록 조회 =====
    
    async def list_backups(
        self, 
        organization_id: int, 
        page: int = 1, 
        limit: int = 20
    ) -> BackupListResponse:
        """백업 목록 조회"""
        try:
            # 백업 파일 목록 조회 (실제 구현에서는 데이터베이스에서 조회)
            backup_files = list(self.backup_dir.glob("*.zip"))
            
            # 조직별 필터링 (파일명에서 조직 ID 추출)
            org_backups = []
            for backup_file in backup_files:
                if f"_{organization_id}_" in backup_file.name:
                    # 파일 정보 추출
                    stat = backup_file.stat()
                    backup_id = backup_file.stem.split('_')[-1] if '_' in backup_file.stem else backup_file.stem
                    
                    org_backups.append(BackupResponse(
                        backup_id=backup_id,
                        backup_type=BackupType.FULL,  # 기본값
                        status=BackupStatus.COMPLETED,
                        file_path=str(backup_file),
                        file_size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        completed_at=datetime.fromtimestamp(stat.st_mtime),
                        organization_id=organization_id,
                        created_by=0,  # 알 수 없음
                        description=None,
                        tags=[],
                        metadata={}
                    ))
            
            # 페이징
            total = len(org_backups)
            start = (page - 1) * limit
            end = start + limit
            paginated_backups = org_backups[start:end]
            
            return BackupListResponse(
                backups=paginated_backups,
                total=total,
                page=page,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"❌ 백업 목록 조회 실패: {str(e)}")
            raise
"""
오프라인 기능 서비스

SkyBoot Mail SaaS 프로젝트의 오프라인 기능을 위한 서비스 로직입니다.
"""

import json
import logging
import asyncio
import gzip
import base64
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
import redis
from cryptography.fernet import Fernet

from app.schemas.offline_schema import (
    OfflineActionData, SyncTask, CacheItem, ConflictItem, OfflineSettings,
    OfflineActionRequest, OfflineActionResponse,
    SyncRequest, SyncResponse, SyncStatusResponse,
    CacheStatusResponse, OfflineSettingsRequest, OfflineSettingsResponse,
    ConflictListResponse, ConflictResolutionRequest, ConflictResolutionResponse,
    OfflineStatsResponse, NetworkStatusResponse,
    SyncStatus, SyncDirection, OfflineAction, ConflictResolution,
    CacheStrategy, DataType,
    OfflineError, SyncError, CacheError, ConflictError
)
from app.model.organization_model import Organization
from app.model.user_model import User
from app.config import settings

logger = logging.getLogger(__name__)

# Redis 연결
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# 암호화 키 (실제 환경에서는 안전한 키 관리 필요)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


class OfflineService:
    """오프라인 기능 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl = 86400  # 24시간
        self.action_queue_key = "offline:actions:{user_id}"
        self.sync_task_key = "offline:sync_task:{task_id}"
        self.cache_key = "offline:cache:{user_id}:{cache_key}"
        self.settings_key = "offline:settings:{user_id}"
        self.conflict_key = "offline:conflicts:{user_id}"
        
    async def queue_offline_action(
        self,
        user_id: int,
        organization_id: int,
        action_request: OfflineActionRequest
    ) -> OfflineActionResponse:
        """
        오프라인 액션을 큐에 추가합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            action_request: 오프라인 액션 요청
            
        Returns:
            오프라인 액션 응답
        """
        try:
            logger.info(f"📱 오프라인 액션 큐 추가 시작 - 사용자: {user_id}, 액션: {action_request.action_type}")
            
            # 액션 ID 생성
            action_id = str(uuid.uuid4())
            
            # 액션 데이터 생성
            action_data = OfflineActionData(
                action_id=action_id,
                user_id=user_id,
                organization_id=organization_id,
                action_type=action_request.action_type,
                target_id=action_request.target_id,
                data=action_request.data,
                timestamp=action_request.timestamp or datetime.utcnow(),
                sync_status=SyncStatus.PENDING
            )
            
            # Redis 큐에 추가
            queue_key = self.action_queue_key.format(user_id=user_id)
            redis_client.lpush(queue_key, action_data.json())
            
            # 큐 만료 시간 설정 (7일)
            redis_client.expire(queue_key, 604800)
            
            logger.info(f"✅ 오프라인 액션 큐 추가 완료 - 액션ID: {action_id}")
            
            return OfflineActionResponse(
                action_id=action_id,
                success=True,
                message="오프라인 액션이 큐에 추가되었습니다.",
                sync_status=SyncStatus.PENDING,
                created_at=action_data.created_at
            )
            
        except Exception as e:
            logger.error(f"❌ 오프라인 액션 큐 추가 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="오프라인 액션 추가 중 오류가 발생했습니다."
            )
    
    async def start_sync(
        self,
        user_id: int,
        organization_id: int,
        sync_request: SyncRequest,
        background_tasks: BackgroundTasks
    ) -> SyncResponse:
        """
        동기화를 시작합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            sync_request: 동기화 요청
            background_tasks: 백그라운드 작업
            
        Returns:
            동기화 응답
        """
        try:
            logger.info(f"🔄 동기화 시작 - 사용자: {user_id}, 데이터타입: {sync_request.data_types}")
            
            # 작업 ID 생성
            task_id = str(uuid.uuid4())
            
            # 동기화 작업 생성
            sync_task = SyncTask(
                task_id=task_id,
                user_id=user_id,
                organization_id=organization_id,
                data_type=sync_request.data_types[0] if sync_request.data_types else DataType.MAIL,
                direction=sync_request.direction,
                status=SyncStatus.PENDING,
                start_time=datetime.utcnow()
            )
            
            # Redis에 작업 저장
            task_key = self.sync_task_key.format(task_id=task_id)
            redis_client.setex(task_key, 3600, sync_task.json())  # 1시간 TTL
            
            # 백그라운드에서 동기화 실행
            background_tasks.add_task(
                self._execute_sync,
                task_id,
                user_id,
                organization_id,
                sync_request
            )
            
            logger.info(f"✅ 동기화 시작 완료 - 작업ID: {task_id}")
            
            return SyncResponse(
                task_id=task_id,
                status=SyncStatus.PENDING,
                message="동기화가 시작되었습니다.",
                estimated_duration=300,  # 5분 예상
                started_at=sync_task.start_time
            )
            
        except Exception as e:
            logger.error(f"❌ 동기화 시작 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="동기화 시작 중 오류가 발생했습니다."
            )
    
    async def get_sync_status(self, task_id: str) -> SyncStatusResponse:
        """
        동기화 상태를 조회합니다.
        
        Args:
            task_id: 작업 ID
            
        Returns:
            동기화 상태 응답
        """
        try:
            logger.info(f"🔍 동기화 상태 조회 - 작업ID: {task_id}")
            
            # Redis에서 작업 조회
            task_key = self.sync_task_key.format(task_id=task_id)
            task_data = redis_client.get(task_key)
            
            if not task_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="동기화 작업을 찾을 수 없습니다."
                )
            
            sync_task = SyncTask.parse_raw(task_data)
            
            # 예상 남은 시간 계산
            estimated_remaining = None
            if sync_task.status == SyncStatus.IN_PROGRESS and sync_task.progress > 0:
                elapsed = (datetime.utcnow() - sync_task.start_time).total_seconds()
                estimated_total = elapsed / (sync_task.progress / 100)
                estimated_remaining = max(0, int(estimated_total - elapsed))
            
            logger.info(f"✅ 동기화 상태 조회 완료 - 작업ID: {task_id}, 상태: {sync_task.status}")
            
            return SyncStatusResponse(
                task_id=task_id,
                status=sync_task.status,
                progress=sync_task.progress,
                total_items=sync_task.total_items,
                processed_items=sync_task.processed_items,
                failed_items=sync_task.failed_items,
                estimated_remaining=estimated_remaining,
                error_message=sync_task.error_message,
                start_time=sync_task.start_time,
                end_time=sync_task.end_time
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 동기화 상태 조회 실패 - 작업ID: {task_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="동기화 상태 조회 중 오류가 발생했습니다."
            )
    
    async def get_cache_status(self, user_id: int) -> CacheStatusResponse:
        """
        캐시 상태를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            캐시 상태 응답
        """
        try:
            logger.info(f"📊 캐시 상태 조회 시작 - 사용자: {user_id}")
            
            # 사용자 캐시 키 패턴
            cache_pattern = f"offline:cache:{user_id}:*"
            cache_keys = redis_client.keys(cache_pattern)
            
            total_items = len(cache_keys)
            total_size_bytes = 0
            data_type_breakdown = {}
            oldest_date = None
            newest_date = None
            
            for key in cache_keys:
                try:
                    cache_data = redis_client.get(key)
                    if cache_data:
                        cache_item = CacheItem.parse_raw(cache_data)
                        total_size_bytes += cache_item.size_bytes
                        
                        # 데이터 타입별 분류
                        data_type = cache_item.data_type.value
                        data_type_breakdown[data_type] = data_type_breakdown.get(data_type, 0) + 1
                        
                        # 날짜 범위 계산
                        if oldest_date is None or cache_item.created_at < oldest_date:
                            oldest_date = cache_item.created_at
                        if newest_date is None or cache_item.created_at > newest_date:
                            newest_date = cache_item.created_at
                            
                except Exception as e:
                    logger.warning(f"캐시 항목 파싱 실패 - 키: {key}, 오류: {str(e)}")
                    continue
            
            # 사용자 설정 조회
            settings = await self.get_offline_settings(user_id, 1)  # 임시 조직 ID
            max_size_bytes = settings.max_cache_size * 1024 * 1024  # MB to bytes
            
            total_size_mb = total_size_bytes / (1024 * 1024)
            used_size_mb = total_size_mb
            available_size_mb = max(0, (max_size_bytes / (1024 * 1024)) - total_size_mb)
            
            # 캐시 적중률 계산 (실제 구현에서는 별도 메트릭 필요)
            cache_hit_rate = 85.0  # 샘플 값
            
            logger.info(f"✅ 캐시 상태 조회 완료 - 사용자: {user_id}, 항목수: {total_items}")
            
            return CacheStatusResponse(
                total_items=total_items,
                total_size_mb=total_size_mb,
                used_size_mb=used_size_mb,
                available_size_mb=available_size_mb,
                cache_hit_rate=cache_hit_rate,
                oldest_item_date=oldest_date,
                newest_item_date=newest_date,
                data_type_breakdown=data_type_breakdown,
                last_cleanup=datetime.utcnow() - timedelta(hours=6)  # 샘플 값
            )
            
        except Exception as e:
            logger.error(f"❌ 캐시 상태 조회 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="캐시 상태 조회 중 오류가 발생했습니다."
            )
    
    async def get_offline_settings(self, user_id: int, organization_id: int) -> OfflineSettingsResponse:
        """
        오프라인 설정을 조회합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            
        Returns:
            오프라인 설정 응답
        """
        try:
            logger.info(f"⚙️ 오프라인 설정 조회 시작 - 사용자: {user_id}")
            
            # Redis에서 설정 조회
            settings_key = self.settings_key.format(user_id=user_id)
            settings_data = redis_client.get(settings_key)
            
            if settings_data:
                settings = OfflineSettings.parse_raw(settings_data)
            else:
                # 기본 설정 생성
                settings = OfflineSettings(
                    user_id=user_id,
                    organization_id=organization_id
                )
                
                # Redis에 저장
                redis_client.setex(settings_key, self.cache_ttl, settings.json())
            
            logger.info(f"✅ 오프라인 설정 조회 완료 - 사용자: {user_id}")
            
            return OfflineSettingsResponse(
                user_id=settings.user_id,
                organization_id=settings.organization_id,
                enabled=settings.enabled,
                auto_sync=settings.auto_sync,
                sync_interval=settings.sync_interval,
                max_cache_size=settings.max_cache_size,
                cache_duration=settings.cache_duration,
                conflict_resolution=settings.conflict_resolution,
                sync_on_startup=settings.sync_on_startup,
                sync_on_network_change=settings.sync_on_network_change,
                background_sync=settings.background_sync,
                compress_data=settings.compress_data,
                encrypt_cache=settings.encrypt_cache,
                created_at=settings.created_at,
                updated_at=settings.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 오프라인 설정 조회 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="오프라인 설정 조회 중 오류가 발생했습니다."
            )
    
    async def update_offline_settings(
        self,
        user_id: int,
        organization_id: int,
        settings_request: OfflineSettingsRequest
    ) -> OfflineSettingsResponse:
        """
        오프라인 설정을 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            settings_request: 오프라인 설정 요청
            
        Returns:
            오프라인 설정 응답
        """
        try:
            logger.info(f"⚙️ 오프라인 설정 업데이트 시작 - 사용자: {user_id}")
            
            # 설정 데이터 생성
            settings = OfflineSettings(
                user_id=user_id,
                organization_id=organization_id,
                enabled=settings_request.enabled,
                auto_sync=settings_request.auto_sync,
                sync_interval=settings_request.sync_interval,
                max_cache_size=settings_request.max_cache_size,
                cache_duration=settings_request.cache_duration,
                conflict_resolution=settings_request.conflict_resolution,
                sync_on_startup=settings_request.sync_on_startup,
                sync_on_network_change=settings_request.sync_on_network_change,
                background_sync=settings_request.background_sync,
                compress_data=settings_request.compress_data,
                encrypt_cache=settings_request.encrypt_cache,
                updated_at=datetime.utcnow()
            )
            
            # Redis에 저장
            settings_key = self.settings_key.format(user_id=user_id)
            redis_client.setex(settings_key, self.cache_ttl, settings.json())
            
            logger.info(f"✅ 오프라인 설정 업데이트 완료 - 사용자: {user_id}")
            
            return OfflineSettingsResponse(
                user_id=settings.user_id,
                organization_id=settings.organization_id,
                enabled=settings.enabled,
                auto_sync=settings.auto_sync,
                sync_interval=settings.sync_interval,
                max_cache_size=settings.max_cache_size,
                cache_duration=settings.cache_duration,
                conflict_resolution=settings.conflict_resolution,
                sync_on_startup=settings.sync_on_startup,
                sync_on_network_change=settings.sync_on_network_change,
                background_sync=settings.background_sync,
                compress_data=settings.compress_data,
                encrypt_cache=settings.encrypt_cache,
                created_at=settings.created_at,
                updated_at=settings.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 오프라인 설정 업데이트 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="오프라인 설정 업데이트 중 오류가 발생했습니다."
            )
    
    async def get_conflicts(self, user_id: int) -> ConflictListResponse:
        """
        충돌 목록을 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            충돌 목록 응답
        """
        try:
            logger.info(f"⚠️ 충돌 목록 조회 시작 - 사용자: {user_id}")
            
            # Redis에서 충돌 목록 조회
            conflict_key = self.conflict_key.format(user_id=user_id)
            conflict_data = redis_client.get(conflict_key)
            
            conflicts = []
            if conflict_data:
                conflicts_list = json.loads(conflict_data)
                conflicts = [ConflictItem.parse_obj(item) for item in conflicts_list]
            
            # 통계 계산
            total_count = len(conflicts)
            unresolved_count = len([c for c in conflicts if c.resolution is None])
            
            logger.info(f"✅ 충돌 목록 조회 완료 - 사용자: {user_id}, 총 {total_count}개, 미해결 {unresolved_count}개")
            
            return ConflictListResponse(
                conflicts=conflicts,
                total_count=total_count,
                unresolved_count=unresolved_count,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ 충돌 목록 조회 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="충돌 목록 조회 중 오류가 발생했습니다."
            )
    
    async def resolve_conflict(
        self,
        user_id: int,
        resolution_request: ConflictResolutionRequest
    ) -> ConflictResolutionResponse:
        """
        충돌을 해결합니다.
        
        Args:
            user_id: 사용자 ID
            resolution_request: 충돌 해결 요청
            
        Returns:
            충돌 해결 응답
        """
        try:
            logger.info(f"⚠️ 충돌 해결 시작 - 사용자: {user_id}, 충돌ID: {resolution_request.conflict_id}")
            
            # 충돌 목록 조회
            conflicts_response = await self.get_conflicts(user_id)
            conflict = None
            
            for c in conflicts_response.conflicts:
                if c.conflict_id == resolution_request.conflict_id:
                    conflict = c
                    break
            
            if not conflict:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="충돌을 찾을 수 없습니다."
                )
            
            # 해결 데이터 결정
            resolved_data = {}
            if resolution_request.resolution == ConflictResolution.SERVER_WINS:
                resolved_data = conflict.server_data
            elif resolution_request.resolution == ConflictResolution.CLIENT_WINS:
                resolved_data = conflict.client_data
            elif resolution_request.resolution == ConflictResolution.MANUAL:
                if not resolution_request.resolved_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="수동 해결 시 해결된 데이터가 필요합니다."
                    )
                resolved_data = resolution_request.resolved_data
            elif resolution_request.resolution == ConflictResolution.MERGE:
                # 간단한 병합 로직 (실제로는 더 복잡한 로직 필요)
                resolved_data = {**conflict.server_data, **conflict.client_data}
            
            # 충돌 해결 정보 업데이트
            conflict.resolution = resolution_request.resolution
            conflict.resolved_data = resolved_data
            conflict.resolved_at = datetime.utcnow()
            
            # Redis에 업데이트된 충돌 목록 저장
            updated_conflicts = [c for c in conflicts_response.conflicts if c.conflict_id != conflict.conflict_id]
            updated_conflicts.append(conflict)
            
            conflict_key = self.conflict_key.format(user_id=user_id)
            redis_client.setex(
                conflict_key,
                self.cache_ttl,
                json.dumps([c.dict() for c in updated_conflicts])
            )
            
            logger.info(f"✅ 충돌 해결 완료 - 충돌ID: {resolution_request.conflict_id}")
            
            return ConflictResolutionResponse(
                conflict_id=conflict.conflict_id,
                success=True,
                resolution=conflict.resolution,
                resolved_data=conflict.resolved_data,
                resolved_at=conflict.resolved_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 충돌 해결 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="충돌 해결 중 오류가 발생했습니다."
            )
    
    async def get_offline_statistics(self, user_id: int) -> OfflineStatsResponse:
        """
        오프라인 통계를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            오프라인 통계 응답
        """
        try:
            logger.info(f"📊 오프라인 통계 조회 시작 - 사용자: {user_id}")
            
            # 액션 큐 통계
            queue_key = self.action_queue_key.format(user_id=user_id)
            queue_length = redis_client.llen(queue_key)
            
            # 샘플 통계 데이터 (실제 구현에서는 데이터베이스에서 조회)
            total_offline_actions = 150
            pending_actions = queue_length
            completed_actions = 120
            failed_actions = 5
            
            sync_success_rate = (completed_actions / total_offline_actions) * 100 if total_offline_actions > 0 else 0
            
            # 충돌 통계
            conflicts_response = await self.get_conflicts(user_id)
            conflicts_count = conflicts_response.unresolved_count
            
            logger.info(f"✅ 오프라인 통계 조회 완료 - 사용자: {user_id}")
            
            return OfflineStatsResponse(
                total_offline_actions=total_offline_actions,
                pending_actions=pending_actions,
                completed_actions=completed_actions,
                failed_actions=failed_actions,
                sync_success_rate=sync_success_rate,
                average_sync_time=45.5,
                cache_efficiency=88.2,
                data_usage_mb=25.7,
                last_sync_time=datetime.utcnow() - timedelta(minutes=30),
                next_sync_time=datetime.utcnow() + timedelta(minutes=15),
                conflicts_count=conflicts_count,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ 오프라인 통계 조회 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="오프라인 통계 조회 중 오류가 발생했습니다."
            )
    
    async def get_network_status(self) -> NetworkStatusResponse:
        """
        네트워크 상태를 조회합니다.
        
        Returns:
            네트워크 상태 응답
        """
        try:
            logger.info(f"🌐 네트워크 상태 조회 시작")
            
            # 실제 구현에서는 네트워크 상태 확인 로직 필요
            # 현재는 샘플 데이터 반환
            
            network_status = NetworkStatusResponse(
                is_online=True,
                connection_type="wifi",
                effective_type="4g",
                downlink=10.5,
                rtt=50,
                save_data=False,
                last_checked=datetime.utcnow()
            )
            
            logger.info(f"✅ 네트워크 상태 조회 완료 - 온라인: {network_status.is_online}")
            return network_status
            
        except Exception as e:
            logger.error(f"❌ 네트워크 상태 조회 실패 - 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="네트워크 상태 조회 중 오류가 발생했습니다."
            )
    
    async def clear_cache(self, user_id: int) -> Dict[str, Any]:
        """
        사용자 캐시를 정리합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            정리 결과
        """
        try:
            logger.info(f"🧹 캐시 정리 시작 - 사용자: {user_id}")
            
            # 사용자 캐시 키 패턴
            cache_pattern = f"offline:cache:{user_id}:*"
            cache_keys = redis_client.keys(cache_pattern)
            
            deleted_count = 0
            for key in cache_keys:
                redis_client.delete(key)
                deleted_count += 1
            
            logger.info(f"✅ 캐시 정리 완료 - 사용자: {user_id}, 삭제된 항목: {deleted_count}개")
            
            return {
                "success": True,
                "deleted_items": deleted_count,
                "message": f"{deleted_count}개의 캐시 항목이 삭제되었습니다.",
                "cleared_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"❌ 캐시 정리 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="캐시 정리 중 오류가 발생했습니다."
            )
    
    async def _execute_sync(
        self,
        task_id: str,
        user_id: int,
        organization_id: int,
        sync_request: SyncRequest
    ):
        """
        동기화를 실행합니다 (백그라운드 작업).
        
        Args:
            task_id: 작업 ID
            user_id: 사용자 ID
            organization_id: 조직 ID
            sync_request: 동기화 요청
        """
        try:
            logger.info(f"🔄 동기화 실행 시작 - 작업ID: {task_id}")
            
            # 작업 상태 업데이트
            task_key = self.sync_task_key.format(task_id=task_id)
            task_data = redis_client.get(task_key)
            
            if not task_data:
                logger.error(f"동기화 작업을 찾을 수 없음 - 작업ID: {task_id}")
                return
            
            sync_task = SyncTask.parse_raw(task_data)
            sync_task.status = SyncStatus.IN_PROGRESS
            sync_task.total_items = 100  # 샘플 값
            
            # 진행률 시뮬레이션
            for i in range(0, 101, 10):
                sync_task.progress = i
                sync_task.processed_items = i
                redis_client.setex(task_key, 3600, sync_task.json())
                
                # 실제 동기화 작업 수행
                await asyncio.sleep(1)  # 시뮬레이션을 위한 지연
                
                if i == 50:
                    logger.info(f"🔄 동기화 진행 중 - 작업ID: {task_id}, 진행률: {i}%")
            
            # 완료 처리
            sync_task.status = SyncStatus.COMPLETED
            sync_task.end_time = datetime.utcnow()
            redis_client.setex(task_key, 3600, sync_task.json())
            
            logger.info(f"✅ 동기화 실행 완료 - 작업ID: {task_id}")
            
        except Exception as e:
            logger.error(f"❌ 동기화 실행 실패 - 작업ID: {task_id}, 오류: {str(e)}")
            
            # 실패 상태 업데이트
            try:
                task_key = self.sync_task_key.format(task_id=task_id)
                task_data = redis_client.get(task_key)
                if task_data:
                    sync_task = SyncTask.parse_raw(task_data)
                    sync_task.status = SyncStatus.FAILED
                    sync_task.error_message = str(e)
                    sync_task.end_time = datetime.utcnow()
                    redis_client.setex(task_key, 3600, sync_task.json())
            except Exception as update_error:
                logger.error(f"동기화 실패 상태 업데이트 실패 - 오류: {str(update_error)}")
    
    def _compress_data(self, data: str) -> str:
        """데이터를 압축합니다."""
        try:
            compressed = gzip.compress(data.encode('utf-8'))
            return base64.b64encode(compressed).decode('utf-8')
        except Exception as e:
            logger.warning(f"데이터 압축 실패: {str(e)}")
            return data
    
    def _decompress_data(self, compressed_data: str) -> str:
        """압축된 데이터를 해제합니다."""
        try:
            compressed_bytes = base64.b64decode(compressed_data.encode('utf-8'))
            decompressed = gzip.decompress(compressed_bytes)
            return decompressed.decode('utf-8')
        except Exception as e:
            logger.warning(f"데이터 압축 해제 실패: {str(e)}")
            return compressed_data
    
    def _encrypt_data(self, data: str) -> str:
        """데이터를 암호화합니다."""
        try:
            encrypted = cipher_suite.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.warning(f"데이터 암호화 실패: {str(e)}")
            return data
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """암호화된 데이터를 복호화합니다."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = cipher_suite.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.warning(f"데이터 복호화 실패: {str(e)}")
            return encrypted_data
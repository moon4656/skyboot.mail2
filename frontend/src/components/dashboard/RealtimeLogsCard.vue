<template>
  <div class="realtime-logs-card">
    <va-card class="logs-card">
      <va-card-title class="card-title">
        <va-icon name="list_alt" color="info" class="title-icon" />
        실시간 활동 로그
        <div class="title-actions">
          <va-button 
            @click="$emit('refresh')"
            icon="refresh"
            preset="secondary"
            size="small"
            :loading="loading"
            class="refresh-btn"
          />
          <va-button 
            @click="toggleAutoRefresh"
            :icon="autoRefresh ? 'pause' : 'play_arrow'"
            :preset="autoRefresh ? 'primary' : 'secondary'"
            size="small"
            class="auto-refresh-btn"
          />
        </div>
      </va-card-title>
      
      <va-card-content>
        <div class="logs-content">
          <!-- 로딩 상태 -->
          <div v-if="loading" class="logs-loading">
            <va-progress-circle indeterminate size="small" />
            <span>로그를 불러오는 중...</span>
          </div>

          <!-- 로그 목록 -->
          <div v-else-if="logs.length > 0" class="logs-list">
            <div 
              v-for="log in logs" 
              :key="log.id"
              :class="['log-item', getLogTypeClass(log.action)]"
            >
              <div class="log-header">
                <div class="log-info">
                  <va-icon :name="getLogIcon(log.action)" :color="getLogColor(log.action)" class="log-icon" />
                  <span class="log-action">{{ formatAction(log.action) }}</span>
                  <span class="log-user">{{ log.user_email || '시스템' }}</span>
                </div>
                <span class="log-time">{{ formatTime(log.created_at) }}</span>
              </div>
              
              <div v-if="log.details" class="log-details">
                <span class="log-description">{{ formatDetails(log.details) }}</span>
              </div>
              
              <div class="log-meta">
                <span v-if="log.ip_address" class="log-ip">
                  <va-icon name="location_on" size="small" />
                  {{ log.ip_address }}
                </span>
                <span v-if="log.organization_name" class="log-org">
                  <va-icon name="business" size="small" />
                  {{ log.organization_name }}
                </span>
              </div>
            </div>
          </div>

          <!-- 빈 상태 -->
          <div v-else class="logs-empty">
            <va-icon name="inbox" size="3rem" color="secondary" />
            <p>표시할 로그가 없습니다</p>
            <p class="empty-subtitle">활동이 발생하면 여기에 표시됩니다</p>
          </div>
        </div>

        <!-- 더 보기 버튼 -->
        <div v-if="logs.length > 0" class="logs-footer">
          <va-button 
            @click="viewAllLogs"
            preset="secondary"
            size="small"
            class="view-all-btn"
          >
            전체 로그 보기
            <va-icon name="arrow_forward" />
          </va-button>
        </div>
      </va-card-content>
    </va-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// Props 정의
interface LogEntry {
  id: number
  action: string
  user_email?: string
  details?: any
  created_at: string
  ip_address?: string
  organization_name?: string
}

interface Props {
  logs: LogEntry[]
  loading: boolean
}

const props = defineProps<Props>()

// Emits 정의
const emit = defineEmits<{
  refresh: []
}>()

// 반응형 데이터
const autoRefresh = ref(false)
let autoRefreshTimer: NodeJS.Timeout | null = null

// 메서드들
const formatAction = (action: string): string => {
  const actionMap: Record<string, string> = {
    'login': '로그인',
    'logout': '로그아웃',
    'send_mail': '메일 발송',
    'receive_mail': '메일 수신',
    'delete_mail': '메일 삭제',
    'create_user': '사용자 생성',
    'update_user': '사용자 수정',
    'delete_user': '사용자 삭제',
    'create_organization': '조직 생성',
    'update_organization': '조직 수정',
    'backup_created': '백업 생성',
    'backup_restored': '백업 복원',
    'system_error': '시스템 오류',
    'api_request': 'API 요청',
    'file_upload': '파일 업로드',
    'file_download': '파일 다운로드'
  }
  return actionMap[action] || action
}

const getLogIcon = (action: string): string => {
  const iconMap: Record<string, string> = {
    'login': 'login',
    'logout': 'logout',
    'send_mail': 'send',
    'receive_mail': 'inbox',
    'delete_mail': 'delete',
    'create_user': 'person_add',
    'update_user': 'person',
    'delete_user': 'person_remove',
    'create_organization': 'business',
    'update_organization': 'edit',
    'backup_created': 'backup',
    'backup_restored': 'restore',
    'system_error': 'error',
    'api_request': 'api',
    'file_upload': 'upload',
    'file_download': 'download'
  }
  return iconMap[action] || 'info'
}

const getLogColor = (action: string): string => {
  const colorMap: Record<string, string> = {
    'login': 'success',
    'logout': 'info',
    'send_mail': 'primary',
    'receive_mail': 'primary',
    'delete_mail': 'warning',
    'create_user': 'success',
    'update_user': 'info',
    'delete_user': 'danger',
    'create_organization': 'success',
    'update_organization': 'info',
    'backup_created': 'success',
    'backup_restored': 'warning',
    'system_error': 'danger',
    'api_request': 'info',
    'file_upload': 'primary',
    'file_download': 'primary'
  }
  return colorMap[action] || 'secondary'
}

const getLogTypeClass = (action: string): string => {
  if (action.includes('error') || action.includes('delete')) {
    return 'log-error'
  }
  if (action.includes('create') || action.includes('login') || action.includes('backup')) {
    return 'log-success'
  }
  if (action.includes('update') || action.includes('send') || action.includes('receive')) {
    return 'log-info'
  }
  return 'log-default'
}

const formatDetails = (details: any): string => {
  if (typeof details === 'string') {
    return details
  }
  if (typeof details === 'object' && details !== null) {
    if (details.message) {
      return details.message
    }
    if (details.description) {
      return details.description
    }
    // 객체의 주요 정보를 문자열로 변환
    const keys = Object.keys(details)
    if (keys.length > 0) {
      return keys.slice(0, 2).map(key => `${key}: ${details[key]}`).join(', ')
    }
  }
  return '상세 정보 없음'
}

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (seconds < 60) {
    return `${seconds}초 전`
  } else if (minutes < 60) {
    return `${minutes}분 전`
  } else if (hours < 24) {
    return `${hours}시간 전`
  } else {
    return date.toLocaleDateString('ko-KR') + ' ' + date.toLocaleTimeString('ko-KR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  autoRefreshTimer = setInterval(() => {
    emit('refresh')
  }, 10000) // 10초마다 새로고침
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

const viewAllLogs = () => {
  // 전체 로그 페이지로 이동하는 로직
  // 라우터를 사용하여 로그 페이지로 이동
  console.log('전체 로그 페이지로 이동')
}

// 컴포넌트 마운트/언마운트 시
onMounted(() => {
  // 기본적으로 자동 새로고침 시작
  autoRefresh.value = true
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.realtime-logs-card {
  width: 100%;
}

.logs-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.title-icon {
  font-size: 1.5rem;
}

.title-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.logs-content {
  min-height: 300px;
}

.logs-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 200px;
  color: #7f8c8d;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid transparent;
  background-color: #f8f9fa;
  transition: all 0.3s ease;
}

.log-item:hover {
  background-color: #e9ecef;
  transform: translateX(4px);
}

.log-success {
  border-left-color: #27ae60;
}

.log-info {
  border-left-color: #3498db;
}

.log-error {
  border-left-color: #e74c3c;
}

.log-default {
  border-left-color: #95a5a6;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-icon {
  font-size: 1.2rem;
}

.log-action {
  font-weight: 600;
  color: #2c3e50;
}

.log-user {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.log-time {
  color: #95a5a6;
  font-size: 0.85rem;
  font-weight: 500;
}

.log-details {
  margin-bottom: 8px;
}

.log-description {
  color: #5a6c7d;
  font-size: 0.9rem;
  line-height: 1.4;
}

.log-meta {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  color: #95a5a6;
}

.log-ip,
.log-org {
  display: flex;
  align-items: center;
  gap: 4px;
}

.logs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #7f8c8d;
  text-align: center;
}

.empty-subtitle {
  font-size: 0.85rem;
  margin-top: 8px;
  opacity: 0.8;
}

.logs-footer {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ecf0f1;
  text-align: center;
}

.view-all-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 768px) {
  .log-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .log-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .title-actions {
    flex-direction: column;
    gap: 4px;
  }
}

@media (max-width: 480px) {
  .log-item {
    padding: 12px;
  }
  
  .log-info {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .card-title {
    font-size: 1.1rem;
    flex-wrap: wrap;
  }
}
</style>
<template>
  <div class="system-status-card">
    <va-card class="status-card">
      <va-card-title class="card-title">
        <va-icon :name="statusIcon" :color="statusColor" class="status-icon" />
        시스템 상태
        <va-button 
          @click="$emit('refresh')"
          icon="refresh"
          preset="secondary"
          size="small"
          class="refresh-btn"
          :loading="refreshing"
        />
      </va-card-title>
      
      <va-card-content>
        <div class="status-content">
          <!-- 메인 상태 표시 -->
          <div class="main-status">
            <div class="status-indicator">
              <div :class="['status-dot', statusClass]"></div>
              <span class="status-text">{{ statusText }}</span>
            </div>
            <div class="status-message">{{ healthStatus.message }}</div>
          </div>

          <!-- 상세 정보 -->
          <div class="status-details">
            <h4 class="details-title">서비스 상태</h4>
            <div class="services-grid">
              <div 
                v-for="(status, service) in healthStatus.services" 
                :key="service"
                class="service-item"
                :class="getServiceStatusClass(status)"
              >
                <span class="service-label">{{ getServiceDisplayName(service) }}:</span>
                <span class="service-status">{{ getServiceStatusText(status) }}</span>
              </div>
            </div>
          </div>

          <!-- 마지막 업데이트 시간 -->
          <div v-if="lastUpdated" class="last-updated">
            <va-icon name="schedule" size="small" />
            마지막 업데이트: {{ formatLastUpdated(lastUpdated) }}
          </div>
        </div>
      </va-card-content>
    </va-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

// Props 정의
interface Props {
  healthStatus: {
    status: string
    last_updated: string
    services: {
      database: string
      mail_server: string
      redis: string
      storage: string
    }
  }
  lastUpdated: Date | null
}

const props = defineProps<Props>()

// Emits 정의
const emit = defineEmits<{
  refresh: []
}>()

// 반응형 데이터
const refreshing = ref(false)

// 계산된 속성들
const statusIcon = computed(() => {
  switch (props.healthStatus.status) {
    case 'healthy':
      return 'check_circle'
    case 'warning':
      return 'warning'
    case 'critical':
    case 'error':
      return 'error'
    default:
      return 'help'
  }
})

const statusColor = computed(() => {
  switch (props.healthStatus.status) {
    case 'healthy':
      return 'success'
    case 'warning':
      return 'warning'
    case 'critical':
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
})

const statusClass = computed(() => {
  switch (props.healthStatus.status) {
    case 'healthy':
      return 'status-healthy'
    case 'warning':
      return 'status-warning'
    case 'critical':
    case 'error':
      return 'status-error'
    default:
      return 'status-unknown'
  }
})

const statusText = computed(() => {
  switch (props.healthStatus.status) {
    case 'healthy':
      return '정상'
    case 'warning':
      return '주의'
    case 'critical':
      return '위험'
    case 'error':
      return '오류'
    default:
      return '알 수 없음'
  }
})

const statusMessage = computed(() => {
  switch (props.healthStatus.status) {
    case 'healthy':
      return '모든 시스템이 정상적으로 작동하고 있습니다.'
    case 'warning':
      return '일부 서비스에 주의가 필요합니다.'
    case 'critical':
      return '시스템에 심각한 문제가 발생했습니다.'
    case 'error':
      return '시스템 오류가 발생했습니다.'
    default:
      return '시스템 상태를 확인할 수 없습니다.'
  }
})

// 메서드들
const getServiceDisplayName = (service: string): string => {
  const serviceMap: Record<string, string> = {
    'database': '데이터베이스',
    'redis': 'Redis',
    'mail_server': '메일 서버',
    'storage': '저장소'
  }
  return serviceMap[service] || service
}

const getServiceStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'healthy': '정상',
    'warning': '주의',
    'critical': '위험',
    'error': '오류'
  }
  return statusMap[status] || status
}

const getServiceStatusClass = (status: string): string => {
  switch (status) {
    case 'healthy': return 'service-healthy'
    case 'warning': return 'service-warning'
    case 'critical': 
    case 'error': return 'service-error'
    default: return 'service-unknown'
  }
}

const formatLastUpdated = (date: Date): string => {
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
    return date.toLocaleString('ko-KR')
  }
}

// 새로고침 핸들러
const handleRefresh = async () => {
  refreshing.value = true
  try {
    emit('refresh')
    // 최소 1초 로딩 표시
    await new Promise(resolve => setTimeout(resolve, 1000))
  } finally {
    refreshing.value = false
  }
}
</script>

<style scoped>
.system-status-card {
  flex: 1;
  min-width: 300px;
}

.status-card {
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease;
}

.status-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.status-icon {
  font-size: 1.5rem;
}

.refresh-btn {
  margin-left: auto;
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-healthy {
  background-color: #27ae60;
}

.status-warning {
  background-color: #f39c12;
}

.status-error {
  background-color: #e74c3c;
}

.status-unknown {
  background-color: #95a5a6;
}

.status-text {
  font-size: 1.1rem;
  font-weight: 600;
}

.status-message {
  color: #7f8c8d;
  font-size: 0.95rem;
  line-height: 1.4;
}

.status-details {
  border-top: 1px solid #ecf0f1;
  padding-top: 16px;
}

.details-title {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 12px;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 15px;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.service-label {
  font-weight: 500;
  color: #495057;
}

.service-status {
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
}

.service-healthy .service-status {
  color: #28a745;
  background: rgba(40, 167, 69, 0.1);
}

.service-warning .service-status {
  color: #ffc107;
  background: rgba(255, 193, 7, 0.1);
}

.service-error .service-status {
  color: #dc3545;
  background: rgba(220, 53, 69, 0.1);
}

.service-unknown .service-status {
  color: #6c757d;
  background: rgba(108, 117, 125, 0.1);
}

.last-updated {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: #95a5a6;
  border-top: 1px solid #ecf0f1;
  padding-top: 12px;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .system-status-card {
    min-width: auto;
  }
  
  .services-grid {
    grid-template-columns: 1fr;
  }
  
  .service-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
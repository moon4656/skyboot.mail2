<template>
  <div class="realtime-logs">
    <div class="logs-header">
      <h3 class="logs-title">
        <va-icon name="list_alt" color="primary" />
        실시간 로그
      </h3>
      <div class="logs-controls">
        <va-button
          :icon="isAutoRefresh ? 'pause' : 'play_arrow'"
          :color="isAutoRefresh ? 'warning' : 'success'"
          size="small"
          @click="toggleAutoRefresh"
        >
          {{ isAutoRefresh ? '일시정지' : '자동새로고침' }}
        </va-button>
        <va-button
          icon="refresh"
          color="primary"
          size="small"
          @click="refreshLogs"
          :loading="loading"
        >
          새로고침
        </va-button>
      </div>
    </div>

    <div class="logs-content">
      <div v-if="loading && logs.length === 0" class="logs-loading">
        <va-progress-circle indeterminate />
        <p>로그를 불러오는 중...</p>
      </div>

      <div v-else-if="logs.length === 0" class="logs-empty">
        <va-icon name="description" size="3rem" color="secondary" />
        <p>표시할 로그가 없습니다</p>
      </div>

      <div v-else class="logs-list">
        <div
          v-for="log in logs"
          :key="log.id"
          :class="['log-item', `log-${log.level.toLowerCase()}`]"
        >
          <div class="log-header">
            <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
            <va-chip
              :color="getLogLevelColor(log.level)"
              size="small"
              class="log-level"
            >
              {{ log.level }}
            </va-chip>
          </div>
          <div class="log-message">{{ log.message }}</div>
          <div v-if="log.details" class="log-details">
            <pre>{{ JSON.stringify(log.details, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// Props 정의
const props = defineProps<{
  logs: Array<{
    id: string
    timestamp: string
    level: string
    message: string
    details?: any
  }>
  loading: boolean
}>()

// Emits 정의
const emit = defineEmits<{
  refresh: []
}>()

// 반응형 데이터
const isAutoRefresh = ref(false)
let autoRefreshInterval: NodeJS.Timeout | null = null

// 메서드들
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

const getLogLevelColor = (level: string): string => {
  switch (level.toLowerCase()) {
    case 'error':
      return 'danger'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    case 'debug':
      return 'secondary'
    default:
      return 'primary'
  }
}

const refreshLogs = () => {
  emit('refresh')
}

const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value
  
  if (isAutoRefresh.value) {
    autoRefreshInterval = setInterval(() => {
      refreshLogs()
    }, 5000) // 5초마다 새로고침
  } else {
    if (autoRefreshInterval) {
      clearInterval(autoRefreshInterval)
      autoRefreshInterval = null
    }
  }
}

// 라이프사이클
onMounted(() => {
  // 컴포넌트 마운트 시 자동 새로고침 시작
  toggleAutoRefresh()
})

onUnmounted(() => {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
  }
})
</script>

<style scoped>
.realtime-logs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
}

.logs-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.logs-controls {
  display: flex;
  gap: 0.5rem;
}

.logs-content {
  max-height: 400px;
  overflow-y: auto;
}

.logs-loading,
.logs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
}

.logs-loading p,
.logs-empty p {
  margin: 0.5rem 0 0 0;
}

.logs-list {
  padding: 0.5rem;
}

.log-item {
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border-radius: 6px;
  border-left: 4px solid;
  background: #f8f9fa;
}

.log-item.log-error {
  border-left-color: #dc3545;
  background: #fff5f5;
}

.log-item.log-warning {
  border-left-color: #ffc107;
  background: #fffbf0;
}

.log-item.log-info {
  border-left-color: #17a2b8;
  background: #f0f9ff;
}

.log-item.log-debug {
  border-left-color: #6c757d;
  background: #f8f9fa;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.log-timestamp {
  font-size: 0.85rem;
  color: #666;
  font-family: 'Courier New', monospace;
}

.log-level {
  font-size: 0.75rem;
  font-weight: 600;
}

.log-message {
  font-size: 0.9rem;
  line-height: 1.4;
  color: #333;
}

.log-details {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  font-size: 0.8rem;
}

.log-details pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Courier New', monospace;
}

/* 스크롤바 스타일링 */
.logs-content::-webkit-scrollbar {
  width: 6px;
}

.logs-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.logs-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.logs-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
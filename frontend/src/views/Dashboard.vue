<template>
  <div class="dashboard">
    <!-- 대시보드 헤더 -->
    <div class="dashboard-header">
      <h1 class="dashboard-title">
        <va-icon name="dashboard" class="title-icon" />
        모니터링 대시보드
      </h1>
      <p class="dashboard-subtitle">시스템 상태 및 사용량 통계를 실시간으로 확인하세요</p>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="loading" class="loading-container">
      <va-progress-circle indeterminate />
      <p>대시보드 데이터를 불러오는 중...</p>
    </div>

    <!-- 에러 상태 -->
    <va-alert v-if="error" color="danger" class="error-alert">
      <va-icon name="error" />
      {{ error }}
      <template #action>
        <va-button @click="loadDashboardData" size="small" color="danger" variant="outlined">
          다시 시도
        </va-button>
      </template>
    </va-alert>

    <!-- 대시보드 콘텐츠 -->
    <div v-if="!loading && !error" class="dashboard-content">
      <!-- 시스템 상태 카드 -->
      <div class="dashboard-row">
        <SystemStatusCard 
          :health-status="healthStatus"
          :last-updated="lastUpdated"
          @refresh="checkSystemHealth"
        />
      </div>

      <!-- 사용량 통계 카드들 -->
      <div class="dashboard-row">
        <UsageStatsCards 
          :usage-data="usageData"
          :loading="usageLoading"
        />
      </div>

      <!-- 차트 섹션 -->
      <div class="dashboard-row">
        <div class="chart-container">
          <MailUsageChart 
            :chart-data="mailChartData"
            :loading="chartLoading"
          />
        </div>
        <div class="chart-container">
          <StorageUsageChart 
            :chart-data="storageChartData"
            :loading="chartLoading"
          />
        </div>
      </div>

      <!-- 실시간 로그 섹션 -->
      <div class="dashboard-row">
        <RealtimeLogsCard 
          :logs="realtimeLogs"
          :loading="logsLoading"
          @refresh="loadRealtimeLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import SystemStatusCard from '@/components/dashboard/SystemStatusCard.vue'
import UsageStatsCards from '@/components/dashboard/UsageStatsCards.vue'
import MailUsageChart from '@/components/dashboard/MailUsageChart.vue'
import StorageUsageChart from '@/components/dashboard/StorageUsageChart.vue'
import RealtimeLogsCard from '@/components/dashboard/RealtimeLogsCard.vue'
import dashboardService, { type DashboardData } from '@/services/dashboardService'

// 반응형 데이터
const loading = ref(true)
const error = ref('')
const lastUpdated = ref<Date | null>(null)
const dashboardData = ref<DashboardData | null>(null)

// 시스템 상태 (API 데이터 기반)
const healthStatus = computed(() => {
  if (!dashboardData.value) return {
    status: 'unknown',
    message: '',
    details: {}
  }
  return dashboardData.value.system_status
})

// 사용량 데이터 (API 데이터 기반)
const usageData = computed(() => {
  if (!dashboardData.value) return {
    current_usage: {
      emails_sent: 0,
      storage_used: 0,
      active_users: 0,
      api_requests: 0
    },
    limits: {
      max_emails_per_day: 1000,
      max_storage_gb: 10,
      max_users: 100,
      max_api_requests_per_hour: 1000
    },
    usage_percentages: {
      emails: 0,
      storage: 0,
      users: 0,
      api: 0
    }
  }
  return dashboardData.value.usage_stats
})

const usageLoading = ref(false)

// 차트 데이터 (API 데이터 기반)
const mailChartData = computed(() => {
  if (!dashboardData.value) return {
    labels: [],
    datasets: []
  }
  return dashboardData.value.mail_usage_chart
})

const storageChartData = computed(() => {
  if (!dashboardData.value) return {
    labels: [],
    datasets: []
  }
  return dashboardData.value.storage_usage_chart
})

const chartLoading = ref(false)

// 실시간 로그 (API 데이터 기반)
const realtimeLogs = computed(() => {
  if (!dashboardData.value) return []
  return dashboardData.value.realtime_logs
})
const logsLoading = ref(false)

// 자동 새로고침 타이머
let refreshTimer: NodeJS.Timeout | null = null

/**
 * 시스템 상태 확인
 */
const checkSystemHealth = async () => {
  await loadDashboardData()
}

/**
 * 사용량 통계 로드
 */
const loadUsageStats = async () => {
  usageLoading.value = true
  try {
    await loadDashboardData()
  } finally {
    usageLoading.value = false
  }
}

/**
 * 차트 데이터 로드
 */
const loadChartData = async () => {
  chartLoading.value = true
  try {
    await loadDashboardData()
  } finally {
    chartLoading.value = false
  }
}

/**
 * 실시간 로그 로드
 */
const loadRealtimeLogs = async () => {
  logsLoading.value = true
  try {
    await loadDashboardData()
  } finally {
    logsLoading.value = false
  }
}

/**
 * 대시보드 데이터 로드
 */
const loadDashboardData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // 실제 API 호출
    dashboardData.value = await dashboardService.getDashboardTestData()
    
    lastUpdated.value = new Date()
    console.log('대시보드 데이터 로드 완료:', dashboardData.value)
  } catch (err: any) {
    console.error('대시보드 데이터 로드 실패:', err)
    error.value = '대시보드 데이터를 불러오는 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

/**
 * 자동 새로고침 설정
 */
const setupAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadDashboardData()
  }, 30000) // 30초마다 새로고침
}

/**
 * 컴포넌트 마운트 시
 */
onMounted(() => {
  loadDashboardData()
  setupAutoRefresh()
})

/**
 * 컴포넌트 언마운트 시
 */
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.dashboard-header {
  margin-bottom: 32px;
  text-align: center;
}

.dashboard-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 2.5rem;
  color: #3498db;
}

.dashboard-subtitle {
  font-size: 1.1rem;
  color: #7f8c8d;
  margin: 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  gap: 16px;
}

.error-alert {
  margin-bottom: 24px;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.dashboard-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.chart-container {
  flex: 1;
  min-width: 400px;
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }
  
  .dashboard-row {
    flex-direction: column;
  }
  
  .chart-container {
    min-width: auto;
  }
  
  .dashboard-title {
    font-size: 2rem;
  }
}
</style>
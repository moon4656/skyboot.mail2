<template>
  <div class="storage-usage-chart">
    <div class="chart-header">
      <h3 class="chart-title">
        <va-icon name="pie_chart" color="success" />
        저장 공간 사용량
      </h3>
      <p class="chart-subtitle">현재 저장 공간 사용 현황</p>
    </div>

    <div class="chart-content">
      <div v-if="loading" class="chart-loading">
        <va-progress-circle indeterminate />
        <p>차트 데이터를 불러오는 중...</p>
      </div>

      <div v-else-if="hasData" class="chart-container">
        <div class="chart-wrapper">
          <Doughnut
            :data="chartData"
            :options="chartOptions"
            :height="250"
          />
        </div>
        
        <!-- 범례 -->
        <div class="chart-legend">
          <div class="legend-item">
            <div class="legend-color used"></div>
            <span class="legend-label">사용 중</span>
            <span class="legend-value">{{ formatStorage(usedStorage) }}</span>
          </div>
          <div class="legend-item">
            <div class="legend-color available"></div>
            <span class="legend-label">사용 가능</span>
            <span class="legend-value">{{ formatStorage(availableStorage) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="chart-empty">
        <va-icon name="storage" size="4rem" color="secondary" />
        <p>저장 공간 정보를 불러올 수 없습니다</p>
      </div>
    </div>

    <!-- 저장 공간 상세 정보 -->
    <div v-if="hasData && !loading" class="storage-details">
      <div class="detail-row">
        <span class="detail-label">총 용량:</span>
        <span class="detail-value">{{ formatStorage(totalStorage) }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">사용률:</span>
        <span :class="['detail-value', usageClass]">
          {{ usagePercentage.toFixed(1) }}%
        </span>
      </div>
      <div class="detail-row">
        <span class="detail-label">남은 용량:</span>
        <span class="detail-value">{{ formatStorage(availableStorage) }}</span>
      </div>
      
      <!-- 사용량 경고 -->
      <div v-if="usagePercentage >= 80" class="usage-warning">
        <va-alert 
          :color="usagePercentage >= 90 ? 'danger' : 'warning'"
          border="left"
          border-color="currentColor"
        >
          <va-icon :name="usagePercentage >= 90 ? 'error' : 'warning'" />
          {{ usagePercentage >= 90 ? '저장 공간이 부족합니다!' : '저장 공간 사용량이 높습니다.' }}
          {{ usagePercentage >= 90 ? '즉시 정리가 필요합니다.' : '정리를 권장합니다.' }}
        </va-alert>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import { Doughnut } from 'vue-chartjs'

// Chart.js 등록
ChartJS.register(ArcElement, Tooltip, Legend)

// Props 정의
const props = defineProps<{
  chartData: {
    labels: string[]
    datasets: Array<{
      data: number[]
      backgroundColor: string[]
      borderColor: string[]
      borderWidth: number
    }>
  }
  loading: boolean
}>()

// 계산된 속성들
const hasData = computed(() => {
  return props.chartData.datasets.length > 0 && 
         props.chartData.datasets[0].data.length > 0
})

const usedStorage = computed(() => {
  if (!hasData.value) return 0
  return props.chartData.datasets[0].data[0] || 0
})

const availableStorage = computed(() => {
  if (!hasData.value) return 0
  return props.chartData.datasets[0].data[1] || 0
})

const totalStorage = computed(() => {
  return usedStorage.value + availableStorage.value
})

const usagePercentage = computed(() => {
  if (totalStorage.value === 0) return 0
  return (usedStorage.value / totalStorage.value) * 100
})

const usageClass = computed(() => {
  if (usagePercentage.value >= 90) return 'usage-critical'
  if (usagePercentage.value >= 80) return 'usage-warning'
  if (usagePercentage.value >= 60) return 'usage-moderate'
  return 'usage-normal'
})

// 메서드들
const formatStorage = (gb: number): string => {
  if (gb >= 1024) {
    return (gb / 1024).toFixed(1) + ' TB'
  }
  return gb.toFixed(1) + ' GB'
}

// 차트 옵션
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false // 커스텀 범례 사용
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: '#27ae60',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: true,
      callbacks: {
        label: (context: any) => {
          const label = context.label || ''
          const value = context.parsed
          const percentage = ((value / totalStorage.value) * 100).toFixed(1)
          return `${label}: ${formatStorage(value)} (${percentage}%)`
        }
      }
    }
  },
  cutout: '60%', // 도넛 차트의 중앙 구멍 크기
  animation: {
    animateRotate: true,
    animateScale: true,
    duration: 1000,
    easing: 'easeInOutQuart' as const
  },
  elements: {
    arc: {
      borderWidth: 2,
      hoverBorderWidth: 4
    }
  }
}))
</script>

<style scoped>
.storage-usage-chart {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}

.chart-header {
  margin-bottom: 24px;
  text-align: center;
}

.chart-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.chart-subtitle {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin: 0;
}

.chart-content {
  position: relative;
  min-height: 300px;
}

.chart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 16px;
  color: #7f8c8d;
}

.chart-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.chart-wrapper {
  position: relative;
  width: 250px;
  height: 250px;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #7f8c8d;
  text-align: center;
}

.chart-legend {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-color.used {
  background-color: rgba(255, 99, 132, 0.8);
}

.legend-color.available {
  background-color: rgba(54, 162, 235, 0.8);
}

.legend-label {
  font-size: 0.9rem;
  color: #2c3e50;
  font-weight: 500;
}

.legend-value {
  font-size: 0.9rem;
  color: #7f8c8d;
  font-weight: 600;
}

.storage-details {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f8f9fa;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  font-weight: 500;
}

.detail-value {
  font-size: 0.9rem;
  font-weight: 600;
}

.usage-normal {
  color: #27ae60;
}

.usage-moderate {
  color: #3498db;
}

.usage-warning {
  color: #f39c12;
}

.usage-critical {
  color: #e74c3c;
}

.usage-warning {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .storage-usage-chart {
    padding: 16px;
  }
  
  .chart-wrapper {
    width: 200px;
    height: 200px;
  }
  
  .chart-legend {
    flex-direction: column;
    gap: 12px;
  }
  
  .legend-item {
    justify-content: center;
  }
  
  .chart-title {
    font-size: 1.1rem;
  }
}

@media (max-width: 480px) {
  .chart-wrapper {
    width: 180px;
    height: 180px;
  }
  
  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
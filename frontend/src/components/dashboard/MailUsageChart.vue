<template>
  <div class="mail-usage-chart">
    <div class="chart-header">
      <h3 class="chart-title">
        <va-icon name="trending_up" color="primary" />
        메일 발송 추이
      </h3>
      <p class="chart-subtitle">최근 7일간 메일 발송량 변화</p>
    </div>

    <div class="chart-content">
      <div v-if="loading" class="chart-loading">
        <va-progress-circle indeterminate />
        <p>차트 데이터를 불러오는 중...</p>
      </div>

      <div v-else-if="hasData" class="chart-container">
        <Line
          :data="chartData"
          :options="chartOptions"
          :height="300"
        />
      </div>

      <div v-else class="chart-empty">
        <va-icon name="bar_chart" size="4rem" color="secondary" />
        <p>표시할 데이터가 없습니다</p>
        <p class="empty-subtitle">메일을 발송하면 여기에 통계가 표시됩니다</p>
      </div>
    </div>

    <!-- 차트 통계 요약 -->
    <div v-if="hasData && !loading" class="chart-stats">
      <div class="stat-item">
        <span class="stat-label">총 발송량:</span>
        <span class="stat-value">{{ totalEmails.toLocaleString() }}건</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">일평균:</span>
        <span class="stat-value">{{ averageEmails.toLocaleString() }}건</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">최대:</span>
        <span class="stat-value">{{ maxEmails.toLocaleString() }}건</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">증감률:</span>
        <span :class="['stat-value', trendClass]">
          {{ trendPercentage >= 0 ? '+' : '' }}{{ trendPercentage.toFixed(1) }}%
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Props 정의
const props = defineProps<{
  chartData: {
    labels: string[]
    datasets: Array<{
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
      tension: number
    }>
  }
  loading: boolean
}>()

// 계산된 속성들
const hasData = computed(() => {
  return props.chartData.labels.length > 0 && 
         props.chartData.datasets.length > 0 &&
         props.chartData.datasets[0].data.length > 0
})

const totalEmails = computed(() => {
  if (!hasData.value) return 0
  return props.chartData.datasets[0].data.reduce((sum, value) => sum + value, 0)
})

const averageEmails = computed(() => {
  if (!hasData.value) return 0
  return Math.round(totalEmails.value / props.chartData.datasets[0].data.length)
})

const maxEmails = computed(() => {
  if (!hasData.value) return 0
  return Math.max(...props.chartData.datasets[0].data)
})

const trendPercentage = computed(() => {
  if (!hasData.value || props.chartData.datasets[0].data.length < 2) return 0
  
  const data = props.chartData.datasets[0].data
  const lastValue = data[data.length - 1]
  const previousValue = data[data.length - 2]
  
  if (previousValue === 0) return 0
  return ((lastValue - previousValue) / previousValue) * 100
})

const trendClass = computed(() => {
  if (trendPercentage.value > 0) return 'trend-up'
  if (trendPercentage.value < 0) return 'trend-down'
  return 'trend-neutral'
})

// 차트 옵션
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 20,
        font: {
          size: 12,
          family: "'Noto Sans KR', sans-serif"
        }
      }
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: '#3498db',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: true,
      callbacks: {
        title: (context: any) => {
          return `날짜: ${context[0].label}`
        },
        label: (context: any) => {
          return `${context.dataset.label}: ${context.parsed.y.toLocaleString()}건`
        }
      }
    }
  },
  scales: {
    x: {
      display: true,
      title: {
        display: true,
        text: '날짜',
        font: {
          size: 12,
          weight: 'bold' as const
        }
      },
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      },
      ticks: {
        font: {
          size: 11
        }
      }
    },
    y: {
      display: true,
      title: {
        display: true,
        text: '메일 발송량 (건)',
        font: {
          size: 12,
          weight: 'bold' as const
        }
      },
      beginAtZero: true,
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      },
      ticks: {
        font: {
          size: 11
        },
        callback: function(value: any) {
          return value.toLocaleString()
        }
      }
    }
  },
  interaction: {
    mode: 'nearest' as const,
    axis: 'x' as const,
    intersect: false
  },
  elements: {
    point: {
      radius: 4,
      hoverRadius: 6,
      borderWidth: 2,
      hoverBorderWidth: 3
    },
    line: {
      borderWidth: 3,
      tension: 0.4
    }
  },
  animation: {
    duration: 1000,
    easing: 'easeInOutQuart' as const
  }
}))
</script>

<style scoped>
.mail-usage-chart {
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
  position: relative;
  height: 300px;
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

.empty-subtitle {
  font-size: 0.85rem;
  margin-top: 8px;
  opacity: 0.8;
}

.chart-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
}

.stat-label {
  font-size: 0.85rem;
  color: #7f8c8d;
  font-weight: 500;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.trend-up {
  color: #27ae60;
}

.trend-down {
  color: #e74c3c;
}

.trend-neutral {
  color: #7f8c8d;
}

@media (max-width: 768px) {
  .mail-usage-chart {
    padding: 16px;
  }
  
  .chart-content {
    min-height: 250px;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .chart-loading,
  .chart-empty {
    height: 250px;
  }
  
  .chart-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .chart-title {
    font-size: 1.1rem;
  }
}

@media (max-width: 480px) {
  .chart-stats {
    grid-template-columns: 1fr;
  }
  
  .stat-item {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }
}
</style>
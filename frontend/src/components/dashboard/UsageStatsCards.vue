<template>
  <div class="usage-stats-cards">
    <!-- 메일 발송량 카드 -->
    <va-card class="stat-card">
      <va-card-content>
        <div class="stat-content">
          <div class="stat-header">
            <va-icon name="email" color="primary" class="stat-icon" />
            <div class="stat-info">
              <h3 class="stat-title">메일 발송량</h3>
              <p class="stat-subtitle">오늘 발송된 메일 수</p>
            </div>
          </div>
          
          <div class="stat-body">
            <div class="stat-value">
              <span v-if="!loading" class="value-number">
                {{ formatNumber(usageData.emails_sent.current) }}
              </span>
              <va-skeleton v-else height="2rem" width="4rem" />
              <span class="value-unit">/ {{ formatNumber(usageData.emails_sent.limit) }}</span>
            </div>
            
            <va-progress-bar
              :model-value="emailsPercentage"
              :color="getProgressColor(emailsPercentage)"
              class="stat-progress"
            />
            
            <div class="stat-percentage">
              {{ emailsPercentage.toFixed(1) }}% 사용
            </div>
          </div>
        </div>
      </va-card-content>
    </va-card>

    <!-- 저장 공간 카드 -->
    <va-card class="stat-card">
      <va-card-content>
        <div class="stat-content">
          <div class="stat-header">
            <va-icon name="storage" color="success" class="stat-icon" />
            <div class="stat-info">
              <h3 class="stat-title">저장 공간</h3>
              <p class="stat-subtitle">사용 중인 저장 공간</p>
            </div>
          </div>
          
          <div class="stat-body">
            <div class="stat-value">
              <span v-if="!loading" class="value-number">
                {{ formatStorage(usageData.storage_used.current) }}
              </span>
              <va-skeleton v-else height="2rem" width="4rem" />
              <span class="value-unit">/ {{ formatStorage(usageData.storage_used.limit) }}</span>
            </div>
            
            <va-progress-bar
              :model-value="storagePercentage"
              :color="getProgressColor(storagePercentage)"
              class="stat-progress"
            />
            
            <div class="stat-percentage">
              {{ storagePercentage.toFixed(1) }}% 사용
            </div>
          </div>
        </div>
      </va-card-content>
    </va-card>

    <!-- 활성 사용자 카드 -->
    <va-card class="stat-card">
      <va-card-content>
        <div class="stat-content">
          <div class="stat-header">
            <va-icon name="people" color="warning" class="stat-icon" />
            <div class="stat-info">
              <h3 class="stat-title">활성 사용자</h3>
              <p class="stat-subtitle">현재 활성 사용자 수</p>
            </div>
          </div>
          
          <div class="stat-body">
            <div class="stat-value">
              <span v-if="!loading" class="value-number">
                {{ formatNumber(usageData.active_users.current) }}
              </span>
              <va-skeleton v-else height="2rem" width="4rem" />
              <span class="value-unit">/ {{ formatNumber(usageData.active_users.limit) }}</span>
            </div>
            
            <va-progress-bar
              :model-value="usersPercentage"
              :color="getProgressColor(usersPercentage)"
              class="stat-progress"
            />
            
            <div class="stat-percentage">
              {{ usersPercentage.toFixed(1) }}% 사용
            </div>
          </div>
        </div>
      </va-card-content>
    </va-card>

    <!-- API 요청 카드 -->
    <va-card class="stat-card">
      <va-card-content>
        <div class="stat-content">
          <div class="stat-header">
            <va-icon name="api" color="info" class="stat-icon" />
            <div class="stat-info">
              <h3 class="stat-title">API 요청</h3>
              <p class="stat-subtitle">시간당 API 요청 수</p>
            </div>
          </div>
          
          <div class="stat-body">
            <div class="stat-value">
              <span v-if="!loading" class="value-number">
                {{ formatNumber(usageData.api_requests.current) }}
              </span>
              <va-skeleton v-else height="2rem" width="4rem" />
              <span class="value-unit">/ {{ formatNumber(usageData.api_requests.limit) }}</span>
            </div>
            
            <va-progress-bar
              :model-value="apiPercentage"
              :color="getProgressColor(apiPercentage)"
              class="stat-progress"
            />
            
            <div class="stat-percentage">
              {{ apiPercentage.toFixed(1) }}% 사용
            </div>
          </div>
        </div>
      </va-card-content>
    </va-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  usageData: {
    emails_sent: { current: number; limit: number; percentage: number }
    storage_used: { current: number; limit: number; percentage: number }
    active_users: { current: number; limit: number; percentage: number }
    api_requests: { current: number; limit: number; percentage: number }
  }
  loading: boolean
}>()

// 계산된 속성들
const emailsPercentage = computed(() => {
  if (!props.usageData) return 0
  return props.usageData.emails_sent.percentage
})

const storagePercentage = computed(() => {
  if (!props.usageData) return 0
  return props.usageData.storage_used.percentage
})

const usersPercentage = computed(() => {
  if (!props.usageData) return 0
  return props.usageData.active_users.percentage
})

const apiPercentage = computed(() => {
  if (!props.usageData) return 0
  return props.usageData.api_requests.percentage
})

// 메서드들
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatStorage = (gb: number): string => {
  if (gb >= 1024) {
    return (gb / 1024).toFixed(1) + 'TB'
  }
  return gb.toFixed(1) + 'GB'
}

const getProgressColor = (percentage: number): string => {
  if (percentage >= 90) {
    return 'danger'
  } else if (percentage >= 75) {
    return 'warning'
  } else if (percentage >= 50) {
    return 'info'
  }
  return 'success'
}
</script>

<style scoped>
.usage-stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  width: 100%;
}

.stat-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
}

.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.stat-icon {
  font-size: 2rem;
  margin-top: 4px;
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.stat-subtitle {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin: 0;
  line-height: 1.3;
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.value-number {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
}

.value-unit {
  font-size: 1rem;
  color: #7f8c8d;
  font-weight: 500;
}

.stat-progress {
  margin: 4px 0;
}

.stat-percentage {
  font-size: 0.9rem;
  color: #7f8c8d;
  text-align: right;
  font-weight: 500;
}

/* 반응형 디자인 */
@media (max-width: 1200px) {
  .usage-stats-cards {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .usage-stats-cards {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stat-card {
    margin: 0;
  }
  
  .value-number {
    font-size: 1.75rem;
  }
  
  .stat-icon {
    font-size: 1.75rem;
  }
}

@media (max-width: 480px) {
  .stat-header {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .stat-icon {
    align-self: center;
  }
  
  .value-number {
    font-size: 1.5rem;
  }
}
</style>
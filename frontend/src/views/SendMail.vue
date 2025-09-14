<template>
  <div class="send-mail-container">
    <va-row>
      <!-- 메일 발송 폼 -->
      <va-col :xs="12" :lg="8">
        <va-card>
          <va-card-title>
            <h2 class="va-h2">메일 발송</h2>
          </va-card-title>
          
          <va-card-content>
            <va-form @submit.prevent="handleSendMail">
              <div class="mb-4">
                <va-input
                  v-model="form.to_email"
                  type="email"
                  label="수신자 이메일"
                  placeholder="수신자 이메일을 입력하세요"
                  :rules="emailRules"
                  :error="!!errors.to_email"
                  :error-messages="errors.to_email"
                  required
                />
              </div>
              
              <div class="mb-4">
                <va-input
                  v-model="form.subject"
                  type="text"
                  label="제목"
                  placeholder="메일 제목을 입력하세요"
                  :rules="subjectRules"
                  :error="!!errors.subject"
                  :error-messages="errors.subject"
                  required
                />
              </div>
              
              <div class="mb-4">
                <va-textarea
                  v-model="form.body"
                  label="본문"
                  placeholder="메일 본문을 입력하세요"
                  :rules="bodyRules"
                  :error="!!errors.body"
                  :error-messages="errors.body"
                  :min-rows="8"
                  :max-rows="15"
                  autosize
                  required
                />
              </div>
              
              <div v-if="errors.general" class="mb-4">
                <va-alert color="danger" :model-value="true">
                  {{ errors.general }}
                </va-alert>
              </div>
              
              <div v-if="successMessage" class="mb-4">
                <va-alert color="success" :model-value="true">
                  {{ successMessage }}
                </va-alert>
              </div>
              
              <div class="d-flex gap-3">
                <va-button
                  type="submit"
                  :loading="isLoading"
                  :disabled="!isFormValid"
                  color="primary"
                  size="large"
                  icon="send"
                >
                  메일 발송
                </va-button>
                
                <va-button
                  @click="clearForm"
                  color="secondary"
                  preset="outline"
                  size="large"
                  icon="clear"
                >
                  초기화
                </va-button>
              </div>
            </va-form>
          </va-card-content>
        </va-card>
      </va-col>
      
      <!-- 메일 발송 이력 -->
      <va-col :xs="12" :lg="4">
        <va-card>
          <va-card-title>
            <h3 class="va-h3">최근 발송 이력</h3>
          </va-card-title>
          
          <va-card-content>
            <div v-if="isLoadingLogs" class="text-center">
              <va-progress-circle indeterminate />
              <p class="mt-2">로딩 중...</p>
            </div>
            
            <div v-else-if="mailLogs.length === 0" class="text-center">
              <va-icon name="mail" size="3rem" color="secondary" class="mb-2" />
              <p class="va-text-secondary">발송 이력이 없습니다.</p>
            </div>
            
            <div v-else>
              <va-list>
                <va-list-item
                  v-for="log in mailLogs"
                  :key="log.id"
                  class="mail-log-item"
                >
                  <va-list-item-section>
                    <va-list-item-label class="font-weight-bold">
                      {{ log.subject }}
                    </va-list-item-label>
                    <va-list-item-label caption>
                      받는 사람: {{ log.to_email }}
                    </va-list-item-label>
                    <va-list-item-label caption>
                      {{ formatDate(log.created_at) }}
                    </va-list-item-label>
                  </va-list-item-section>
                  
                  <va-list-item-section side>
                    <va-chip
                      :color="log.status === 'sent' ? 'success' : 'danger'"
                      size="small"
                    >
                      {{ log.status === 'sent' ? '성공' : '실패' }}
                    </va-chip>
                  </va-list-item-section>
                </va-list-item>
              </va-list>
              
              <div class="text-center mt-3">
                <va-button
                  @click="loadMailLogs"
                  color="secondary"
                  preset="outline"
                  size="small"
                >
                  새로고침
                </va-button>
              </div>
            </div>
          </va-card-content>
        </va-card>
      </va-col>
    </va-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { mailApi } from '@/services/api'

/**
 * 메일 발송 페이지 컴포넌트
 * 메일 발송 폼과 발송 이력을 제공
 */

// 메일 로그 인터페이스
interface MailLog {
  id: number
  to_email: string
  subject: string
  body: string
  status: string
  created_at: string
}

// 폼 데이터
const form = reactive({
  to_email: '',
  subject: '',
  body: ''
})

// 상태 관리
const isLoading = ref(false)
const isLoadingLogs = ref(false)
const successMessage = ref('')
const mailLogs = ref<MailLog[]>([])

// 에러 상태
const errors = reactive({
  to_email: '',
  subject: '',
  body: '',
  general: ''
})

// 유효성 검사 규칙
const emailRules = [
  (value: string) => !!value || '수신자 이메일을 입력해주세요.',
  (value: string) => /.+@.+\..+/.test(value) || '올바른 이메일 형식을 입력해주세요.'
]

const subjectRules = [
  (value: string) => !!value || '제목을 입력해주세요.',
  (value: string) => value.length <= 500 || '제목은 최대 500자까지 가능합니다.'
]

const bodyRules = [
  (value: string) => !!value || '본문을 입력해주세요.',
  (value: string) => value.length <= 5000 || '본문은 최대 5000자까지 가능합니다.'
]

// 폼 유효성 검사
const isFormValid = computed(() => {
  return form.to_email && form.subject && form.body &&
         emailRules.every(rule => rule(form.to_email) === true) &&
         subjectRules.every(rule => rule(form.subject) === true) &&
         bodyRules.every(rule => rule(form.body) === true)
})

/**
 * 에러 초기화 함수
 */
const clearErrors = () => {
  errors.to_email = ''
  errors.subject = ''
  errors.body = ''
  errors.general = ''
}

/**
 * 폼 초기화 함수
 */
const clearForm = () => {
  form.to_email = ''
  form.subject = ''
  form.body = ''
  clearErrors()
  successMessage.value = ''
}

/**
 * 날짜 포맷팅 함수
 */
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 메일 발송 처리 함수
 */
const handleSendMail = async () => {
  if (!isFormValid.value) return
  
  isLoading.value = true
  clearErrors()
  successMessage.value = ''
  
  try {
    const response = await mailApi.sendMail({
      to_email: form.to_email,
      subject: form.subject,
      body: form.body
    })
    
    successMessage.value = '메일이 성공적으로 발송되었습니다!'
    clearForm()
    
    // 발송 이력 새로고침
    await loadMailLogs()
    
  } catch (error: any) {
    errors.general = error.response?.data?.detail || '메일 발송에 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}

/**
 * 메일 로그 로드 함수
 */
const loadMailLogs = async () => {
  isLoadingLogs.value = true
  
  try {
    const response = await mailApi.getMailLogs({ limit: 10 })
    mailLogs.value = response.data
  } catch (error) {
    console.error('메일 로그 로드 실패:', error)
  } finally {
    isLoadingLogs.value = false
  }
}

// 컴포넌트 마운트 시 메일 로그 로드
onMounted(() => {
  loadMailLogs()
})
</script>

<style scoped>
.send-mail-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.d-flex {
  display: flex;
}

.gap-3 {
  gap: 1rem;
}

.text-center {
  text-align: center;
}

.font-weight-bold {
  font-weight: bold;
}

.mail-log-item {
  border-bottom: 1px solid var(--va-background-border);
}

.mail-log-item:last-child {
  border-bottom: none;
}
</style>
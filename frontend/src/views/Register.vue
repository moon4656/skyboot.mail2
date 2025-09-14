<template>
  <div class="register-container">
    <va-card class="register-card">
      <va-card-content>
        <div class="text-center mb-4">
          <h1 class="va-h1">회원가입</h1>
          <p class="va-text-secondary">새 계정을 만들어 메일 발송 기능을 이용하세요</p>
        </div>
        
        <va-form @submit.prevent="handleRegister">
          <div class="mb-4">
            <va-input
              v-model="form.email"
              type="email"
              label="이메일"
              placeholder="이메일을 입력하세요"
              :rules="emailRules"
              :error="!!errors.email"
              :error-messages="errors.email"
              required
            />
          </div>
          
          <div class="mb-4">
            <va-input
              v-model="form.username"
              type="text"
              label="사용자명"
              placeholder="사용자명을 입력하세요"
              :rules="usernameRules"
              :error="!!errors.username"
              :error-messages="errors.username"
              required
            />
          </div>
          
          <div class="mb-4">
            <va-input
              v-model="form.password"
              type="password"
              label="비밀번호"
              placeholder="비밀번호를 입력하세요"
              :rules="passwordRules"
              :error="!!errors.password"
              :error-messages="errors.password"
              required
            />
          </div>
          
          <div class="mb-4">
            <va-input
              v-model="form.confirmPassword"
              type="password"
              label="비밀번호 확인"
              placeholder="비밀번호를 다시 입력하세요"
              :rules="confirmPasswordRules"
              :error="!!errors.confirmPassword"
              :error-messages="errors.confirmPassword"
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
          
          <div class="mb-4">
            <va-button
              type="submit"
              :loading="isLoading"
              :disabled="!isFormValid"
              color="primary"
              class="w-100"
              size="large"
            >
              회원가입
            </va-button>
          </div>
          
          <div class="text-center">
            <p class="va-text-secondary">
              이미 계정이 있으신가요?
              <router-link to="/login" class="va-link">
                로그인
              </router-link>
            </p>
          </div>
        </va-form>
      </va-card-content>
    </va-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

/**
 * 회원가입 페이지 컴포넌트
 * 새 사용자 계정 생성을 위한 회원가입 폼 제공
 */

const router = useRouter()
const userStore = useUserStore()

// 폼 데이터
const form = reactive({
  email: '',
  username: '',
  password: '',
  confirmPassword: ''
})

// 로딩 상태
const isLoading = ref(false)

// 성공 메시지
const successMessage = ref('')

// 에러 상태
const errors = reactive({
  email: '',
  username: '',
  password: '',
  confirmPassword: '',
  general: ''
})

// 유효성 검사 규칙
const emailRules = [
  (value: string) => !!value || '이메일을 입력해주세요.',
  (value: string) => /.+@.+\..+/.test(value) || '올바른 이메일 형식을 입력해주세요.'
]

const usernameRules = [
  (value: string) => !!value || '사용자명을 입력해주세요.',
  (value: string) => value.length >= 3 || '사용자명은 최소 3자 이상이어야 합니다.',
  (value: string) => value.length <= 20 || '사용자명은 최대 20자까지 가능합니다.'
]

const passwordRules = [
  (value: string) => !!value || '비밀번호를 입력해주세요.',
  (value: string) => value.length >= 6 || '비밀번호는 최소 6자 이상이어야 합니다.',
  (value: string) => value.length <= 50 || '비밀번호는 최대 50자까지 가능합니다.'
]

const confirmPasswordRules = [
  (value: string) => !!value || '비밀번호 확인을 입력해주세요.',
  (value: string) => value === form.password || '비밀번호가 일치하지 않습니다.'
]

// 폼 유효성 검사
const isFormValid = computed(() => {
  return form.email && form.username && form.password && form.confirmPassword &&
         emailRules.every(rule => rule(form.email) === true) &&
         usernameRules.every(rule => rule(form.username) === true) &&
         passwordRules.every(rule => rule(form.password) === true) &&
         confirmPasswordRules.every(rule => rule(form.confirmPassword) === true)
})

/**
 * 에러 초기화 함수
 */
const clearErrors = () => {
  errors.email = ''
  errors.username = ''
  errors.password = ''
  errors.confirmPassword = ''
  errors.general = ''
}

/**
 * 회원가입 처리 함수
 */
const handleRegister = async () => {
  if (!isFormValid.value) return
  
  isLoading.value = true
  clearErrors()
  successMessage.value = ''
  
  try {
    await userStore.register({
      email: form.email,
      username: form.username,
      password: form.password
    })
    
    successMessage.value = '회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.'
    
    // 2초 후 로그인 페이지로 이동
    setTimeout(() => {
      router.push('/login')
    }, 2000)
    
  } catch (error: any) {
    errors.general = error.message || '회원가입에 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: 2rem;
}

.register-card {
  width: 100%;
  max-width: 450px;
}

.w-100 {
  width: 100%;
}

.text-center {
  text-align: center;
}

.va-link {
  color: var(--va-primary);
  text-decoration: none;
}

.va-link:hover {
  text-decoration: underline;
}
</style>
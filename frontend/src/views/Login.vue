<template>
  <div class="login-container">
    <va-card class="login-card">
      <va-card-content>
        <div class="text-center mb-4">
          <h1 class="va-h1">로그인</h1>
          <p class="va-text-secondary">계정에 로그인하여 메일 발송 기능을 이용하세요</p>
        </div>
        
        <va-form @submit.prevent="handleLogin">
          <div class="mb-4">
            <va-input
              v-model="form.userId"
              type="text"
              label="사용자 ID"
              placeholder="사용자 ID를 입력하세요"
              :rules="userIdRules"
              :error="!!errors.userId"
              :error-messages="errors.userId"
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
              autocomplete="current-password"
              required
            />
          </div>
          
          <div v-if="errors.general" class="mb-4">
            <va-alert color="danger" :model-value="true">
              {{ errors.general }}
            </va-alert>
          </div>
          
          <div class="mb-4">
            <va-button
              type="submit"
              :loading="isLoading"
              :disabled="!isFormValid || isLoading"
              color="primary"
              class="w-100"
              size="large"
            >
              로그인
            </va-button>
          </div>
          
          <div class="text-center">
            <p class="va-text-secondary">
              계정이 없으신가요?
              <router-link to="/register" class="va-link">
                회원가입
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
 * 로그인 페이지 컴포넌트
 * 사용자 인증을 위한 로그인 폼 제공
 */

// 타입 정의
interface LoginForm {
  userId: string
  password: string
}

interface LoginErrors {
  userId: string
  password: string
  general: string
}

interface LoginCredentials {
  username: string
  password: string
}

const router = useRouter()
const userStore = useUserStore()

// 폼 데이터
const form = reactive<LoginForm>({
  userId: '',
  password: ''
})

// 로딩 상태
const isLoading = ref<boolean>(false)

// 에러 상태
const errors = reactive<LoginErrors>({
  userId: '',
  password: '',
  general: ''
})

// 유효성 검사 규칙
const userIdRules = [
  (value: string) => !!value || '사용자 ID를 입력해주세요.',
  (value: string) => value.length >= 3 || '사용자 ID는 최소 3자 이상이어야 합니다.',
  (value: string) => /^[a-zA-Z0-9_]+$/.test(value) || '사용자 ID는 영문, 숫자, 언더스코어만 사용 가능합니다.'
]

const passwordRules = [
  (value: string) => !!value || '비밀번호를 입력해주세요.',
  (value: string) => value.length >= 4 || '비밀번호는 최소 4자 이상이어야 합니다.',
  (value: string) => value.length <= 50 || '비밀번호는 최대 50자까지 입력 가능합니다.'
]

// 폼 유효성 검사
const isFormValid = computed<boolean>(() => {
  return form.userId.trim() !== '' && 
         form.password.trim() !== '' && 
         userIdRules.every(rule => rule(form.userId) === true) &&
         passwordRules.every(rule => rule(form.password) === true)
})

/**
 * 에러 초기화 함수
 */
const clearErrors = (): void => {
  errors.userId = ''
  errors.password = ''
  errors.general = ''
}

/**
 * 개별 필드 유효성 검사 함수
 */
const validateField = (field: keyof LoginForm): boolean => {
  clearErrors()
  
  if (field === 'userId') {
    const userIdError = userIdRules.find(rule => rule(form.userId) !== true)
    if (userIdError) {
      errors.userId = userIdError(form.userId) as string
      return false
    }
  }
  
  if (field === 'password') {
    const passwordError = passwordRules.find(rule => rule(form.password) !== true)
    if (passwordError) {
      errors.password = passwordError(form.password) as string
      return false
    }
  }
  
  return true
}

/**
 * 로그인 처리 함수
 */
const handleLogin = async (): Promise<void> => {
  // 폼 유효성 검사 활성화
  if (!isFormValid.value) {
    validateField('userId')
    validateField('password')
    return
  }
  
  isLoading.value = true
  clearErrors()
  
  try {
    const credentials: LoginCredentials = {
      username: form.userId.trim(),
      password: form.password
    }
    
    await userStore.login(credentials)
    
    // 로그인 성공 시 홈페이지로 이동
    await router.push('/home')
  } catch (error: unknown) {
    // 에러 타입 안전성 개선
    if (error instanceof Error) {
      errors.general = error.message || '로그인에 실패했습니다.'
    } else if (typeof error === 'string') {
      errors.general = error
    } else if (error && typeof error === 'object' && 'message' in error) {
      errors.general = (error as { message: string }).message
    } else {
      errors.general = '알 수 없는 오류가 발생했습니다. 다시 시도해주세요.'
    }
    
    // 로그인 실패 시 폼 초기화 (보안상 비밀번호만)
    form.password = ''
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: 2rem;
}

.login-card {
  width: 100%;
  max-width: 400px;
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
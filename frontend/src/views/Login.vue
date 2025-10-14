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
              :disabled="!isFormValid"
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

const router = useRouter()
const userStore = useUserStore()

// 폼 데이터
const form = reactive({
  userId: '',
  password: ''
})

// 로딩 상태
const isLoading = ref(false)

// 에러 상태
const errors = reactive({
  userId: '',
  password: '',
  general: ''
})

// 유효성 검사 규칙
const userIdRules = [
  (value: string) => !!value || '사용자 ID를 입력해주세요.',
  (value: string) => value.length >= 3 || '사용자 ID는 최소 3자 이상이어야 합니다.'
]

const passwordRules = [
  (value: string) => !!value || '비밀번호를 입력해주세요.',
  (value: string) => value.length >= 4 || '비밀번호는 최소 4자 이상이어야 합니다.'
]

// 폼 유효성 검사
const isFormValid = computed(() => {
  return form.userId && form.password && 
         userIdRules.every(rule => rule(form.userId) === true) &&
         passwordRules.every(rule => rule(form.password) === true)
})

/**
 * 에러 초기화 함수
 */
const clearErrors = () => {
  errors.userId = ''
  errors.password = ''
  errors.general = ''
}

/**
 * 로그인 처리 함수
 */
const handleLogin = async () => {
  // if (!isFormValid.value) return
  
  isLoading.value = true
  clearErrors()
  
  try {
    await userStore.login({
      username: form.userId,
      password: form.password
    })
    
    // 로그인 성공 시 홈페이지로 이동
    router.push('/')
  } catch (error: any) {
    errors.general = error.message || '로그인에 실패했습니다.'
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
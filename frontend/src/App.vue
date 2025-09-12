<template>
  <va-app>
    <!-- 네비게이션 바 -->
    <va-navbar color="primary" class="mb-4">
      <template #left>
        <va-navbar-item>
          <router-link to="/" class="text-white text-decoration-none">
            <h3>SkyBoot Mail</h3>
          </router-link>
        </va-navbar-item>
      </template>
      
      <template #right>
        <va-navbar-item v-if="!isAuthenticated">
          <router-link to="/login" class="text-white text-decoration-none mr-3">
            로그인
          </router-link>
          <router-link to="/register" class="text-white text-decoration-none">
            회원가입
          </router-link>
        </va-navbar-item>
        
        <va-navbar-item v-else>
          <span class="text-white mr-3">{{ userStore.user?.username }}님</span>
          <va-button @click="logout" color="danger" size="small">
            로그아웃
          </va-button>
        </va-navbar-item>
      </template>
    </va-navbar>
    
    <!-- 메인 콘텐츠 -->
    <va-container>
      <router-view />
    </va-container>
  </va-app>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

/**
 * 메인 애플리케이션 컴포넌트
 * 네비게이션 바와 라우터 뷰를 포함
 */

const router = useRouter()
const userStore = useUserStore()

// 인증 상태 확인
const isAuthenticated = computed(() => userStore.isAuthenticated)

/**
 * 로그아웃 처리 함수
 */
const logout = async () => {
  await userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.text-decoration-none {
  text-decoration: none;
}
</style>
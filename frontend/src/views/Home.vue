<template>
  <div class="home">
    <va-card>
      <va-card-content>
        <div class="text-center">
          <h1 class="va-h1 mb-4">SkyBoot Mail 시스템에 오신 것을 환영합니다!</h1>
          
          <div v-if="!isAuthenticated" class="mb-4">
            <p class="va-text-secondary mb-4">
              이메일 발송 시스템을 사용하려면 로그인이 필요합니다.
            </p>
            
            <div class="d-flex justify-center gap-3">
              <va-button 
                @click="$router.push('/login')"
                color="primary"
                size="large"
              >
                로그인
              </va-button>
              
              <va-button 
                @click="$router.push('/register')"
                color="secondary"
                size="large"
                preset="outline"
              >
                회원가입
              </va-button>
            </div>
          </div>
          
          <div v-else class="mb-4">
            <p class="va-text-secondary mb-4">
              안녕하세요! 이제 메일 발송 기능을 사용하실 수 있습니다.
            </p>
            
            <va-button 
              @click="$router.push('/send-mail')"
              color="primary"
              size="large"
              icon="mail"
            >
              메일 발송하기
            </va-button>
          </div>
        </div>
        
        <!-- 기능 소개 섹션 -->
        <va-divider class="my-6" />
        
        <div class="features">
          <h2 class="va-h2 text-center mb-4">주요 기능</h2>
          
          <va-row>
            <va-col :xs="12" :md="4">
              <va-card class="feature-card">
                <va-card-content class="text-center">
                  <va-icon name="security" size="3rem" color="primary" class="mb-3" />
                  <h3 class="va-h3 mb-2">JWT 인증</h3>
                  <p class="va-text-secondary">
                    안전한 JWT 기반 인증 시스템으로 사용자 정보를 보호합니다.
                  </p>
                </va-card-content>
              </va-card>
            </va-col>
            
            <va-col :xs="12" :md="4">
              <va-card class="feature-card">
                <va-card-content class="text-center">
                  <va-icon name="mail" size="3rem" color="success" class="mb-3" />
                  <h3 class="va-h3 mb-2">메일 발송</h3>
                  <p class="va-text-secondary">
                    Postfix SMTP를 통한 안정적인 이메일 발송 기능을 제공합니다.
                  </p>
                </va-card-content>
              </va-card>
            </va-col>
            
            <va-col :xs="12" :md="4">
              <va-card class="feature-card">
                <va-card-content class="text-center">
                  <va-icon name="history" size="3rem" color="info" class="mb-3" />
                  <h3 class="va-h3 mb-2">발송 이력</h3>
                  <p class="va-text-secondary">
                    모든 메일 발송 이력을 확인하고 관리할 수 있습니다.
                  </p>
                </va-card-content>
              </va-card>
            </va-col>
          </va-row>
        </div>
      </va-card-content>
    </va-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

/**
 * 홈 페이지 컴포넌트
 * 애플리케이션의 메인 랜딩 페이지
 */

const userStore = useUserStore()

// 인증 상태 확인
const isAuthenticated = computed(() => userStore.isAuthenticated)
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.feature-card {
  height: 100%;
  transition: transform 0.2s ease-in-out;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.d-flex {
  display: flex;
}

.justify-center {
  justify-content: center;
}

.gap-3 {
  gap: 1rem;
}

.text-center {
  text-align: center;
}
</style>
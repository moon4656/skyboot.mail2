import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import SendMail from '@/views/SendMail.vue'
import Dashboard from '@/views/Dashboard.vue'

/**
 * Vue Router 설정
 * 애플리케이션의 라우팅 규칙 정의
 * 기본적으로 모든 페이지는 인증이 필요하며, 로그인/회원가입만 예외
 */
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Root',
      redirect: '/login'  // 루트 경로는 항상 로그인 페이지로 리다이렉트
    },
    {
      path: '/home',
      name: 'Home',
      component: Home,
      meta: { requiresAuth: true }  // 홈 페이지도 인증 필요
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: Register,
      meta: { requiresGuest: true }
    },
    {
      path: '/send-mail',
      name: 'SendMail',
      component: SendMail,
      meta: { requiresAuth: true }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    }
  ]
})

/**
 * 라우터 가드 설정
 * 강력한 인증 기반 접근 제어 - 기본적으로 모든 페이지는 인증 필요
 * 로그인/회원가입 페이지만 예외적으로 게스트 접근 허용
 */
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isAuthenticated = userStore.isAuthenticated
  
  // 게스트 전용 페이지 (로그인/회원가입)
  if (to.meta.requiresGuest) {
    if (isAuthenticated) {
      // 이미 로그인된 사용자는 홈 페이지로 리다이렉트
      next('/home')
      return
    }
    // 로그인하지 않은 사용자는 접근 허용
    next()
    return
  }
  
  // 기본적으로 모든 페이지는 인증 필요 (requiresAuth가 명시되지 않아도)
  // 로그인/회원가입 페이지가 아닌 모든 페이지는 인증 필요
  if (!isAuthenticated) {
    next('/login')
    return
  }
  
  // 인증된 사용자는 접근 허용
  next()
})

export default router
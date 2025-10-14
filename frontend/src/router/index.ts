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
 */
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
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
 * 인증이 필요한 페이지와 게스트 전용 페이지 접근 제어
 */
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isAuthenticated = userStore.isAuthenticated
  
  // 인증이 필요한 페이지
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
    return
  }
  
  // 게스트 전용 페이지 (로그인된 사용자는 접근 불가)
  if (to.meta.requiresGuest && isAuthenticated) {
    next('/')
    return
  }
  
  next()
})

export default router
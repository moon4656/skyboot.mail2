import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuestic } from 'vuestic-ui'
import 'vuestic-ui/css'
import App from './App.vue'
import router from './router'

/**
 * Vue 애플리케이션 초기화 및 설정
 */
const app = createApp(App)

// Pinia 상태 관리 라이브러리 설정
app.use(createPinia())

// Vue Router 설정
app.use(router)

// Vuestic UI 라이브러리 설정
app.use(createVuestic({
  config: {
    colors: {
      variables: {
        primary: '#1976d2',
        secondary: '#424242',
        success: '#4caf50',
        info: '#2196f3',
        warning: '#ff9800',
        danger: '#f44336',
      },
    },
  },
}))

// 애플리케이션 마운트
app.mount('#app')
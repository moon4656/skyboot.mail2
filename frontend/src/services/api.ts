import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user'

/**
 * API 기본 URL 설정
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Axios 인스턴스 생성
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 요청 인터셉터 설정
 * 모든 요청에 액세스 토큰을 자동으로 추가
 */
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const userStore = useUserStore()
    const token = userStore.accessToken
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 응답 인터셉터 설정
 * 401 에러 시 토큰 갱신 시도
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // 401 에러이고 재시도하지 않은 요청인 경우
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const userStore = useUserStore()
        await userStore.refreshAccessToken()
        
        // 새로운 토큰으로 원래 요청 재시도
        const token = userStore.accessToken
        if (token) {
          originalRequest.headers.Authorization = `Bearer ${token}`
        }
        
        return apiClient(originalRequest)
      } catch (refreshError) {
        // 토큰 갱신 실패 시 로그인 페이지로 리다이렉트
        const userStore = useUserStore()
        userStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)

/**
 * 메일 발송 API 함수
 */
export const mailApi = {
  /**
   * 메일 발송
   */
  sendMail: (data: { to_email: string; subject: string; body: string }) => {
    return apiClient.post('/mail/send', data)
  },
  
  /**
   * 메일 로그 조회
   */
  getMailLogs: (params?: { limit?: number; offset?: number }) => {
    return apiClient.get('/mail/logs', { params })
  },
  
  /**
   * 특정 메일 로그 조회
   */
  getMailLog: (mailId: number) => {
    return apiClient.get(`/mail/logs/${mailId}`)
  }
}

/**
 * 인증 API 함수
 */
export const authApi = {
  /**
   * 회원가입
   */
  register: (data: { email: string; username: string; password: string }) => {
    return apiClient.post('/auth/register', data)
  },
  
  /**
   * 로그인
   */
  login: (data: { email: string; password: string }) => {
    return apiClient.post('/auth/login', data)
  },
  
  /**
   * 토큰 갱신
   */
  refreshToken: (data: { refresh_token: string }) => {
    return apiClient.post('/auth/refresh', data)
  }
}
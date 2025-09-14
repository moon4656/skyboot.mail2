import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/services/api'

/**
 * 사용자 인터페이스 정의
 */
export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
}

/**
 * 로그인 응답 인터페이스 정의
 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

/**
 * 사용자 상태 관리 스토어
 * 인증, 사용자 정보, 토큰 관리 기능 제공
 */
export const useUserStore = defineStore('user', () => {
  // 상태 정의
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  
  // 계산된 속성
  const isAuthenticated = computed(() => !!accessToken.value)
  
  /**
   * 토큰 저장 함수
   */
  const setTokens = (access: string, refresh: string) => {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }
  
  /**
   * 토큰 제거 함수
   */
  const clearTokens = () => {
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }
  
  /**
   * 회원가입 함수
   */
  const register = async (userData: {
    email: string
    username: string
    password: string
  }) => {
    try {
      const response = await apiClient.post('/auth/register', userData)
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '회원가입에 실패했습니다.')
    }
  }
  
  /**
   * 로그인 함수
   */
  const login = async (credentials: { email: string; password: string }) => {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials)
      const { access_token, refresh_token } = response.data
      
      setTokens(access_token, refresh_token)
      
      // 사용자 정보 가져오기 (토큰에서 디코딩하거나 별도 API 호출)
      // 여기서는 간단히 토큰 저장만 수행
      
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '로그인에 실패했습니다.')
    }
  }
  
  /**
   * 로그아웃 함수
   */
  const logout = () => {
    user.value = null
    clearTokens()
  }
  
  /**
   * 토큰 갱신 함수
   */
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('리프레시 토큰이 없습니다.')
      }
      
      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken.value
      })
      
      const { access_token } = response.data
      accessToken.value = access_token
      localStorage.setItem('access_token', access_token)
      
      return access_token
    } catch (error) {
      // 리프레시 토큰이 만료된 경우 로그아웃
      logout()
      throw error
    }
  }
  
  return {
    // 상태
    user,
    accessToken,
    refreshToken,
    
    // 계산된 속성
    isAuthenticated,
    
    // 액션
    register,
    login,
    logout,
    refreshAccessToken,
    setTokens,
    clearTokens
  }
})
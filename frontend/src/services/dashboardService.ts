import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

export interface SystemStatus {
  status: string
  last_updated: string
  services: {
    database: string
    mail_server: string
    redis: string
    storage: string
  }
}

export interface UsageStats {
  emails_sent: {
    current: number
    limit: number
    percentage: number
  }
  storage_used: {
    current: number
    limit: number
    percentage: number
  }
  active_users: {
    current: number
    limit: number
    percentage: number
  }
  api_requests: {
    current: number
    limit: number
    percentage: number
  }
}

export interface MailUsageChart {
  labels: string[]
  data: number[]
  total_sent: number
  daily_average: number
  max_daily: number
  trend_percentage: number
}

export interface StorageUsage {
  used: number
  available: number
  total: number
  percentage: number
  breakdown: {
    emails: number
    attachments: number
    system: number
  }
}

export interface RealtimeLog {
  id: string
  action: string
  user: string
  timestamp: string
  ip_address: string
  organization: string
  status: string
}

export interface DashboardData {
  system_status: SystemStatus
  usage_stats: UsageStats
  mail_usage_chart: MailUsageChart
  storage_usage: StorageUsage
  realtime_logs: RealtimeLog[]
}

class DashboardService {
  /**
   * 대시보드 테스트 데이터를 가져옵니다
   */
  async getDashboardTestData(): Promise<DashboardData> {
    try {
      const response = await axios.get(`${API_BASE_URL}/debug/dashboard-test`)
      return response.data
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error)
      throw error
    }
  }

  /**
   * 실제 대시보드 데이터를 가져옵니다 (인증 필요)
   */
  async getDashboardData(token: string): Promise<DashboardData> {
    try {
      const response = await axios.get(`${API_BASE_URL}/monitoring/dashboard`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return response.data
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error)
      throw error
    }
  }
}

export default new DashboardService()
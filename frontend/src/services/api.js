const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiService {
  constructor() {
    this.token = null
  }

  setToken(token) {
    this.token = token
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  async getStocksByYear(year, limit = 10, forceRefresh = false) {
    return this.request(`/api/stocks/top/year/${year}?top_n=${limit}&force_refresh=${forceRefresh}`)
  }

  async getStocksByMonth(year, month, limit = 10, forceRefresh = false) {
    return this.request(`/api/stocks/top/monthly/${year}/${month}?top_n=${limit}&force_refresh=${forceRefresh}`)
  }

  async getCacheStats() {
    return this.request('/api/admin/cache/stats')
  }

  async warmCache(year) {
    return this.request(`/api/admin/warm-cache/${year}`, { method: 'POST' })
  }

  async invalidateCache(year = null) {
    const endpoint = year ? `/api/admin/cache/invalidate/${year}` : '/api/admin/cache/invalidate'
    return this.request(endpoint, { method: 'DELETE' })
  }

  async getHealth() {
    return this.request('/health')
  }
}

export default new ApiService()

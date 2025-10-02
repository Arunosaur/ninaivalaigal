import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:13390'

// Admin Analytics API client
export const adminApi = {
  // Platform Overview (matches backend endpoint)
  async getPlatformMetrics() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/platform-overview`)
    return response.data
  },

  // Revenue Cohorts
  async getRevenueAnalytics() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/revenue-cohorts`)
    return response.data
  },

  // Churn Analysis
  async getChurnAnalysis() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/churn-analysis`)
    return response.data
  },

  // Business Intelligence
  async getBusinessIntelligence() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/business-intelligence`)
    return response.data
  },

  // User Engagement
  async getUserEngagement() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/user-engagement`)
    return response.data
  },

  // Real-time Metrics
  async getRealTimeMetrics() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/real-time-metrics`)
    return response.data
  },
}

export default adminApi

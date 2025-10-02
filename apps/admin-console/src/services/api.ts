import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:13370'

// Admin Analytics API client
export const adminApi = {
  // Platform Metrics
  async getPlatformMetrics() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/platform-metrics`)
    return response.data
  },

  // Revenue Analytics
  async getRevenueAnalytics() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/revenue-analytics`)
    return response.data
  },

  // Churn Analysis
  async getChurnAnalysis() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/churn-analysis`)
    return response.data
  },

  // Team Cohort Analysis
  async getTeamCohorts() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/team-cohorts`)
    return response.data
  },

  // User Engagement
  async getUserEngagement() {
    const response = await axios.get(`${API_BASE_URL}/admin-analytics/user-engagement`)
    return response.data
  },
}

export default adminApi

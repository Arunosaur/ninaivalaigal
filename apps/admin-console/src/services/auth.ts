// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:13390'

interface LoginResponse {
  access_token: string
  token_type: string
  user?: {
    id: string
    email: string
    username: string
  }
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, {
      email,
      password,
    })

    if (response.data.access_token) {
      localStorage.setItem('admin_token', response.data.access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
    }

    return response.data
  },

  logout() {
    localStorage.removeItem('admin_token')
    delete axios.defaults.headers.common['Authorization']
  },

  getToken(): string | null {
    return localStorage.getItem('admin_token')
  },

  isAuthenticated(): boolean {
    return !!this.getToken()
  },

  initializeAuth() {
    const token = this.getToken()
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  },
}

// Initialize auth on module load
authService.initializeAuth()

export default authService

// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import axios from 'axios'
import { clearAuthToken, getAuthToken, setAuthToken } from './tokenStorage'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:13390'
const DEFAULT_TOKEN_TYPE = 'Bearer'

interface LoginResponse {
  access_token?: string
  jwt_token?: string
  token_type?: string
  expires_in?: number
  user?: {
    id: string
    email: string
    username: string
  }
}

axios.defaults.withCredentials = true

function extractToken(response: LoginResponse): string | null {
  if (response.access_token) {
    return response.access_token
  }

  if (response.jwt_token) {
    return response.jwt_token
  }

  return null
}

function applyAuthHeader(token: string | null, tokenType: string = DEFAULT_TOKEN_TYPE) {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `${tokenType} ${token}`
  } else {
    delete axios.defaults.headers.common['Authorization']
  }
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await axios.post(
      `${API_BASE_URL}/auth/login`,
      {
        email,
        password,
      },
      {
        withCredentials: true,
      }
    )

    const token = extractToken(response.data)

    if (token) {
      const tokenType = response.data.token_type ?? DEFAULT_TOKEN_TYPE
      setAuthToken(token, response.data.expires_in)
      applyAuthHeader(token, tokenType)
    }

    return response.data
  },

  logout() {
    clearAuthToken()
    applyAuthHeader(null)
  },

  getToken(): string | null {
    return getAuthToken()
  },

  isAuthenticated(): boolean {
    return !!getAuthToken()
  },

  initializeAuth() {
    const token = getAuthToken()
    applyAuthHeader(token)
  },
}

// Initialize auth on module load
authService.initializeAuth()

export default authService

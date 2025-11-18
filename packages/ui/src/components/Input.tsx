// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import React from 'react'
import { cn } from '../utils/cn'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-2">
          {label}
        </label>
      )}
      <input
        className={cn(
          'w-full px-4 py-3 bg-gray-700 border rounded-lg text-white placeholder-gray-400',
          'focus:outline-none focus:ring-2 focus:border-transparent',
          error ? 'border-error-500 focus:ring-error-500' : 'border-gray-600 focus:ring-primary-500',
          className
        )}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-error-500">{error}</p>}
    </div>
  )
}

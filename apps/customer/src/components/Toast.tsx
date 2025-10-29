// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { useEffect } from 'react';

export interface ToastProps {
  message: string;
  type?: 'error' | 'success' | 'info' | 'warning';
  onClose: () => void;
  duration?: number;
}

export function Toast({ message, type = 'error', onClose, duration = 5000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const colors = {
    error: 'bg-red-900/90 border-red-700 text-red-200',
    success: 'bg-green-900/90 border-green-700 text-green-200',
    info: 'bg-blue-900/90 border-blue-700 text-blue-200',
    warning: 'bg-yellow-900/90 border-yellow-700 text-yellow-200',
  };

  const icons = {
    error: '❌',
    success: '✅',
    info: 'ℹ️',
    warning: '⚠️',
  };

  return (
    <div className="fixed top-4 right-4 z-[9999] animate-in slide-in-from-top-5 duration-300">
      <div className={`${colors[type]} border rounded-lg shadow-2xl p-4 pr-12 max-w-md`}>
        <div className="flex items-start gap-3">
          <span className="text-xl">{icons[type]}</span>
          <p className="text-sm font-medium flex-1">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-slate-400 hover:text-white transition-colors p-1"
          aria-label="Close"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

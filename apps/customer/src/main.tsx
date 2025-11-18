// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import './styles/memory-browser.css'
import { AuthProvider } from './lib/authContext'
import { register } from './lib/pwa/serviceWorker'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>,
)

// Register service worker for PWA
register({
  onSuccess: () => {
    console.log('[PWA] Service worker registered successfully');
  },
  onUpdate: () => {
    console.log('[PWA] New content available, please refresh');
  },
});

// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Analytics from './pages/Analytics'
import Teams from './pages/Teams'
import Users from './pages/Users'
import ProtectedRoute from './components/ProtectedRoute'
import { routerFutureFlags } from './router/futureFlags'

function App() {
  return (
  <BrowserRouter future={routerFutureFlags}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/users" element={<Users />} />
        </Route>
        <Route path="/" element={<Navigate to="/analytics" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

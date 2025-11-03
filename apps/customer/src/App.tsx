// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './pages/Landing'
import { Signup } from './pages/Signup'
import { Login } from './pages/Login'
import Dashboard from './pages/Dashboard'
import MemoryBrowser from './pages/MemoryBrowser'
import Teams from './pages/Teams'
import TeamCreate from './pages/TeamCreate'
import TeamDashboard from './pages/TeamDashboard'
import TeamBilling from './pages/TeamBilling'
import TeamPaymentMethod from './pages/TeamPaymentMethod'
import TeamInvoiceList from './pages/TeamInvoiceList'
import TeamUsage from './pages/TeamUsage'
import TeamInvite from './pages/TeamInvite'
import TeamUpgrade from './pages/TeamUpgrade'
import ProtectedRoute from './components/ProtectedRoute'
import EMC2Prototype from './pages/prototypes/EMC2Prototype'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/prototype/emc2" element={<EMC2Prototype />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/memory-browser" element={<MemoryBrowser />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/team/create" element={<TeamCreate />} />
          <Route path="/team/dashboard" element={<TeamDashboard />} />
          <Route path="/team/billing" element={<TeamBilling />} />
          <Route path="/team/billing/payment-method" element={<TeamPaymentMethod />} />
          <Route path="/team/billing/invoices" element={<TeamInvoiceList />} />
          <Route path="/team/usage" element={<TeamUsage />} />
          <Route path="/team/:teamId/invite" element={<TeamInvite />} />
          <Route path="/team/:teamId/upgrade" element={<TeamUpgrade />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useState } from 'react';
import { Button, Card, Callout } from '@ninaivalaigal/ui-components';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../contexts/AuthContext';
import { useSessions } from '../../../hooks/useSessions';

interface StatusMessage {
  type: 'success' | 'error';
  text: string;
}

export default function SessionsPage() {
  const router = useRouter();
  const { sessions, isLoading, error, refetch, logoutSession } = useSessions();
  const { logoutAllDevices } = useAuth();
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [isLogoutAllLoading, setIsLogoutAllLoading] = useState(false);
  const [pendingSessionId, setPendingSessionId] = useState<string | null>(null);

  const handleLogoutSession = async (sessionId: string) => {
    setStatus(null);
    setPendingSessionId(sessionId);
    const result = await logoutSession(sessionId);
    setPendingSessionId(null);

    if (!result.success) {
      setStatus({ type: 'error', text: result.error || 'Failed to log out session.' });
      return;
    }

    setStatus({ type: 'success', text: 'Session logged out successfully.' });
  };

  const handleLogoutAll = async () => {
    setStatus(null);
    setIsLogoutAllLoading(true);
    const { error: logoutError } = await logoutAllDevices();
    setIsLogoutAllLoading(false);

    if (logoutError) {
      setStatus({ type: 'error', text: logoutError });
      return;
    }

    setStatus({ type: 'success', text: 'All sessions logged out. Redirecting to login…' });
    router.push('/login');
  };

  const handleRefetch = async () => {
    setStatus(null);
    await refetch();
  };

  const renderSessionInfo = () => {
    if (isLoading) {
      return <p className="text-sm text-gray-600">Loading active sessions…</p>;
    }

    if (error) {
      return (
        <Callout variant="error" title="Unable to load sessions">
          <p className="mb-3 text-sm">{error}</p>
          <Button size="sm" onClick={refetch}>
            Retry
          </Button>
        </Callout>
      );
    }

    if (sessions.length === 0) {
      return (
        <Callout variant="info" title="No active sessions">
          <p className="text-sm">You are not signed in on any other devices.</p>
        </Callout>
      );
    }

    return (
      <div className="space-y-4">
        {sessions.map((session) => {
          const isCurrent = Boolean(session.is_current);
          const lastActive = session.last_active_at
            ? new Date(session.last_active_at).toLocaleString()
            : 'Last active time unavailable';
          return (
            <Card key={session.id} className={`bg-white ${isCurrent ? 'border-blue-200 shadow-sm' : ''}`}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {session.device || 'Unknown device'}
                    {isCurrent && <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">Current device</span>}
                  </p>
                  <p className="text-xs text-gray-500">
                    {session.location || 'Location unavailable'} • {session.ip_address || 'IP hidden'}
                  </p>
                  <p className="text-xs text-gray-400">{lastActive}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleLogoutSession(session.id)}
                    disabled={isCurrent || pendingSessionId === session.id}
                  >
                    {pendingSessionId === session.id ? 'Logging out…' : 'Logout session'}
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-6 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Active Sessions</h1>
            <p className="text-sm text-gray-500">Manage the devices that are currently signed in to your account.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={handleRefetch} disabled={isLoading}>
              Refresh list
            </Button>
            <Button size="sm" onClick={handleLogoutAll} disabled={isLogoutAllLoading}>
              {isLogoutAllLoading ? 'Logging out…' : 'Logout all devices'}
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        {status && (
          <Callout
            variant={status.type === 'error' ? 'error' : 'success'}
            title={status.type === 'error' ? 'Action required' : 'Update'}
            className="mb-6"
          >
            <p className="text-sm text-gray-700">{status.text}</p>
          </Callout>
        )}

        {renderSessionInfo()}
      </main>
    </div>
  );
}

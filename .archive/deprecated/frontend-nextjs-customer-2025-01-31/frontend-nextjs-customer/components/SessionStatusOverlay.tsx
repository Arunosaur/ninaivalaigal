// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useState } from 'react';
import { Button, Callout } from '@ninaivalaigal/ui-components';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';

export function SessionStatusOverlay() {
  const {
    isRefreshingToken,
    refreshError,
    refreshSession,
    logout,
    showExpiryWarning,
    dismissExpiryWarning,
    sessionExpiresAt,
    logoutAllDevices,
  } = useAuth();
  const router = useRouter();
  const [isManualRefreshLoading, setIsManualRefreshLoading] = useState(false);
  const [isLogoutAllLoading, setIsLogoutAllLoading] = useState(false);

  const handleManualRefresh = async () => {
    setIsManualRefreshLoading(true);
    const { error } = await refreshSession();
    setIsManualRefreshLoading(false);

    if (error) {
      return;
    }

    dismissExpiryWarning();
  };

  const handleLogoutAll = async () => {
    setIsLogoutAllLoading(true);
    const { error } = await logoutAllDevices();
    setIsLogoutAllLoading(false);

    if (!error) {
      router.push('/login');
    }
  };

  const handleSignInAgain = () => {
    logout();
    router.push('/login');
  };

  if (!isRefreshingToken && !refreshError && !showExpiryWarning) {
    return null;
  }

  const secondsUntilExpiry = sessionExpiresAt
    ? Math.max(0, Math.floor(sessionExpiresAt - Date.now() / 1000))
    : null;
  const minutesUntilExpiry = secondsUntilExpiry ? Math.floor(secondsUntilExpiry / 60) : null;

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 flex flex-col gap-3 sm:left-auto sm:w-96">
      {isRefreshingToken && (
        <div className="flex items-center gap-2 rounded-md bg-blue-600/95 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-blue-500/20">
          <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-white/60 border-t-transparent" />
          <span>Refreshing session…</span>
        </div>
      )}

      {refreshError && (
        <Callout variant="error" title="Session refresh failed">
          <p className="mb-2 text-sm">{refreshError}</p>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" onClick={handleManualRefresh} disabled={isManualRefreshLoading}>
              {isManualRefreshLoading ? 'Retrying…' : 'Retry now'}
            </Button>
            <Button size="sm" variant="secondary" onClick={handleSignInAgain}>
              Sign in again
            </Button>
          </div>
        </Callout>
      )}

      {showExpiryWarning && !refreshError && (
        <Callout variant="warning" title="Session expiring soon">
          <p className="mb-3 text-sm">
            {minutesUntilExpiry !== null
              ? `Your session will expire in under ${Math.max(1, minutesUntilExpiry)} minute${
                  minutesUntilExpiry === 1 ? '' : 's'
                }.`
              : 'Your session will expire soon.'}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" onClick={handleManualRefresh} disabled={isManualRefreshLoading}>
              {isManualRefreshLoading ? 'Refreshing…' : 'Refresh now'}
            </Button>
            <Button size="sm" variant="secondary" onClick={dismissExpiryWarning}>
              Dismiss
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={handleLogoutAll}
              disabled={isLogoutAllLoading}
            >
              {isLogoutAllLoading ? 'Logging out…' : 'Logout all devices'}
            </Button>
          </div>
        </Callout>
      )}
    </div>
  );
}

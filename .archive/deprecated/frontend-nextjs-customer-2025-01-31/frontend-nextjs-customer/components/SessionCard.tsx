// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

'use client';

import type { MouseEvent } from 'react';
import { Button, Card } from '@ninaivalaigal/ui-components';
import type { ActiveSession } from '../types/api';

type SessionCardProps = {
  session: ActiveSession;
  onLogout?: (sessionId: string) => void;
  isPending?: boolean;
  disabled?: boolean;
  logoutButtonTestId?: string;
};

const FALLBACK_DEVICE = 'Unknown device';
const FALLBACK_LOCATION = 'Location unavailable';
const FALLBACK_IP = 'IP hidden';
const FALLBACK_LAST_ACTIVE = 'Last active time unavailable';

const resolveLastActive = (value?: string) => {
  if (!value) {
    return FALLBACK_LAST_ACTIVE;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return FALLBACK_LAST_ACTIVE;
  }

  return parsed.toLocaleString();
};

export function SessionCard({
  session,
  onLogout,
  isPending = false,
  disabled = false,
  logoutButtonTestId,
}: SessionCardProps) {
  const isCurrent = Boolean(session.is_current);
  const deviceLabel = session.device || FALLBACK_DEVICE;
  const locationLabel = session.location || FALLBACK_LOCATION;
  const ipLabel = session.ip_address || FALLBACK_IP;
  const lastActive = resolveLastActive(session.last_active_at);
  const userAgent = session.user_agent;

  const isLogoutDisabled = isCurrent || disabled || isPending || !onLogout;

  const handleLogoutClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    if (isLogoutDisabled || !onLogout) {
      return;
    }

    onLogout(session.id);
  };

  const baseClasses = ['bg-white'];
  if (isCurrent) {
    baseClasses.push('border-blue-200', 'shadow-sm');
  }

  return (
    <Card className={baseClasses.join(' ')} data-session-id={session.id}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-gray-900">{deviceLabel}</p>
            {isCurrent ? (
              <span className="ml-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">
                Current device
              </span>
            ) : null}
          </div>
          {userAgent ? (
            <p className="text-xs text-gray-500" data-testid="session-user-agent">
              {userAgent}
            </p>
          ) : null}
          <p className="text-xs text-gray-500">
            {locationLabel} • {ipLabel}
          </p>
          <p className="text-xs text-gray-400">{lastActive}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={handleLogoutClick}
            disabled={isLogoutDisabled}
            data-testid={logoutButtonTestId}
          >
            {isPending ? 'Logging out…' : 'Logout session'}
          </Button>
        </div>
      </div>
    </Card>
  );
}

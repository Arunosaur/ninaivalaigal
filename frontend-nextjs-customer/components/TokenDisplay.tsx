// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

'use client';

import { useState } from 'react';
import { Button, Card } from '@ninaivalaigal/ui-components';

const maskToken = (token: string) => {
  if (token.length <= 4) {
    return '*'.repeat(token.length);
  }

  const maskedLength = Math.min(token.length - 4, 8);
  return `${'*'.repeat(maskedLength)}${token.slice(-4)}`;
};

const normalizeExpiry = (value?: number | null) => {
  if (typeof value !== 'number') {
    return null;
  }

  return value > 1_000_000_000_000 ? value : value * 1000;
};

const formatExpiry = (value?: number | null) => {
  const expiry = normalizeExpiry(value);
  if (!expiry) {
    return 'Expiry unknown';
  }

  const diff = expiry - Date.now();
  if (diff <= 0) {
    return 'Expired';
  }

  const minutes = Math.round(diff / 60000);
  if (minutes <= 1) {
    return 'Expires in under a minute';
  }

  if (minutes < 60) {
    return `Expires in ${minutes} minutes`;
  }

  const hours = Math.round(minutes / 60);
  return `Expires in ${hours} hour${hours === 1 ? '' : 's'}`;
};

type TokenType = 'access' | 'refresh';

type TokenDisplayProps = {
  accessToken?: string | null;
  refreshToken?: string | null;
  accessTokenExpiresAt?: number | null;
  refreshTokenExpiresAt?: number | null;
  title?: string;
  description?: string;
  onCopy?: (type: TokenType, token: string) => void | Promise<void>;
};

const TokenRow = ({
  label,
  token,
  isVisible,
  expiry,
  onToggleVisibility,
  onCopy,
}: {
  label: string;
  token?: string | null;
  isVisible: boolean;
  expiry?: number | null;
  onToggleVisibility: () => void;
  onCopy: () => void;
}) => {
  const hasToken = Boolean(token);
  const content = hasToken ? (isVisible ? token : maskToken(token!)) : 'Not available';
  const toggleLabel = isVisible ? 'Hide token' : 'Show token';
  const testId = `${label.toLowerCase().replace(/\s+/g, '-')}-value`;

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-900">{label}</p>
          <p
            className="break-all font-mono text-xs text-gray-700"
            data-testid={testId}
            suppressHydrationWarning
          >
            {content}
          </p>
          <p className="text-xs text-gray-500" suppressHydrationWarning>
            {formatExpiry(expiry)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={onToggleVisibility} disabled={!hasToken}>
            {toggleLabel}
          </Button>
          <Button size="sm" onClick={onCopy} disabled={!hasToken}>
            Copy token
          </Button>
        </div>
      </div>
    </div>
  );
};

export function TokenDisplay({
  accessToken,
  refreshToken,
  accessTokenExpiresAt,
  refreshTokenExpiresAt,
  title = 'Authentication tokens',
  description = 'Review and manage the tokens currently stored in your browser.',
  onCopy,
}: TokenDisplayProps) {
  const [isAccessVisible, setAccessVisible] = useState(false);
  const [isRefreshVisible, setRefreshVisible] = useState(false);

  const handleCopy = async (type: TokenType, value?: string | null) => {
    if (!value) {
      return;
    }

    if (onCopy) {
      await onCopy(type, value);
      return;
    }

    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(value);
      } catch (error) {
        console.warn('TokenDisplay: Failed to copy token', error);
      }
    }
  };

  return (
    <Card className="space-y-6 bg-white">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <p className="mt-1 text-sm text-gray-600">{description}</p>
      </div>

      <TokenRow
        label="Access token"
        token={accessToken}
        isVisible={isAccessVisible}
        expiry={accessTokenExpiresAt}
        onToggleVisibility={() => setAccessVisible((value) => !value)}
        onCopy={() => {
          void handleCopy('access', accessToken);
        }}
      />

      <TokenRow
        label="Refresh token"
        token={refreshToken}
        isVisible={isRefreshVisible}
        expiry={refreshTokenExpiresAt}
        onToggleVisibility={() => setRefreshVisible((value) => !value)}
        onCopy={() => {
          void handleCopy('refresh', refreshToken);
        }}
      />
    </Card>
  );
}

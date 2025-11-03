// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect, beforeEach } from 'vitest';
import { useNotificationStore } from './notificationStore';

describe('NotificationStore', () => {
  beforeEach(() => {
    // Reset store state
    const state = useNotificationStore.getState();
    state.clear();
  });

  it('should initialize with empty notifications', () => {
    const state = useNotificationStore.getState();

    expect(state.notifications).toEqual([]);
  });

  it('should push notification', () => {
    const state = useNotificationStore.getState();

    state.push({
      id: '1',
      title: 'Test Title',
      message: 'Test notification',
      createdAt: new Date().toISOString(),
      variant: 'info',
    });

    const updated = useNotificationStore.getState();
    expect(updated.notifications).toHaveLength(1);
    expect(updated.notifications[0].message).toBe('Test notification');
  });

  it('should dismiss notification', () => {
    const state = useNotificationStore.getState();

    state.push({
      id: '1',
      title: 'Test Title',
      message: 'Test notification',
      createdAt: new Date().toISOString(),
      variant: 'info',
    });

    let updated = useNotificationStore.getState();
    expect(updated.notifications).toHaveLength(1);

    state.dismiss('1');

    updated = useNotificationStore.getState();
    expect(updated.notifications).toHaveLength(0);
  });

  it('should clear all notifications', () => {
    const state = useNotificationStore.getState();

    state.push({
      id: '1',
      title: 'Title 1',
      message: 'Notification 1',
      createdAt: new Date().toISOString(),
      variant: 'info',
    });
    state.push({
      id: '2',
      title: 'Title 2',
      message: 'Notification 2',
      createdAt: new Date().toISOString(),
      variant: 'success',
    });

    let updated = useNotificationStore.getState();
    expect(updated.notifications).toHaveLength(2);

    state.clear();

    updated = useNotificationStore.getState();
    expect(updated.notifications).toHaveLength(0);
  });
});

// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { create } from "zustand";
import { notificationSchema, type Notification } from "../lib/schemas";

export type NotificationState = {
  notifications: Notification[];
  push: (notification: Notification) => void;
  dismiss: (id: string) => void;
  clear: () => void;
};

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  push: (notification: Notification) => {
    const result = notificationSchema.safeParse(notification);
    if (!result.success) {
      console.warn("Invalid notification payload", result.error.flatten());
      return;
    }
    set((state: NotificationState) => ({ notifications: [...state.notifications, result.data] }));
  },
  dismiss: (id: string) =>
    set((state: NotificationState) => ({
      notifications: state.notifications.filter((item: Notification) => item.id !== id)
    })),
  clear: () => set({ notifications: [] })
}));

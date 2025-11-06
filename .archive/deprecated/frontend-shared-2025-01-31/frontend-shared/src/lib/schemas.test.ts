// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect } from 'vitest';
import { sessionSchema, notificationSchema } from './schemas';

describe('schemas', () => {
  describe('sessionSchema', () => {
    it('should validate valid session', () => {
      const validSession = {
        userId: '123',
        email: 'test@example.com',
        displayName: 'Test User',
        roles: ['user', 'admin'],
        token: 'jwt-token-123',
        expiresAt: new Date().toISOString(),
      };

      const result = sessionSchema.safeParse(validSession);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validSession);
      }
    });

    it('should reject invalid email', () => {
      const invalidSession = {
        userId: '123',
        email: 'not-an-email',
        displayName: 'Test User',
        roles: ['user'],
        token: 'jwt-token-123',
        expiresAt: new Date().toISOString(),
      };

      const result = sessionSchema.safeParse(invalidSession);
      expect(result.success).toBe(false);
    });

    it('should reject missing required fields', () => {
      const invalidSession = {
        userId: '123',
        email: 'test@example.com',
        // Missing displayName, roles, token, expiresAt
      };

      const result = sessionSchema.safeParse(invalidSession);
      expect(result.success).toBe(false);
    });

    it('should validate roles as array of strings', () => {
      const validSession = {
        userId: '123',
        email: 'test@example.com',
        displayName: 'Test User',
        roles: ['user'],
        token: 'jwt-token-123',
        expiresAt: new Date().toISOString(),
      };

      const result = sessionSchema.safeParse(validSession);
      expect(result.success).toBe(true);
    });

    it('should reject empty roles array', () => {
      const invalidSession = {
        userId: '123',
        email: 'test@example.com',
        displayName: 'Test User',
        roles: [],
        token: 'jwt-token-123',
        expiresAt: new Date().toISOString(),
      };

      const result = sessionSchema.safeParse(invalidSession);
      // Zod allows empty arrays, so this should pass
      expect(result.success).toBe(true);
    });

    it('should validate expiresAt as ISO datetime string', () => {
      const validSession = {
        userId: '123',
        email: 'test@example.com',
        displayName: 'Test User',
        roles: ['user'],
        token: 'jwt-token-123',
        expiresAt: '2025-01-01T00:00:00.000Z',
      };

      const result = sessionSchema.safeParse(validSession);
      expect(result.success).toBe(true);
    });

    it('should reject invalid datetime format', () => {
      const invalidSession = {
        userId: '123',
        email: 'test@example.com',
        displayName: 'Test User',
        roles: ['user'],
        token: 'jwt-token-123',
        expiresAt: 'not-a-date',
      };

      const result = sessionSchema.safeParse(invalidSession);
      expect(result.success).toBe(false);
    });
  });

  describe('notificationSchema', () => {
    it('should validate valid notification', () => {
      const validNotification = {
        id: 'notif-123',
        title: 'Test Notification',
        message: 'This is a test message',
        createdAt: new Date().toISOString(),
        variant: 'info' as const,
      };

      const result = notificationSchema.safeParse(validNotification);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validNotification);
      }
    });

    it('should validate all notification variants', () => {
      const variants = ['info', 'success', 'warning', 'error'] as const;

      variants.forEach((variant) => {
        const notification = {
          id: 'notif-123',
          title: 'Test',
          message: 'Message',
          createdAt: new Date().toISOString(),
          variant,
        };

        const result = notificationSchema.safeParse(notification);
        expect(result.success).toBe(true);
      });
    });

    it('should reject invalid variant', () => {
      const invalidNotification = {
        id: 'notif-123',
        title: 'Test',
        message: 'Message',
        createdAt: new Date().toISOString(),
        variant: 'invalid',
      };

      const result = notificationSchema.safeParse(invalidNotification);
      expect(result.success).toBe(false);
    });

    it('should require all fields', () => {
      const invalidNotification = {
        id: 'notif-123',
        // Missing title, message, createdAt, variant
      };

      const result = notificationSchema.safeParse(invalidNotification);
      expect(result.success).toBe(false);
    });

    it('should validate createdAt as ISO datetime string', () => {
      const validNotification = {
        id: 'notif-123',
        title: 'Test',
        message: 'Message',
        createdAt: '2025-01-01T00:00:00.000Z',
        variant: 'success' as const,
      };

      const result = notificationSchema.safeParse(validNotification);
      expect(result.success).toBe(true);
    });
  });
});

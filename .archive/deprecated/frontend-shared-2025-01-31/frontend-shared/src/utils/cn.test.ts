// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect } from 'vitest';
import { cn, formatDate } from '../lib/utils';

describe('cn utility function', () => {
  it('should merge class names correctly', () => {
    const result = cn('px-4', 'py-2');
    expect(result).toContain('px-4');
    expect(result).toContain('py-2');
  });

  it('should handle conditional classes', () => {
    const result = cn('px-4', true && 'py-2', false && 'px-6');
    expect(result).toContain('px-4');
    expect(result).toContain('py-2');
    expect(result).not.toContain('px-6');
  });

  it('should merge conflicting Tailwind classes', () => {
    // tailwind-merge should deduplicate conflicting utilities
    const result = cn('px-4', 'px-6');
    // The last one should win
    expect(result).toContain('px-6');
  });

  it('should handle undefined and null', () => {
    const result = cn('px-4', undefined, null, 'py-2');
    expect(result).toContain('px-4');
    expect(result).toContain('py-2');
  });

  it('should handle empty strings', () => {
    const result = cn('px-4', '', 'py-2');
    expect(result).toContain('px-4');
    expect(result).toContain('py-2');
  });

  it('should handle arrays', () => {
    const result = cn(['px-4', 'py-2'], 'bg-blue-500');
    expect(result).toContain('px-4');
    expect(result).toContain('py-2');
    expect(result).toContain('bg-blue-500');
  });

  it('should handle objects with boolean values', () => {
    const result = cn({
      'px-4': true,
      'py-2': true,
      'px-6': false,
    });
    expect(result).toContain('px-4');
    expect(result).toContain('py-2');
    expect(result).not.toContain('px-6');
  });
});

describe('formatDate utility function', () => {
  it('should format Date object', () => {
    const date = new Date('2025-01-15T10:30:00Z');
    const result = formatDate(date);

    expect(result).toContain('Jan');
    expect(result).toContain('2025');
    expect(result).toContain('15');
  });

  it('should format ISO date string', () => {
    const dateString = '2025-01-15T10:30:00Z';
    const result = formatDate(dateString);

    expect(result).toContain('Jan');
    expect(result).toContain('2025');
  });

  it('should format timestamp number', () => {
    const timestamp = new Date('2025-06-20T12:00:00Z').getTime();
    const result = formatDate(timestamp);

    expect(result).toContain('Jun');
    expect(result).toContain('2025');
  });

  it('should return empty string for invalid date', () => {
    const result = formatDate('invalid-date');
    expect(result).toBe('');
  });

  it('should return empty string for NaN timestamp', () => {
    const result = formatDate(NaN);
    expect(result).toBe('');
  });

  it('should use custom locale', () => {
    const date = new Date('2025-01-15T10:30:00Z');
    const result = formatDate(date, 'de-DE');

    // German locale should format differently
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
  });

  it('should handle different months correctly', () => {
    const months = [
      new Date('2025-01-15'),
      new Date('2025-06-15'),
      new Date('2025-12-15'),
    ];

    months.forEach((date) => {
      const result = formatDate(date);
      expect(result).toBeTruthy();
      expect(result.length).toBeGreaterThan(0);
    });
  });
});

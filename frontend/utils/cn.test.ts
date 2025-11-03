// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect } from 'vitest';
import { cn } from './cn';

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

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to merge Tailwind CSS classes with proper precedence.
 * Combines clsx for conditional classes and tailwind-merge for deduplication.
 *
 * @param inputs - Class names, objects, or arrays to merge
 * @returns Merged class string
 *
 * @example
 * ```tsx
 * cn('px-4 py-2', 'bg-blue-500', { 'text-white': true })
 * // Returns: "px-4 py-2 bg-blue-500 text-white"
 *
 * cn('px-4 py-2', 'px-6')
 * // Returns: "py-2 px-6" (tailwind-merge removes conflicting px-4)
 * ```
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

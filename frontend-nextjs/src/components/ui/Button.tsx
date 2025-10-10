import { cva, type VariantProps } from 'class-variance-authority';
import React from 'react';

import { cn } from '@/utils/cn';

// Button variants using class-variance-authority for type-safe styling
const buttonVariants = cva(
  // Base styles - applied to all buttons
  [
    'inline-flex items-center justify-center gap-2',
    'rounded-md font-medium transition-all duration-base',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    'select-none',
  ],
  {
    variants: {
      variant: {
        primary: [
          'bg-primary-600 text-white border border-primary-600',
          'hover:bg-primary-700 hover:border-primary-700',
          'active:bg-primary-800 active:border-primary-800',
          'focus-visible:ring-primary-500',
        ],
        secondary: [
          'bg-white text-secondary-700 border border-secondary-300',
          'hover:bg-secondary-50 hover:border-secondary-400',
          'active:bg-secondary-100 active:border-secondary-500',
          'focus-visible:ring-secondary-500',
        ],
        ghost: [
          'bg-transparent text-secondary-700 border border-transparent',
          'hover:bg-secondary-100',
          'active:bg-secondary-200',
          'focus-visible:ring-secondary-500',
        ],
        destructive: [
          'bg-error-600 text-white border border-error-600',
          'hover:bg-error-700 hover:border-error-700',
          'active:bg-error-800 active:border-error-800',
          'focus-visible:ring-error-500',
        ],
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-6 text-lg',
        icon: 'h-10 w-10 p-0',
      },
      fullWidth: {
        true: 'w-full',
        false: 'w-auto',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
      fullWidth: false,
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /**
   * If true, the button will show a loading spinner and be disabled
   */
  loading?: boolean;
  /**
   * Icon to display before the button text
   */
  startIcon?: React.ReactNode;
  /**
   * Icon to display after the button text
   */
  endIcon?: React.ReactNode;
  /**
   * Custom class names to apply to the button
   */
  className?: string;
  /**
   * Button content
   */
  children?: React.ReactNode;
}

/**
 * Button component with multiple variants, sizes, and accessibility features.
 *
 * @example
 * ```tsx
 * // Primary button
 * <Button>Save Changes</Button>
 *
 * // Secondary button with icon
 * <Button variant="secondary" startIcon={<PlusIcon />}>
 *   Add Item
 * </Button>
 *
 * // Loading state
 * <Button loading>Saving...</Button>
 *
 * // Full width destructive action
 * <Button variant="destructive" fullWidth>
 *   Delete Account
 * </Button>
 * ```
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      loading = false,
      startIcon,
      endIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        className={cn(buttonVariants({ variant, size, fullWidth }), className)}
        ref={ref}
        disabled={isDisabled}
        aria-disabled={isDisabled}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!loading && startIcon && (
          <span className="flex-shrink-0" aria-hidden="true">
            {startIcon}
          </span>
        )}
        {children && <span>{children}</span>}
        {!loading && endIcon && (
          <span className="flex-shrink-0" aria-hidden="true">
            {endIcon}
          </span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

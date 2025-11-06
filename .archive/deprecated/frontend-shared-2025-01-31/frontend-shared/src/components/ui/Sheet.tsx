// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import React from 'react';
import { cn } from '../../lib/utils';

export interface SheetProps {
  /** Whether the sheet is open */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Sheet content */
  children: React.ReactNode;
}

/**
 * Sheet component for slide-in panels
 *
 * @example
 * ```tsx
 * <Sheet open={isOpen} onOpenChange={setIsOpen}>
 *   <SheetContent>
 *     <SheetHeader>
 *       <SheetTitle>Settings</SheetTitle>
 *     </SheetHeader>
 *   </SheetContent>
 * </Sheet>
 * ```
 */
export const Sheet: React.FC<SheetProps> = ({ open, onOpenChange, children }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="fixed inset-0 bg-black/50"
        onClick={() => onOpenChange?.(false)}
        aria-label="Close sheet"
      />
      {children}
    </div>
  );
};

export interface SheetContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Position of the sheet */
  position?: 'right' | 'left' | 'top' | 'bottom';
}

/**
 * SheetContent component for sheet body
 */
export const SheetContent = React.forwardRef<
  HTMLDivElement,
  SheetContentProps
>(({ className, position = 'right', children, ...props }, ref) => {
  const positionStyles = {
    right: 'right-0 top-0 h-full w-full sm:w-96',
    left: 'left-0 top-0 h-full w-full sm:w-96',
    top: 'top-0 left-0 w-full h-full sm:h-96',
    bottom: 'bottom-0 left-0 w-full h-full sm:h-96',
  };

  return (
    <div
      ref={ref}
      className={cn(
        'fixed bg-white shadow-xl',
        'transition-transform duration-300',
        positionStyles[position],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

SheetContent.displayName = 'SheetContent';

export interface SheetHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

/**
 * SheetHeader component for sheet header section
 */
export const SheetHeader = React.forwardRef<HTMLDivElement, SheetHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-2 p-6', className)}
      {...props}
    />
  )
);

SheetHeader.displayName = 'SheetHeader';

export interface SheetTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

/**
 * SheetTitle component for sheet title
 */
export const SheetTitle = React.forwardRef<HTMLHeadingElement, SheetTitleProps>(
  ({ className, ...props }, ref) => (
    <h2
      ref={ref}
      className={cn('text-lg font-semibold text-gray-900', className)}
      {...props}
    />
  )
);

SheetTitle.displayName = 'SheetTitle';

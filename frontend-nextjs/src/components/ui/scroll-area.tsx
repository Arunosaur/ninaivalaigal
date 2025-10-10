import React from 'react';
import { cn } from '@/utils/cn';

export interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('relative overflow-auto', className)}
      {...props}
    >
      {children}
    </div>
  )
);
ScrollArea.displayName = 'ScrollArea';

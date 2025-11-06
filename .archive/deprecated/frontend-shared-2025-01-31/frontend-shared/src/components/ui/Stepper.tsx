// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import React from 'react';
import { cn } from '../../lib/utils';

export interface Step {
  id: string;
  title: string;
  description?: string;
}

export interface StepperProps {
  /** Array of steps */
  steps: Step[];
  /** Current active step index (0-based) */
  currentStep: number;
  /** Callback when step is clicked */
  onStepChange?: (stepIndex: number) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Stepper component for multi-step workflows
 *
 * @example
 * ```tsx
 * const steps = [
 *   { id: '1', title: 'Account', description: 'Create your account' },
 *   { id: '2', title: 'Profile', description: 'Complete your profile' },
 *   { id: '3', title: 'Done', description: 'All set!' }
 * ];
 *
 * <Stepper steps={steps} currentStep={1} />
 * ```
 */
export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStep,
  onStepChange,
  className,
}) => {
  return (
    <nav aria-label="Progress" className={className}>
      <ol className="flex items-center">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isClickable = onStepChange && (isCompleted || isCurrent);

          return (
            <li
              key={step.id}
              className={cn(
                'relative',
                index !== steps.length - 1 && 'flex-1'
              )}
            >
              <div className="flex items-center">
                {/* Step indicator */}
                <button
                  type="button"
                  onClick={() => isClickable && onStepChange(index)}
                  disabled={!isClickable}
                  className={cn(
                    'relative flex h-8 w-8 items-center justify-center rounded-full',
                    'transition-colors duration-200',
                    isCompleted && 'bg-green-600 hover:bg-green-700',
                    isCurrent && 'border-2 border-blue-600 bg-white',
                    !isCompleted && !isCurrent && 'border-2 border-gray-300 bg-white',
                    isClickable && 'cursor-pointer',
                    !isClickable && 'cursor-default'
                  )}
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  {isCompleted ? (
                    <svg
                      className="h-5 w-5 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <span
                      className={cn(
                        'text-sm font-medium',
                        isCurrent ? 'text-blue-600' : 'text-gray-500'
                      )}
                    >
                      {index + 1}
                    </span>
                  )}
                </button>

                {/* Connector line */}
                {index !== steps.length - 1 && (
                  <div
                    className={cn(
                      'h-0.5 w-full ml-2',
                      isCompleted ? 'bg-green-600' : 'bg-gray-300'
                    )}
                  />
                )}
              </div>

              {/* Step title */}
              <div className="mt-2 text-center">
                <span
                  className={cn(
                    'text-sm font-medium',
                    isCurrent && 'text-blue-600',
                    isCompleted && 'text-gray-900',
                    !isCompleted && !isCurrent && 'text-gray-500'
                  )}
                >
                  {step.title}
                </span>
                {step.description && (
                  <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { cva, type VariantProps } from 'class-variance-authority';
import React, { useState, useCallback } from 'react';

import { cn } from '../utils/cn';

// Stepper variants using class-variance-authority for narrative UI
const stepperVariants = cva(
  // Base styles - applied to all steppers
  [
    'flex items-center justify-between',
    'p-4 rounded-lg border',
    'bg-white shadow-sm',
    'transition-all duration-base',
  ],
  {
    variants: {
      variant: {
        timeline: [
          'flex-col space-y-4',
          'border-primary-200',
          'bg-gradient-to-b from-primary-50 to-white',
        ],
        horizontal: [
          'flex-row space-x-4',
          'border-secondary-200',
          'bg-secondary-50',
        ],
        compact: [
          'flex-row space-x-2 p-2',
          'border-secondary-300',
          'bg-white',
        ],
      },
      size: {
        sm: 'text-sm',
        md: 'text-base',
        lg: 'text-lg',
      },
      state: {
        active: [
          'border-primary-500 shadow-md',
          'ring-2 ring-primary-200',
        ],
        completed: [
          'border-success-400',
          'bg-success-50',
        ],
        pending: [
          'border-secondary-300',
          'opacity-75',
        ],
      },
    },
    defaultVariants: {
      variant: 'timeline',
      size: 'md',
      state: 'pending',
    },
  }
);

const stepIndicatorVariants = cva(
  [
    'flex items-center justify-center',
    'w-8 h-8 rounded-full',
    'font-medium text-sm',
    'transition-all duration-base',
  ],
  {
    variants: {
      state: {
        active: [
          'bg-primary-600 text-white',
          'shadow-lg ring-2 ring-primary-200',
        ],
        completed: [
          'bg-success-500 text-white',
          'shadow-md',
        ],
        pending: [
          'bg-secondary-200 text-secondary-600',
          'border border-secondary-300',
        ],
      },
    },
    defaultVariants: {
      state: 'pending',
    },
  }
);

// Step data interface
export interface StepData {
  id: string;
  title: string;
  description?: string;
  content?: React.ReactNode;
  metadata?: Record<string, any>;
}

// Stepper component props
export interface StepperProps extends VariantProps<typeof stepperVariants> {
  steps: StepData[];
  currentStep: number;
  onStepChange?: (stepIndex: number, step: StepData) => void;
  onComplete?: () => void;
  className?: string;
  showProgress?: boolean;
  allowSkip?: boolean;
  disableStepClick?: boolean; // Disable clicking on step circles
  children?: React.ReactNode;
}

// Individual step component
interface StepProps {
  step: StepData;
  index: number;
  isActive: boolean;
  isCompleted: boolean;
  onClick?: () => void;
  variant?: VariantProps<typeof stepperVariants>['variant'];
  size?: VariantProps<typeof stepperVariants>['size'];
}

interface StepPropsExtended extends StepProps {
  isLastStep: boolean;
  totalSteps: number;
}

const Step: React.FC<StepPropsExtended> = ({
  step,
  index,
  isActive,
  isCompleted,
  onClick,
  variant = 'timeline',
  size = 'md',
  isLastStep,
  totalSteps,
}) => {
  const state = isCompleted ? 'completed' : isActive ? 'active' : 'pending';

  return (
    <div
      className={cn(
        'relative flex items-start space-x-3 cursor-pointer group',
        variant === 'horizontal' && 'flex-col items-center space-x-0 space-y-2',
        variant === 'compact' && 'flex-row items-center space-y-0 space-x-2'
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-current={isActive ? 'step' : undefined}
      aria-setsize={totalSteps}
      aria-posinset={index + 1}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      {/* Step Indicator */}
      <div className={stepIndicatorVariants({ state })}>
        {isCompleted ? (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <span>{index + 1}</span>
        )}
      </div>

      {/* Step Content */}
      <div className={cn(
        'flex-1 min-w-0',
        variant === 'horizontal' && 'text-center',
        variant === 'compact' && 'flex-none'
      )}>
        <h3 className={cn(
          'font-medium text-secondary-900 group-hover:text-primary-700',
          size === 'sm' && 'text-sm',
          size === 'md' && 'text-base',
          size === 'lg' && 'text-lg',
          isActive && 'text-primary-700 font-semibold'
        )}>
          {step.title}
        </h3>

        {step.description && variant !== 'compact' && (
          <p className={cn(
            'mt-1 text-secondary-600 group-hover:text-secondary-800',
            size === 'sm' && 'text-xs',
            size === 'md' && 'text-sm',
            size === 'lg' && 'text-base'
          )}>
            {step.description}
          </p>
        )}
      </div>

      {/* Connection Line (for timeline variant, hidden on last step) */}
      {variant === 'timeline' && !isLastStep && (
        <div className={cn(
          'absolute left-4 top-12 w-0.5 h-8 -mt-2',
          isCompleted ? 'bg-success-400' : 'bg-secondary-300'
        )} />
      )}
    </div>
  );
};

/**
 * Stepper component for guided narrative walkthroughs
 *
 * Provides step-by-step navigation with visual progress indicators,
 * accessibility support, and integration with SPEC-075 design tokens.
 *
 * @example
 * ```tsx
 * const steps = [
 *   { id: '1', title: 'Welcome', description: 'Getting started' },
 *   { id: '2', title: 'Setup', description: 'Configure your preferences' },
 *   { id: '3', title: 'Complete', description: 'You\'re all set!' }
 * ];
 *
 * <Stepper
 *   steps={steps}
 *   currentStep={0}
 *   onStepChange={(index, step) => console.log('Step:', index, step)}
 *   variant="timeline"
 *   showProgress
 * />
 * ```
 */
export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStep,
  onStepChange,
  onComplete,
  variant = 'timeline',
  size = 'md',
  state = 'active',
  className,
  showProgress = true,
  allowSkip = false,
  disableStepClick = false,
  children,
  ...props
}) => {
  const [internalStep, setInternalStep] = useState(currentStep);
  const activeStep = currentStep ?? internalStep;

  const handleStepClick = useCallback((stepIndex: number) => {
    // Don't handle clicks if step clicking is disabled
    if (disableStepClick) {
      console.log('🚫 Step clicking is disabled');
      return;
    }

    if (!allowSkip && stepIndex > activeStep + 1) {
      return; // Don't allow skipping ahead unless explicitly allowed
    }

    const step = steps[stepIndex];
    if (onStepChange) {
      onStepChange(stepIndex, step);
    } else {
      setInternalStep(stepIndex);
    }

    // Don't auto-complete when clicking on last step
    // Let the parent component handle completion
  }, [activeStep, allowSkip, disableStepClick, steps, onStepChange, onComplete]);

  // Arrow key navigation handler
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
      e.preventDefault();
      const nextStep = Math.min(activeStep + 1, steps.length - 1);
      handleStepClick(nextStep);
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      e.preventDefault();
      const prevStep = Math.max(activeStep - 1, 0);
      handleStepClick(prevStep);
    }
  }, [activeStep, steps.length, handleStepClick]);

  const progressPercentage = ((activeStep + 1) / steps.length) * 100;

  return (
    <div
      className={cn(stepperVariants({ variant, size, state }), className)}
      role="navigation"
      aria-label="Step navigation"
      onKeyDown={handleKeyDown}
      {...props}
    >
      {/* Progress Bar */}
      {showProgress && (
        <div className="w-full mb-4">
          <div className="flex justify-between text-xs text-secondary-600 mb-1">
            <span>Progress</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
          <div className="w-full bg-secondary-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
              role="progressbar"
              aria-valuenow={Math.round(progressPercentage)}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>
      )}

      {/* Steps */}
      <div
        className={cn(
          'relative',
          variant === 'timeline' && 'space-y-6',
          variant === 'horizontal' && 'flex justify-between items-start',
          variant === 'compact' && 'flex space-x-4'
        )}
        role="list"
        aria-label="Steps"
      >
        {steps.map((step, index) => (
          <Step
            key={step.id}
            step={step}
            index={index}
            isActive={index === activeStep}
            isCompleted={index < activeStep}
            onClick={() => handleStepClick(index)}
            variant={variant}
            size={size}
            isLastStep={index === steps.length - 1}
            totalSteps={steps.length}
          />
        ))}
      </div>

      {/* Step Content Area */}
      {children && (
        <div className="mt-6 p-4 bg-secondary-50 rounded-lg border border-secondary-200">
          {children}
        </div>
      )}

      {/* Navigation Controls */}
      <div className="flex justify-between mt-6">
        <button
          type="button"
          onClick={() => handleStepClick(Math.max(0, activeStep - 1))}
          disabled={activeStep === 0}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md',
            'border border-secondary-300 text-secondary-700',
            'hover:bg-secondary-50 focus:outline-none focus:ring-2 focus:ring-primary-500',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          Previous
        </button>

        <button
          type="button"
          onClick={() => {
            if (activeStep === steps.length - 1) {
              onComplete?.();
            } else {
              handleStepClick(activeStep + 1);
            }
          }}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md',
            'bg-primary-600 text-white border border-primary-600',
            'hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500'
          )}
        >
          {activeStep === steps.length - 1 ? 'Complete' : 'Next'}
        </button>
      </div>
    </div>
  );
};

export default Stepper;

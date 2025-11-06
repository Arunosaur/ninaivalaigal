// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from '@storybook/react';
import { Stepper, type StepData } from './Stepper';
import { useState } from 'react';
import { Button } from '../ui/Button';

const meta = {
  title: 'Narrative/Stepper',
  component: Stepper,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['timeline', 'horizontal', 'compact'],
      description: 'Visual style variant',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size of stepper',
    },
  },
} satisfies Meta<typeof Stepper>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleSteps: StepData[] = [
  {
    id: 'step-1',
    title: 'Welcome',
    description: 'Get started with your journey',
    content: 'Welcome to the onboarding process',
  },
  {
    id: 'step-2',
    title: 'Setup Profile',
    description: 'Add your personal information',
    content: 'Fill out your profile details',
  },
  {
    id: 'step-3',
    title: 'Preferences',
    description: 'Customize your experience',
    content: 'Choose your preferences',
  },
  {
    id: 'step-4',
    title: 'Complete',
    description: 'Finish setup',
    content: 'You are all set!',
  },
];

// Timeline variant
export const TimelineVariant: Story = {
  render: () => {
    const [currentStep, setCurrentStep] = useState(0);

    return (
      <div className="w-full max-w-2xl">
        <Stepper
          steps={sampleSteps}
          currentStep={currentStep}
          variant="timeline"
          onStepChange={(index) => setCurrentStep(index)}
          showProgress
        />
        <div className="mt-6 flex justify-between">
          <Button
            variant="secondary"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          <Button
            onClick={() => setCurrentStep(Math.min(sampleSteps.length - 1, currentStep + 1))}
            disabled={currentStep === sampleSteps.length - 1}
          >
            Next
          </Button>
        </div>
      </div>
    );
  },
};

// Horizontal variant
export const HorizontalVariant: Story = {
  render: () => {
    const [currentStep, setCurrentStep] = useState(1);

    return (
      <div className="w-full max-w-4xl">
        <Stepper
          steps={sampleSteps}
          currentStep={currentStep}
          variant="horizontal"
          onStepChange={(index) => setCurrentStep(index)}
          showProgress
        />
        <div className="mt-6 flex justify-between">
          <Button
            variant="secondary"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          <Button
            onClick={() => setCurrentStep(Math.min(sampleSteps.length - 1, currentStep + 1))}
            disabled={currentStep === sampleSteps.length - 1}
          >
            Next
          </Button>
        </div>
      </div>
    );
  },
};

// Compact variant
export const CompactVariant: Story = {
  render: () => {
    const [currentStep, setCurrentStep] = useState(2);

    return (
      <div className="w-full max-w-3xl">
        <Stepper
          steps={sampleSteps}
          currentStep={currentStep}
          variant="compact"
          onStepChange={(index) => setCurrentStep(index)}
        />
        <div className="mt-6 flex justify-between">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          <Button
            size="sm"
            onClick={() => setCurrentStep(Math.min(sampleSteps.length - 1, currentStep + 1))}
            disabled={currentStep === sampleSteps.length - 1}
          >
            Next
          </Button>
        </div>
      </div>
    );
  },
};

// Interactive with completion
export const InteractiveComplete: Story = {
  render: () => {
    const [currentStep, setCurrentStep] = useState(0);
    const [completed, setCompleted] = useState(false);

    const handleComplete = () => {
      setCompleted(true);
    };

    if (completed) {
      return (
        <div className="w-full max-w-2xl text-center p-8 bg-success-50 rounded-lg border border-success-200">
          <h2 className="text-2xl font-bold text-success-900 mb-2">
            🎉 Completed!
          </h2>
          <p className="text-success-700 mb-4">
            You have successfully finished all steps.
          </p>
          <Button
            variant="secondary"
            onClick={() => {
              setCurrentStep(0);
              setCompleted(false);
            }}
          >
            Start Over
          </Button>
        </div>
      );
    }

    return (
      <div className="w-full max-w-2xl">
        <Stepper
          steps={sampleSteps}
          currentStep={currentStep}
          onStepChange={(index) => setCurrentStep(index)}
          onComplete={handleComplete}
          showProgress
        />
        <div className="mt-6 flex justify-between">
          <Button
            variant="secondary"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          {currentStep === sampleSteps.length - 1 ? (
            <Button onClick={handleComplete}>
              Complete
            </Button>
          ) : (
            <Button onClick={() => setCurrentStep(currentStep + 1)}>
              Next
            </Button>
          )}
        </div>
      </div>
    );
  },
};

// All sizes
export const AllSizes: Story = {
  render: () => (
    <div className="space-y-8 w-full max-w-4xl">
      <div>
        <h3 className="text-sm font-medium text-secondary-700 mb-2">Small</h3>
        <Stepper
          steps={sampleSteps.slice(0, 3)}
          currentStep={1}
          size="sm"
        />
      </div>
      <div>
        <h3 className="text-sm font-medium text-secondary-700 mb-2">Medium (Default)</h3>
        <Stepper
          steps={sampleSteps.slice(0, 3)}
          currentStep={1}
          size="md"
        />
      </div>
      <div>
        <h3 className="text-sm font-medium text-secondary-700 mb-2">Large</h3>
        <Stepper
          steps={sampleSteps.slice(0, 3)}
          currentStep={1}
          size="lg"
        />
      </div>
    </div>
  ),
  parameters: {
    layout: 'padded',
  },
};

// Onboarding flow example
export const OnboardingFlow: Story = {
  render: () => {
    const [currentStep, setCurrentStep] = useState(0);

    const onboardingSteps: StepData[] = [
      {
        id: 'welcome',
        title: 'Welcome to Ninaivalaigal',
        description: 'Your personal memory garden',
        content: 'Create, connect, and cultivate your memories',
      },
      {
        id: 'profile',
        title: 'Create Your Profile',
        description: 'Tell us about yourself',
        content: 'Add your name, interests, and goals',
      },
      {
        id: 'first-memory',
        title: 'Capture First Memory',
        description: 'Try creating a memory',
        content: 'Write down something meaningful',
      },
      {
        id: 'explore',
        title: 'Explore Features',
        description: 'Discover what you can do',
        content: 'Graph view, AI insights, and more',
      },
    ];

    return (
      <div className="w-full max-w-2xl">
        <Stepper
          steps={onboardingSteps}
          currentStep={currentStep}
          variant="timeline"
          onStepChange={(index) => setCurrentStep(index)}
          showProgress
        />
        <div className="mt-6 flex justify-between">
          <Button
            variant="ghost"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            ← Back
          </Button>
          <Button
            onClick={() => setCurrentStep(Math.min(onboardingSteps.length - 1, currentStep + 1))}
            disabled={currentStep === onboardingSteps.length - 1}
          >
            Continue →
          </Button>
        </div>
      </div>
    );
  },
};

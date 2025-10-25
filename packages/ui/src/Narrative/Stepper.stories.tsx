// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { Stepper, type StepData } from './Stepper';

const meta = {
  title: 'Narrative/Stepper',
  component: Stepper,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Stepper component provides guided navigation for narrative walkthroughs.
It's designed for SPEC-076 Visual Narrative Layer to create interactive
step-by-step experiences with accessibility support and SPEC-075 design tokens.

## Features
- **Multiple Variants**: Timeline, horizontal, and compact layouts
- **Progress Tracking**: Visual progress bar with percentage
- **Accessibility**: Full keyboard navigation and screen reader support
- **Interactive Controls**: Previous/Next navigation with completion handling
- **Flexible Content**: Support for custom step content and metadata
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['timeline', 'horizontal', 'compact'],
      description: 'Visual layout variant',
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
      description: 'Size of the stepper',
    },
    state: {
      control: { type: 'select' },
      options: ['active', 'completed', 'pending'],
      description: 'Overall state of the stepper',
    },
    showProgress: {
      control: 'boolean',
      description: 'Show progress bar',
    },
    allowSkip: {
      control: 'boolean',
      description: 'Allow skipping ahead to future steps',
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Stepper>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample step data for stories
const sampleSteps: StepData[] = [
  {
    id: 'welcome',
    title: 'Welcome',
    description: 'Get started with your guided tour',
    metadata: { duration: '1 min' },
  },
  {
    id: 'setup',
    title: 'Setup Profile',
    description: 'Configure your preferences and settings',
    metadata: { duration: '3 min' },
  },
  {
    id: 'explore',
    title: 'Explore Features',
    description: 'Discover the main features and capabilities',
    metadata: { duration: '5 min' },
  },
  {
    id: 'complete',
    title: 'Complete Setup',
    description: 'Finish your onboarding process',
    metadata: { duration: '2 min' },
  },
];

const memoryBrowserSteps: StepData[] = [
  {
    id: 'search',
    title: 'Search Memories',
    description: 'Use the search bar to find specific memories',
    metadata: { aiContext: 'High relevance based on recent activity' },
  },
  {
    id: 'filter',
    title: 'Apply Filters',
    description: 'Narrow down results using tags and date ranges',
    metadata: { aiContext: 'Suggested filters based on your patterns' },
  },
  {
    id: 'explore-graph',
    title: 'Explore Connections',
    description: 'View related memories in the graph visualization',
    metadata: { aiContext: 'Graph shows 15 related memories' },
  },
  {
    id: 'guided-mode',
    title: 'Guided Walkthrough',
    description: 'Follow the narrative path through your memories',
    metadata: { aiContext: 'AI-generated story based on memory relationships' },
  },
];

// Basic stepper variants
export const Timeline: Story = {
  args: {
    steps: sampleSteps,
    currentStep: 1,
    variant: 'timeline',
    size: 'md',
    showProgress: true,
    allowSkip: false,
  },
};

export const Horizontal: Story = {
  args: {
    steps: sampleSteps,
    currentStep: 2,
    variant: 'horizontal',
    size: 'md',
    showProgress: true,
    allowSkip: false,
  },
};

export const Compact: Story = {
  args: {
    steps: sampleSteps,
    currentStep: 0,
    variant: 'compact',
    size: 'sm',
    showProgress: false,
    allowSkip: true,
  },
};

// Interactive stepper with state management
export const Interactive: Story = {
  render: (args) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [completedSteps, setCompletedSteps] = useState<string[]>([]);

    const handleStepChange = (stepIndex: number, step: StepData) => {
      setCurrentStep(stepIndex);

      // Mark previous steps as completed
      const newCompleted = sampleSteps
        .slice(0, stepIndex)
        .map(s => s.id)
        .filter(id => !completedSteps.includes(id));

      setCompletedSteps(prev => [...prev, ...newCompleted]);
    };

    const handleComplete = () => {
      setCompletedSteps(sampleSteps.map(s => s.id));
      alert('Stepper completed! 🎉');
    };

    return (
      <div className="max-w-2xl mx-auto">
        <Stepper
          {...args}
          steps={sampleSteps}
          currentStep={currentStep}
          onStepChange={handleStepChange}
          onComplete={handleComplete}
        >
          <div className="text-center">
            <h3 className="text-lg font-medium text-secondary-900 mb-2">
              {sampleSteps[currentStep]?.title}
            </h3>
            <p className="text-secondary-600 mb-4">
              {sampleSteps[currentStep]?.description}
            </p>
            <div className="bg-primary-50 p-4 rounded-lg">
              <p className="text-sm text-primary-700">
                Step {currentStep + 1} content goes here. This could include
                forms, instructions, or any interactive elements.
              </p>
            </div>
          </div>
        </Stepper>
      </div>
    );
  },
  args: {
    variant: 'timeline',
    size: 'md',
    showProgress: true,
    allowSkip: false,
  },
};

// Memory Browser walkthrough example
export const MemoryBrowserWalkthrough: Story = {
  render: (args) => {
    const [currentStep, setCurrentStep] = useState(0);

    return (
      <div className="max-w-3xl mx-auto">
        <div className="mb-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <h2 className="text-lg font-semibold text-primary-900 mb-2">
            🧠 Memory Browser Guided Tour
          </h2>
          <p className="text-primary-700">
            This demonstrates SPEC-076 integration with Memory Browser (SPEC-031).
            The stepper guides users through memory exploration with AI context.
          </p>
        </div>

        <Stepper
          {...args}
          steps={memoryBrowserSteps}
          currentStep={currentStep}
          onStepChange={(index) => setCurrentStep(index)}
          onComplete={() => alert('Memory Browser tour completed!')}
        >
          <div className="bg-white border border-secondary-200 rounded-lg p-6">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-secondary-900 mb-2">
                  {memoryBrowserSteps[currentStep]?.title}
                </h3>
                <p className="text-secondary-600 mb-3">
                  {memoryBrowserSteps[currentStep]?.description}
                </p>
                {memoryBrowserSteps[currentStep]?.metadata?.aiContext && (
                  <div className="bg-primary-50 border border-primary-200 rounded-md p-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                      <span className="text-sm font-medium text-primary-700">AI Context</span>
                    </div>
                    <p className="text-sm text-primary-600 mt-1">
                      {memoryBrowserSteps[currentStep]?.metadata?.aiContext}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Stepper>
      </div>
    );
  },
  args: {
    variant: 'timeline',
    size: 'md',
    showProgress: true,
    allowSkip: false,
  },
};

// Different sizes
export const SmallSize: Story = {
  args: {
    steps: sampleSteps.slice(0, 3),
    currentStep: 1,
    variant: 'timeline',
    size: 'sm',
    showProgress: true,
  },
};

export const LargeSize: Story = {
  args: {
    steps: sampleSteps,
    currentStep: 2,
    variant: 'horizontal',
    size: 'lg',
    showProgress: true,
  },
};

// Completed state
export const Completed: Story = {
  args: {
    steps: sampleSteps,
    currentStep: 3,
    variant: 'timeline',
    size: 'md',
    state: 'completed',
    showProgress: true,
  },
};

// With skip functionality
export const AllowSkipping: Story = {
  args: {
    steps: sampleSteps,
    currentStep: 0,
    variant: 'timeline',
    size: 'md',
    showProgress: true,
    allowSkip: true,
  },
};

// Accessibility demonstration
export const AccessibilityDemo: Story = {
  render: (args) => (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-success-50 border border-success-200 rounded-lg p-4">
        <h3 className="text-success-800 font-medium mb-2">♿ Accessibility Features</h3>
        <ul className="text-success-700 text-sm space-y-1">
          <li>• Full keyboard navigation (Tab, Enter, Space)</li>
          <li>• Screen reader support with ARIA labels</li>
          <li>• Focus management and visual indicators</li>
          <li>• Progress announcements for assistive technology</li>
          <li>• High contrast colors meeting WCAG AA standards</li>
        </ul>
      </div>

      <Stepper
        {...args}
        steps={sampleSteps}
        currentStep={1}
      />

      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <p className="text-primary-700 text-sm">
          <strong>Try it:</strong> Use Tab to navigate, Enter/Space to activate steps,
          and arrow keys for step navigation. Screen readers will announce progress
          and step information.
        </p>
      </div>
    </div>
  ),
  args: {
    variant: 'timeline',
    size: 'md',
    showProgress: true,
    allowSkip: false,
  },
};

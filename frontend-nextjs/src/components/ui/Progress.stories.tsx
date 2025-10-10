import type { Meta, StoryObj } from '@storybook/react';
import { Progress } from './progress';
import { useState, useEffect } from 'react';

const meta = {
  title: 'UI/Progress',
  component: Progress,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
      description: 'Current progress value',
    },
    max: {
      control: { type: 'number' },
      description: 'Maximum value',
    },
  },
} satisfies Meta<typeof Progress>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic progress bars
export const Empty: Story = {
  args: {
    value: 0,
  },
  render: (args) => (
    <div className="w-[300px]">
      <Progress {...args} />
    </div>
  ),
};

export const Quarter: Story = {
  args: {
    value: 25,
  },
  render: (args) => (
    <div className="w-[300px]">
      <Progress {...args} />
    </div>
  ),
};

export const Half: Story = {
  args: {
    value: 50,
  },
  render: (args) => (
    <div className="w-[300px]">
      <Progress {...args} />
    </div>
  ),
};

export const ThreeQuarters: Story = {
  args: {
    value: 75,
  },
  render: (args) => (
    <div className="w-[300px]">
      <Progress {...args} />
    </div>
  ),
};

export const Complete: Story = {
  args: {
    value: 100,
  },
  render: (args) => (
    <div className="w-[300px]">
      <Progress {...args} />
    </div>
  ),
};

// With labels
export const WithLabel: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <div className="flex justify-between text-sm text-secondary-700">
        <span>Uploading...</span>
        <span>65%</span>
      </div>
      <Progress value={65} />
    </div>
  ),
};

// Multiple progress bars
export const Multiple: Story = {
  render: () => (
    <div className="w-[400px] space-y-4">
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Profile Completion</span>
          <span className="text-secondary-600">80%</span>
        </div>
        <Progress value={80} />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Skills Assessment</span>
          <span className="text-secondary-600">45%</span>
        </div>
        <Progress value={45} />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Portfolio Items</span>
          <span className="text-secondary-600">100%</span>
        </div>
        <Progress value={100} />
      </div>
    </div>
  ),
};

// Animated progress
export const Animated: Story = {
  render: () => {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) return 0;
          return prev + 1;
        });
      }, 50);

      return () => clearInterval(interval);
    }, []);

    return (
      <div className="w-[300px] space-y-2">
        <div className="flex justify-between text-sm text-secondary-700">
          <span>Loading...</span>
          <span>{progress}%</span>
        </div>
        <Progress value={progress} />
      </div>
    );
  },
};

// Different sizes
export const Sizes: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div className="space-y-2">
        <span className="text-xs text-secondary-600">Thin</span>
        <Progress value={60} className="h-1" />
      </div>
      <div className="space-y-2">
        <span className="text-xs text-secondary-600">Default</span>
        <Progress value={60} />
      </div>
      <div className="space-y-2">
        <span className="text-xs text-secondary-600">Thick</span>
        <Progress value={60} className="h-4" />
      </div>
    </div>
  ),
};

// Custom colors
export const CustomColors: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div className="space-y-2">
        <span className="text-xs text-secondary-600">Success</span>
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary-200">
          <div
            className="h-full bg-success-600 transition-all duration-300"
            style={{ width: '70%' }}
          />
        </div>
      </div>
      <div className="space-y-2">
        <span className="text-xs text-secondary-600">Warning</span>
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary-200">
          <div
            className="h-full bg-warning-600 transition-all duration-300"
            style={{ width: '50%' }}
          />
        </div>
      </div>
      <div className="space-y-2">
        <span className="text-xs text-secondary-600">Error</span>
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary-200">
          <div
            className="h-full bg-error-600 transition-all duration-300"
            style={{ width: '30%' }}
          />
        </div>
      </div>
    </div>
  ),
};

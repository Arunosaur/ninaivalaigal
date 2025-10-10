import type { Meta, StoryObj } from '@storybook/react';
import { Callout, type AIContext } from './Callout';
import { Button } from '../ui/Button';

const meta = {
  title: 'Narrative/Callout',
  component: Callout,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['tooltip', 'annotation', 'warning', 'error', 'success', 'ai'],
      description: 'Visual style variant',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg', 'xl'],
      description: 'Size of callout',
    },
    position: {
      control: 'select',
      options: ['top', 'bottom', 'left', 'right', 'top-left', 'top-right', 'bottom-left', 'bottom-right'],
      description: 'Position of callout',
    },
  },
} satisfies Meta<typeof Callout>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic tooltip
export const Tooltip: Story = {
  args: {
    content: 'This is a helpful tooltip',
    variant: 'tooltip',
    isVisible: true,
  },
  render: (args) => (
    <div className="p-20">
      <Callout {...args}>
        <Button>Hover for tooltip</Button>
      </Callout>
    </div>
  ),
};

// Annotation variant
export const Annotation: Story = {
  args: {
    title: 'Important Note',
    content: 'This section contains critical information that requires your attention.',
    variant: 'annotation',
    isVisible: true,
  },
  render: (args) => (
    <div className="p-20">
      <Callout {...args}>
        <span className="text-sm text-secondary-700">Annotated text</span>
      </Callout>
    </div>
  ),
};

// Warning variant
export const Warning: Story = {
  args: {
    content: 'Warning: This action may have unintended consequences.',
    variant: 'warning',
    isVisible: true,
  },
  render: (args) => (
    <div className="p-20">
      <Callout {...args}>
        <Button variant="outline">Action with warning</Button>
      </Callout>
    </div>
  ),
};

// Error variant
export const Error: Story = {
  args: {
    content: 'Error: This field is required and cannot be empty.',
    variant: 'error',
    isVisible: true,
  },
  render: (args) => (
    <div className="p-20">
      <Callout {...args}>
        <input
          type="text"
          className="px-3 py-2 border border-error-300 rounded-md"
          placeholder="Required field"
        />
      </Callout>
    </div>
  ),
};

// Success variant
export const Success: Story = {
  args: {
    content: 'Successfully saved your changes!',
    variant: 'success',
    isVisible: true,
  },
  render: (args) => (
    <div className="p-20">
      <Callout {...args}>
        <Button variant="secondary">Saved item</Button>
      </Callout>
    </div>
  ),
};

// AI-powered callout
export const AICallout: Story = {
  args: {
    title: 'AI Insight',
    content: 'This memory relates to your project planning from last week. Consider linking it to your current sprint goals.',
    variant: 'ai',
    isVisible: true,
    aiContext: {
      confidence: 0.85,
      source: 'SPEC-040 Feedback Loop',
      relatedMemories: ['mem_123', 'mem_456'],
      tags: ['planning', 'sprint', 'goals'],
      reasoning: 'Semantic similarity detected based on content analysis',
    } as AIContext,
  },
  render: (args) => (
    <div className="p-20">
      <Callout {...args}>
        <div className="p-3 border border-primary-200 rounded-md bg-white">
          <p className="text-sm">Memory about sprint planning...</p>
        </div>
      </Callout>
    </div>
  ),
};

// Different positions
export const AllPositions: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-16 p-20">
      {/* Top positions */}
      <Callout content="Top Left" position="top-left" isVisible>
        <Button size="sm">TL</Button>
      </Callout>
      <Callout content="Top" position="top" isVisible>
        <Button size="sm">T</Button>
      </Callout>
      <Callout content="Top Right" position="top-right" isVisible>
        <Button size="sm">TR</Button>
      </Callout>

      {/* Middle positions */}
      <Callout content="Left" position="left" isVisible>
        <Button size="sm">L</Button>
      </Callout>
      <div className="flex items-center justify-center">
        <span className="text-sm text-secondary-600">Center</span>
      </div>
      <Callout content="Right" position="right" isVisible>
        <Button size="sm">R</Button>
      </Callout>

      {/* Bottom positions */}
      <Callout content="Bottom Left" position="bottom-left" isVisible>
        <Button size="sm">BL</Button>
      </Callout>
      <Callout content="Bottom" position="bottom" isVisible>
        <Button size="sm">B</Button>
      </Callout>
      <Callout content="Bottom Right" position="bottom-right" isVisible>
        <Button size="sm">BR</Button>
      </Callout>
    </div>
  ),
  parameters: {
    layout: 'fullscreen',
  },
};

// Different sizes
export const AllSizes: Story = {
  render: () => (
    <div className="flex flex-col gap-16 p-20">
      <Callout
        content="Small size callout with minimal content"
        size="sm"
        isVisible
      >
        <Button size="sm">Small</Button>
      </Callout>
      <Callout
        content="Medium size callout with a bit more content to display"
        size="md"
        isVisible
      >
        <Button>Medium</Button>
      </Callout>
      <Callout
        content="Large size callout with even more content and additional details that need to be shown to the user"
        size="lg"
        isVisible
      >
        <Button size="lg">Large</Button>
      </Callout>
      <Callout
        content="Extra large callout with extensive content, multiple paragraphs, and comprehensive information that requires significant space to display properly to the user."
        size="xl"
        isVisible
      >
        <Button size="lg">Extra Large</Button>
      </Callout>
    </div>
  ),
  parameters: {
    layout: 'padded',
  },
};

// AI Context with different confidence levels
export const AIConfidenceLevels: Story = {
  render: () => (
    <div className="flex flex-col gap-8 p-20">
      <Callout
        title="High Confidence"
        content="Strong match found based on semantic analysis"
        variant="ai"
        isVisible
        aiContext={{
          confidence: 0.92,
          source: 'Memory Graph Analysis',
          relatedMemories: ['mem_789'],
        } as AIContext}
      >
        <div className="p-3 border rounded-md">High confidence match</div>
      </Callout>

      <Callout
        title="Medium Confidence"
        content="Possible connection detected, requires verification"
        variant="ai"
        isVisible
        aiContext={{
          confidence: 0.65,
          source: 'Content Similarity',
          relatedMemories: ['mem_456'],
        } as AIContext}
      >
        <div className="p-3 border rounded-md">Medium confidence match</div>
      </Callout>

      <Callout
        title="Low Confidence"
        content="Weak correlation found, may not be relevant"
        variant="ai"
        isVisible
        aiContext={{
          confidence: 0.35,
          source: 'Keyword Match',
          relatedMemories: ['mem_123'],
        } as AIContext}
      >
        <div className="p-3 border rounded-md">Low confidence match</div>
      </Callout>
    </div>
  ),
};

// Interactive callout
export const Interactive: Story = {
  render: () => (
    <div className="p-20">
      <Callout
        title="Memory Suggestion"
        content="Would you like to link this to your project timeline?"
        variant="ai"
        interactive
        isVisible
        onInteraction={(action) => alert(`Action: ${action}`)}
      >
        <div className="p-4 border border-primary-200 rounded-md bg-white">
          <p className="text-sm">Interactive memory card</p>
        </div>
      </Callout>
    </div>
  ),
};

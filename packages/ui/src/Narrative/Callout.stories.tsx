// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { Callout, useCallouts } from './Callout';
import type { AIContext } from './Callout';

const meta = {
  title: 'Narrative/Callout',
  component: Callout,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Callout component provides AI-powered annotations and contextual information
for narrative walkthroughs. It supports multiple variants, confidence indicators,
and interactive feedback collection.

## Features
- **Multiple Variants**: Tooltip, annotation, warning, error, success, and AI modes
- **AI Integration**: Confidence indicators and contextual insights from SPEC-040
- **Interactive Feedback**: User feedback collection for AI improvement
- **Positioning**: Flexible positioning with automatic arrow placement
- **Auto-hide**: Configurable auto-hide timers
- **Accessibility**: Full ARIA support and keyboard navigation
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['tooltip', 'annotation', 'warning', 'error', 'success', 'ai'],
      description: 'Callout visual variant',
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg', 'xl'],
      description: 'Callout size',
    },
    position: {
      control: { type: 'select' },
      options: ['top', 'bottom', 'left', 'right', 'top-left', 'top-right', 'bottom-left', 'bottom-right'],
      description: 'Arrow and positioning',
    },
    showArrow: {
      control: 'boolean',
      description: 'Show positioning arrow',
    },
    interactive: {
      control: 'boolean',
      description: 'Enable interactive feedback buttons',
    },
    autoHide: {
      control: 'number',
      description: 'Auto-hide delay in milliseconds (0 = no auto-hide)',
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Callout>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample AI context data
const sampleAIContext: AIContext = {
  confidence: 0.85,
  source: 'SPEC-040 Feedback Loop',
  relatedMemories: ['mem_123', 'mem_456', 'mem_789'],
  tags: ['planning', 'architecture', 'performance'],
  timestamp: new Date(),
  reasoning: 'High relevance based on recent activity patterns and semantic similarity'
};

// Basic callout variants
export const Tooltip: Story = {
  render: (args) => (
    <div className="p-8 flex justify-center">
      <Callout
        {...args}
        content="This is a helpful tooltip that provides additional context."
      >
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Hover for Tooltip
        </button>
      </Callout>
    </div>
  ),
  args: {
    variant: 'tooltip',
    size: 'md',
    position: 'top',
    showArrow: true,
    isVisible: true,
  },
};

export const AIAnnotation: Story = {
  render: (args) => (
    <div className="p-8 space-y-6">
      <div className="bg-gray-100 p-4 rounded-lg">
        <h3 className="font-semibold text-gray-900 mb-2">Memory Content</h3>
        <p className="text-gray-700">
          "Discussed the database architecture and identified key optimization opportunities
          for the upcoming Q4 release. Focus on indexing strategies and query performance."
        </p>
      </div>

      <Callout
        {...args}
        title="AI Insight"
        content="This memory relates to your recent database performance work and connects to 3 other architecture discussions from this week."
        aiContext={sampleAIContext}
        interactive={true}
        onInteraction={(action) => console.log('User interaction:', action)}
      />
    </div>
  ),
  args: {
    variant: 'ai',
    size: 'lg',
    position: 'bottom',
    showArrow: true,
    isVisible: true,
  },
};

export const WarningCallout: Story = {
  render: (args) => (
    <div className="p-8">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
        <p className="text-yellow-800">This action will affect multiple memories.</p>
      </div>

      <Callout
        {...args}
        content="This action cannot be undone and will permanently modify your memory collection."
        position="top"
      />
    </div>
  ),
  args: {
    variant: 'warning',
    size: 'md',
    showArrow: true,
    isVisible: true,
  },
};

// Interactive AI callout demo
export const InteractiveAIDemo: Story = {
  render: (args) => {
    const [feedback, setFeedback] = useState<string | null>(null);
    const [calloutVisible, setCalloutVisible] = useState(true);

    const handleInteraction = (action: string) => {
      setFeedback(`You clicked: ${action}`);
      if (action === 'helpful' || action === 'not-helpful') {
        setTimeout(() => setCalloutVisible(false), 1500);
      }
    };

    return (
      <div className="p-8 space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Memory: Project Architecture Review</h3>
          <p className="text-blue-800">
            "Reviewed the microservices architecture and identified opportunities for
            improved service communication and data consistency patterns."
          </p>
        </div>

        {calloutVisible && (
          <Callout
            {...args}
            title="🤖 AI Analysis"
            content="This memory is highly relevant to your current architecture work. It connects to your recent discussions about service mesh implementation and database optimization strategies."
            aiContext={{
              ...sampleAIContext,
              confidence: 0.92,
              relatedMemories: ['architecture-patterns', 'service-mesh-eval', 'db-optimization'],
            }}
            interactive={true}
            onInteraction={handleInteraction}
            onClose={() => setCalloutVisible(false)}
          />
        )}

        {feedback && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <p className="text-green-800 text-sm">✅ {feedback}</p>
          </div>
        )}

        {!calloutVisible && (
          <button
            onClick={() => {
              setCalloutVisible(true);
              setFeedback(null);
            }}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Show AI Callout Again
          </button>
        )}
      </div>
    );
  },
  args: {
    variant: 'ai',
    size: 'xl',
    position: 'bottom',
    showArrow: true,
    isVisible: true,
  },
};

// Multiple callouts management demo
export const MultipleCalloutsDemo: Story = {
  render: (args) => {
    const { callouts, showCallout, hideCallout, hideAllCallouts } = useCallouts();

    const memories = [
      {
        id: 'mem1',
        title: 'API Design Review',
        content: 'Reviewed REST API endpoints and GraphQL schema design.',
        aiContext: { ...sampleAIContext, confidence: 0.88 }
      },
      {
        id: 'mem2',
        title: 'Performance Testing',
        content: 'Conducted load testing and identified bottlenecks.',
        aiContext: { ...sampleAIContext, confidence: 0.94 }
      },
      {
        id: 'mem3',
        title: 'Security Audit',
        content: 'Performed security review and updated authentication.',
        aiContext: { ...sampleAIContext, confidence: 0.76 }
      }
    ];

    return (
      <div className="p-8 space-y-6">
        <div className="flex space-x-2 mb-6">
          <button
            onClick={() => memories.forEach((mem, i) =>
              showCallout(mem.id, {
                content: `AI insight for: ${mem.content}`,
                variant: 'ai',
                aiContext: mem.aiContext,
                interactive: true,
                onInteraction: (action) => console.log(`${mem.id}: ${action}`),
                onClose: () => hideCallout(mem.id),
                autoHide: 5000,
              })
            )}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Show All AI Callouts
          </button>

          <button
            onClick={hideAllCallouts}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Hide All Callouts
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {memories.map((memory) => (
            <div key={memory.id} className="bg-white border rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-2">{memory.title}</h3>
              <p className="text-gray-600 text-sm mb-3">{memory.content}</p>
              <button
                onClick={() => showCallout(memory.id, {
                  content: `This memory shows ${Math.round(memory.aiContext.confidence * 100)}% relevance to your current work context.`,
                  variant: 'ai',
                  aiContext: memory.aiContext,
                  interactive: true,
                  onInteraction: (action) => console.log(`${memory.id}: ${action}`),
                  onClose: () => hideCallout(memory.id),
                })}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Show AI Context
              </button>
            </div>
          ))}
        </div>

        {/* Render active callouts */}
        <div className="fixed inset-0 pointer-events-none z-50">
          {callouts.map((callout, index) => (
            <div
              key={callout.id}
              className="absolute pointer-events-auto"
              style={{
                top: `${100 + index * 120}px`,
                right: '20px',
              }}
            >
              <Callout
                {...callout.props}
                isVisible={true}
              />
            </div>
          ))}
        </div>
      </div>
    );
  },
  args: {
    variant: 'ai',
    size: 'md',
    interactive: true,
  },
};

// Confidence levels demo
export const ConfidenceLevelsDemo: Story = {
  render: (args) => {
    const confidenceLevels = [
      { level: 0.95, label: 'Very High', color: 'green' },
      { level: 0.82, label: 'High', color: 'green' },
      { level: 0.68, label: 'Medium', color: 'yellow' },
      { level: 0.45, label: 'Low', color: 'red' },
    ];

    return (
      <div className="p-8 space-y-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          AI Confidence Indicators
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {confidenceLevels.map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-700">
                  Sample memory content for confidence level demonstration...
                </p>
              </div>

              <Callout
                variant="ai"
                size="md"
                position="bottom"
                showArrow={true}
                isVisible={true}
                title={`${item.label} Confidence`}
                content={`AI analysis with ${Math.round(item.level * 100)}% confidence. This represents ${item.label.toLowerCase()} certainty in the contextual relevance.`}
                aiContext={{
                  ...sampleAIContext,
                  confidence: item.level,
                }}
                interactive={true}
                onInteraction={(action) => console.log(`${item.label} confidence: ${action}`)}
              />
            </div>
          ))}
        </div>
      </div>
    );
  },
  args: {
    variant: 'ai',
    interactive: true,
  },
};

// Auto-hide demonstration
export const AutoHideDemo: Story = {
  render: (args) => {
    const [visible, setVisible] = useState(false);
    const [countdown, setCountdown] = useState(0);

    const showAutoHideCallout = (duration: number) => {
      setVisible(true);
      setCountdown(duration / 1000);

      const interval = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(interval);
            setVisible(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    };

    return (
      <div className="p-8 space-y-6">
        <div className="flex space-x-4">
          <button
            onClick={() => showAutoHideCallout(3000)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            3 Second Auto-hide
          </button>

          <button
            onClick={() => showAutoHideCallout(5000)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            5 Second Auto-hide
          </button>

          <button
            onClick={() => showAutoHideCallout(10000)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            10 Second Auto-hide
          </button>
        </div>

        <div className="bg-gray-100 p-4 rounded-lg">
          <p className="text-gray-700">
            Click one of the buttons above to see auto-hide callouts in action.
            The callout will automatically disappear after the specified duration.
          </p>
        </div>

        {visible && (
          <Callout
            {...args}
            isVisible={visible}
            title="Auto-hide Demo"
            content={`This callout will disappear in ${countdown} seconds...`}
            onClose={() => setVisible(false)}
            autoHide={0} // Handled manually for demo
          />
        )}
      </div>
    );
  },
  args: {
    variant: 'annotation',
    size: 'md',
    position: 'top',
    showArrow: true,
  },
};

// Accessibility demonstration
export const AccessibilityDemo: Story = {
  render: (args) => (
    <div className="p-8 space-y-6">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h3 className="text-green-800 font-medium mb-2">♿ Accessibility Features</h3>
        <ul className="text-green-700 text-sm space-y-1">
          <li>• ARIA live regions for dynamic content</li>
          <li>• Keyboard navigation support</li>
          <li>• High contrast color indicators</li>
          <li>• Screen reader friendly content structure</li>
          <li>• Focus management for interactive elements</li>
        </ul>
      </div>

      <div className="space-y-4">
        <Callout
          variant="ai"
          size="lg"
          position="bottom"
          showArrow={true}
          isVisible={true}
          title="Accessible AI Callout"
          content="This callout demonstrates full accessibility compliance with ARIA labels, keyboard navigation, and screen reader support."
          aiContext={sampleAIContext}
          interactive={true}
          onInteraction={(action) => console.log('Accessible interaction:', action)}
        />

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-700 text-sm">
            <strong>Try this:</strong> Use Tab to navigate through interactive elements,
            Enter to activate buttons, and screen readers will announce all content
            including confidence levels and AI context.
          </p>
        </div>
      </div>
    </div>
  ),
  args: {
    variant: 'ai',
    size: 'lg',
    interactive: true,
  },
};

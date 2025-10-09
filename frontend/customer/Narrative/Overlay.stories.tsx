import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { Overlay, GuidedStep } from './Overlay';

const meta = {
  title: 'Narrative/Overlay',
  component: Overlay,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
The Overlay component provides modal, spotlight, and guided overlay modes for
narrative walkthroughs. It's designed for SPEC-076 Visual Narrative Layer to
create immersive storytelling experiences.

## Features
- **Multiple Variants**: Modal, spotlight, guided, and fullscreen modes
- **Focus Management**: Automatic focus trapping and restoration
- **Accessibility**: Full ARIA support and keyboard navigation
- **Spotlight Effects**: SVG-based spotlight highlighting with custom shapes
- **Animation Support**: Fade, slide, and zoom animations
- **Escape Handling**: Configurable escape key and backdrop click behavior
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['modal', 'spotlight', 'guided', 'fullscreen'],
      description: 'Overlay display variant',
    },
    animation: {
      control: { type: 'select' },
      options: ['fade', 'slide', 'zoom', 'none'],
      description: 'Entry animation type',
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg', 'full'],
      description: 'Content container size',
    },
    position: {
      control: { type: 'select' },
      options: ['center', 'top', 'bottom', 'top-left', 'top-right', 'bottom-left', 'bottom-right'],
      description: 'Content positioning',
    },
    closeOnBackdrop: {
      control: 'boolean',
      description: 'Close overlay when clicking backdrop',
    },
    closeOnEscape: {
      control: 'boolean',
      description: 'Close overlay when pressing escape',
    },
    showCloseButton: {
      control: 'boolean',
      description: 'Show close button in header',
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Overlay>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic overlay variants
export const Modal: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <button
          onClick={() => setIsOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Open Modal Overlay
        </button>

        <Overlay
          {...args}
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Modal Overlay"
        >
          <div className="space-y-4">
            <p className="text-gray-600">
              This is a modal overlay that blocks interaction with the background content.
              Perfect for important announcements or confirmations.
            </p>
            <div className="flex space-x-2">
              <button className="px-3 py-1 bg-green-600 text-white rounded text-sm">
                Confirm
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="px-3 py-1 bg-gray-600 text-white rounded text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </Overlay>
      </div>
    );
  },
  args: {
    variant: 'modal',
    animation: 'fade',
    size: 'md',
    position: 'center',
    closeOnBackdrop: true,
    closeOnEscape: true,
    showCloseButton: true,
  },
};

export const Spotlight: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8 space-y-4">
        <div className="bg-blue-100 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-900">Important Feature</h3>
          <p className="text-blue-700">This area will be highlighted by the spotlight overlay.</p>
        </div>

        <button
          onClick={() => setIsOpen(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Show Spotlight
        </button>

        <Overlay
          {...args}
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          spotlight={{
            x: 32,
            y: 32,
            width: 300,
            height: 100,
            borderRadius: 8,
          }}
        >
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">✨ Feature Spotlight</h3>
            <p className="text-gray-600">
              The spotlight effect draws attention to specific UI elements while
              dimming the background. Perfect for guided tours and feature introductions.
            </p>
            <button
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg"
            >
              Got it!
            </button>
          </div>
        </Overlay>
      </div>
    );
  },
  args: {
    variant: 'spotlight',
    animation: 'zoom',
    size: 'md',
    position: 'bottom-right',
    closeOnBackdrop: false,
    closeOnEscape: true,
    showCloseButton: false,
  },
};

export const GuidedTour: Story = {
  render: (args) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isActive, setIsActive] = useState(false);

    const tourSteps = [
      {
        title: 'Welcome to the Tour',
        content: 'This guided tour will show you the key features of our narrative system.',
        position: 'center' as const,
      },
      {
        title: 'Navigation Controls',
        content: 'Use these buttons to navigate through your memories in a guided sequence.',
        position: 'top-right' as const,
        targetSelector: '.navigation-demo',
      },
      {
        title: 'AI Context',
        content: 'Our AI provides contextual insights about each memory and its connections.',
        position: 'bottom-left' as const,
        targetSelector: '.ai-demo',
      },
      {
        title: 'Memory Connections',
        content: 'See how your memories connect to each other through our graph visualization.',
        position: 'top' as const,
        targetSelector: '.graph-demo',
      },
    ];

    const handleNext = () => {
      if (currentStep < tourSteps.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        setIsActive(false);
        setCurrentStep(0);
      }
    };

    const handlePrevious = () => {
      if (currentStep > 0) {
        setCurrentStep(currentStep - 1);
      }
    };

    const startTour = () => {
      setCurrentStep(0);
      setIsActive(true);
    };

    return (
      <div className="p-8 space-y-6">
        <div className="text-center">
          <button
            onClick={startTour}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-lg"
          >
            🎯 Start Guided Tour
          </button>
        </div>

        {/* Demo UI elements */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="navigation-demo bg-green-100 p-4 rounded-lg">
            <h3 className="font-semibold text-green-900">Navigation</h3>
            <p className="text-green-700">Step through memories sequentially</p>
          </div>

          <div className="ai-demo bg-blue-100 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-900">AI Insights</h3>
            <p className="text-blue-700">Contextual explanations and connections</p>
          </div>

          <div className="graph-demo bg-orange-100 p-4 rounded-lg">
            <h3 className="font-semibold text-orange-900">Graph View</h3>
            <p className="text-orange-700">Visual memory relationships</p>
          </div>
        </div>

        <GuidedStep
          isActive={isActive}
          targetSelector={tourSteps[currentStep]?.targetSelector}
          title={tourSteps[currentStep]?.title || ''}
          content={tourSteps[currentStep]?.content || ''}
          position={tourSteps[currentStep]?.position}
          onNext={handleNext}
          onPrevious={currentStep > 0 ? handlePrevious : undefined}
          onSkip={() => {
            setIsActive(false);
            setCurrentStep(0);
          }}
        />
      </div>
    );
  },
  args: {
    variant: 'guided',
    animation: 'slide',
  },
};

// Memory Browser Integration Demo
export const MemoryBrowserIntegration: Story = {
  render: (args) => {
    const [narrativeMode, setNarrativeMode] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);

    const memories = [
      {
        id: '1',
        title: 'Project Planning Session',
        content: 'Discussed the roadmap for Q4 including new feature development and performance improvements.',
        context: 'project-planning',
        tags: ['planning', 'roadmap', 'q4'],
        relevance: 0.95,
      },
      {
        id: '2',
        title: 'Database Architecture Review',
        content: 'Reviewed the current database schema and identified optimization opportunities.',
        context: 'technical-architecture',
        tags: ['database', 'performance', 'optimization'],
        relevance: 0.88,
      },
      {
        id: '3',
        title: 'User Feedback Analysis',
        content: 'Analyzed user feedback from the latest release and prioritized improvement areas.',
        context: 'user-research',
        tags: ['feedback', 'users', 'improvements'],
        relevance: 0.82,
      },
    ];

    const handleToggleNarrative = () => {
      setNarrativeMode(!narrativeMode);
      if (!narrativeMode) {
        setCurrentStep(0);
      }
    };

    const handleNext = () => {
      if (currentStep < memories.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        setNarrativeMode(false);
        setCurrentStep(0);
      }
    };

    const handlePrevious = () => {
      if (currentStep > 0) {
        setCurrentStep(currentStep - 1);
      }
    };

    return (
      <div className="p-8">
        {/* Memory Browser Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Memory Browser</h2>
          <button
            onClick={handleToggleNarrative}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
              narrativeMode
                ? 'bg-purple-800 hover:bg-purple-900 text-white'
                : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}
          >
            <span>📖</span>
            <span>{narrativeMode ? 'Exit Narrative' : 'Narrative Mode'}</span>
          </button>
        </div>

        {/* Memory Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {memories.map((memory, index) => (
            <div
              key={memory.id}
              className={`bg-white rounded-lg shadow-md p-4 transition-all ${
                narrativeMode && index === currentStep
                  ? 'ring-4 ring-purple-500 ring-opacity-75 transform scale-105'
                  : ''
              }`}
            >
              <h3 className="font-semibold text-gray-900 mb-2">{memory.title}</h3>
              <p className="text-gray-600 text-sm mb-3">{memory.content}</p>
              <div className="flex justify-between items-center">
                <div className="flex space-x-1">
                  {memory.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
                <span className="text-xs text-gray-500">
                  {Math.round(memory.relevance * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Narrative Overlay */}
        <Overlay
          isOpen={narrativeMode}
          variant="guided"
          position="center"
          closeOnBackdrop={false}
          closeOnEscape={false}
          showCloseButton={false}
        >
          <div className="space-y-6">
            {/* Progress */}
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Step {currentStep + 1} of {memories.length}</span>
                <span>{Math.round(((currentStep + 1) / memories.length) * 100)}% Complete</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((currentStep + 1) / memories.length) * 100}%` }}
                />
              </div>
            </div>

            {/* Memory Content */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                📖 {memories[currentStep]?.title}
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <p className="text-gray-700">{memories[currentStep]?.content}</p>
              </div>

              {/* AI Context */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span className="text-sm font-medium text-purple-700">AI Context</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-gray-600">92%</span>
                  </div>
                </div>
                <p className="text-sm text-purple-600">
                  This memory shows high relevance to your current project planning context.
                  It connects to 3 other related memories in your knowledge graph.
                </p>
                <div className="text-xs text-gray-500 mt-2">
                  Source: SPEC-040 AI Context
                </div>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className="px-4 py-2 text-sm font-medium rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>

              <div className="flex space-x-2">
                <button
                  onClick={() => setNarrativeMode(false)}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-800"
                >
                  Skip Tour
                </button>

                <button
                  onClick={handleNext}
                  className="px-4 py-2 text-sm font-medium rounded-md bg-purple-600 text-white hover:bg-purple-700"
                >
                  {currentStep === memories.length - 1 ? 'Complete' : 'Next'}
                </button>
              </div>
            </div>
          </div>
        </Overlay>
      </div>
    );
  },
  args: {
    variant: 'guided',
    animation: 'fade',
  },
};

// Accessibility demonstration
export const AccessibilityDemo: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8 space-y-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="text-green-800 font-medium mb-2">♿ Accessibility Features</h3>
          <ul className="text-green-700 text-sm space-y-1">
            <li>• Focus trapping and restoration</li>
            <li>• Full keyboard navigation (Tab, Enter, Escape)</li>
            <li>• Screen reader support with ARIA labels</li>
            <li>• High contrast indicators and colors</li>
            <li>• Configurable close behaviors</li>
          </ul>
        </div>

        <button
          onClick={() => setIsOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Test Accessibility Features
        </button>

        <Overlay
          {...args}
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Accessibility Test"
        >
          <div className="space-y-4">
            <p className="text-gray-600">
              This overlay demonstrates full accessibility compliance:
            </p>
            <ul className="text-sm text-gray-600 space-y-2">
              <li>✓ Focus is trapped within the overlay</li>
              <li>✓ Tab navigation cycles through interactive elements</li>
              <li>✓ Escape key closes the overlay</li>
              <li>✓ Screen readers announce the dialog role</li>
              <li>✓ Focus returns to trigger button on close</li>
            </ul>
            <div className="flex space-x-2">
              <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm">
                First Button
              </button>
              <button className="px-3 py-1 bg-green-600 text-white rounded text-sm">
                Second Button
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="px-3 py-1 bg-gray-600 text-white rounded text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </Overlay>
      </div>
    );
  },
  args: {
    variant: 'modal',
    animation: 'fade',
    size: 'md',
    position: 'center',
    focusTrap: true,
    closeOnBackdrop: true,
    closeOnEscape: true,
    showCloseButton: true,
  },
};

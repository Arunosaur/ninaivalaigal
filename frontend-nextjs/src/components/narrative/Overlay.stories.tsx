import type { Meta, StoryObj } from '@storybook/react';
import { Overlay } from './Overlay';
import { Button } from '../ui/Button';
import { useState } from 'react';

const meta = {
  title: 'Narrative/Overlay',
  component: Overlay,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['modal', 'spotlight', 'guided', 'fullscreen'],
      description: 'Overlay variant',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg', 'full'],
      description: 'Content size',
    },
    animation: {
      control: 'select',
      options: ['fade', 'slide', 'zoom', 'none'],
      description: 'Animation type',
    },
  },
} satisfies Meta<typeof Overlay>;

export default meta;
type Story = StoryObj<typeof meta>;

// Modal variant
export const Modal: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setIsOpen(true)}>Open Modal</Button>
        <Overlay
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          variant="modal"
          title="Modal Title"
        >
          <div className="p-6">
            <h2 className="text-xl font-bold text-secondary-900 mb-4">
              Confirm Action
            </h2>
            <p className="text-secondary-700 mb-6">
              Are you sure you want to proceed with this action? This cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => setIsOpen(false)}>
                Confirm
              </Button>
            </div>
          </div>
        </Overlay>
      </div>
    );
  },
};

// Spotlight variant
export const Spotlight: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setIsOpen(true)}>Show Spotlight</Button>
        <Overlay
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          variant="spotlight"
        >
          <div className="p-8 text-center">
            <h2 className="text-2xl font-bold text-secondary-900 mb-4">
              🎯 Feature Spotlight
            </h2>
            <p className="text-secondary-700 mb-6 max-w-md">
              This highlights an important feature or area of your application.
              The rest of the screen is darkened for focus.
            </p>
            <Button onClick={() => setIsOpen(false)}>
              Got It
            </Button>
          </div>
        </Overlay>
      </div>
    );
  },
};

// Guided tour variant
export const GuidedTour: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    const [step, setStep] = useState(1);

    const tourSteps = [
      {
        title: 'Welcome',
        content: 'Let us show you around the application',
      },
      {
        title: 'Dashboard',
        content: 'Here you can see all your key metrics at a glance',
      },
      {
        title: 'Navigation',
        content: 'Use this sidebar to access different sections',
      },
      {
        title: 'Finish',
        content: 'You are all set! Start exploring on your own.',
      },
    ];

    return (
      <div className="p-8">
        <Button onClick={() => setIsOpen(true)}>Start Guided Tour</Button>
        <Overlay
          isOpen={isOpen}
          onClose={() => {
            setIsOpen(false);
            setStep(1);
          }}
          variant="guided"
        >
          <div className="p-6 max-w-md">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-medium text-secondary-600">
                Step {step} of {tourSteps.length}
              </span>
              <button
                onClick={() => {
                  setIsOpen(false);
                  setStep(1);
                }}
                className="text-secondary-400 hover:text-secondary-600"
              >
                ✕
              </button>
            </div>
            <h2 className="text-xl font-bold text-secondary-900 mb-3">
              {tourSteps[step - 1].title}
            </h2>
            <p className="text-secondary-700 mb-6">
              {tourSteps[step - 1].content}
            </p>
            <div className="flex justify-between">
              {step > 1 ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setStep(step - 1)}
                >
                  Previous
                </Button>
              ) : (
                <div />
              )}
              {step < tourSteps.length ? (
                <Button size="sm" onClick={() => setStep(step + 1)}>
                  Next
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => {
                    setIsOpen(false);
                    setStep(1);
                  }}
                >
                  Finish
                </Button>
              )}
            </div>
          </div>
        </Overlay>
      </div>
    );
  },
};

// Fullscreen variant
export const Fullscreen: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setIsOpen(true)}>Open Fullscreen</Button>
        <Overlay
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          variant="fullscreen"
          size="full"
        >
          <div className="p-12 h-full flex flex-col">
            <div className="flex justify-between items-center mb-8">
              <h1 className="text-3xl font-bold text-secondary-900">
                Fullscreen View
              </h1>
              <button
                onClick={() => setIsOpen(false)}
                className="text-secondary-600 hover:text-secondary-900 text-2xl"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 flex items-center justify-center">
              <div className="max-w-2xl text-center">
                <p className="text-lg text-secondary-700 mb-6">
                  This is a fullscreen overlay that takes up the entire viewport.
                  Perfect for immersive experiences or detailed content.
                </p>
                <Button onClick={() => setIsOpen(false)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </Overlay>
      </div>
    );
  },
};

// Different sizes
export const DifferentSizes: Story = {
  render: () => {
    const [size, setSize] = useState<'sm' | 'md' | 'lg' | null>(null);

    return (
      <div className="p-8 space-x-4">
        <Button onClick={() => setSize('sm')}>Small</Button>
        <Button onClick={() => setSize('md')}>Medium</Button>
        <Button onClick={() => setSize('lg')}>Large</Button>

        <Overlay
          isOpen={size !== null}
          onClose={() => setSize(null)}
          variant="modal"
          size={size || 'md'}
        >
          <div className="p-6">
            <h2 className="text-xl font-bold text-secondary-900 mb-4">
              {size?.toUpperCase()} Size Modal
            </h2>
            <p className="text-secondary-700 mb-6">
              This modal uses the <strong>{size}</strong> size variant.
            </p>
            <Button onClick={() => setSize(null)}>Close</Button>
          </div>
        </Overlay>
      </div>
    );
  },
};

// Different animations
export const DifferentAnimations: Story = {
  render: () => {
    const [animation, setAnimation] = useState<'fade' | 'slide' | 'zoom' | null>(null);

    return (
      <div className="p-8 space-x-4">
        <Button onClick={() => setAnimation('fade')}>Fade</Button>
        <Button onClick={() => setAnimation('slide')}>Slide</Button>
        <Button onClick={() => setAnimation('zoom')}>Zoom</Button>

        <Overlay
          isOpen={animation !== null}
          onClose={() => setAnimation(null)}
          variant="modal"
          animation={animation || 'fade'}
        >
          <div className="p-6">
            <h2 className="text-xl font-bold text-secondary-900 mb-4">
              {animation} Animation
            </h2>
            <p className="text-secondary-700 mb-6">
              This modal uses the <strong>{animation}</strong> animation.
            </p>
            <Button onClick={() => setAnimation(null)}>Close</Button>
          </div>
        </Overlay>
      </div>
    );
  },
};

// Form in modal
export const FormModal: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setIsOpen(true)}>Create Memory</Button>
        <Overlay
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          variant="modal"
        >
          <div className="p-6">
            <h2 className="text-xl font-bold text-secondary-900 mb-6">
              Create New Memory
            </h2>
            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-secondary-900 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-secondary-300 rounded-md"
                  placeholder="Enter memory title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-900 mb-1">
                  Description
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-secondary-300 rounded-md"
                  rows={4}
                  placeholder="Describe your memory..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-900 mb-1">
                  Tags
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-secondary-300 rounded-md"
                  placeholder="Add tags (comma separated)"
                />
              </div>
              <div className="flex gap-3 justify-end pt-4">
                <Button variant="secondary" onClick={() => setIsOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsOpen(false)}>
                  Create Memory
                </Button>
              </div>
            </form>
          </div>
        </Overlay>
      </div>
    );
  },
};

// Confirmation dialog
export const ConfirmationDialog: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <Button variant="destructive" onClick={() => setIsOpen(true)}>
          Delete Account
        </Button>
        <Overlay
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          variant="modal"
          size="sm"
        >
          <div className="p-6">
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-error-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚠️</span>
              </div>
              <h2 className="text-xl font-bold text-secondary-900 mb-2">
                Delete Account?
              </h2>
              <p className="text-secondary-600 text-sm">
                This action cannot be undone. All your data will be permanently deleted.
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="secondary"
                fullWidth
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                fullWidth
                onClick={() => setIsOpen(false)}
              >
                Delete
              </Button>
            </div>
          </div>
        </Overlay>
      </div>
    );
  },
};

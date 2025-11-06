// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import type { Meta, StoryObj } from '@storybook/react';
import { ErrorBoundary, ErrorMessage } from './ErrorBoundary';
import { Button } from './Button';

// Component that throws error for demonstration
function ErrorThrower(): JSX.Element {
  throw new Error('This is a simulated error for demonstration');
  return <div>This should never render</div>;
}

const errorBoundaryMeta: Meta<typeof ErrorBoundary> = {
  title: 'UI/ErrorBoundary',
  component: ErrorBoundary,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default errorBoundaryMeta;

export const WithError: StoryObj<typeof ErrorBoundary> = {
  render: () => (
    <ErrorBoundary>
      <ErrorThrower />
    </ErrorBoundary>
  ),
};

export const WithCustomFallback: StoryObj<typeof ErrorBoundary> = {
  render: () => (
    <ErrorBoundary
      fallback={
        <div className="p-6 bg-red-100 rounded-lg">
          <h3 className="text-red-800 font-bold">Custom Error UI</h3>
          <p className="text-red-700">This is a custom error fallback</p>
        </div>
      }
    >
      <ErrorThrower />
    </ErrorBoundary>
  ),
};

export const NoError: StoryObj<typeof ErrorBoundary> = {
  render: () => (
    <ErrorBoundary>
      <div className="p-6 bg-green-100 rounded-lg">
        <h3 className="text-green-800 font-bold">✓ Everything works!</h3>
        <p className="text-green-700">No errors here</p>
      </div>
    </ErrorBoundary>
  ),
};

// ErrorMessage stories
const errorMessageMeta: Meta<typeof ErrorMessage> = {
  title: 'UI/ErrorBoundary/ErrorMessage',
  component: ErrorMessage,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export const BasicErrorMessage: StoryObj<typeof ErrorMessage> = {
  args: {
    message: 'Something went wrong. Please try again.',
  },
};

export const WithCustomTitle: StoryObj<typeof ErrorMessage> = {
  args: {
    title: 'Load Failed',
    message: 'Unable to fetch your data from the server.',
  },
};

export const WithRetry: StoryObj<typeof ErrorMessage> = {
  args: {
    title: 'Connection Error',
    message: 'Lost connection to the server. Please check your internet.',
    onRetry: () => alert('Retrying...'),
  },
};

export const LongMessage: StoryObj<typeof ErrorMessage> = {
  args: {
    title: 'Validation Error',
    message: 'The form submission failed because several fields are invalid. Please check your email address format, ensure your password is at least 8 characters long, and verify that all required fields are filled in.',
  },
};

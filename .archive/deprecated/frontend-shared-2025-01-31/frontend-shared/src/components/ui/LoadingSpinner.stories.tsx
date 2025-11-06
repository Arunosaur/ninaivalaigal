// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import type { Meta, StoryObj } from '@storybook/react';
import { LoadingSpinner, FullPageLoadingSpinner } from './LoadingSpinner';

const meta: Meta<typeof LoadingSpinner> = {
  title: 'UI/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size of the spinner',
    },
    message: {
      control: 'text',
      description: 'Loading message to display',
    },
  },
};

export default meta;
type Story = StoryObj<typeof LoadingSpinner>;

export const Small: Story = {
  args: {
    size: 'sm',
  },
};

export const Medium: Story = {
  args: {
    size: 'md',
  },
};

export const Large: Story = {
  args: {
    size: 'lg',
  },
};

export const WithMessage: Story = {
  args: {
    size: 'md',
    message: 'Loading your data...',
  },
};

export const LongMessage: Story = {
  args: {
    size: 'md',
    message: 'Please wait while we fetch your memories and prepare your dashboard...',
  },
};

// Full page spinner stories
const fullPageMeta: Meta<typeof FullPageLoadingSpinner> = {
  title: 'UI/LoadingSpinner/FullPage',
  component: FullPageLoadingSpinner,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export const FullPageDefault: StoryObj<typeof FullPageLoadingSpinner> = {
  render: () => <FullPageLoadingSpinner />,
};

export const FullPageWithMessage: StoryObj<typeof FullPageLoadingSpinner> = {
  render: () => <FullPageLoadingSpinner message="Loading application..." />,
};

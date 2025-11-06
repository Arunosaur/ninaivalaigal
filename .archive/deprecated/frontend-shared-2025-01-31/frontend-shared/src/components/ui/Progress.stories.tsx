// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import type { Meta, StoryObj } from '@storybook/react';
import { Progress } from './Progress';

const meta: Meta<typeof Progress> = {
  title: 'UI/Progress',
  component: Progress,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    variant: {
      control: 'select',
      options: ['primary', 'success', 'warning', 'danger'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof Progress>;

export const Default: Story = {
  args: {
    value: 50,
  },
};

export const WithLabel: Story = {
  args: {
    value: 75,
    showLabel: true,
  },
};

export const Small: Story = {
  args: {
    value: 60,
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    value: 60,
    size: 'lg',
  },
};

export const Success: Story = {
  args: {
    value: 100,
    variant: 'success',
    showLabel: true,
  },
};

export const Warning: Story = {
  args: {
    value: 65,
    variant: 'warning',
    showLabel: true,
  },
};

export const Danger: Story = {
  args: {
    value: 25,
    variant: 'danger',
    showLabel: true,
  },
};

export const Empty: Story = {
  args: {
    value: 0,
    showLabel: true,
  },
};

export const Complete: Story = {
  args: {
    value: 100,
    variant: 'success',
    showLabel: true,
  },
};

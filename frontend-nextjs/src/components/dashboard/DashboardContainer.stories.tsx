import type { Meta, StoryObj } from '@storybook/react';
import { DashboardContainer } from './DashboardContainer';

const meta = {
  title: 'Dashboard/DashboardContainer',
  component: DashboardContainer,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Main dashboard container with real-time WebSocket updates. In Storybook, WebSocket connections are mocked.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof DashboardContainer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const UserDashboard: Story = {
  args: {
    userRole: 'user',
    userId: 'user_123',
  },
};

export const TeamAdminDashboard: Story = {
  args: {
    userRole: 'team_admin',
    userId: 'admin_456',
  },
};

export const OrgAdminDashboard: Story = {
  args: {
    userRole: 'org_admin',
    userId: 'org_789',
  },
};

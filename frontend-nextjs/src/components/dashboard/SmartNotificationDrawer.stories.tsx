import type { Meta, StoryObj } from '@storybook/react';
import { SmartNotificationDrawer } from './SmartNotificationDrawer';
import { useState } from 'react';
import { Button } from '../ui/Button';

const meta = {
  title: 'Dashboard/SmartNotificationDrawer',
  component: SmartNotificationDrawer,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Smart notification drawer with priority-based alerts and real-time updates.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof SmartNotificationDrawer>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockNotifications = [
  {
    type: 'alert',
    priority: 'high' as const,
    title: 'New Achievement Unlocked!',
    description: 'You earned the "Memory Master" badge',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    icon: '🏆',
  },
  {
    type: 'mention',
    priority: 'medium' as const,
    title: 'You were mentioned',
    description: 'Sarah mentioned you in "Q4 Planning" discussion',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    icon: '💬',
  },
  {
    type: 'insight',
    priority: 'low' as const,
    title: 'AI Suggestion',
    description: 'Consider linking these related memories together',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    icon: '💡',
  },
];

const mockWidgetAlerts = [
  {
    type: 'trending',
    priority: 'medium' as const,
    title: 'Trending Topic',
    description: 'Project planning discussions are trending this week',
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    widget_id: 'sentiment_trends',
    icon: '📈',
  },
];

export const WithNotifications: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setIsOpen(true)}>
          Open Notifications
          <span className="ml-2 bg-error-600 text-white rounded-full px-2 py-0.5 text-xs">
            3
          </span>
        </Button>
        <SmartNotificationDrawer
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          notifications={mockNotifications}
          widgetAlerts={mockWidgetAlerts}
        />
      </div>
    );
  },
  args: {
    isOpen: false,
    onClose: () => {},
    notifications: mockNotifications,
    widgetAlerts: mockWidgetAlerts,
  },
};

export const Empty: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="p-8">
        <Button onClick={() => setIsOpen(true)}>
          Open Notifications
        </Button>
        <SmartNotificationDrawer
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          notifications={[]}
          widgetAlerts={[]}
        />
      </div>
    );
  },
  args: {
    isOpen: false,
    onClose: () => {},
    notifications: [],
    widgetAlerts: [],
  },
};

export const HighPriorityOnly: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    const highPriorityNotifs = mockNotifications.filter(n => n.priority === 'high');

    return (
      <div className="p-8">
        <Button variant="destructive" onClick={() => setIsOpen(true)}>
          Urgent Notifications
          <span className="ml-2 bg-white text-error-600 rounded-full px-2 py-0.5 text-xs font-bold">
            !
          </span>
        </Button>
        <SmartNotificationDrawer
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          notifications={highPriorityNotifs}
          widgetAlerts={[]}
        />
      </div>
    );
  },
  args: {
    isOpen: false,
    onClose: () => {},
    notifications: mockNotifications.filter(n => n.priority === 'high'),
    widgetAlerts: [],
  },
};

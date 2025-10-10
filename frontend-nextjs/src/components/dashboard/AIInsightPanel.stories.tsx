import type { Meta, StoryObj } from '@storybook/react';
import { AIInsightPanel } from './AIInsightPanel';

const meta = {
  title: 'Dashboard/AIInsightPanel',
  component: AIInsightPanel,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'AI-powered insights panel showing memory analytics and AI performance metrics.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof AIInsightPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    tagSuggestionStats: {
      acceptance_rate: 0.75,
      suggestions_generated: 234,
      avg_response_time: 1.2,
      confidence_score: 0.85,
    },
    pagerankEffectiveness: {
      memories_ranked: 567,
      ranking_accuracy: 0.89,
      user_engagement_lift: 0.34,
    },
    intelligenceTrends: [
      { metric: 'Tag Accuracy', value: 0.85, trend: 'up', unit: '%' },
      { metric: 'Response Time', value: 1.2, trend: 'down', unit: 's' },
      { metric: 'User Satisfaction', value: 0.92, trend: 'up', unit: '%' },
    ],
    alerts: [
      {
        type: 'performance',
        priority: 'medium',
        title: 'AI Performance Improving',
        description: 'Tag suggestion accuracy increased by 12% this week',
        icon: '📈',
      },
    ],
  },
};

export const HighPerformance: Story = {
  args: {
    tagSuggestionStats: {
      acceptance_rate: 0.92,
      suggestions_generated: 456,
      avg_response_time: 0.8,
      confidence_score: 0.94,
    },
    pagerankEffectiveness: {
      memories_ranked: 1234,
      ranking_accuracy: 0.95,
      user_engagement_lift: 0.58,
    },
    intelligenceTrends: [
      { metric: 'Tag Accuracy', value: 0.94, trend: 'up', unit: '%' },
      { metric: 'Response Time', value: 0.8, trend: 'down', unit: 's' },
      { metric: 'User Satisfaction', value: 0.97, trend: 'up', unit: '%' },
    ],
    alerts: [
      {
        type: 'achievement',
        priority: 'high',
        title: 'Outstanding AI Performance!',
        description: 'All AI metrics in top 5% globally',
        icon: '🏆',
      },
    ],
  },
};

export const NeedsImprovement: Story = {
  args: {
    tagSuggestionStats: {
      acceptance_rate: 0.58,
      suggestions_generated: 89,
      avg_response_time: 2.5,
      confidence_score: 0.67,
    },
    pagerankEffectiveness: {
      memories_ranked: 234,
      ranking_accuracy: 0.72,
      user_engagement_lift: 0.15,
    },
    intelligenceTrends: [
      { metric: 'Tag Accuracy', value: 0.67, trend: 'down', unit: '%' },
      { metric: 'Response Time', value: 2.5, trend: 'up', unit: 's' },
      { metric: 'User Satisfaction', value: 0.68, trend: 'stable', unit: '%' },
    ],
    alerts: [
      {
        type: 'warning',
        priority: 'high',
        title: 'AI Performance Declining',
        description: 'Consider reviewing AI model parameters',
        icon: '⚠️',
      },
    ],
  },
};

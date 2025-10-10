import type { Meta, StoryObj } from '@storybook/react';
import { TopMemoryCard } from './TopMemoryCard';

const meta = {
  title: 'Dashboard/TopMemoryCard',
  component: TopMemoryCard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof TopMemoryCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockMemories = [
  {
    id: 'mem_1',
    title: 'Project Planning Session',
    score: 0.92,
    discussion_count: 15,
    sentiment_score: 0.85,
  },
  {
    id: 'mem_2',
    title: 'Team Retrospective Notes',
    score: 0.88,
    discussion_count: 12,
    sentiment_score: 0.78,
  },
  {
    id: 'mem_3',
    title: 'Design System Documentation',
    score: 0.85,
    discussion_count: 8,
    sentiment_score: 0.92,
  },
  {
    id: 'mem_4',
    title: 'Sprint Goals and Objectives',
    score: 0.82,
    discussion_count: 6,
    sentiment_score: 0.75,
  },
];

const mockTrendingTopics = {
  'planning': 12,
  'design': 8,
  'sprint': 7,
  'documentation': 5,
  'architecture': 4,
};

const mockAIInsights = {
  quality_trend: 'Improving',
  engagement_level: 'High',
  knowledge_velocity: 1.8,
};

const mockAlerts = [
  {
    type: 'milestone',
    priority: 'medium',
    title: 'New Milestone Reached',
    description: 'Your team created 50+ quality memories this week!',
    icon: '🎯',
  },
];

export const Default: Story = {
  args: {
    memories: mockMemories,
    totalMemories: 127,
    avgScore: 0.87,
    trendingTopics: mockTrendingTopics,
    aiInsights: mockAIInsights,
    alerts: mockAlerts,
  },
};

export const HighPerformance: Story = {
  args: {
    memories: mockMemories.map(m => ({ ...m, score: m.score + 0.05 })),
    totalMemories: 250,
    avgScore: 0.93,
    trendingTopics: mockTrendingTopics,
    aiInsights: {
      quality_trend: 'Excellent',
      engagement_level: 'Very High',
      knowledge_velocity: 2.5,
    },
    alerts: [
      {
        type: 'achievement',
        priority: 'high',
        title: 'Outstanding Performance!',
        description: 'Team quality score reached 93% - Top 5% globally!',
        icon: '🏆',
      },
    ],
  },
};

export const NeedsAttention: Story = {
  args: {
    memories: mockMemories.map(m => ({ ...m, score: m.score - 0.2 })),
    totalMemories: 45,
    avgScore: 0.65,
    trendingTopics: { 'issues': 5, 'bugs': 3 },
    aiInsights: {
      quality_trend: 'Declining',
      engagement_level: 'Low',
      knowledge_velocity: 0.8,
    },
    alerts: [
      {
        type: 'warning',
        priority: 'high',
        title: 'Quality Score Dropping',
        description: 'Consider reviewing recent memories for improvement opportunities.',
        icon: '⚠️',
      },
    ],
  },
};

export const NoAlerts: Story = {
  args: {
    memories: mockMemories,
    totalMemories: 127,
    avgScore: 0.87,
    trendingTopics: mockTrendingTopics,
    aiInsights: mockAIInsights,
    alerts: [],
  },
};

export const FewMemories: Story = {
  args: {
    memories: mockMemories.slice(0, 2),
    totalMemories: 12,
    avgScore: 0.75,
    trendingTopics: { 'getting-started': 3 },
    aiInsights: {
      quality_trend: 'Growing',
      engagement_level: 'Medium',
      knowledge_velocity: 1.2,
    },
    alerts: [
      {
        type: 'tip',
        priority: 'low',
        title: 'Keep Building!',
        description: 'Create more memories to unlock insights and trends.',
        icon: '💡',
      },
    ],
  },
};

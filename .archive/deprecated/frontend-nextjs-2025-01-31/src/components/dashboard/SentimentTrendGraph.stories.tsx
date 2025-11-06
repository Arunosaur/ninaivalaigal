// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from '@storybook/react';
import { SentimentTrendGraph } from './SentimentTrendGraph';

const meta = {
  title: 'Dashboard/SentimentTrendGraph',
  component: SentimentTrendGraph,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Visualizes sentiment trends over time with interactive graph.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof SentimentTrendGraph>;

export default meta;
type Story = StoryObj<typeof meta>;

export const PositiveTrend: Story = {
  args: {
    currentSentiment: 0.82,
    sentimentHistory: [
      { date: 'Mon', sentiment: 0.68, volume: 15 },
      { date: 'Tue', sentiment: 0.72, volume: 18 },
      { date: 'Wed', sentiment: 0.75, volume: 22 },
      { date: 'Thu', sentiment: 0.78, volume: 20 },
      { date: 'Fri', sentiment: 0.82, volume: 25 },
    ],
    predictedSentiment: 0.85,
    trendDirection: 'up',
    discussionVolume: 100,
    topPositiveTopics: ['planning', 'collaboration', 'innovation'],
    aiInsights: {
      sentiment_stability: 'Improving',
      engagement_quality: 'High',
      team_health_score: 0.88,
    },
    alerts: [],
  },
};

export const NegativeTrend: Story = {
  args: {
    currentSentiment: 0.58,
    sentimentHistory: [
      { date: 'Mon', sentiment: 0.75, volume: 20 },
      { date: 'Tue', sentiment: 0.70, volume: 18 },
      { date: 'Wed', sentiment: 0.65, volume: 15 },
      { date: 'Thu', sentiment: 0.62, volume: 12 },
      { date: 'Fri', sentiment: 0.58, volume: 10 },
    ],
    predictedSentiment: 0.55,
    trendDirection: 'down',
    discussionVolume: 75,
    topPositiveTopics: ['retrospective', 'feedback'],
    aiInsights: {
      sentiment_stability: 'Declining',
      engagement_quality: 'Medium',
      team_health_score: 0.62,
    },
    alerts: [
      {
        type: 'warning',
        priority: 'high',
        title: 'Sentiment Declining',
        description: 'Team sentiment has dropped 20% this week',
        icon: '⚠️',
      },
    ],
  },
};

export const StableTrend: Story = {
  args: {
    currentSentiment: 0.75,
    sentimentHistory: [
      { date: 'Mon', sentiment: 0.74, volume: 18 },
      { date: 'Tue', sentiment: 0.76, volume: 20 },
      { date: 'Wed', sentiment: 0.75, volume: 19 },
      { date: 'Thu', sentiment: 0.74, volume: 21 },
      { date: 'Fri', sentiment: 0.75, volume: 18 },
    ],
    predictedSentiment: 0.75,
    trendDirection: 'stable',
    discussionVolume: 96,
    topPositiveTopics: ['steady-progress', 'consistency'],
    aiInsights: {
      sentiment_stability: 'Stable',
      engagement_quality: 'Good',
      team_health_score: 0.75,
    },
    alerts: [],
  },
};

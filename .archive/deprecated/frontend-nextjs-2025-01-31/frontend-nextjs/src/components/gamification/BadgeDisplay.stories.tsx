// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Meta, StoryObj } from '@storybook/react';
import { BadgeDisplay } from './BadgeDisplay';

const meta = {
  title: 'Gamification/BadgeDisplay',
  component: BadgeDisplay,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof BadgeDisplay>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockEarnedBadges = [
  {
    badge: {
      id: 'badge_1',
      type: 'contribution',
      level: 'gold' as const,
      title: 'Memory Master',
      description: 'Created 100+ quality memories',
      icon: '🏆',
      points: 500,
      rarity: 0.08,
    },
    earned_at: '2025-10-01T10:30:00Z',
    progress: {
      memories_created: { current: 100, required: 100, percentage: 100 },
    },
  },
  {
    badge: {
      id: 'badge_2',
      type: 'engagement',
      level: 'silver' as const,
      title: 'Discussion Leader',
      description: 'Participated in 50 discussions',
      icon: '💬',
      points: 250,
      rarity: 0.15,
    },
    earned_at: '2025-09-28T14:20:00Z',
    progress: {
      discussions: { current: 50, required: 50, percentage: 100 },
    },
  },
  {
    badge: {
      id: 'badge_3',
      type: 'quality',
      level: 'bronze' as const,
      title: 'Quality Contributor',
      description: 'Maintained 80%+ quality score',
      icon: '⭐',
      points: 150,
      rarity: 0.25,
    },
    earned_at: '2025-09-25T09:15:00Z',
    progress: {
      quality_score: { current: 85, required: 80, percentage: 100 },
    },
  },
];

const mockCloseBadges = [
  {
    badge: {
      id: 'badge_4',
      type: 'contribution',
      level: 'platinum' as const,
      title: 'Legend',
      description: 'Create 500 memories',
      icon: '👑',
      points: 1000,
      rarity: 0.02,
    },
    progress: {
      memories_created: { current: 420, required: 500, percentage: 84 },
    },
    overall_progress: 84,
  },
  {
    badge: {
      id: 'badge_5',
      type: 'streak',
      level: 'gold' as const,
      title: 'Consistent Creator',
      description: 'Create memories for 30 consecutive days',
      icon: '🔥',
      points: 400,
      rarity: 0.12,
    },
    progress: {
      streak_days: { current: 24, required: 30, percentage: 80 },
    },
    overall_progress: 80,
  },
];

export const WithBadges: Story = {
  args: {
    earnedBadges: mockEarnedBadges,
    closeBadges: mockCloseBadges,
    totalPoints: 900,
    teamRank: 3,
  },
};

export const NewUser: Story = {
  args: {
    earnedBadges: [],
    closeBadges: [
      {
        badge: {
          id: 'badge_starter',
          type: 'onboarding',
          level: 'bronze' as const,
          title: 'First Steps',
          description: 'Create your first 5 memories',
          icon: '🌱',
          points: 50,
          rarity: 0.95,
        },
        progress: {
          memories_created: { current: 2, required: 5, percentage: 40 },
        },
        overall_progress: 40,
      },
    ],
    totalPoints: 0,
    teamRank: 'Unranked',
  },
};

export const TopPerformer: Story = {
  args: {
    earnedBadges: [
      ...mockEarnedBadges,
      {
        badge: {
          id: 'badge_platinum',
          type: 'achievement',
          level: 'platinum' as const,
          title: 'Elite Contributor',
          description: 'Reached top 1% globally',
          icon: '💎',
          points: 2000,
          rarity: 0.01,
        },
        earned_at: '2025-10-08T16:00:00Z',
        progress: {},
        next_level: {
          id: 'badge_ultimate',
          type: 'achievement',
          level: 'platinum' as const,
          title: 'Ultimate Master',
          description: 'Legendary status',
          icon: '🌟',
          points: 5000,
          rarity: 0.001,
        },
      },
    ],
    closeBadges: [],
    totalPoints: 3850,
    teamRank: 1,
  },
};

export const WithNextLevel: Story = {
  args: {
    earnedBadges: [
      {
        ...mockEarnedBadges[0],
        next_level: {
          id: 'badge_platinum_memory',
          type: 'contribution',
          level: 'platinum' as const,
          title: 'Memory Legend',
          description: 'Created 500+ quality memories',
          icon: '🏆',
          points: 1000,
          rarity: 0.03,
        },
      },
    ],
    closeBadges: mockCloseBadges,
    totalPoints: 500,
    teamRank: 5,
  },
};

export const HighRarity: Story = {
  args: {
    earnedBadges: [
      {
        badge: {
          id: 'badge_legendary',
          type: 'special',
          level: 'platinum' as const,
          title: 'Legendary Innovator',
          description: 'Pioneered new memory patterns',
          icon: '🚀',
          points: 3000,
          rarity: 0.001,
        },
        earned_at: '2025-10-09T12:00:00Z',
        progress: {},
      },
      {
        badge: {
          id: 'badge_rare',
          type: 'special',
          level: 'gold' as const,
          title: 'Rare Achiever',
          description: 'Completed rare challenge',
          icon: '💫',
          points: 750,
          rarity: 0.05,
        },
        earned_at: '2025-10-07T18:30:00Z',
        progress: {},
      },
    ],
    closeBadges: [],
    totalPoints: 3750,
    teamRank: 2,
  },
};

export const WithCelebration: Story = {
  args: {
    earnedBadges: mockEarnedBadges,
    closeBadges: mockCloseBadges,
    totalPoints: 900,
    teamRank: 3,
    onCelebrate: (badgeId: string) => alert(`Celebrating badge: ${badgeId}! 🎉`),
  },
};

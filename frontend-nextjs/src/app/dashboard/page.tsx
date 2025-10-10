'use client';

import { useState, useEffect } from 'react';
import { DashboardContainer } from '@/components/dashboard/DashboardContainer';
import { TopMemoryCard } from '@/components/dashboard/TopMemoryCard';
import { AIInsightPanel } from '@/components/dashboard/AIInsightPanel';
import { SentimentTrendGraph } from '@/components/dashboard/SentimentTrendGraph';
import { BadgeDisplay } from '@/components/gamification/BadgeDisplay';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';

// Mock data for dashboard (will be replaced with API calls)
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
];

const mockTrendingTopics = {
  'planning': 12,
  'design': 8,
  'sprint': 7,
  'documentation': 5,
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

const mockTagSuggestionStats = {
  acceptance_rate: 0.75,
  suggestions_generated: 234,
  avg_response_time: 1.2,
  confidence_score: 0.85,
};

const mockPagerankEffectiveness = {
  memories_ranked: 567,
  ranking_accuracy: 0.89,
  user_engagement_lift: 0.34,
};

const mockIntelligenceTrends = [
  { metric: 'Tag Accuracy', value: 0.85, trend: 'up' as const, unit: '%' },
  { metric: 'Response Time', value: 1.2, trend: 'down' as const, unit: 's' },
  { metric: 'User Satisfaction', value: 0.92, trend: 'up' as const, unit: '%' },
];

const mockSentimentHistory = [
  { date: 'Mon', sentiment: 0.68, volume: 15 },
  { date: 'Tue', sentiment: 0.72, volume: 18 },
  { date: 'Wed', sentiment: 0.75, volume: 22 },
  { date: 'Thu', sentiment: 0.78, volume: 20 },
  { date: 'Fri', sentiment: 0.82, volume: 25 },
];

const mockSentimentAIInsights = {
  sentiment_stability: 'Improving',
  engagement_quality: 'High',
  team_health_score: 0.88,
};

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
];

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [userRole] = useState<'user' | 'team_admin' | 'org_admin'>('user');

  useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-secondary-700">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-secondary-50">
      {/* Header */}
      <header className="bg-white border-b border-secondary-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-secondary-900">Dashboard</h1>
              <p className="text-sm text-secondary-600">Welcome back! Here's your overview.</p>
            </div>
            <div className="flex gap-3">
              <Button variant="ghost" size="sm">
                Settings
              </Button>
              <Button size="sm">
                New Memory
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Top Memories */}
            <TopMemoryCard
              memories={mockMemories}
              totalMemories={127}
              avgScore={0.87}
              trendingTopics={mockTrendingTopics}
              aiInsights={mockAIInsights}
              alerts={mockAlerts}
            />

            {/* Sentiment Trend */}
            <SentimentTrendGraph
              currentSentiment={0.82}
              sentimentHistory={mockSentimentHistory}
              predictedSentiment={0.85}
              trendDirection="up"
              discussionVolume={100}
              topPositiveTopics={['planning', 'collaboration', 'innovation']}
              aiInsights={mockSentimentAIInsights}
              alerts={[]}
            />

            {/* AI Insights */}
            <AIInsightPanel
              tagSuggestionStats={mockTagSuggestionStats}
              pagerankEffectiveness={mockPagerankEffectiveness}
              intelligenceTrends={mockIntelligenceTrends}
              alerts={mockAlerts}
            />
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-6">
            {/* Gamification */}
            <BadgeDisplay
              earnedBadges={mockEarnedBadges}
              closeBadges={mockCloseBadges}
              totalPoints={900}
              teamRank={3}
            />

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" fullWidth size="sm">
                  📝 Create Memory
                </Button>
                <Button variant="outline" fullWidth size="sm">
                  🔗 Link Memories
                </Button>
                <Button variant="outline" fullWidth size="sm">
                  📊 View Analytics
                </Button>
                <Button variant="outline" fullWidth size="sm">
                  🎯 Set Goals
                </Button>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex gap-2">
                    <span className="text-secondary-600">2m ago</span>
                    <span className="text-secondary-900">Memory created</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-secondary-600">1h ago</span>
                    <span className="text-secondary-900">Badge earned</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-secondary-600">3h ago</span>
                    <span className="text-secondary-900">Comment added</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}

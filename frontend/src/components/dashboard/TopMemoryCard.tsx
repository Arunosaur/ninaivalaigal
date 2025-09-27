import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, MessageCircle, Star, ExternalLink } from 'lucide-react';

interface Memory {
  id: string;
  title: string;
  score: number;
  discussion_count: number;
  sentiment_score: number;
}

interface TopMemoryCardProps {
  memories: Memory[];
  totalMemories: number;
  avgScore: number;
  trendingTopics: Record<string, number>;
  aiInsights: {
    quality_trend: string;
    engagement_level: string;
    knowledge_velocity: number;
  };
  alerts: Array<{
    type: string;
    priority: string;
    title: string;
    description: string;
    icon: string;
  }>;
}

export const TopMemoryCard: React.FC<TopMemoryCardProps> = ({
  memories,
  totalMemories,
  avgScore,
  trendingTopics,
  aiInsights,
  alerts
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getSentimentEmoji = (sentiment: number) => {
    if (sentiment >= 0.7) return '😊';
    if (sentiment >= 0.5) return '😐';
    return '😟';
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-500" />
            Top Memories
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {totalMemories} total
          </Badge>
        </div>

        {/* AI Insights Summary */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <TrendingUp className="h-4 w-4" />
            Quality: {aiInsights.quality_trend}
          </div>
          <div>
            Engagement: {aiInsights.engagement_level}
          </div>
          <div>
            Velocity: {aiInsights.knowledge_velocity.toFixed(1)}x
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Alert Banner */}
        {alerts.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <span className="text-lg">{alerts[0].icon}</span>
              <div className="flex-1">
                <p className="font-medium text-blue-900 text-sm">
                  {alerts[0].title}
                </p>
                <p className="text-blue-700 text-xs mt-1">
                  {alerts[0].description}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Memory List */}
        <div className="space-y-3">
          {memories.slice(0, 4).map((memory, index) => (
            <div
              key={memory.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer group"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-900 truncate">
                    {memory.title}
                  </span>
                  <ExternalLink className="h-3 w-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <MessageCircle className="h-3 w-3" />
                    {memory.discussion_count}
                  </div>
                  <div className="flex items-center gap-1">
                    <span>{getSentimentEmoji(memory.sentiment_score)}</span>
                    {(memory.sentiment_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <Badge
                className={`ml-2 text-xs ${getScoreColor(memory.score)}`}
                variant="secondary"
              >
                {(memory.score * 100).toFixed(0)}
              </Badge>
            </div>
          ))}
        </div>

        {/* Trending Topics */}
        <div className="pt-3 border-t">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Trending Topics</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(trendingTopics).slice(0, 5).map(([topic, count]) => (
              <Badge key={topic} variant="outline" className="text-xs">
                {topic} ({count})
              </Badge>
            ))}
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="pt-3 border-t">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <div className="text-lg font-semibold text-gray-900">
                {(avgScore * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">Avg Quality</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-gray-900">
                {memories.reduce((sum, m) => sum + m.discussion_count, 0)}
              </div>
              <div className="text-xs text-gray-500">Discussions</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

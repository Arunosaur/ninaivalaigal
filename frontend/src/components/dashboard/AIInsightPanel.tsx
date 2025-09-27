import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Bot, Target, Clock, Users, TrendingUp, AlertCircle } from 'lucide-react';

interface AIInsightPanelProps {
  tagSuggestionStats: {
    acceptance_rate: number;
    suggestions_generated: number;
    avg_response_time: number;
    confidence_score: number;
  };
  pagerankEffectiveness: {
    memories_ranked: number;
    ranking_accuracy: number;
    user_engagement_lift: number;
  };
  intelligenceTrends: Array<{
    metric: string;
    value: number;
    trend: 'up' | 'down' | 'stable';
    unit?: string;
  }>;
  alerts: Array<{
    type: string;
    priority: string;
    title: string;
    description: string;
    icon: string;
  }>;
}

export const AIInsightPanel: React.FC<AIInsightPanelProps> = ({
  tagSuggestionStats,
  pagerankEffectiveness,
  intelligenceTrends,
  alerts
}) => {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-3 w-3 text-green-500" />;
      case 'down': return <TrendingUp className="h-3 w-3 text-red-500 rotate-180" />;
      default: return <div className="w-3 h-3 bg-gray-400 rounded-full" />;
    }
  };

  const getPerformanceColor = (value: number, isTime: boolean = false) => {
    if (isTime) {
      // For response time, lower is better
      if (value <= 100) return 'text-green-600';
      if (value <= 200) return 'text-yellow-600';
      return 'text-red-600';
    } else {
      // For rates/scores, higher is better
      if (value >= 0.8) return 'text-green-600';
      if (value >= 0.6) return 'text-yellow-600';
      return 'text-red-600';
    }
  };

  const getProgressColor = (value: number) => {
    if (value >= 80) return 'bg-green-500';
    if (value >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <Bot className="h-5 w-5 text-purple-500" />
          AI Intelligence
        </CardTitle>
        <div className="text-sm text-gray-600">
          Real-time AI performance and insights
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Alert Banner */}
        {alerts.length > 0 && (
          <div className={`border rounded-lg p-3 ${
            alerts[0].type === 'ai_success'
              ? 'bg-green-50 border-green-200'
              : alerts[0].type === 'performance'
              ? 'bg-yellow-50 border-yellow-200'
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-start gap-2">
              <span className="text-lg">{alerts[0].icon}</span>
              <div className="flex-1">
                <p className={`font-medium text-sm ${
                  alerts[0].type === 'ai_success'
                    ? 'text-green-900'
                    : alerts[0].type === 'performance'
                    ? 'text-yellow-900'
                    : 'text-blue-900'
                }`}>
                  {alerts[0].title}
                </p>
                <p className={`text-xs mt-1 ${
                  alerts[0].type === 'ai_success'
                    ? 'text-green-700'
                    : alerts[0].type === 'performance'
                    ? 'text-yellow-700'
                    : 'text-blue-700'
                }`}>
                  {alerts[0].description}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tag Suggestion Performance */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
            <Target className="h-4 w-4 text-blue-500" />
            Tag Suggestion Engine
          </h4>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Acceptance Rate</span>
                <span className={`text-sm font-semibold ${getPerformanceColor(tagSuggestionStats.acceptance_rate)}`}>
                  {(tagSuggestionStats.acceptance_rate * 100).toFixed(1)}%
                </span>
              </div>
              <Progress
                value={tagSuggestionStats.acceptance_rate * 100}
                className="h-2"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Confidence</span>
                <span className={`text-sm font-semibold ${getPerformanceColor(tagSuggestionStats.confidence_score)}`}>
                  {(tagSuggestionStats.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
              <Progress
                value={tagSuggestionStats.confidence_score * 100}
                className="h-2"
              />
            </div>
          </div>

          <div className="flex justify-between text-xs text-gray-600">
            <div>
              <span className="font-medium">{tagSuggestionStats.suggestions_generated}</span> suggestions
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span className={getPerformanceColor(tagSuggestionStats.avg_response_time, true)}>
                {tagSuggestionStats.avg_response_time}ms
              </span>
            </div>
          </div>
        </div>

        {/* PageRank Effectiveness */}
        <div className="space-y-3 pt-3 border-t">
          <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
            <Users className="h-4 w-4 text-green-500" />
            PageRank Intelligence
          </h4>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Ranking Accuracy</span>
                <span className={`text-sm font-semibold ${getPerformanceColor(pagerankEffectiveness.ranking_accuracy)}`}>
                  {(pagerankEffectiveness.ranking_accuracy * 100).toFixed(1)}%
                </span>
              </div>
              <Progress
                value={pagerankEffectiveness.ranking_accuracy * 100}
                className="h-2"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Engagement Lift</span>
                <span className={`text-sm font-semibold ${getPerformanceColor(pagerankEffectiveness.user_engagement_lift)}`}>
                  +{(pagerankEffectiveness.user_engagement_lift * 100).toFixed(1)}%
                </span>
              </div>
              <Progress
                value={pagerankEffectiveness.user_engagement_lift * 100}
                className="h-2"
              />
            </div>
          </div>

          <div className="text-xs text-gray-600">
            <span className="font-medium">{pagerankEffectiveness.memories_ranked}</span> memories analyzed
          </div>
        </div>

        {/* Intelligence Trends */}
        <div className="space-y-3 pt-3 border-t">
          <h4 className="text-sm font-medium text-gray-700">Performance Trends</h4>

          <div className="space-y-2">
            {intelligenceTrends.map((trend, index) => (
              <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700">{trend.metric}</span>
                  {getTrendIcon(trend.trend)}
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-sm font-medium">
                    {trend.unit === 'ms' ? trend.value : (trend.value * 100).toFixed(1)}
                  </span>
                  <span className="text-xs text-gray-500">
                    {trend.unit || '%'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Health */}
        <div className="pt-3 border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-semibold text-green-600">
                {(tagSuggestionStats.acceptance_rate * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">AI Accuracy</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-blue-600">
                {tagSuggestionStats.avg_response_time}ms
              </div>
              <div className="text-xs text-gray-500">Response Time</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-purple-600">
                {((tagSuggestionStats.acceptance_rate + pagerankEffectiveness.ranking_accuracy) / 2 * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">Overall Health</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

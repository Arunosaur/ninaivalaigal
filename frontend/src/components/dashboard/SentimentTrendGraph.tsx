import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Smile } from 'lucide-react';

interface SentimentData {
  date: string;
  sentiment: number;
  volume: number;
}

interface SentimentTrendGraphProps {
  currentSentiment: number;
  sentimentHistory: SentimentData[];
  predictedSentiment: number;
  trendDirection: 'up' | 'down' | 'stable';
  discussionVolume: number;
  topPositiveTopics: string[];
  aiInsights: {
    sentiment_stability: string;
    engagement_quality: string;
    team_health_score: number;
  };
  alerts: Array<{
    type: string;
    priority: string;
    title: string;
    description: string;
    icon: string;
  }>;
}

export const SentimentTrendGraph: React.FC<SentimentTrendGraphProps> = ({
  currentSentiment,
  sentimentHistory,
  predictedSentiment,
  trendDirection,
  discussionVolume,
  topPositiveTopics,
  aiInsights,
  alerts
}) => {
  const getTrendIcon = () => {
    switch (trendDirection) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = () => {
    switch (trendDirection) {
      case 'up': return 'text-green-600 bg-green-50';
      case 'down': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return '#10b981'; // green
    if (sentiment >= 0.5) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="font-medium">{formatDate(label)}</p>
          <p className="text-sm text-gray-600">
            Sentiment: {(data.sentiment * 100).toFixed(1)}%
          </p>
          <p className="text-sm text-gray-600">
            Volume: {data.volume} discussions
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Smile className="h-5 w-5 text-blue-500" />
            Team Sentiment
          </CardTitle>
          <div className="flex items-center gap-2">
            {getTrendIcon()}
            <Badge className={getTrendColor()} variant="secondary">
              {trendDirection}
            </Badge>
          </div>
        </div>

        {/* Current Metrics */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div>
            Current: {(currentSentiment * 100).toFixed(1)}%
          </div>
          <div>
            Predicted: {(predictedSentiment * 100).toFixed(1)}%
          </div>
          <div>
            Health: {aiInsights.team_health_score.toFixed(0)}/100
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Alert Banner */}
        {alerts.length > 0 && (
          <div className={`border rounded-lg p-3 ${
            alerts[0].type === 'positive_trend'
              ? 'bg-green-50 border-green-200'
              : 'bg-yellow-50 border-yellow-200'
          }`}>
            <div className="flex items-start gap-2">
              <span className="text-lg">{alerts[0].icon}</span>
              <div className="flex-1">
                <p className={`font-medium text-sm ${
                  alerts[0].type === 'positive_trend'
                    ? 'text-green-900'
                    : 'text-yellow-900'
                }`}>
                  {alerts[0].title}
                </p>
                <p className={`text-xs mt-1 ${
                  alerts[0].type === 'positive_trend'
                    ? 'text-green-700'
                    : 'text-yellow-700'
                }`}>
                  {alerts[0].description}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Sentiment Chart */}
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sentimentHistory}>
              <defs>
                <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={getSentimentColor(currentSentiment)} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={getSentimentColor(currentSentiment)} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={{ fontSize: 12 }}
                stroke="#666"
              />
              <YAxis
                domain={[0, 1]}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                tick={{ fontSize: 12 }}
                stroke="#666"
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="sentiment"
                stroke={getSentimentColor(currentSentiment)}
                strokeWidth={2}
                fill="url(#sentimentGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Positive Topics */}
        <div className="pt-3 border-t">
          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
            <Smile className="h-4 w-4 text-green-500" />
            Positive Discussion Topics
          </h4>
          <div className="flex flex-wrap gap-2">
            {topPositiveTopics.map((topic, index) => (
              <Badge key={topic} variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                {topic}
              </Badge>
            ))}
          </div>
        </div>

        {/* AI Insights */}
        <div className="pt-3 border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-sm font-semibold text-gray-900">
                {aiInsights.sentiment_stability}
              </div>
              <div className="text-xs text-gray-500">Stability</div>
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900">
                {aiInsights.engagement_quality}
              </div>
              <div className="text-xs text-gray-500">Quality</div>
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900">
                {discussionVolume}
              </div>
              <div className="text-xs text-gray-500">Volume</div>
            </div>
          </div>
        </div>

        {/* Prediction Indicator */}
        <div className="pt-3 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Tomorrow's Prediction:</span>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                predictedSentiment > currentSentiment ? 'bg-green-400' :
                predictedSentiment < currentSentiment ? 'bg-red-400' : 'bg-gray-400'
              }`} />
              <span className="font-medium">
                {(predictedSentiment * 100).toFixed(1)}%
              </span>
              {predictedSentiment > currentSentiment && (
                <TrendingUp className="h-3 w-3 text-green-500" />
              )}
              {predictedSentiment < currentSentiment && (
                <TrendingDown className="h-3 w-3 text-red-500" />
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

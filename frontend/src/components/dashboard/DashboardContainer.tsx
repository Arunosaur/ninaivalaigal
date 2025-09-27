import React, { useState, useEffect } from 'react';
import { TopMemoryCard } from './TopMemoryCard';
import { SentimentTrendGraph } from './SentimentTrendGraph';
import { AIInsightPanel } from './AIInsightPanel';
import { SmartNotificationDrawer } from './SmartNotificationDrawer';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Bell, RefreshCw, Settings, Maximize2 } from 'lucide-react';

interface DashboardContainerProps {
  userRole: 'user' | 'team_admin' | 'org_admin';
  userId: string;
}

interface WidgetData {
  widget_id: string;
  data: any;
  alerts: any[];
  timestamp: string;
}

export const DashboardContainer: React.FC<DashboardContainerProps> = ({
  userRole,
  userId
}) => {
  const [widgetData, setWidgetData] = useState<Record<string, WidgetData>>({});
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isNotificationDrawerOpen, setIsNotificationDrawerOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/dashboard-widgets/ws/${userId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('Dashboard WebSocket connected');
      
      // Subscribe to widgets based on user role
      const widgets = userRole === 'user' 
        ? ['top_memories', 'sentiment_trends']
        : ['top_memories', 'sentiment_trends', 'ai_performance'];
      
      widgets.forEach(widgetId => {
        ws.send(JSON.stringify({
          type: 'subscribe_widget',
          widget_id: widgetId
        }));
      });
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'widget_update') {
        setWidgetData(prev => ({
          ...prev,
          [message.widget_id]: {
            widget_id: message.widget_id,
            data: message.data,
            alerts: message.alerts,
            timestamp: message.timestamp
          }
        }));
        setLastUpdate(new Date());
      } else if (message.type === 'smart_alert') {
        setNotifications(prev => [message.alert, ...prev.slice(0, 9)]); // Keep last 10
        
        // Auto-open drawer for high priority alerts
        if (message.alert.priority === 'high') {
          setIsNotificationDrawerOpen(true);
        }
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('Dashboard WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('Dashboard WebSocket error:', error);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [userId, userRole]);

  // Load initial widget data
  useEffect(() => {
    const loadWidgetData = async () => {
      const widgets = userRole === 'user' 
        ? ['top_memories', 'sentiment_trends']
        : ['top_memories', 'sentiment_trends', 'ai_performance'];
      
      for (const widgetId of widgets) {
        try {
          const response = await fetch(`/api/dashboard-widgets/widgets/${widgetId}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          
          if (response.ok) {
            const result = await response.json();
            setWidgetData(prev => ({
              ...prev,
              [widgetId]: {
                widget_id: widgetId,
                data: result.widget.data,
                alerts: result.widget.alerts,
                timestamp: result.widget.last_updated
              }
            }));
          }
        } catch (error) {
          console.error(`Failed to load widget ${widgetId}:`, error);
        }
      }
    };

    loadWidgetData();
  }, [userRole]);

  const refreshAllWidgets = async () => {
    // Trigger manual refresh of all widgets
    const widgets = Object.keys(widgetData);
    
    for (const widgetId of widgets) {
      try {
        const response = await fetch(`/api/dashboard-widgets/widgets/${widgetId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          const result = await response.json();
          setWidgetData(prev => ({
            ...prev,
            [widgetId]: {
              widget_id: widgetId,
              data: result.widget.data,
              alerts: result.widget.alerts,
              timestamp: result.widget.last_updated
            }
          }));
        }
      } catch (error) {
        console.error(`Failed to refresh widget ${widgetId}:`, error);
      }
    }
    
    setLastUpdate(new Date());
  };

  const totalAlerts = Object.values(widgetData).reduce(
    (sum, widget) => sum + (widget.alerts?.length || 0), 
    0
  ) + notifications.length;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Dashboard Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              AI Intelligence Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Real-time insights and team collaboration analytics
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-400' : 'bg-red-400'
              }`} />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Live' : 'Disconnected'}
              </span>
            </div>
            
            {/* Last Update */}
            <span className="text-xs text-gray-500">
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
            
            {/* Notifications */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsNotificationDrawerOpen(true)}
              className="relative"
            >
              <Bell className="h-4 w-4" />
              {totalAlerts > 0 && (
                <Badge 
                  className="absolute -top-2 -right-2 h-5 w-5 p-0 text-xs bg-red-500"
                  variant="destructive"
                >
                  {totalAlerts > 9 ? '9+' : totalAlerts}
                </Badge>
              )}
            </Button>
            
            {/* Refresh */}
            <Button
              variant="outline"
              size="sm"
              onClick={refreshAllWidgets}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            
            {/* Settings */}
            <Button
              variant="outline"
              size="sm"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        {/* Role Badge */}
        <div className="mt-3">
          <Badge variant="outline" className="capitalize">
            {userRole.replace('_', ' ')} Dashboard
          </Badge>
        </div>
      </div>

      {/* Widget Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Top Memories Widget */}
        {widgetData.top_memories && (
          <div className="col-span-12 lg:col-span-6">
            <TopMemoryCard
              memories={widgetData.top_memories.data.memories || []}
              totalMemories={widgetData.top_memories.data.total_memories || 0}
              avgScore={widgetData.top_memories.data.avg_score || 0}
              trendingTopics={widgetData.top_memories.data.trending_topics || {}}
              aiInsights={widgetData.top_memories.data.ai_insights || {}}
              alerts={widgetData.top_memories.alerts || []}
            />
          </div>
        )}

        {/* Sentiment Trends Widget */}
        {widgetData.sentiment_trends && (
          <div className="col-span-12 lg:col-span-6">
            <SentimentTrendGraph
              currentSentiment={widgetData.sentiment_trends.data.current_sentiment || 0.7}
              sentimentHistory={widgetData.sentiment_trends.data.sentiment_history || []}
              predictedSentiment={widgetData.sentiment_trends.data.predicted_sentiment || 0.7}
              trendDirection={widgetData.sentiment_trends.data.trend_direction || 'stable'}
              discussionVolume={widgetData.sentiment_trends.data.discussion_volume || 0}
              topPositiveTopics={widgetData.sentiment_trends.data.top_positive_topics || []}
              aiInsights={widgetData.sentiment_trends.data.ai_insights || {}}
              alerts={widgetData.sentiment_trends.alerts || []}
            />
          </div>
        )}

        {/* AI Performance Widget (Team Admin+ only) */}
        {userRole !== 'user' && widgetData.ai_performance && (
          <div className="col-span-12 lg:col-span-8">
            <AIInsightPanel
              tagSuggestionStats={widgetData.ai_performance.data.tag_suggestion_stats || {}}
              pagerankEffectiveness={widgetData.ai_performance.data.pagerank_effectiveness || {}}
              intelligenceTrends={widgetData.ai_performance.data.intelligence_trends || []}
              alerts={widgetData.ai_performance.alerts || []}
            />
          </div>
        )}

        {/* Placeholder for future widgets */}
        {userRole !== 'user' && (
          <div className="col-span-12 lg:col-span-4">
            <div className="h-full border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-white">
              <div className="text-center text-gray-500">
                <Maximize2 className="h-8 w-8 mx-auto mb-2" />
                <p className="text-sm">More widgets coming soon</p>
                <p className="text-xs">Gamification & Advanced Analytics</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Smart Notification Drawer */}
      <SmartNotificationDrawer
        isOpen={isNotificationDrawerOpen}
        onClose={() => setIsNotificationDrawerOpen(false)}
        notifications={notifications}
        widgetAlerts={Object.values(widgetData).flatMap(w => w.alerts || [])}
      />
    </div>
  );
};

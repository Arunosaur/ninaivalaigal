import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { X, Clock, AlertTriangle, Info, CheckCircle, TrendingUp } from 'lucide-react';

interface Notification {
  type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  timestamp: string;
  widget_id?: string;
  icon?: string;
  action?: string;
}

interface SmartNotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: Notification[];
  widgetAlerts: Notification[];
}

export const SmartNotificationDrawer: React.FC<SmartNotificationDrawerProps> = ({
  isOpen,
  onClose,
  notifications,
  widgetAlerts
}) => {
  const allNotifications = [...notifications, ...widgetAlerts].sort((a, b) => {
    // Sort by priority first, then by timestamp
    const priorityOrder = { high: 3, medium: 2, low: 1 };
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityDiff !== 0) return priorityDiff;
    
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'medium': return <Info className="h-4 w-4 text-yellow-500" />;
      default: return <CheckCircle className="h-4 w-4 text-blue-500" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-200 bg-red-50';
      case 'medium': return 'border-yellow-200 bg-yellow-50';
      default: return 'border-blue-200 bg-blue-50';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'trending': return '📈';
      case 'quality': return '⭐';
      case 'positive_trend': return '😊';
      case 'negative_trend': return '⚠️';
      case 'ai_success': return '🤖';
      case 'performance': return '⏱️';
      default: return '🔔';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const groupedNotifications = allNotifications.reduce((groups, notification) => {
    const category = notification.type.includes('trend') ? 'Trends' :
                    notification.type.includes('ai') ? 'AI Performance' :
                    notification.type.includes('quality') ? 'Content Quality' :
                    'General';
    
    if (!groups[category]) groups[category] = [];
    groups[category].push(notification);
    return groups;
  }, {} as Record<string, Notification[]>);

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-96 sm:w-[400px]">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-500" />
              Smart Alerts
            </SheetTitle>
            <Badge variant="outline" className="text-xs">
              {allNotifications.length} active
            </Badge>
          </div>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-100px)] mt-6">
          <div className="space-y-6">
            {Object.keys(groupedNotifications).length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p className="text-sm">No active alerts</p>
                <p className="text-xs text-gray-400 mt-1">
                  You're all caught up! 🎉
                </p>
              </div>
            ) : (
              Object.entries(groupedNotifications).map(([category, categoryNotifications]) => (
                <div key={category} className="space-y-3">
                  <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    {category === 'Trends' && <TrendingUp className="h-4 w-4" />}
                    {category === 'AI Performance' && <span>🤖</span>}
                    {category === 'Content Quality' && <span>⭐</span>}
                    {category === 'General' && <span>🔔</span>}
                    {category}
                    <Badge variant="outline" className="text-xs">
                      {categoryNotifications.length}
                    </Badge>
                  </h3>
                  
                  <div className="space-y-2">
                    {categoryNotifications.map((notification, index) => (
                      <div
                        key={`${category}-${index}`}
                        className={`p-3 rounded-lg border ${getPriorityColor(notification.priority)} hover:shadow-sm transition-shadow cursor-pointer`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 mt-0.5">
                            {notification.icon ? (
                              <span className="text-lg">{notification.icon}</span>
                            ) : (
                              <span className="text-lg">{getTypeIcon(notification.type)}</span>
                            )}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="text-sm font-medium text-gray-900 leading-tight">
                                {notification.title}
                              </h4>
                              <div className="flex items-center gap-1 flex-shrink-0">
                                {getPriorityIcon(notification.priority)}
                                <Badge 
                                  variant="outline" 
                                  className={`text-xs ${
                                    notification.priority === 'high' ? 'text-red-600 border-red-200' :
                                    notification.priority === 'medium' ? 'text-yellow-600 border-yellow-200' :
                                    'text-blue-600 border-blue-200'
                                  }`}
                                >
                                  {notification.priority}
                                </Badge>
                              </div>
                            </div>
                            
                            <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                              {notification.description}
                            </p>
                            
                            <div className="flex items-center justify-between mt-2">
                              <div className="flex items-center gap-1 text-xs text-gray-500">
                                <Clock className="h-3 w-3" />
                                {formatTimestamp(notification.timestamp)}
                              </div>
                              
                              {notification.action && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 px-2 text-xs"
                                  onClick={() => {
                                    // Handle navigation to action URL
                                    console.log('Navigate to:', notification.action);
                                  }}
                                >
                                  View
                                </Button>
                              )}
                            </div>
                            
                            {notification.widget_id && (
                              <div className="mt-2">
                                <Badge variant="outline" className="text-xs bg-gray-100">
                                  {notification.widget_id.replace('_', ' ')}
                                </Badge>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {/* Footer Actions */}
        {allNotifications.length > 0 && (
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-white border-t">
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => {
                  // Mark all as read
                  console.log('Mark all as read');
                }}
              >
                Mark All Read
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => {
                  // Clear all notifications
                  console.log('Clear all');
                }}
              >
                Clear All
              </Button>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
};

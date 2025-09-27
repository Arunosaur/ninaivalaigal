import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Trophy, Star, Target, TrendingUp, Award } from 'lucide-react';

interface BadgeData {
  id: string;
  type: string;
  level: 'bronze' | 'silver' | 'gold' | 'platinum';
  title: string;
  description: string;
  icon: string;
  points: number;
  rarity: number;
}

interface UserBadge {
  badge: BadgeData;
  earned_at: string;
  progress: Record<string, any>;
  next_level?: BadgeData;
}

interface BadgeProgress {
  badge: BadgeData;
  progress: Record<string, any>;
  overall_progress: number;
}

interface BadgeDisplayProps {
  earnedBadges: UserBadge[];
  closeBadges: BadgeProgress[];
  totalPoints: number;
  teamRank: number | string;
  onCelebrate?: (badgeId: string) => void;
}

export const BadgeDisplay: React.FC<BadgeDisplayProps> = ({
  earnedBadges,
  closeBadges,
  totalPoints,
  teamRank,
  onCelebrate
}) => {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'bronze': return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'silver': return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'gold': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'platinum': return 'text-purple-600 bg-purple-50 border-purple-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRarityLabel = (rarity: number) => {
    if (rarity <= 0.05) return 'Legendary';
    if (rarity <= 0.15) return 'Rare';
    if (rarity <= 0.3) return 'Uncommon';
    return 'Common';
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            Your Achievements
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{totalPoints}</div>
              <div className="text-xs text-gray-500">Total Points</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{earnedBadges.length}</div>
              <div className="text-xs text-gray-500">Badges Earned</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">#{teamRank}</div>
              <div className="text-xs text-gray-500">Team Rank</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Badges */}
      {earnedBadges.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Award className="h-4 w-4 text-green-500" />
              Recent Badges
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {earnedBadges.slice(-3).reverse().map((userBadge) => (
              <div
                key={userBadge.badge.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="text-2xl">{userBadge.badge.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-sm text-gray-900 truncate">
                      {userBadge.badge.title}
                    </h4>
                    <Badge 
                      className={`text-xs ${getLevelColor(userBadge.badge.level)}`}
                      variant="outline"
                    >
                      {userBadge.badge.level}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600 mb-1">
                    {userBadge.badge.description}
                  </p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Earned {formatDate(userBadge.earned_at)}</span>
                    <div className="flex items-center gap-2">
                      <span>{userBadge.badge.points} pts</span>
                      <Badge variant="outline" className="text-xs">
                        {getRarityLabel(userBadge.badge.rarity)}
                      </Badge>
                    </div>
                  </div>
                </div>
                {onCelebrate && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={() => onCelebrate(userBadge.badge.id)}
                  >
                    🎉
                  </Button>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Progress Toward Next Badges */}
      {closeBadges.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-500" />
              Almost There!
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {closeBadges.slice(0, 3).map((badgeProgress) => (
              <div key={badgeProgress.badge.id} className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className="text-xl opacity-60">{badgeProgress.badge.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-sm text-gray-900">
                        {badgeProgress.badge.title}
                      </h4>
                      <span className="text-xs text-gray-500">
                        {badgeProgress.overall_progress.toFixed(0)}%
                      </span>
                    </div>
                    <Progress 
                      value={badgeProgress.overall_progress} 
                      className="h-2 mb-2"
                    />
                    <p className="text-xs text-gray-600 mb-2">
                      {badgeProgress.badge.description}
                    </p>
                    
                    {/* Detailed Progress */}
                    <div className="space-y-1">
                      {Object.entries(badgeProgress.progress).map(([criterion, data]: [string, any]) => (
                        <div key={criterion} className="flex items-center justify-between text-xs">
                          <span className="text-gray-600 capitalize">
                            {criterion.replace('_', ' ')}:
                          </span>
                          <span className="font-medium">
                            {data.current}/{data.required}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Badge Collection Overview */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Star className="h-4 w-4 text-yellow-500" />
            Badge Collection
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-2">
            {earnedBadges.map((userBadge) => (
              <div
                key={userBadge.badge.id}
                className="aspect-square bg-gray-50 rounded-lg flex flex-col items-center justify-center p-2 hover:bg-gray-100 transition-colors cursor-pointer group"
                title={`${userBadge.badge.title} - ${userBadge.badge.description}`}
              >
                <div className="text-lg mb-1">{userBadge.badge.icon}</div>
                <Badge 
                  className={`text-xs ${getLevelColor(userBadge.badge.level)} group-hover:scale-105 transition-transform`}
                  variant="outline"
                >
                  {userBadge.badge.level}
                </Badge>
              </div>
            ))}
            
            {/* Empty slots for visual appeal */}
            {Array.from({ length: Math.max(0, 8 - earnedBadges.length) }).map((_, index) => (
              <div
                key={`empty-${index}`}
                className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300"
              >
                <div className="text-gray-400 text-xs">?</div>
              </div>
            ))}
          </div>
          
          {earnedBadges.length === 0 && (
            <div className="text-center py-4 text-gray-500">
              <Trophy className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Start earning badges!</p>
              <p className="text-xs text-gray-400 mt-1">
                Contribute to discussions and help your team
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Next Level Preview */}
      {earnedBadges.some(b => b.next_level) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              Level Up!
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {earnedBadges
              .filter(b => b.next_level)
              .slice(0, 2)
              .map((userBadge) => (
                <div key={`next-${userBadge.badge.id}`} className="space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="text-xl">{userBadge.next_level!.icon}</div>
                    <div className="flex-1">
                      <h4 className="font-medium text-sm text-gray-900">
                        {userBadge.next_level!.title}
                      </h4>
                      <p className="text-xs text-gray-600">
                        {userBadge.next_level!.description}
                      </p>
                      <div className="text-xs text-gray-500 mt-1">
                        +{userBadge.next_level!.points} points
                      </div>
                    </div>
                  </div>
                  
                  {/* Progress toward next level */}
                  {Object.entries(userBadge.progress).map(([criterion, data]: [string, any]) => (
                    <div key={criterion} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600 capitalize">
                          {criterion.replace('_', ' ')}
                        </span>
                        <span>{data.current}/{data.required}</span>
                      </div>
                      <Progress value={data.percentage} className="h-1" />
                    </div>
                  ))}
                </div>
              ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

import { useState } from "react";
import Header from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useChannelAnalytics, useSystemStatus } from "@/hooks/use-analytics";
import { useProjects } from "@/hooks/use-projects";
import { 
  BarChart3, 
  Eye, 
  ThumbsUp, 
  MessageSquare, 
  Share2, 
  DollarSign,
  TrendingUp,
  TrendingDown,
  Download,
  ExternalLink,
  Calendar,
  Users,
  PlayCircle,
  Clock
} from "lucide-react";
import { format, subDays, startOfMonth } from "date-fns";

export default function Analytics() {
  const [dateRange, setDateRange] = useState<"7d" | "30d" | "90d">("30d");
  const { data: projects } = useProjects();
  
  const startDate = dateRange === "7d" 
    ? subDays(new Date(), 7)
    : dateRange === "30d"
    ? subDays(new Date(), 30)
    : subDays(new Date(), 90);

  const { data: analytics, isLoading } = useChannelAnalytics(startDate, new Date());

  // Calculate aggregated metrics
  const totalViews = analytics?.reduce((sum, a) => sum + (a.views || 0), 0) || 0;
  const totalLikes = analytics?.reduce((sum, a) => sum + (a.likes || 0), 0) || 0;
  const totalComments = analytics?.reduce((sum, a) => sum + (a.comments || 0), 0) || 0;
  const totalRevenue = analytics?.reduce((sum, a) => sum + parseFloat(a.revenue || "0"), 0) || 0;
  const totalWatchTime = analytics?.reduce((sum, a) => sum + (a.watchTime || 0), 0) || 0;

  // Calculate engagement rate
  const engagementRate = totalViews > 0 
    ? ((totalLikes + totalComments) / totalViews * 100)
    : 0;

  // Mock previous period data for comparison (in a real app, this would come from API)
  const prevViews = Math.floor(totalViews * 0.85);
  const prevLikes = Math.floor(totalLikes * 0.92);
  const prevRevenue = totalRevenue * 0.78;
  const prevEngagement = engagementRate * 0.88;

  const getChangePercentage = (current: number, previous: number) => {
    if (previous === 0) return 0;
    return ((current - previous) / previous * 100);
  };

  const formatWatchTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const topPerformingProjects = projects?.filter(p => p.status === "uploaded")
    .slice(0, 5) || [];

  const dateRangeOptions = [
    { id: "7d", label: "Last 7 days" },
    { id: "30d", label: "Last 30 days" },
    { id: "90d", label: "Last 90 days" },
  ];

  return (
    <div data-testid="analytics-page">
      <Header 
        title="Channel Analytics" 
        subtitle="Track performance and growth of your 404 Circus content"
      />
      
      <div className="p-6 space-y-6">
        {/* Date Range Selector */}
        <div className="flex items-center justify-between" data-testid="date-range-controls">
          <div className="flex gap-2">
            {dateRangeOptions.map(option => (
              <Badge
                key={option.id}
                variant={dateRange === option.id ? "default" : "outline"}
                className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                onClick={() => setDateRange(option.id as "7d" | "30d" | "90d")}
                data-testid={`date-range-${option.id}`}
              >
                {option.label}
              </Badge>
            ))}
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm" data-testid="button-export">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm" data-testid="button-youtube-studio">
              <ExternalLink className="w-4 h-4 mr-2" />
              YouTube Studio
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="key-metrics">
          <Card className="neon-border border-primary/30">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Views</p>
                  <p className="text-2xl font-bold text-primary" data-testid="metric-views">
                    {totalViews.toLocaleString()}
                  </p>
                </div>
                <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center">
                  <Eye className="w-6 h-6 text-primary" />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm">
                {getChangePercentage(totalViews, prevViews) >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-success mr-1" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-destructive mr-1" />
                )}
                <span className={getChangePercentage(totalViews, prevViews) >= 0 ? "text-success" : "text-destructive"}>
                  {Math.abs(getChangePercentage(totalViews, prevViews)).toFixed(1)}%
                </span>
                <span className="text-muted-foreground ml-1">vs previous period</span>
              </div>
            </CardContent>
          </Card>

          <Card className="neon-border border-accent/30">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Engagement Rate</p>
                  <p className="text-2xl font-bold text-accent" data-testid="metric-engagement">
                    {engagementRate.toFixed(1)}%
                  </p>
                </div>
                <div className="w-12 h-12 bg-accent/20 rounded-lg flex items-center justify-center">
                  <ThumbsUp className="w-6 h-6 text-accent" />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm">
                {getChangePercentage(engagementRate, prevEngagement) >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-success mr-1" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-destructive mr-1" />
                )}
                <span className={getChangePercentage(engagementRate, prevEngagement) >= 0 ? "text-success" : "text-destructive"}>
                  {Math.abs(getChangePercentage(engagementRate, prevEngagement)).toFixed(1)}%
                </span>
                <span className="text-muted-foreground ml-1">vs previous period</span>
              </div>
            </CardContent>
          </Card>

          <Card className="neon-border border-warning/30">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Watch Time</p>
                  <p className="text-2xl font-bold text-warning" data-testid="metric-watch-time">
                    {formatWatchTime(totalWatchTime)}
                  </p>
                </div>
                <div className="w-12 h-12 bg-warning/20 rounded-lg flex items-center justify-center">
                  <Clock className="w-6 h-6 text-warning" />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm">
                <TrendingUp className="w-4 h-4 text-success mr-1" />
                <span className="text-success">+12%</span>
                <span className="text-muted-foreground ml-1">vs previous period</span>
              </div>
            </CardContent>
          </Card>

          <Card className="neon-border border-destructive/30">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Revenue</p>
                  <p className="text-2xl font-bold text-destructive" data-testid="metric-revenue">
                    ${totalRevenue.toFixed(2)}
                  </p>
                </div>
                <div className="w-12 h-12 bg-destructive/20 rounded-lg flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-destructive" />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm">
                {getChangePercentage(totalRevenue, prevRevenue) >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-success mr-1" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-destructive mr-1" />
                )}
                <span className={getChangePercentage(totalRevenue, prevRevenue) >= 0 ? "text-success" : "text-destructive"}>
                  {Math.abs(getChangePercentage(totalRevenue, prevRevenue)).toFixed(1)}%
                </span>
                <span className="text-muted-foreground ml-1">vs previous period</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Overview */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Channel Growth */}
          <Card className="xl:col-span-2 neon-border" data-testid="channel-growth">
            <CardHeader className="border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-primary" />
                  Channel Performance
                </CardTitle>
                <Badge variant="outline">Last {dateRange}</Badge>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              {isLoading ? (
                <div className="animate-pulse">
                  <div className="h-64 bg-muted rounded"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Performance Summary */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-xl font-bold text-primary" data-testid="summary-subscribers">
                        2.34K
                      </div>
                      <div className="text-xs text-muted-foreground">Subscribers</div>
                      <div className="text-xs text-success">+5.2%</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xl font-bold text-accent" data-testid="summary-avg-views">
                        {Math.round(totalViews / (analytics?.length || 1)).toLocaleString()}
                      </div>
                      <div className="text-xs text-muted-foreground">Avg. Views</div>
                      <div className="text-xs text-success">+8.1%</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xl font-bold text-warning" data-testid="summary-ctr">
                        4.2%
                      </div>
                      <div className="text-xs text-muted-foreground">Click Rate</div>
                      <div className="text-xs text-destructive">-1.3%</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xl font-bold text-destructive" data-testid="summary-retention">
                        67%
                      </div>
                      <div className="text-xs text-muted-foreground">Retention</div>
                      <div className="text-xs text-success">+3.4%</div>
                    </div>
                  </div>

                  {/* Placeholder for chart */}
                  <div className="h-48 bg-muted/20 rounded-lg flex items-center justify-center border border-border">
                    <div className="text-center text-muted-foreground">
                      <BarChart3 className="w-12 h-12 mx-auto mb-2" />
                      <p>Performance chart would appear here</p>
                      <p className="text-xs">Integration with charting library required</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Content */}
          <Card className="neon-border" data-testid="top-content">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-success" />
                Top Performing
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                {topPerformingProjects.length > 0 ? (
                  topPerformingProjects.map((project, index) => (
                    <div key={project.id} className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-primary/20 rounded flex items-center justify-center text-xs font-bold text-primary">
                        #{index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate" data-testid={`top-content-title-${index}`}>
                          {project.title}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {/* Mock view data since we don't have real analytics yet */}
                          {Math.floor(Math.random() * 50000 + 10000).toLocaleString()} views
                        </p>
                      </div>
                      <div className="text-xs text-success">
                        +{Math.floor(Math.random() * 30 + 5)}%
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    <PlayCircle className="w-8 h-8 mx-auto mb-2" />
                    <p>No uploaded videos yet</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Audience Insights */}
          <Card className="neon-border" data-testid="audience-insights">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5 text-accent" />
                Audience Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Tech Enthusiasts</span>
                    <span className="text-sm font-medium">42%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-primary h-2 rounded-full" style={{ width: "42%" }}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Developers</span>
                    <span className="text-sm font-medium">28%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-accent h-2 rounded-full" style={{ width: "28%" }}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Gamers</span>
                    <span className="text-sm font-medium">18%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-warning h-2 rounded-full" style={{ width: "18%" }}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Students</span>
                    <span className="text-sm font-medium">12%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-destructive h-2 rounded-full" style={{ width: "12%" }}></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Traffic Sources */}
          <Card className="neon-border" data-testid="traffic-sources">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <Share2 className="w-5 h-5 text-warning" />
                Traffic Sources
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    <span className="text-sm">YouTube Search</span>
                  </div>
                  <div className="text-sm font-medium">34%</div>
                </div>
                
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-accent rounded-full"></div>
                    <span className="text-sm">Suggested Videos</span>
                  </div>
                  <div className="text-sm font-medium">28%</div>
                </div>
                
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-warning rounded-full"></div>
                    <span className="text-sm">External Sources</span>
                  </div>
                  <div className="text-sm font-medium">22%</div>
                </div>
                
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-destructive rounded-full"></div>
                    <span className="text-sm">Direct</span>
                  </div>
                  <div className="text-sm font-medium">16%</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Revenue Breakdown */}
        <Card className="neon-border" data-testid="revenue-breakdown">
          <CardHeader className="border-b border-border">
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-success" />
              Revenue Analytics
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-success mb-1">$1,247</div>
                <div className="text-sm text-muted-foreground">Ad Revenue</div>
                <div className="text-xs text-success mt-1">+15% this month</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-primary mb-1">$328</div>
                <div className="text-sm text-muted-foreground">Memberships</div>
                <div className="text-xs text-success mt-1">+8% this month</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-accent mb-1">$156</div>
                <div className="text-sm text-muted-foreground">Super Chat</div>
                <div className="text-xs text-destructive mt-1">-2% this month</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

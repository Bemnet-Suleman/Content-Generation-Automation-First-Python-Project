import { useQuery } from "@tanstack/react-query";
import Header from "@/components/header";
import StatsCard from "@/components/stats-card";
import ProjectCard from "@/components/project-card";
import ContentItem from "@/components/content-item";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useProjects, useCreateProject, useUpdateProject, useUploadProject } from "@/hooks/use-projects";
import { useTrendingContent } from "@/hooks/use-content-research";
import { useSystemStatus } from "@/hooks/use-analytics";
import { useToast } from "@/hooks/use-toast";
import { 
  Video, 
  Clock, 
  Upload, 
  Eye, 
  Plus, 
  CloudUpload, 
  Image, 
  CalendarClock,
  Search,
  ServerCog,
  BarChart3,
  Zap,
  CheckCircle,
  AlertCircle,
  XCircle
} from "lucide-react";

export default function Dashboard() {
  const { toast } = useToast();
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const { data: trendingContent, isLoading: trendingLoading } = useTrendingContent(5);
  const { data: systemStatus } = useSystemStatus();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const uploadProject = useUploadProject();

  const activeProjects = projects?.filter(p => p.status === "processing" || p.status === "ready") || [];
  const processingProjects = projects?.filter(p => p.status === "processing") || [];
  const monthlyUploads = projects?.filter(p => {
    const createdDate = new Date(p.createdAt);
    const now = new Date();
    const monthAgo = new Date(now.getFullYear(), now.getMonth(), 1);
    return createdDate >= monthAgo && p.status === "uploaded";
  }) || [];

  const handleCreateProject = () => {
    createProject.mutate({
      title: "New Tech Fail Project",
      description: "404 Circus compilation project",
      status: "draft",
      progress: 0
    }, {
      onSuccess: () => {
        toast({
          title: "Project Created",
          description: "New project has been created successfully.",
        });
      },
      onError: () => {
        toast({
          title: "Error",
          description: "Failed to create project. Please try again.",
          variant: "destructive",
        });
      }
    });
  };

  const handleAddToQueue = (content: any) => {
    createProject.mutate({
      title: `404 Circus: ${content.title}`,
      description: content.description || "",
      sourceUrl: content.url,
      sourceText: content.title,
      status: "processing",
      progress: 0
    }, {
      onSuccess: () => {
        toast({
          title: "Added to Queue",
          description: "Content has been added to processing queue.",
        });
      }
    });
  };

  const handleUploadProject = (projectId: string) => {
    uploadProject.mutate(projectId, {
      onSuccess: () => {
        toast({
          title: "Upload Started",
          description: "Video upload to YouTube has been initiated.",
        });
      }
    });
  };

  const getSystemStatusIcon = (status: string) => {
    switch (status) {
      case "online":
        return <CheckCircle className="w-6 h-6 text-success" />;
      case "processing":
        return <ServerCog className="w-6 h-6 text-warning animate-spin" />;
      case "error":
        return <XCircle className="w-6 h-6 text-destructive" />;
      default:
        return <AlertCircle className="w-6 h-6 text-muted-foreground" />;
    }
  };

  const getSystemStatusText = (service: string, status: string) => {
    const serviceNames = {
      content_scraper: "Content Scraper",
      video_processor: "Video Processor", 
      upload_manager: "Upload Manager",
      analytics_engine: "Analytics Engine"
    };
    
    return serviceNames[service as keyof typeof serviceNames] || service;
  };

  return (
    <div data-testid="dashboard-page">
      <Header 
        title="Dashboard Overview" 
        subtitle="Manage your 404 Circus content automation"
        onNewProject={handleCreateProject}
      />
      
      <div className="p-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="stats-grid">
          <StatsCard
            title="Active Projects"
            value={activeProjects.length}
            change="+2"
            changeType="positive"
            icon={Video}
            iconColor="primary"
          />
          <StatsCard
            title="Queue Processing"
            value={processingProjects.length}
            icon={Clock}
            iconColor="warning"
            progress={65}
          />
          <StatsCard
            title="Monthly Uploads"
            value={monthlyUploads.length}
            change="+15%"
            changeType="positive"
            icon={Upload}
            iconColor="accent"
          />
          <StatsCard
            title="Total Views"
            value="1.2M"
            change="+23%"
            changeType="positive"
            icon={Eye}
            iconColor="destructive"
          />
        </div>

        {/* Content Research & Active Projects */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Trending Content */}
          <Card className="neon-border" data-testid="trending-content-section">
            <CardHeader className="border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-semibold">Trending Tech Fails</CardTitle>
                <Button variant="ghost" size="sm" data-testid="button-refresh-trending">
                  <Search className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground mt-1">AI-discovered viral content opportunities</p>
            </CardHeader>
            <CardContent className="p-6">
              {trendingLoading ? (
                <div className="space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="flex items-start space-x-4">
                        <div className="w-16 h-12 bg-muted rounded"></div>
                        <div className="flex-1 space-y-2">
                          <div className="h-4 bg-muted rounded w-3/4"></div>
                          <div className="h-3 bg-muted rounded w-1/2"></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {trendingContent?.map((content) => (
                    <ContentItem
                      key={content.id}
                      content={content}
                      onAddToQueue={handleAddToQueue}
                    />
                  ))}
                  {!trendingContent?.length && (
                    <div className="text-center text-muted-foreground py-8" data-testid="no-trending-content">
                      No trending content available. Try refreshing the research data.
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Active Projects */}
          <Card className="neon-border" data-testid="active-projects-section">
            <CardHeader className="border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-semibold">Active Projects</CardTitle>
                <Button variant="ghost" size="sm" data-testid="button-view-all-projects">
                  <Video className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground mt-1">Currently processing and scheduled content</p>
            </CardHeader>
            <CardContent className="p-6">
              {projectsLoading ? (
                <div className="space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="border border-border rounded-lg p-4">
                        <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                        <div className="h-3 bg-muted rounded w-1/2 mb-4"></div>
                        <div className="h-2 bg-muted rounded w-full"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {activeProjects.slice(0, 3).map((project) => (
                    <ProjectCard
                      key={project.id}
                      project={project}
                      onUpload={handleUploadProject}
                    />
                  ))}
                  {!activeProjects.length && (
                    <div className="text-center text-muted-foreground py-8" data-testid="no-active-projects">
                      No active projects. Create a new project to get started.
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions & System Status */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <Card className="neon-border" data-testid="quick-actions-section">
            <CardHeader className="border-b border-border">
              <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">Streamlined workflow shortcuts</p>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <Button
                className="w-full bg-primary text-primary-foreground hover:bg-primary/80 neon-glow"
                onClick={handleCreateProject}
                data-testid="button-create-project"
              >
                <Video className="w-4 h-4 mr-2" />
                Create New Video Project
              </Button>
              <Button
                variant="secondary"
                className="w-full"
                data-testid="button-bulk-upload"
              >
                <CloudUpload className="w-4 h-4 mr-2" />
                Bulk Upload Content
              </Button>
              <Button
                variant="outline"
                className="w-full border-accent text-accent hover:bg-accent hover:text-accent-foreground"
                data-testid="button-generate-thumbnails"
              >
                <Image className="w-4 h-4 mr-2" />
                Generate Thumbnails
              </Button>
              <Button
                variant="outline"
                className="w-full border-warning text-warning hover:bg-warning hover:text-background"
                data-testid="button-schedule-batch"
              >
                <CalendarClock className="w-4 h-4 mr-2" />
                Schedule Upload Batch
              </Button>
            </CardContent>
          </Card>

          {/* System Status */}
          <Card className="xl:col-span-2 neon-border" data-testid="system-status-section">
            <CardHeader className="border-b border-border">
              <CardTitle className="text-lg font-semibold">System Status</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">Real-time automation pipeline health</p>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {systemStatus?.map((status) => (
                  <div key={status.service} className="text-center" data-testid={`system-status-${status.service}`}>
                    <div className="w-16 h-16 mx-auto mb-3 rounded-full flex items-center justify-center">
                      {getSystemStatusIcon(status.status)}
                    </div>
                    <h4 className="font-medium mb-1">{getSystemStatusText(status.service, status.status)}</h4>
                    <p className={`text-xs mb-1 ${
                      status.status === 'online' ? 'text-success' :
                      status.status === 'processing' ? 'text-warning' :
                      status.status === 'error' ? 'text-destructive' :
                      'text-muted-foreground'
                    }`}>
                      {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {status.metadata?.lastScan && `Last scan: ${status.metadata.lastScan}`}
                      {status.metadata?.queueSize && `Queue: ${status.metadata.queueSize} items`}
                      {!status.metadata?.lastScan && !status.metadata?.queueSize && 'System ready'}
                    </p>
                  </div>
                )) || (
                  // Default system status display when no data
                  <>
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-3 bg-success/20 rounded-full flex items-center justify-center">
                        <Search className="w-6 h-6 text-success" />
                      </div>
                      <h4 className="font-medium mb-1">Content Scraper</h4>
                      <p className="text-xs text-success">Online</p>
                      <p className="text-xs text-muted-foreground">Ready to scan</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-3 bg-warning/20 rounded-full flex items-center justify-center">
                        <ServerCog className="w-6 h-6 text-warning" />
                      </div>
                      <h4 className="font-medium mb-1">Video Processor</h4>
                      <p className="text-xs text-warning">Ready</p>
                      <p className="text-xs text-muted-foreground">Queue empty</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-3 bg-primary/20 rounded-full flex items-center justify-center">
                        <Upload className="w-6 h-6 text-primary" />
                      </div>
                      <h4 className="font-medium mb-1">Upload Manager</h4>
                      <p className="text-xs text-primary">Ready</p>
                      <p className="text-xs text-muted-foreground">Awaiting content</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-3 bg-accent/20 rounded-full flex items-center justify-center">
                        <BarChart3 className="w-6 h-6 text-accent" />
                      </div>
                      <h4 className="font-medium mb-1">Analytics Engine</h4>
                      <p className="text-xs text-accent">Online</p>
                      <p className="text-xs text-muted-foreground">Data synced</p>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Floating Action Button */}
      <div className="fixed bottom-6 right-6">
        <Button
          className="w-14 h-14 rounded-full shadow-lg bg-primary text-primary-foreground hover:bg-primary/80 animate-pulse-neon p-0"
          onClick={handleCreateProject}
          data-testid="fab-create-project"
        >
          <Plus className="w-6 h-6" />
        </Button>
      </div>
    </div>
  );
}

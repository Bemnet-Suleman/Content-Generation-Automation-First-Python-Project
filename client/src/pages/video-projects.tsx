import { useState } from "react";
import Header from "@/components/header";
import ProjectCard from "@/components/project-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useProjects, useCreateProject, useUpdateProject, useDeleteProject, useUploadProject } from "@/hooks/use-projects";
import { useToast } from "@/hooks/use-toast";
import { 
  Search, 
  Plus, 
  Filter, 
  Video, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Upload,
  Trash2
} from "lucide-react";

export default function VideoProjects() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const { toast } = useToast();
  
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const uploadProject = useUploadProject();

  const handleCreateProject = () => {
    createProject.mutate({
      title: "New 404 Circus Project",
      description: "Tech fail compilation video",
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
          description: "Failed to create project.",
          variant: "destructive",
        });
      }
    });
  };

  const handlePauseProject = (id: string) => {
    updateProject.mutate({
      id,
      updates: { status: "paused" }
    }, {
      onSuccess: () => {
        toast({
          title: "Project Paused",
          description: "Processing has been paused.",
        });
      }
    });
  };

  const handleCancelProject = (id: string) => {
    deleteProject.mutate(id, {
      onSuccess: () => {
        toast({
          title: "Project Cancelled",
          description: "Project has been deleted.",
        });
      },
      onError: () => {
        toast({
          title: "Error",
          description: "Failed to delete project.",
          variant: "destructive",
        });
      }
    });
  };

  const handleScheduleProject = (id: string) => {
    // For demo purposes, schedule for tomorrow at 9 AM
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);

    updateProject.mutate({
      id,
      updates: { scheduledUploadTime: tomorrow.toISOString() }
    }, {
      onSuccess: () => {
        toast({
          title: "Upload Scheduled",
          description: "Project has been scheduled for tomorrow at 9:00 AM.",
        });
      }
    });
  };

  const handleUploadProject = (id: string) => {
    uploadProject.mutate(id, {
      onSuccess: () => {
        toast({
          title: "Upload Started",
          description: "Video upload to YouTube has been initiated.",
        });
      },
      onError: () => {
        toast({
          title: "Error",
          description: "Failed to start upload.",
          variant: "destructive",
        });
      }
    });
  };

  const handleResumeProject = (id: string) => {
    updateProject.mutate({
      id,
      updates: { status: "processing", progress: 0 }
    }, {
      onSuccess: () => {
        toast({
          title: "Processing Resumed",
          description: "Project processing has been restarted.",
        });
      }
    });
  };

  const filteredProjects = projects?.filter(project => {
    const matchesSearch = project.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (selectedStatus === "all") return matchesSearch;
    return matchesSearch && project.status === selectedStatus;
  });

  const statusFilters = [
    { id: "all", label: "All", count: projects?.length || 0, icon: Filter },
    { id: "processing", label: "Processing", count: projects?.filter(p => p.status === "processing").length || 0, icon: Clock },
    { id: "ready", label: "Ready", count: projects?.filter(p => p.status === "ready").length || 0, icon: CheckCircle },
    { id: "uploaded", label: "Uploaded", count: projects?.filter(p => p.status === "uploaded").length || 0, icon: Upload },
    { id: "error", label: "Error", count: projects?.filter(p => p.status === "error").length || 0, icon: AlertCircle },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processing":
        return <Clock className="w-4 h-4 text-warning" />;
      case "ready":
        return <CheckCircle className="w-4 h-4 text-primary" />;
      case "uploaded":
        return <Upload className="w-4 h-4 text-success" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-destructive" />;
      default:
        return <Video className="w-4 h-4 text-muted-foreground" />;
    }
  };

  return (
    <div data-testid="video-projects-page">
      <Header 
        title="Video Projects" 
        subtitle="Manage your 404 Circus video production pipeline"
        onNewProject={handleCreateProject}
      />
      
      <div className="p-6 space-y-6">
        {/* Search and Filters */}
        <Card className="neon-border" data-testid="project-controls">
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
              <div className="flex-1 flex gap-4 items-center">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    placeholder="Search projects..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                    data-testid="input-search-projects"
                  />
                </div>
              </div>
              
              <div className="flex gap-2 flex-wrap">
                {statusFilters.map(filter => {
                  const Icon = filter.icon;
                  return (
                    <Badge
                      key={filter.id}
                      variant={selectedStatus === filter.id ? "default" : "outline"}
                      className="cursor-pointer hover:bg-primary hover:text-primary-foreground flex items-center gap-1"
                      onClick={() => setSelectedStatus(filter.id)}
                      data-testid={`filter-${filter.id}`}
                    >
                      <Icon className="w-3 h-3" />
                      {filter.label} ({filter.count})
                    </Badge>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Project Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4" data-testid="project-stats">
          <Card className="bg-card/50 border-primary/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <Video className="w-6 h-6 text-primary" />
              </div>
              <div className="text-2xl font-bold text-primary">{projects?.length || 0}</div>
              <div className="text-xs text-muted-foreground">Total Projects</div>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50 border-warning/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <Clock className="w-6 h-6 text-warning" />
              </div>
              <div className="text-2xl font-bold text-warning">
                {projects?.filter(p => p.status === "processing").length || 0}
              </div>
              <div className="text-xs text-muted-foreground">Processing</div>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50 border-success/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <CheckCircle className="w-6 h-6 text-success" />
              </div>
              <div className="text-2xl font-bold text-success">
                {projects?.filter(p => p.status === "ready").length || 0}
              </div>
              <div className="text-xs text-muted-foreground">Ready</div>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50 border-accent/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <Upload className="w-6 h-6 text-accent" />
              </div>
              <div className="text-2xl font-bold text-accent">
                {projects?.filter(p => p.status === "uploaded").length || 0}
              </div>
              <div className="text-xs text-muted-foreground">Uploaded</div>
            </CardContent>
          </Card>
        </div>

        {/* Projects List */}
        <Card className="neon-border" data-testid="projects-list">
          <CardHeader className="border-b border-border">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(selectedStatus)}
                {selectedStatus === "all" ? "All Projects" : `${selectedStatus.charAt(0).toUpperCase() + selectedStatus.slice(1)} Projects`}
              </CardTitle>
              <Badge variant="outline">
                {filteredProjects?.length || 0} projects
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {isLoading ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="border border-border rounded-lg p-4">
                      <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-muted rounded w-1/2 mb-4"></div>
                      <div className="h-2 bg-muted rounded w-full mb-4"></div>
                      <div className="flex justify-between">
                        <div className="h-3 bg-muted rounded w-1/3"></div>
                        <div className="h-3 bg-muted rounded w-1/4"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredProjects?.length ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredProjects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onPause={handlePauseProject}
                    onCancel={handleCancelProject}
                    onSchedule={handleScheduleProject}
                    onUpload={handleUploadProject}
                    onResume={handleResumeProject}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-12" data-testid="no-projects">
                <Video className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <h3 className="text-lg font-medium mb-2">No Projects Found</h3>
                <p className="mb-4">
                  {searchTerm || selectedStatus !== "all" 
                    ? "Try adjusting your search or filter criteria." 
                    : "Create your first project to get started with 404 Circus automation."
                  }
                </p>
                <Button
                  className="bg-primary text-primary-foreground hover:bg-primary/80"
                  onClick={handleCreateProject}
                  data-testid="button-create-first-project"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create New Project
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

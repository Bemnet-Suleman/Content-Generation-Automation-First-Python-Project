import { useState } from "react";
import Header from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useProjects } from "@/hooks/use-projects";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { 
  Calendar,
  Clock, 
  Upload, 
  Play, 
  Pause, 
  Trash2, 
  CheckCircle, 
  AlertCircle,
  RotateCcw,
  Edit3
} from "lucide-react";
import { format } from "date-fns";

interface QueueItem {
  id: string;
  projectId: string;
  scheduledTime: string;
  status: "pending" | "uploading" | "completed" | "failed";
  retryCount: number;
  error?: string;
  createdAt: string;
  project?: {
    id: string;
    title: string;
    description?: string;
    status: string;
  };
}

export default function UploadQueue() {
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: projects } = useProjects();

  const { data: queueItems, isLoading } = useQuery<QueueItem[]>({
    queryKey: ["/api/upload-queue"],
  });

  const updateQueueItem = useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: any }) => {
      const response = await apiRequest("PATCH", `/api/upload-queue/${id}`, updates);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/upload-queue"] });
    },
  });

  const removeQueueItem = useMutation({
    mutationFn: async (id: string) => {
      await apiRequest("DELETE", `/api/upload-queue/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/upload-queue"] });
      toast({
        title: "Item Removed",
        description: "Upload queue item has been removed.",
      });
    },
  });

  const addToQueue = useMutation({
    mutationFn: async (data: { projectId: string; scheduledTime: string }) => {
      const response = await apiRequest("POST", "/api/upload-queue", data);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/upload-queue"] });
      toast({
        title: "Added to Queue",
        description: "Project has been scheduled for upload.",
      });
    },
  });

  const handleScheduleUpload = (projectId: string) => {
    // Schedule for tomorrow at 9 AM for demo
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);

    addToQueue.mutate({
      projectId,
      scheduledTime: tomorrow.toISOString()
    });
  };

  const handleRetry = (id: string) => {
    updateQueueItem.mutate({
      id,
      updates: { status: "pending", retryCount: 0 }
    }, {
      onSuccess: () => {
        toast({
          title: "Upload Retrying",
          description: "Upload has been queued for retry.",
        });
      }
    });
  };

  const handleReschedule = (id: string) => {
    // Reschedule for 1 hour from now for demo
    const newTime = new Date();
    newTime.setHours(newTime.getHours() + 1);

    updateQueueItem.mutate({
      id,
      updates: { scheduledTime: newTime.toISOString(), status: "pending" }
    }, {
      onSuccess: () => {
        toast({
          title: "Upload Rescheduled",
          description: "Upload has been rescheduled.",
        });
      }
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-warning/20 text-warning";
      case "uploading":
        return "bg-primary/20 text-primary";
      case "completed":
        return "bg-success/20 text-success";
      case "failed":
        return "bg-destructive/20 text-destructive";
      default:
        return "bg-muted/20 text-muted-foreground";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <Clock className="w-4 h-4" />;
      case "uploading":
        return <Upload className="w-4 h-4 animate-pulse" />;
      case "completed":
        return <CheckCircle className="w-4 h-4" />;
      case "failed":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const filteredItems = queueItems?.filter(item => {
    if (selectedStatus === "all") return true;
    return item.status === selectedStatus;
  });

  const statusFilters = [
    { id: "all", label: "All", count: queueItems?.length || 0 },
    { id: "pending", label: "Pending", count: queueItems?.filter(q => q.status === "pending").length || 0 },
    { id: "uploading", label: "Uploading", count: queueItems?.filter(q => q.status === "uploading").length || 0 },
    { id: "completed", label: "Completed", count: queueItems?.filter(q => q.status === "completed").length || 0 },
    { id: "failed", label: "Failed", count: queueItems?.filter(q => q.status === "failed").length || 0 },
  ];

  const readyProjects = projects?.filter(p => p.status === "ready" && !queueItems?.some(q => q.projectId === p.id));

  return (
    <div data-testid="upload-queue-page">
      <Header 
        title="Upload Queue" 
        subtitle="Manage scheduled YouTube uploads and batch operations"
      />
      
      <div className="p-6 space-y-6">
        {/* Queue Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4" data-testid="queue-stats">
          <Card className="bg-card/50 border-warning/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <Clock className="w-6 h-6 text-warning" />
              </div>
              <div className="text-2xl font-bold text-warning">
                {queueItems?.filter(q => q.status === "pending").length || 0}
              </div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50 border-primary/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <Upload className="w-6 h-6 text-primary" />
              </div>
              <div className="text-2xl font-bold text-primary">
                {queueItems?.filter(q => q.status === "uploading").length || 0}
              </div>
              <div className="text-xs text-muted-foreground">Uploading</div>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50 border-success/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <CheckCircle className="w-6 h-6 text-success" />
              </div>
              <div className="text-2xl font-bold text-success">
                {queueItems?.filter(q => q.status === "completed").length || 0}
              </div>
              <div className="text-xs text-muted-foreground">Completed</div>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50 border-destructive/20">
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <AlertCircle className="w-6 h-6 text-destructive" />
              </div>
              <div className="text-2xl font-bold text-destructive">
                {queueItems?.filter(q => q.status === "failed").length || 0}
              </div>
              <div className="text-xs text-muted-foreground">Failed</div>
            </CardContent>
          </Card>
        </div>

        {/* Ready Projects */}
        {readyProjects && readyProjects.length > 0 && (
          <Card className="neon-border border-primary/30" data-testid="ready-projects">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2 text-primary">
                <Play className="w-5 h-5" />
                Ready for Upload
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Projects completed and ready to be scheduled
              </p>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {readyProjects.map((project) => (
                  <Card key={project.id} className="bg-primary/5 border-primary/20">
                    <CardContent className="p-4">
                      <h4 className="font-medium mb-2" data-testid="ready-project-title">
                        {project.title}
                      </h4>
                      <p className="text-sm text-muted-foreground mb-4">
                        {project.description || "No description"}
                      </p>
                      <Button
                        className="w-full bg-primary text-primary-foreground hover:bg-primary/80"
                        onClick={() => handleScheduleUpload(project.id)}
                        disabled={addToQueue.isPending}
                        data-testid={`button-schedule-${project.id}`}
                      >
                        <Calendar className="w-4 h-4 mr-2" />
                        Schedule Upload
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Status Filters */}
        <div className="flex gap-2 flex-wrap" data-testid="status-filters">
          {statusFilters.map(filter => (
            <Badge
              key={filter.id}
              variant={selectedStatus === filter.id ? "default" : "outline"}
              className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
              onClick={() => setSelectedStatus(filter.id)}
              data-testid={`filter-${filter.id}`}
            >
              {filter.label} ({filter.count})
            </Badge>
          ))}
        </div>

        {/* Upload Queue */}
        <Card className="neon-border" data-testid="upload-queue-list">
          <CardHeader className="border-b border-border">
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-accent" />
              Upload Schedule
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Manage your YouTube upload pipeline
            </p>
          </CardHeader>
          <CardContent className="p-6">
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="border border-border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                          <div className="h-3 bg-muted rounded w-1/2"></div>
                        </div>
                        <div className="h-6 w-20 bg-muted rounded"></div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="h-3 bg-muted rounded w-1/3"></div>
                        <div className="flex gap-2">
                          <div className="h-8 w-8 bg-muted rounded"></div>
                          <div className="h-8 w-8 bg-muted rounded"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredItems?.length ? (
              <div className="space-y-4">
                {filteredItems.map((item) => {
                  const project = projects?.find(p => p.id === item.projectId);
                  return (
                    <Card key={item.id} className="border border-border">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex-1">
                            <h4 className="font-medium" data-testid="queue-item-title">
                              {project?.title || "Unknown Project"}
                            </h4>
                            <p className="text-sm text-muted-foreground mt-1">
                              {project?.description || "No description available"}
                            </p>
                          </div>
                          <Badge className={getStatusColor(item.status)} data-testid="queue-item-status">
                            <div className="flex items-center gap-1">
                              {getStatusIcon(item.status)}
                              {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                            </div>
                          </Badge>
                        </div>

                        {item.error && (
                          <div className="bg-destructive/10 border border-destructive/20 rounded p-3 mb-4">
                            <p className="text-sm text-destructive" data-testid="queue-item-error">
                              Error: {item.error}
                            </p>
                          </div>
                        )}

                        <div className="flex justify-between items-center text-sm">
                          <div className="text-muted-foreground">
                            <span>Scheduled: </span>
                            <span className="font-mono" data-testid="queue-item-scheduled">
                              {format(new Date(item.scheduledTime), "MMM dd, yyyy 'at' h:mm a")}
                            </span>
                            {item.retryCount > 0 && (
                              <span className="ml-4 text-warning">
                                Retry #{item.retryCount}
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {item.status === "failed" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRetry(item.id)}
                                className="text-primary hover:text-primary/80"
                                data-testid="button-retry"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </Button>
                            )}
                            
                            {(item.status === "pending" || item.status === "failed") && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleReschedule(item.id)}
                                className="text-accent hover:text-accent/80"
                                data-testid="button-reschedule"
                              >
                                <Edit3 className="w-4 h-4" />
                              </Button>
                            )}
                            
                            {item.status !== "uploading" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeQueueItem.mutate(item.id)}
                                className="text-destructive hover:text-destructive/80"
                                data-testid="button-remove"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-12" data-testid="no-queue-items">
                <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <h3 className="text-lg font-medium mb-2">No Uploads Scheduled</h3>
                <p className="mb-4">
                  {selectedStatus === "all" 
                    ? "Schedule your first upload to get started with automated publishing."
                    : `No ${selectedStatus} uploads found.`
                  }
                </p>
                {readyProjects?.length ? (
                  <p className="text-sm text-primary">
                    {readyProjects.length} projects are ready to be scheduled above.
                  </p>
                ) : null}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Project } from "@shared/schema";
import { Pause, X, Calendar, Upload, Play } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  project: Project;
  onPause?: (id: string) => void;
  onCancel?: (id: string) => void;
  onSchedule?: (id: string) => void;
  onUpload?: (id: string) => void;
  onResume?: (id: string) => void;
}

export default function ProjectCard({ 
  project, 
  onPause, 
  onCancel, 
  onSchedule, 
  onUpload,
  onResume 
}: ProjectCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "processing":
        return "bg-warning/20 text-warning";
      case "ready":
        return "bg-primary/20 text-primary";
      case "uploaded":
        return "bg-success/20 text-success";
      case "error":
        return "bg-destructive/20 text-destructive";
      default:
        return "bg-muted/20 text-muted-foreground";
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case "processing":
        return "bg-warning animate-pulse-neon";
      case "ready":
      case "uploaded":
        return "bg-primary";
      case "error":
        return "bg-destructive";
      default:
        return "bg-muted";
    }
  };

  return (
    <Card className="border border-border" data-testid={`project-card-${project.id}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h4 className="font-medium" data-testid="project-title">{project.title}</h4>
            <p className="text-sm text-muted-foreground mt-1" data-testid="project-description">
              {project.description || "No description"}
            </p>
          </div>
          <Badge className={cn("ml-2", getStatusColor(project.status))} data-testid="project-status">
            {project.status}
          </Badge>
        </div>

        {/* Progress Section */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span>
              {project.status === "processing" ? "Video Processing" : 
               project.status === "ready" ? "Ready for Upload" : 
               project.status === "uploaded" ? "Completed" : "Progress"}
            </span>
            <span data-testid="project-progress">
              {project.status === "ready" || project.status === "uploaded" ? "100%" : `${project.progress}%`}
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className={cn("h-2 rounded-full transition-all duration-300", getProgressColor(project.status))}
              style={{ width: project.status === "ready" || project.status === "uploaded" ? "100%" : `${project.progress}%` }}
            />
          </div>
        </div>

        {/* Error Display */}
        {project.status === "error" && project.metadata?.error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded p-3 mb-4" data-testid="project-error">
            <p className="text-sm text-destructive">Error: {project.metadata.error}</p>
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-primary hover:text-primary/80 mt-2 p-0 h-auto"
              onClick={() => onResume?.(project.id)}
              data-testid="button-retry"
            >
              <Play className="w-3 h-3 mr-1" />
              Retry Processing
            </Button>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span data-testid="project-time">
            {project.scheduledUploadTime 
              ? `Scheduled: ${new Date(project.scheduledUploadTime).toLocaleDateString()}`
              : `Created: ${new Date(project.createdAt).toLocaleDateString()}`
            }
          </span>
          <div className="flex items-center space-x-2">
            {project.status === "processing" && onPause && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-primary hover:text-primary/80 p-1 h-6 w-6"
                onClick={() => onPause(project.id)}
                data-testid="button-pause"
              >
                <Pause className="w-3 h-3" />
              </Button>
            )}
            {project.status === "ready" && onSchedule && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-accent hover:text-accent/80 p-1 h-6 w-6"
                onClick={() => onSchedule(project.id)}
                data-testid="button-schedule"
              >
                <Calendar className="w-3 h-3" />
              </Button>
            )}
            {project.status === "ready" && onUpload && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-primary hover:text-primary/80 p-1 h-6 w-6"
                onClick={() => onUpload(project.id)}
                data-testid="button-upload"
              >
                <Upload className="w-3 h-3" />
              </Button>
            )}
            {onCancel && project.status !== "uploaded" && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-destructive hover:text-destructive/80 p-1 h-6 w-6"
                onClick={() => onCancel(project.id)}
                data-testid="button-cancel"
              >
                <X className="w-3 h-3" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

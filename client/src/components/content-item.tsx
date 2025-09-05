import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ContentSource } from "@shared/schema";
import { Plus, ExternalLink } from "lucide-react";

interface ContentItemProps {
  content: ContentSource;
  onAddToQueue?: (content: ContentSource) => void;
  onViewSource?: (content: ContentSource) => void;
}

export default function ContentItem({ content, onAddToQueue, onViewSource }: ContentItemProps) {
  const getPotentialBadge = (score: number) => {
    if (score >= 80) return { text: "High Potential", color: "bg-success/20 text-success" };
    if (score >= 60) return { text: "Good Potential", color: "bg-primary/20 text-primary" };
    if (score >= 40) return { text: "Medium Potential", color: "bg-warning/20 text-warning" };
    return { text: "Low Potential", color: "bg-muted/20 text-muted-foreground" };
  };

  const getSourceBadge = (source: string) => {
    switch (source.toLowerCase()) {
      case "reddit":
        return { text: "Reddit", color: "bg-orange-500/20 text-orange-400" };
      case "tiktok":
        return { text: "TikTok", color: "bg-pink-500/20 text-pink-400" };
      case "twitter":
        return { text: "Twitter", color: "bg-blue-500/20 text-blue-400" };
      default:
        return { text: source, color: "bg-muted/20 text-muted-foreground" };
    }
  };

  const potential = getPotentialBadge(content.trendingScore);
  const sourceBadge = getSourceBadge(content.source);

  return (
    <Card 
      className="p-3 hover:bg-muted/50 transition-colors cursor-pointer" 
      data-testid={`content-item-${content.id}`}
    >
      <CardContent className="p-0">
        <div className="flex items-start space-x-4">
          {/* Thumbnail */}
          {content.thumbnailUrl && (
            <img 
              src={content.thumbnailUrl}
              alt={content.title}
              className="w-16 h-12 rounded object-cover neon-border"
              data-testid="content-thumbnail"
            />
          )}
          
          {/* Content Info */}
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm truncate" data-testid="content-title">
              {content.title}
            </h4>
            <p className="text-xs text-muted-foreground" data-testid="content-source">
              {content.source} • {content.upvotes || content.likes || content.views || 0} {
                content.upvotes ? 'upvotes' : 
                content.likes ? 'likes' : 
                content.views ? 'views' : 'interactions'
              }
            </p>
            
            {/* Tags */}
            <div className="flex items-center space-x-2 mt-2">
              <Badge className={potential.color} data-testid="potential-badge">
                {potential.text}
              </Badge>
              <Badge className={sourceBadge.color} data-testid="source-badge">
                {sourceBadge.text}
              </Badge>
              {content.tags && content.tags.slice(0, 2).map((tag, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex items-center space-x-1">
            {onViewSource && (
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-foreground p-1 h-6 w-6"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewSource(content);
                }}
                data-testid="button-view-source"
              >
                <ExternalLink className="w-3 h-3" />
              </Button>
            )}
            {onAddToQueue && !content.isProcessed && (
              <Button
                variant="ghost"
                size="sm"
                className="text-primary hover:text-primary/80 p-1 h-6 w-6"
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToQueue(content);
                }}
                data-testid="button-add-to-queue"
              >
                <Plus className="w-3 h-3" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

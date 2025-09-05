import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: LucideIcon;
  iconColor: "primary" | "warning" | "accent" | "destructive";
  progress?: number;
}

export default function StatsCard({ 
  title, 
  value, 
  change, 
  changeType = "neutral", 
  icon: Icon, 
  iconColor,
  progress 
}: StatsCardProps) {
  const iconColorClasses = {
    primary: "text-primary bg-primary/20",
    warning: "text-warning bg-warning/20",
    accent: "text-accent bg-accent/20",
    destructive: "text-destructive bg-destructive/20"
  };

  const changeColorClasses = {
    positive: "text-success",
    negative: "text-destructive",
    neutral: "text-muted-foreground"
  };

  return (
    <Card className="neon-border" data-testid={`stats-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground" data-testid="stats-title">{title}</p>
            <p className={`text-2xl font-bold ${iconColor === 'primary' ? 'text-primary' : iconColor === 'warning' ? 'text-warning' : iconColor === 'accent' ? 'text-accent' : 'text-destructive'}`} data-testid="stats-value">
              {value}
            </p>
          </div>
          <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center", iconColorClasses[iconColor])}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
        
        {progress !== undefined && (
          <div className="mt-4">
            <div className="w-full bg-muted rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${iconColor === 'warning' ? 'bg-warning' : 'bg-primary'}`} 
                style={{ width: `${progress}%` }}
                data-testid="stats-progress"
              />
            </div>
          </div>
        )}
        
        {change && (
          <div className="mt-4 flex items-center text-sm">
            <span className={changeColorClasses[changeType]} data-testid="stats-change">
              {change}
            </span>
            <span className="text-muted-foreground ml-1">from yesterday</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

import { Button } from "@/components/ui/button";
import { Plus, User } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle: string;
  onNewProject?: () => void;
}

export default function Header({ title, subtitle, onNewProject }: HeaderProps) {
  return (
    <header className="bg-card border-b border-border px-6 py-4" data-testid="page-header">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold" data-testid="page-title">{title}</h2>
          <p className="text-sm text-muted-foreground" data-testid="page-subtitle">{subtitle}</p>
        </div>
        <div className="flex items-center space-x-4">
          {onNewProject && (
            <Button 
              className="bg-primary text-primary-foreground hover:bg-primary/80 neon-border"
              onClick={onNewProject}
              data-testid="button-new-project"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          )}
          <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center" data-testid="user-avatar">
            <User className="w-4 h-4 text-muted-foreground" />
          </div>
        </div>
      </div>
    </header>
  );
}

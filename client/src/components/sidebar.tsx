import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { 
  Gauge, 
  Search, 
  Video, 
  Upload, 
  BarChart3, 
  Settings,
  Zap
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: Gauge },
  { name: "Content Research", href: "/content-research", icon: Search },
  { name: "Video Projects", href: "/video-projects", icon: Video },
  { name: "Upload Queue", href: "/upload-queue", icon: Upload },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const [location] = useLocation();

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col" data-testid="sidebar">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-bold font-mono glitch-text" data-text="404 CIRCUS" data-testid="logo">
          404 CIRCUS
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Automation Dashboard</p>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center space-x-3 px-3 py-2 rounded-lg text-foreground hover:bg-secondary transition-colors",
                  isActive && "bg-primary text-primary-foreground neon-glow"
                )}
                data-testid={`nav-${item.name.toLowerCase().replace(' ', '-')}`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>
      
      {/* Status Indicator */}
      <div className="p-4 border-t border-border" data-testid="system-status">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-success rounded-full animate-pulse"></div>
          <span className="text-sm text-muted-foreground">System Online</span>
        </div>
        <div className="text-xs text-muted-foreground mt-1 font-mono">
          <Zap className="inline w-3 h-3 mr-1" />
          Uptime: 48h 32m
        </div>
      </div>
    </aside>
  );
}

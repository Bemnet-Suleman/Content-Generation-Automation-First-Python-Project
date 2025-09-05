import { useState } from "react";
import Header from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  Settings as SettingsIcon,
  Youtube,
  Key,
  Database,
  Bell,
  Palette,
  Download,
  Upload,
  Shield,
  Zap,
  Save,
  TestTube,
  AlertTriangle,
  CheckCircle,
  XCircle
} from "lucide-react";

export default function Settings() {
  const { toast } = useToast();
  
  // YouTube API Settings
  const [youtubeApiKey, setYoutubeApiKey] = useState("");
  const [channelId, setChannelId] = useState("");
  const [defaultTags, setDefaultTags] = useState("fail,glitch,404Circus,compilation,tech fails,viral");
  const [defaultCategory, setDefaultCategory] = useState("28");
  
  // Content Settings
  const [autoProcessing, setAutoProcessing] = useState(true);
  const [autoScheduling, setAutoScheduling] = useState(false);
  const [qualityPreset, setQualityPreset] = useState("high");
  const [thumbnailStyle, setThumbnailStyle] = useState("glitch");
  
  // Notification Settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [processingAlerts, setProcessingAlerts] = useState(true);
  const [uploadAlerts, setUploadAlerts] = useState(true);
  const [errorAlerts, setErrorAlerts] = useState(true);
  
  // System Settings
  const [scrapingInterval, setScrapingInterval] = useState("60");
  const [maxRetries, setMaxRetries] = useState("3");
  const [storageLimit, setStorageLimit] = useState("100");
  
  // Connection Status (mock data)
  const [connectionStatus, setConnectionStatus] = useState({
    youtube: "connected",
    database: "connected",
    python: "connected",
    ffmpeg: "connected"
  });

  const handleSaveSettings = () => {
    // In a real app, this would save to backend
    toast({
      title: "Settings Saved",
      description: "Your configuration has been updated successfully.",
    });
  };

  const handleTestYouTubeConnection = () => {
    // Mock testing - in real app would test API connection
    setConnectionStatus(prev => ({ ...prev, youtube: "testing" }));
    setTimeout(() => {
      setConnectionStatus(prev => ({ ...prev, youtube: "connected" }));
      toast({
        title: "Connection Successful",
        description: "YouTube API connection is working properly.",
      });
    }, 2000);
  };

  const handleBackupSettings = () => {
    const settings = {
      youtubeApiKey: "***", // Don't export sensitive data
      channelId,
      defaultTags,
      defaultCategory,
      autoProcessing,
      autoScheduling,
      qualityPreset,
      thumbnailStyle,
      emailNotifications,
      processingAlerts,
      uploadAlerts,
      errorAlerts,
      scrapingInterval,
      maxRetries,
      storageLimit
    };
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '404-circus-settings.json';
    a.click();
    
    toast({
      title: "Settings Exported",
      description: "Configuration has been downloaded as JSON file.",
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="w-4 h-4 text-success" />;
      case "testing":
        return <TestTube className="w-4 h-4 text-warning animate-pulse" />;
      case "error":
        return <XCircle className="w-4 h-4 text-destructive" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "connected":
        return "Connected";
      case "testing":
        return "Testing...";
      case "error":
        return "Connection Error";
      default:
        return "Disconnected";
    }
  };

  return (
    <div data-testid="settings-page">
      <Header 
        title="Settings" 
        subtitle="Configure your 404 Circus automation system"
      />
      
      <div className="p-6 space-y-6">
        {/* System Status */}
        <Card className="neon-border border-primary/30" data-testid="system-status">
          <CardHeader className="border-b border-border">
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-primary" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <Youtube className="w-5 h-5 text-destructive" />
                  <span className="font-medium">YouTube API</span>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(connectionStatus.youtube)}
                  <span className="text-sm">{getStatusText(connectionStatus.youtube)}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-accent" />
                  <span className="font-medium">Database</span>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(connectionStatus.database)}
                  <span className="text-sm">{getStatusText(connectionStatus.database)}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <TestTube className="w-5 h-5 text-warning" />
                  <span className="font-medium">Python Scripts</span>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(connectionStatus.python)}
                  <span className="text-sm">{getStatusText(connectionStatus.python)}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5 text-primary" />
                  <span className="font-medium">FFmpeg</span>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(connectionStatus.ffmpeg)}
                  <span className="text-sm">{getStatusText(connectionStatus.ffmpeg)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Settings Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* YouTube Settings */}
          <Card className="neon-border" data-testid="youtube-settings">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <Youtube className="w-5 h-5 text-destructive" />
                YouTube Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div>
                <Label htmlFor="youtube-api-key">YouTube API Key</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="youtube-api-key"
                    type="password"
                    value={youtubeApiKey}
                    onChange={(e) => setYoutubeApiKey(e.target.value)}
                    placeholder="Enter your YouTube Data API key"
                    data-testid="input-youtube-api-key"
                  />
                  <Button
                    variant="outline"
                    onClick={handleTestYouTubeConnection}
                    disabled={!youtubeApiKey || connectionStatus.youtube === "testing"}
                    data-testid="button-test-youtube"
                  >
                    <TestTube className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div>
                <Label htmlFor="channel-id">Channel ID</Label>
                <Input
                  id="channel-id"
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  placeholder="Your YouTube channel ID"
                  className="mt-1"
                  data-testid="input-channel-id"
                />
              </div>

              <div>
                <Label htmlFor="default-tags">Default Tags</Label>
                <Input
                  id="default-tags"
                  value={defaultTags}
                  onChange={(e) => setDefaultTags(e.target.value)}
                  placeholder="Comma-separated tags"
                  className="mt-1"
                  data-testid="input-default-tags"
                />
              </div>

              <div>
                <Label htmlFor="default-category">Default Category</Label>
                <Input
                  id="default-category"
                  value={defaultCategory}
                  onChange={(e) => setDefaultCategory(e.target.value)}
                  placeholder="YouTube category ID"
                  className="mt-1"
                  data-testid="input-default-category"
                />
              </div>
            </CardContent>
          </Card>

          {/* Content Processing */}
          <Card className="neon-border" data-testid="processing-settings">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <SettingsIcon className="w-5 h-5 text-accent" />
                Content Processing
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto Processing</Label>
                  <p className="text-xs text-muted-foreground">Automatically process new content</p>
                </div>
                <Switch
                  checked={autoProcessing}
                  onCheckedChange={setAutoProcessing}
                  data-testid="switch-auto-processing"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto Scheduling</Label>
                  <p className="text-xs text-muted-foreground">Schedule uploads automatically</p>
                </div>
                <Switch
                  checked={autoScheduling}
                  onCheckedChange={setAutoScheduling}
                  data-testid="switch-auto-scheduling"
                />
              </div>

              <div>
                <Label htmlFor="quality-preset">Video Quality</Label>
                <select
                  id="quality-preset"
                  value={qualityPreset}
                  onChange={(e) => setQualityPreset(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-input border border-border rounded-md"
                  data-testid="select-quality-preset"
                >
                  <option value="low">Low (720p)</option>
                  <option value="medium">Medium (1080p)</option>
                  <option value="high">High (1440p)</option>
                  <option value="ultra">Ultra (4K)</option>
                </select>
              </div>

              <div>
                <Label htmlFor="thumbnail-style">Thumbnail Style</Label>
                <select
                  id="thumbnail-style"
                  value={thumbnailStyle}
                  onChange={(e) => setThumbnailStyle(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-input border border-border rounded-md"
                  data-testid="select-thumbnail-style"
                >
                  <option value="glitch">Glitch Effect</option>
                  <option value="neon">Neon Glow</option>
                  <option value="error">Error Theme</option>
                  <option value="matrix">Matrix Style</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card className="neon-border" data-testid="notification-settings">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-warning" />
                Notifications
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Email Notifications</Label>
                  <p className="text-xs text-muted-foreground">Receive email updates</p>
                </div>
                <Switch
                  checked={emailNotifications}
                  onCheckedChange={setEmailNotifications}
                  data-testid="switch-email-notifications"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Processing Alerts</Label>
                  <p className="text-xs text-muted-foreground">Notify when processing completes</p>
                </div>
                <Switch
                  checked={processingAlerts}
                  onCheckedChange={setProcessingAlerts}
                  data-testid="switch-processing-alerts"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Upload Alerts</Label>
                  <p className="text-xs text-muted-foreground">Notify on successful uploads</p>
                </div>
                <Switch
                  checked={uploadAlerts}
                  onCheckedChange={setUploadAlerts}
                  data-testid="switch-upload-alerts"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Error Alerts</Label>
                  <p className="text-xs text-muted-foreground">Immediate error notifications</p>
                </div>
                <Switch
                  checked={errorAlerts}
                  onCheckedChange={setErrorAlerts}
                  data-testid="switch-error-alerts"
                />
              </div>
            </CardContent>
          </Card>

          {/* System Configuration */}
          <Card className="neon-border" data-testid="system-configuration">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-success" />
                System Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div>
                <Label htmlFor="scraping-interval">Content Scraping Interval (minutes)</Label>
                <Input
                  id="scraping-interval"
                  type="number"
                  value={scrapingInterval}
                  onChange={(e) => setScrapingInterval(e.target.value)}
                  min="1"
                  max="1440"
                  className="mt-1"
                  data-testid="input-scraping-interval"
                />
              </div>

              <div>
                <Label htmlFor="max-retries">Max Upload Retries</Label>
                <Input
                  id="max-retries"
                  type="number"
                  value={maxRetries}
                  onChange={(e) => setMaxRetries(e.target.value)}
                  min="1"
                  max="10"
                  className="mt-1"
                  data-testid="input-max-retries"
                />
              </div>

              <div>
                <Label htmlFor="storage-limit">Storage Limit (GB)</Label>
                <Input
                  id="storage-limit"
                  type="number"
                  value={storageLimit}
                  onChange={(e) => setStorageLimit(e.target.value)}
                  min="10"
                  max="1000"
                  className="mt-1"
                  data-testid="input-storage-limit"
                />
              </div>

              <div className="pt-2">
                <Badge variant="outline" className="text-xs">
                  Current usage: 23.4 GB / {storageLimit} GB
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <Card className="neon-border" data-testid="settings-actions">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row gap-4 justify-between">
              <div className="flex gap-2">
                <Button
                  className="bg-primary text-primary-foreground hover:bg-primary/80 neon-glow"
                  onClick={handleSaveSettings}
                  data-testid="button-save-settings"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save Settings
                </Button>
                
                <Button
                  variant="outline"
                  onClick={handleBackupSettings}
                  data-testid="button-backup-settings"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export Settings
                </Button>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="border-warning text-warning hover:bg-warning hover:text-background"
                  data-testid="button-reset-settings"
                >
                  Reset to Defaults
                </Button>
                
                <Button
                  variant="outline"
                  className="border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground"
                  data-testid="button-clear-cache"
                >
                  Clear Cache
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Warning Notice */}
        <Card className="border-warning/50 bg-warning/5" data-testid="warning-notice">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-warning mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-warning mb-1">Important Security Notice</h4>
                <p className="text-sm text-muted-foreground">
                  Keep your API keys secure and never share them publicly. 
                  Enable two-factor authentication on all connected accounts for maximum security.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

import { useState } from "react";
import Header from "@/components/header";
import ContentItem from "@/components/content-item";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useContentSources, useTrendingContent, useScrapeContent } from "@/hooks/use-content-research";
import { useCreateProject } from "@/hooks/use-projects";
import { useToast } from "@/hooks/use-toast";
import { Search, RefreshCw, Filter, TrendingUp, Clock, ExternalLink } from "lucide-react";

export default function ContentResearch() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const { toast } = useToast();
  
  const { data: contentSources, isLoading: sourcesLoading, refetch: refetchSources } = useContentSources(50);
  const { data: trendingContent, isLoading: trendingLoading, refetch: refetchTrending } = useTrendingContent(20);
  const scrapeContent = useScrapeContent();
  const createProject = useCreateProject();

  const handleScrapeContent = () => {
    scrapeContent.mutate(undefined, {
      onSuccess: () => {
        toast({
          title: "Content Scraping Started",
          description: "New content will be available shortly.",
        });
      },
      onError: () => {
        toast({
          title: "Error",
          description: "Failed to start content scraping.",
          variant: "destructive",
        });
      }
    });
  };

  const handleRefresh = () => {
    refetchSources();
    refetchTrending();
    toast({
      title: "Content Refreshed",
      description: "Research data has been updated.",
    });
  };

  const handleAddToQueue = (content: any) => {
    createProject.mutate({
      title: `404 Circus: ${content.title.slice(0, 50)}...`,
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
      },
      onError: () => {
        toast({
          title: "Error",
          description: "Failed to add content to queue.",
          variant: "destructive",
        });
      }
    });
  };

  const handleViewSource = (content: any) => {
    window.open(content.url, '_blank');
  };

  const filteredContent = contentSources?.filter(content => {
    const matchesSearch = content.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         content.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (selectedFilter === "all") return matchesSearch;
    if (selectedFilter === "unprocessed") return matchesSearch && !content.isProcessed;
    if (selectedFilter === "high-potential") return matchesSearch && (content.trendingScore || 0) >= 70;
    return matchesSearch;
  });

  const filters = [
    { id: "all", label: "All Content", count: contentSources?.length || 0 },
    { id: "unprocessed", label: "Unprocessed", count: contentSources?.filter(c => !c.isProcessed).length || 0 },
    { id: "high-potential", label: "High Potential", count: contentSources?.filter(c => (c.trendingScore || 0) >= 70).length || 0 },
  ];

  return (
    <div data-testid="content-research-page">
      <Header 
        title="Content Research" 
        subtitle="Discover and analyze trending tech fails for your next viral video"
      />
      
      <div className="p-6 space-y-6">
        {/* Search and Controls */}
        <Card className="neon-border" data-testid="search-controls">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <div className="flex-1 flex gap-4 items-center">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    placeholder="Search content..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                    data-testid="input-search"
                  />
                </div>
                
                <div className="flex gap-2">
                  {filters.map(filter => (
                    <Badge
                      key={filter.id}
                      variant={selectedFilter === filter.id ? "default" : "outline"}
                      className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                      onClick={() => setSelectedFilter(filter.id)}
                      data-testid={`filter-${filter.id}`}
                    >
                      {filter.label} ({filter.count})
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleRefresh}
                  disabled={sourcesLoading || trendingLoading}
                  data-testid="button-refresh"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${(sourcesLoading || trendingLoading) ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                
                <Button
                  className="bg-primary text-primary-foreground hover:bg-primary/80"
                  onClick={handleScrapeContent}
                  disabled={scrapeContent.isPending}
                  data-testid="button-scrape"
                >
                  <TrendingUp className={`w-4 h-4 mr-2 ${scrapeContent.isPending ? 'animate-pulse' : ''}`} />
                  Scrape New Content
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Trending Section */}
        <Card className="neon-border" data-testid="trending-section">
          <CardHeader className="border-b border-border">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                Trending Now
              </CardTitle>
              <Badge className="bg-success/20 text-success">
                Live Updates
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Hot content with viral potential
            </p>
          </CardHeader>
          <CardContent className="p-6">
            {trendingLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-start space-x-4 p-3">
                      <div className="w-16 h-12 bg-muted rounded"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-muted rounded w-3/4"></div>
                        <div className="h-3 bg-muted rounded w-1/2"></div>
                        <div className="flex gap-2">
                          <div className="h-5 w-16 bg-muted rounded"></div>
                          <div className="h-5 w-12 bg-muted rounded"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trendingContent?.map((content) => (
                  <ContentItem
                    key={content.id}
                    content={content}
                    onAddToQueue={handleAddToQueue}
                    onViewSource={handleViewSource}
                  />
                ))}
                {!trendingContent?.length && (
                  <div className="col-span-full text-center text-muted-foreground py-12" data-testid="no-trending">
                    <TrendingUp className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                    <h3 className="text-lg font-medium mb-2">No Trending Content</h3>
                    <p>Try scraping for new content or check back later.</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* All Content */}
        <Card className="neon-border" data-testid="all-content-section">
          <CardHeader className="border-b border-border">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-accent" />
                Research Archive
              </CardTitle>
              <Badge variant="outline">
                {filteredContent?.length || 0} items
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Complete database of discovered content
            </p>
          </CardHeader>
          <CardContent className="p-6">
            {sourcesLoading ? (
              <div className="space-y-4">
                {[...Array(10)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-start space-x-4 p-3">
                      <div className="w-16 h-12 bg-muted rounded"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-muted rounded w-3/4"></div>
                        <div className="h-3 bg-muted rounded w-1/2"></div>
                        <div className="flex gap-2">
                          <div className="h-5 w-20 bg-muted rounded"></div>
                          <div className="h-5 w-16 bg-muted rounded"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredContent?.map((content) => (
                  <ContentItem
                    key={content.id}
                    content={content}
                    onAddToQueue={handleAddToQueue}
                    onViewSource={handleViewSource}
                  />
                ))}
                {!filteredContent?.length && (
                  <div className="text-center text-muted-foreground py-12" data-testid="no-content">
                    <Search className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                    <h3 className="text-lg font-medium mb-2">No Content Found</h3>
                    <p>Try adjusting your search or filter criteria.</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

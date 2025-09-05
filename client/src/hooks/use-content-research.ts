import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ContentSource, InsertContentSource } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";

export function useContentSources(limit?: number) {
  return useQuery<ContentSource[]>({
    queryKey: ["/api/content-sources", { limit }],
  });
}

export function useTrendingContent(limit?: number) {
  return useQuery<ContentSource[]>({
    queryKey: ["/api/content-sources/trending", { limit }],
  });
}

export function useCreateContentSource() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (source: InsertContentSource): Promise<ContentSource> => {
      const response = await apiRequest("POST", "/api/content-sources", source);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/content-sources"] });
      queryClient.invalidateQueries({ queryKey: ["/api/content-sources/trending"] });
    },
  });
}

export function useScrapeContent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (): Promise<{ message: string }> => {
      const response = await apiRequest("POST", "/api/content-sources/scrape");
      return response.json();
    },
    onSuccess: () => {
      // Refetch content after scraping
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["/api/content-sources"] });
        queryClient.invalidateQueries({ queryKey: ["/api/content-sources/trending"] });
      }, 5000); // Wait 5 seconds for scraping to complete
    },
  });
}

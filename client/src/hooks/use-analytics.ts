import { useQuery } from "@tanstack/react-query";
import { Analytics } from "@shared/schema";

export function useChannelAnalytics(startDate?: Date, endDate?: Date) {
  return useQuery<Analytics[]>({
    queryKey: ["/api/analytics/channel", { startDate: startDate?.toISOString(), endDate: endDate?.toISOString() }],
  });
}

export function useProjectAnalytics(projectId: string) {
  return useQuery<Analytics[]>({
    queryKey: ["/api/analytics/projects", projectId],
    enabled: !!projectId,
  });
}

export function useSystemStatus() {
  return useQuery({
    queryKey: ["/api/system-status"],
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

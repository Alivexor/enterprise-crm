import { apiClient } from "@/services/api-client";
import type { AnalyticsData, DashboardData, OperationalHealth } from "@/types/dashboard";

export const dashboardService = {
  getOperationalHealth(): Promise<OperationalHealth> {
    return apiClient.get<OperationalHealth>("/dashboard/health", { cache: "no-store" });
  },
  getAnalytics(): Promise<AnalyticsData> {
    return apiClient.get<AnalyticsData>("/dashboard/analytics", { cache: "no-store" });
  },
  getDashboard(): Promise<DashboardData> {
    return apiClient.get<DashboardData>("/dashboard", { cache: "no-store" });
  },
};

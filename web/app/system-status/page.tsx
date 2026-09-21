import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("System Status", "Sentinel system status");

export default async function SystemStatusPage() {
  return <DashboardPageView initialPage="admin" />;
}

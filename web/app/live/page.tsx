import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("Live Monitor", "Sentinel live session monitoring");

export default async function LivePage() {
  return <DashboardPageView initialPage="live" />;
}

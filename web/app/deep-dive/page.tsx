import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("Game Deep Dive", "Sentinel analysis detail workspace");

export default async function DeepDivePage() {
  return <DashboardPageView initialPage="deep-dive" />;
}

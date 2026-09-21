import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("Tournament Dashboard", "Sentinel tournament view");

export default async function TournamentPage() {
  return <DashboardPageView initialPage="tournament" />;
}

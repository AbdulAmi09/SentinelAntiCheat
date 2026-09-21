import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("Player Profile", "Sentinel player profile and history");

export default async function PlayerPage() {
  return <DashboardPageView initialPage="player" />;
}

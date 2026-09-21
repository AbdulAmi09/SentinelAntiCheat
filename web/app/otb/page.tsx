import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("OTB Monitor", "Sentinel OTB board and camera monitor");

export default async function OtbPage() {
  return <DashboardPageView initialPage="otb" />;
}

import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("Cases", "Sentinel case management");

export default async function CasesPage() {
  return <DashboardPageView initialPage="cases" />;
}

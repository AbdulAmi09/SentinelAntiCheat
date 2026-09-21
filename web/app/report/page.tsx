import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("Report Composer", "Sentinel report generation");

export default async function ReportPage() {
  return <DashboardPageView initialPage="report" />;
}

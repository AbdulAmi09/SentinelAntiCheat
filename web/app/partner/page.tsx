import { DashboardPageView, buildDashboardMetadata } from "../../lib/dashboard-page";

export const metadata = buildDashboardMetadata("Partner API", "Sentinel partner key management");

export default async function PartnerPage() {
  return <DashboardPageView initialPage="partner" />;
}

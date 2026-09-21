import { DashboardPageView, buildDashboardMetadata } from "../lib/dashboard-page";

export const metadata = buildDashboardMetadata(
  "Arbiter Dashboard",
  "Sentinel monitoring and arbitration interface",
);

export const revalidate = 30;

function getEnvConfig() {
  const apiBase =
    process.env.NEXT_PUBLIC_SENTINEL_API?.replace(/\/$/, "") ??
    "http://localhost:8000";
  const apiRole = process.env.NEXT_PUBLIC_SENTINEL_ROLE?.trim() || "system_admin";
  const apiFederationId = process.env.NEXT_PUBLIC_FEDERATION_ID?.trim() || "";

  const supabaseReady = Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  );

  const missingEnvVars: string[] = [];
  if (!process.env.NEXT_PUBLIC_SENTINEL_API) missingEnvVars.push("NEXT_PUBLIC_SENTINEL_API");
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) missingEnvVars.push("NEXT_PUBLIC_SUPABASE_URL");
  if (!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) missingEnvVars.push("NEXT_PUBLIC_SUPABASE_ANON_KEY");

  return { apiBase, apiRole, apiFederationId, supabaseReady, missingEnvVars };
}

export default async function HomePage() {
  return <DashboardPageView initialPage="command" />;
}

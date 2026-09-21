import "./globals.css";
import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, JetBrains_Mono, Space_Grotesk } from "next/font/google";

// ─── Fonts ────────────────────────────────────────────────────────────────────

const headingFont = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-heading",
  display: "swap",
  preload: true,
});

const bodyFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
  preload: true,
});

const dataFont = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-data",
  display: "swap",
  preload: false, // Secondary font — load lazily
});

// ─── Metadata ─────────────────────────────────────────────────────────────────

export const metadata: Metadata = {
  title: {
    default: "Sentinel — Chess Integrity",
    template: "%s | Sentinel",
  },
  description:
    "Real-time chess integrity risk assessment and anti-cheat dashboard powered by statistical analysis.",
  keywords: ["chess", "anti-cheat", "integrity", "risk assessment", "arbiter"],
  authors: [{ name: "Sentinel" }],
  robots: { index: false, follow: false }, // Internal tool — keep out of search engines
  openGraph: {
    title: "Sentinel Anti-Cheat",
    description: "Chess integrity risk assessment dashboard",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0f" },
  ],
  width: "device-width",
  initialScale: 1,
};

// ─── Layout ───────────────────────────────────────────────────────────────────

const fontVariables = [
  headingFont.variable,
  bodyFont.variable,
  dataFont.variable,
].join(" ");

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={fontVariables}>
        {children}
      </body>
    </html>
  );
}

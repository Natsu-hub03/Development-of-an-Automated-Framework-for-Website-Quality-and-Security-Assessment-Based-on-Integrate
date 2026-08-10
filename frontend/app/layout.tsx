import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WebScan — AI-Assisted Web Standards & Vulnerability Scanner",
  description:
    "Scan and analyze web technologies, security vulnerabilities, and standards compliance quickly and accurately.",
  keywords: ["web scanner", "wappalyzer", "ZAP", "web standards", "security", "vulnerability", "WCAG"],
  authors: [{ name: "WebScan Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        {/* Syne (display) + IBM Plex Sans (body) + IBM Plex Mono (mono/terminal) */}
        <link
          href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {/* interface-kit: skip link — first focusable element */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}

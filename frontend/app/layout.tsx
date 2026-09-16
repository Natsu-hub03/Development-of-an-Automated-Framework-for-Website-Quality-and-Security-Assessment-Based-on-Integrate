import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WebScan — Automated Web Standards & Vulnerability Scanner",
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
    <html lang="th" suppressHydrationWarning>
      <head>
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

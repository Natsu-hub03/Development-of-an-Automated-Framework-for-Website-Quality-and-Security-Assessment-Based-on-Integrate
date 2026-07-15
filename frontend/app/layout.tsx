import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WebScan — เครื่องมือวิเคราะห์มาตรฐานเว็บไซต์",
  description:
    "สแกนและวิเคราะห์เทคโนโลยี ความปลอดภัย และมาตรฐานเว็บไซต์ของคุณอย่างรวดเร็วและแม่นยำ",
  keywords: ["web scanner", "wappalyzer", "web standards", "security", "vulnerability"],
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
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}

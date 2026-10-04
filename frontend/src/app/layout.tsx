import type { Metadata, Viewport } from "next";
import { Noto_Sans, Outfit } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { AuthProvider } from "@/context/AuthContext";
import { PwaProvider } from "@/components/pwa/PwaProvider";
import AuthGuard from "@/components/auth/AuthGuard";

const notoSans = Noto_Sans({
  subsets: ["latin", "devanagari"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  variable: "--font-noto-sans",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-numbers",
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#ffffff",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};

export const metadata: Metadata = {
  title: "AirIndex India — Real-Time Indian Airfare Price Index",
  description:
    "High-frequency domestic airfare inflation monitoring platform under Ministry of Statistics and Programme Implementation (MoSPI) / NSO CPI methodology.",
  applicationName: "AirIndex India",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "AirIndex",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/icon-192x192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512x512.png", sizes: "512x512", type: "image/png" },
    ],
    shortcut: "/favicon.ico",
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`h-full antialiased ${notoSans.variable} ${outfit.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col font-sans app-bg-primary app-text-primary transition-colors duration-200 selection:bg-[var(--color-gold-bg)] selection:text-[var(--color-gold)]">
        <AuthProvider>
          <PwaProvider>
            <Navbar />
            <AuthGuard>
              <main className="flex-1">{children}</main>
              <Footer />
            </AuthGuard>
          </PwaProvider>
        </AuthProvider>
      </body>
    </html>
  );
}


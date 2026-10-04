import type { NextConfig } from "next";

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  devIndicators: false,
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: `${BACKEND_URL}/auth/:path*`,
      },
      {
        source: "/index/:path*",
        destination: `${BACKEND_URL}/index/:path*`,
      },
      {
        source: "/audit/:path*",
        destination: `${BACKEND_URL}/audit/:path*`,
      },
      {
        source: "/validation/:path*",
        destination: `${BACKEND_URL}/validation/:path*`,
      },
      {
        source: "/export",
        destination: `${BACKEND_URL}/export`,
      },
      {
        source: "/harvest/:path*",
        destination: `${BACKEND_URL}/harvest/:path*`,
      },
    ];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    // In production (Vercel), api.ts uses NEXT_PUBLIC_API_URL directly — no proxy needed.
    // In development, proxy /api/* to the local backend so cookies/auth headers work cross-origin.
    if (process.env.NODE_ENV === "production") return [];
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

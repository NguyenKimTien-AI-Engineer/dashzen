import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig: NextConfig = {
  // Runtime proxy: pages/api/[...path].ts. Rewrites are a build-time fallback for local parity.
  async rewrites() {
    const backend = process.env.API_BACKEND_URL?.replace(/\/$/, "");
    if (!backend) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);

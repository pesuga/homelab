import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  /* config options here */
  eslint: {
    // Disable ESLint during builds (treat warnings as warnings, not errors)
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Disable TypeScript errors during builds (if needed)
    ignoreBuildErrors: false,
  },
  webpack(config) {
    config.module.rules.push({
      test: /\.svg$/,
      use: ["@svgr/webpack"],
    });
    return config;
  },
};

export default nextConfig;

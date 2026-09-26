import type { NextConfig } from "next";

const backendApiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "https://plant-disease-api-1-0-0.onrender.com").replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    useTypeScriptCli: false,
  },
  async rewrites() {
    return [
      {
        source: "/plant-api/:path*",
        destination: `${backendApiUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

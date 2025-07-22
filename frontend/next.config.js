/** @type {import('next').NextConfig} */
const nextConfig = {
  // Edge Runtime compatible configuration
  trailingSlash: true,
  
  // Environment variables for Edge Runtime
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Edge Runtime optimizations
  images: {
    unoptimized: true,
  },
  
  // WebPack configuration for Edge Runtime compatibility
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Client-side polyfills for Edge Runtime
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
}

module.exports = nextConfig
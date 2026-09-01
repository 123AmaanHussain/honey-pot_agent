/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {}, // Empty config to use Turbopack with default settings
  allowedDevOrigins: ['192.168.118.1'], // Allow network access for HMR
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

export default nextConfig;

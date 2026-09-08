import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // This repository keeps its own docs; no generated agent rule files.
  agentRules: false,
};

export default nextConfig;

import type { NextConfig } from 'next';
const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const servicesMode = process.env.PG_VERCEL_SERVICES === '1';
if (process.env.VERCEL && !servicesMode) {
  if (!process.env.BACKEND_URL) {
    throw new Error('Set BACKEND_URL to the hosted Python backend HTTPS URL before deploying to Vercel.');
  }
  const url = new URL(backend);
  if (url.protocol !== 'https:' || ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) {
    throw new Error('Vercel requires a reachable HTTPS BACKEND_URL, not a localhost address.');
  }
}
const config:NextConfig = {
  output:'standalone',
  async rewrites(){return servicesMode ? [] : [{source:'/api/:path*',destination:`${backend.replace(/\/$/, '')}/api/:path*`}];}
};
export default config;

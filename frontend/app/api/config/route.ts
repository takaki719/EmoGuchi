import { NextResponse } from 'next/server';
import { getApiUrl } from '@/utils/api';

// Edge Runtime対応
export const runtime = 'edge';

export async function GET() {
  const backendUrl = getApiUrl();
  
  return NextResponse.json({
    backendUrl,
    frontendVersion: process.env.npm_package_version || '0.1.0',
    environment: process.env.NODE_ENV || 'development'
  });
}
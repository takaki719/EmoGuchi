import { NextResponse } from 'next/server';

// Edge Runtime対応
export const runtime = 'edge';

export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  return NextResponse.json({
    backendUrl,
    frontendVersion: process.env.npm_package_version || '0.1.0',
    environment: process.env.NODE_ENV || 'development'
  });
}
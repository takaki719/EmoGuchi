import { NextResponse } from 'next/server';

// Edge Runtime対応
export const runtime = 'edge';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    runtime: 'edge'
  });
}
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    // 转发请求到后端热门文章API
    const response = await fetch(`${BACKEND_URL}/api/articles/hot_articles/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch hot articles');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching hot articles:', error);
    return NextResponse.json(
      { error: 'Failed to fetch hot articles' },
      { status: 500 }
    );
  }
}
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  try {
    // 获取认证头
    const authorization = request.headers.get('authorization')

    // 构建后端请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (authorization) {
      headers['Authorization'] = authorization
    }

    // 代理请求到后端
    const response = await fetch(`${BACKEND_URL}/articles/${id}/comments/`, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: `Backend request failed: ${response.status}` },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('API proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  try {
    const authorization = request.headers.get('authorization')
    const body = await request.json()

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (authorization) {
      headers['Authorization'] = authorization
    }

    const response = await fetch(`${BACKEND_URL}/articles/${id}/comments/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.detail || `Backend request failed: ${response.status}` },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('API proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

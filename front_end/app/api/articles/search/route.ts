import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export async function GET(request: NextRequest) {
  try {
    // 获取搜索参数
    const { searchParams } = new URL(request.url)
    const query = searchParams.get('q')
    const type = searchParams.get('type') || 'all'
    const ordering = searchParams.get('ordering') || '-created_at'
    const page = searchParams.get('page') || '1'

    // 验证必需的搜索参数
    if (!query || query.trim().length === 0) {
      return NextResponse.json(
        { error: '搜索关键词不能为空' },
        { status: 400 }
      )
    }

    // 构建后端请求URL
    const backendSearchParams = new URLSearchParams({
      q: query.trim(),
      type,
      ordering,
      page
    })

    // 获取认证头
    const authorization = request.headers.get('authorization')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (authorization) {
      headers['Authorization'] = authorization
    }

    // 代理请求到后端搜索API
    const response = await fetch(`${BACKEND_URL}/articles/search/?${backendSearchParams.toString()}`, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.error || `搜索请求失败: ${response.status}` },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('搜索API代理错误:', error)
    return NextResponse.json(
      { error: '搜索服务暂时不可用' },
      { status: 500 }
    )
  }
}

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; commentId: string }> }
) {
  const { id, commentId } = await params
  try {
    const authorization = request.headers.get('authorization')

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (authorization) {
      headers['Authorization'] = authorization
    }

    console.log(`删除评论API代理: DELETE ${BACKEND_URL}/articles/${id}/comments/${commentId}/`)
    const response = await fetch(`${BACKEND_URL}/articles/${id}/comments/${commentId}/`, {
      method: 'DELETE',
      headers,
    })
    console.log(`后端响应状态: ${response.status} ${response.statusText}`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.detail || `Backend request failed: ${response.status}` },
        { status: response.status }
      )
    }

    // 对于DELETE操作，后端通常返回204 No Content，没有响应体
    // 直接返回成功状态
    return NextResponse.json({ success: true }, { status: 200 })
  } catch (error) {
    console.error('API proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

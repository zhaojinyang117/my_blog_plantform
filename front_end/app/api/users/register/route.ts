import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/users/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.log('Backend error response:', errorData)

      // 处理Django REST Framework的错误格式
      let errorMessage = 'Registration failed'
      if (errorData.detail) {
        errorMessage = errorData.detail
      } else if (errorData.non_field_errors) {
        errorMessage = errorData.non_field_errors.join(', ')
      } else if (typeof errorData === 'object') {
        // 处理字段级错误
        const fieldErrors = Object.entries(errorData)
          .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
          .join('; ')
        if (fieldErrors) {
          errorMessage = fieldErrors
        }
      }

      return NextResponse.json(
        { error: errorMessage },
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

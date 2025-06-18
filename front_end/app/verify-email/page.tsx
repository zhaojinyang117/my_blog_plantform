"use client"

import { useState, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { CheckCircle, XCircle, Loader2, Mail } from "lucide-react"

type VerificationStatus = 'loading' | 'success' | 'already_verified' | 'error'

export default function VerifyEmailPage() {
  const [status, setStatus] = useState<VerificationStatus>('loading')
  const [message, setMessage] = useState('')
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('缺少验证令牌')
      return
    }

    verifyEmail(token)
  }, [token])

  const verifyEmail = async (token: string) => {
    try {
      const response = await fetch(`/api/users/verify-email?token=${token}`)
      const data = await response.json()

      if (response.ok) {
        if (data.status === 'already_verified') {
          setStatus('already_verified')
          setMessage(data.message)
        } else {
          setStatus('success')
          setMessage(data.message)
        }
      } else {
        setStatus('error')
        setMessage(data.error || '验证失败')
      }
    } catch (error) {
      console.error('邮箱验证失败:', error)
      setStatus('error')
      setMessage('网络错误，请稍后再试')
    }
  }

  const handleGoToLogin = () => {
    router.push('/login?verified=true')
  }

  const handleGoHome = () => {
    router.push('/')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
              <Mail className="h-6 w-6 text-blue-600" />
            </div>
            <CardTitle className="text-2xl font-bold">邮箱验证</CardTitle>
            <CardDescription>
              正在验证您的邮箱地址...
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {status === 'loading' && (
              <div className="text-center">
                <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600" />
                <p className="mt-2 text-sm text-gray-600">正在验证中，请稍候...</p>
              </div>
            )}

            {status === 'success' && (
              <>
                <Alert className="border-green-200 bg-green-50">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertTitle className="text-green-800">验证成功！</AlertTitle>
                  <AlertDescription className="text-green-700">
                    {message}
                  </AlertDescription>
                </Alert>
                <div className="space-y-3">
                  <Button onClick={handleGoToLogin} className="w-full">
                    立即登录
                  </Button>
                  <Button variant="outline" onClick={handleGoHome} className="w-full">
                    返回首页
                  </Button>
                </div>
              </>
            )}

            {status === 'already_verified' && (
              <>
                <Alert className="border-blue-200 bg-blue-50">
                  <CheckCircle className="h-4 w-4 text-blue-600" />
                  <AlertTitle className="text-blue-800">邮箱已验证</AlertTitle>
                  <AlertDescription className="text-blue-700">
                    {message}
                  </AlertDescription>
                </Alert>
                <div className="space-y-3">
                  <Button onClick={handleGoToLogin} className="w-full">
                    前往登录
                  </Button>
                  <Button variant="outline" onClick={handleGoHome} className="w-full">
                    返回首页
                  </Button>
                </div>
              </>
            )}

            {status === 'error' && (
              <>
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertTitle>验证失败</AlertTitle>
                  <AlertDescription>
                    {message}
                  </AlertDescription>
                </Alert>
                <div className="space-y-3">
                  <Button variant="outline" onClick={handleGoHome} className="w-full">
                    返回首页
                  </Button>
                  <div className="text-center">
                    <p className="text-sm text-gray-600">
                      需要帮助？{' '}
                      <Link href="/register" className="text-blue-600 hover:text-blue-500">
                        重新注册
                      </Link>
                    </p>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

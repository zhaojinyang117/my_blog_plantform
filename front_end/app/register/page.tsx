"use client"

import { useState, type FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Terminal, Mail, CheckCircle } from "lucide-react"
import api from "@/lib/api"

export default function RegisterPage() {
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [registrationSuccess, setRegistrationSuccess] = useState(false)
  const [registeredEmail, setRegisteredEmail] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError("两次输入的密码不一致。")
      return
    }
    setError(null)
    setIsLoading(true)
    try {
      await api.register({ username, email, password })
      setRegisteredEmail(email)
      setRegistrationSuccess(true)
    } catch (err: any) {
      setError(err.message || "注册失败，请稍后再试。")
    } finally {
      setIsLoading(false)
    }
  }

  // 如果注册成功，显示邮箱验证提示
  if (registrationSuccess) {
    return (
      <div className="flex items-center justify-center py-12">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <CardTitle className="text-2xl text-green-800">注册成功！</CardTitle>
            <CardDescription>
              我们已向您的邮箱发送了验证邮件
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert className="border-blue-200 bg-blue-50">
              <Mail className="h-4 w-4 text-blue-600" />
              <AlertTitle className="text-blue-800">请验证您的邮箱</AlertTitle>
              <AlertDescription className="text-blue-700">
                我们已向 <strong>{registeredEmail}</strong> 发送了验证邮件。
                请检查您的邮箱（包括垃圾邮件文件夹）并点击验证链接以激活您的账户。
              </AlertDescription>
            </Alert>
            <div className="space-y-3">
              <Button
                onClick={() => router.push('/login')}
                className="w-full"
              >
                前往登录
              </Button>
              <Button
                variant="outline"
                onClick={() => setRegistrationSuccess(false)}
                className="w-full"
              >
                重新注册
              </Button>
            </div>
          </CardContent>
          <CardFooter className="text-sm text-center text-gray-600">
            <p>
              没有收到邮件？请检查垃圾邮件文件夹，或{' '}
              <Link href="/register" className="text-blue-600 hover:text-blue-500">
                重新注册
              </Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">创建新账户</CardTitle>
          <CardDescription>填写以下信息以完成注册。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <Terminal className="h-4 w-4" />
              <AlertTitle>注册错误</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                type="text"
                placeholder="请输入用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                type="email"
                placeholder="请输入您的邮箱"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                placeholder="请输入密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">确认密码</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "注册中..." : "注册"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="text-sm">
          已经有账户了?{" "}
          <Link href="/login" className="ml-1 font-semibold text-primary hover:underline">
            立即登录
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}

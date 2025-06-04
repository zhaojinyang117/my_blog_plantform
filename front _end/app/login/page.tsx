"use client"

import { useState, type FormEvent } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Terminal } from "lucide-react"

export default function LoginPage() {
  const [username, setUsername] = useState("") // 实际存储邮箱地址
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const registrationSuccess = searchParams.get("registrationSuccess")

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)
    try {
      await login({ username, password }) // username 字段实际包含邮箱地址
      router.push("/") // Redirect handled by AuthContext, this is a fallback
    } catch (err: any) {
      setError(err.message || "登录失败，请检查您的凭据。")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">登录您的账户</CardTitle>
          <CardDescription>输入您的邮箱和密码以继续。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {registrationSuccess && (
            <Alert variant="default" className="bg-green-50 border-green-200 text-green-700">
              <Terminal className="h-4 w-4 !text-green-700" />
              <AlertTitle>注册成功!</AlertTitle>
              <AlertDescription>您现在可以使用您的新账户登录了。</AlertDescription>
            </Alert>
          )}
          {error && (
            <Alert variant="destructive">
              <Terminal className="h-4 w-4" />
              <AlertTitle>登录错误</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">邮箱</Label>
              <Input
                id="username"
                type="email"
                placeholder="请输入您的邮箱地址"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                placeholder="请输入您的密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "登录中..." : "登录"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="text-sm">
          还没有账户?{" "}
          <Link href="/register" className="ml-1 font-semibold text-primary hover:underline">
            立即注册
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}

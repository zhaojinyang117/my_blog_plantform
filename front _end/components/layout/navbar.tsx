"use client"

import Link from "next/link"
import { useAuth } from "@/hooks/use-auth"
import { Button } from "@/components/ui/button"
import { LogIn, LogOut, UserIcon, Newspaper } from "lucide-react"
import { usePathname } from "next/navigation"

export default function Navbar() {
  const { isAuthenticated, user, logout, isLoading } = useAuth()
  const pathname = usePathname()

  const navLinkClasses = (path: string) =>
    `text-sm font-medium transition-colors hover:text-primary ${pathname === path ? "text-primary" : "text-muted-foreground"}`

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <Newspaper className="h-6 w-6" />
            <span className="font-bold">我的博客</span>
          </Link>
          <nav className="hidden md:flex items-center space-x-6">
            <Link href="/" className={navLinkClasses("/")}>
              首页
            </Link>
            {isAuthenticated && (
              <>
                <Link href="/create-article" className={navLinkClasses("/create-article")}>
                  写文章
                </Link>
                <Link href="/drafts" className={navLinkClasses("/drafts")}>
                  草稿箱
                </Link>
              </>
            )}
          </nav>
        </div>

        <div className="flex items-center space-x-3">
          {isLoading && !isAuthenticated ? (
            <div className="animate-pulse h-8 w-24 bg-muted rounded-md"></div>
          ) : isAuthenticated ? (
            <>
              <span className="text-sm text-muted-foreground hidden sm:inline">你好, {user?.username}</span>
              <Button variant="outline" size="sm" onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" /> 退出
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/login">
                  <LogIn className="mr-2 h-4 w-4" /> 登录
                </Link>
              </Button>
              <Button size="sm" asChild>
                <Link href="/register">
                  <UserIcon className="mr-2 h-4 w-4" /> 注册
                </Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

"use client"

import { useState } from "react"
import Link from "next/link"
import { useAuth } from "@/hooks/use-auth"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { LogIn, LogOut, UserIcon, Newspaper, AlertCircle, Menu, X } from "lucide-react"
import { usePathname } from "next/navigation"

export default function Navbar() {
  const { isAuthenticated, user, logout, isLoading } = useAuth()
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinkClasses = (path: string) =>
    `text-sm font-medium transition-colors hover:text-primary ${pathname === path ? "text-primary" : "text-muted-foreground"}`

  const mobileNavLinkClasses = (path: string) =>
    `block px-3 py-2 text-base font-medium transition-colors hover:text-primary hover:bg-accent rounded-md ${pathname === path ? "text-primary bg-accent" : "text-muted-foreground"}`

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* 左侧品牌和导航 */}
          <div className="flex items-center flex-1">
            <Link href="/" className="mr-6 flex items-center space-x-2 flex-shrink-0">
              <Newspaper className="h-6 w-6" />
              <span className="font-bold text-lg">我的博客</span>
            </Link>
            <nav className="hidden md:flex items-center space-x-6 lg:space-x-8">
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
                  <Link href="/profile" className={navLinkClasses("/profile")}>
                    个人中心
                  </Link>
                </>
              )}
            </nav>
          </div>

          {/* 右侧用户操作区域 */}
          <div className="flex items-center space-x-3 sm:space-x-4 lg:space-x-6 ml-4 sm:ml-6 lg:ml-8">
            {/* 桌面端用户信息和按钮 */}
            <div className="hidden sm:flex items-center space-x-3 lg:space-x-4">
              {isLoading && !isAuthenticated ? (
                <div className="animate-pulse h-8 w-24 bg-muted rounded-md"></div>
              ) : isAuthenticated ? (
                <>
                  <div className="flex items-center space-x-2 lg:space-x-3">
                    <span className="text-sm text-muted-foreground lg:text-base">
                      你好, {user?.username}
                    </span>
                    {user && !user.is_active && (
                      <div className="flex items-center text-orange-600">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        <span className="text-xs hidden lg:inline">未激活</span>
                      </div>
                    )}
                  </div>
                  <Button variant="outline" size="sm" onClick={logout} className="lg:size-default">
                    <LogOut className="mr-2 h-4 w-4" />
                    退出
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="ghost" size="sm" asChild className="lg:size-default">
                    <Link href="/login">
                      <LogIn className="mr-2 h-4 w-4" />
                      登录
                    </Link>
                  </Button>
                  <Button size="sm" asChild className="lg:size-default">
                    <Link href="/register">
                      <UserIcon className="mr-2 h-4 w-4" />
                      注册
                    </Link>
                  </Button>
                </>
              )}
            </div>

            {/* 移动端菜单按钮 */}
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="sm" className="sm:hidden">
                  <Menu className="h-5 w-5" />
                  <span className="sr-only">打开菜单</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[300px] sm:hidden">
                <div className="flex flex-col space-y-4 mt-6">
                  {/* 移动端导航链接 */}
                  <nav className="flex flex-col space-y-2">
                    <Link
                      href="/"
                      className={mobileNavLinkClasses("/")}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      首页
                    </Link>
                    {isAuthenticated && (
                      <>
                        <Link
                          href="/create-article"
                          className={mobileNavLinkClasses("/create-article")}
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          写文章
                        </Link>
                        <Link
                          href="/drafts"
                          className={mobileNavLinkClasses("/drafts")}
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          草稿箱
                        </Link>
                        <Link
                          href="/profile"
                          className={mobileNavLinkClasses("/profile")}
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          个人中心
                        </Link>
                      </>
                    )}
                  </nav>

                  {/* 移动端用户操作 */}
                  <div className="border-t pt-4">
                    {isLoading && !isAuthenticated ? (
                      <div className="animate-pulse h-8 w-full bg-muted rounded-md"></div>
                    ) : isAuthenticated ? (
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2 px-3 py-2 bg-accent rounded-md">
                          <span className="text-sm text-muted-foreground">
                            你好, {user?.username}
                          </span>
                          {user && !user.is_active && (
                            <div className="flex items-center text-orange-600">
                              <AlertCircle className="h-4 w-4 mr-1" />
                              <span className="text-xs">未激活</span>
                            </div>
                          )}
                        </div>
                        <Button
                          variant="outline"
                          className="w-full"
                          onClick={() => {
                            logout()
                            setMobileMenuOpen(false)
                          }}
                        >
                          <LogOut className="mr-2 h-4 w-4" />
                          退出登录
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Button variant="ghost" asChild className="w-full justify-start">
                          <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                            <LogIn className="mr-2 h-4 w-4" />
                            登录
                          </Link>
                        </Button>
                        <Button asChild className="w-full justify-start">
                          <Link href="/register" onClick={() => setMobileMenuOpen(false)}>
                            <UserIcon className="mr-2 h-4 w-4" />
                            注册
                          </Link>
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  )
}

import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import Navbar from "@/components/layout/navbar"
import Footer from "@/components/layout/footer"
import { AuthProvider } from "@/contexts/auth-context"
import { Toaster } from "@/components/ui/toaster" // For showing notifications

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "我的博客",
  description: "一个使用 Next.js 和 Django 构建的博客平台",
  generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="zh-CN">
      <body className={`${inter.className} flex flex-col min-h-screen`} suppressHydrationWarning={true}>
        <AuthProvider>
          <Navbar />
          <main className="flex-grow container mx-auto px-4 py-8">{children}</main>
          <Footer />
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  )
}

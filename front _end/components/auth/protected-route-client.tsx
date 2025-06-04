"use client"
// This is a client component wrapper for pages that need auth
import type React from "react"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"
import { Loader2 } from "lucide-react"

interface ProtectedRouteClientProps {
  children: React.ReactNode
}

export default function ProtectedRouteClient({ children }: ProtectedRouteClientProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login?redirect=" + encodeURIComponent(window.location.pathname))
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-200px)]">
        {" "}
        {/* Adjust height as needed */}
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="ml-4 text-lg">加载中，请稍候...</p>
      </div>
    )
  }

  return <>{children}</>
}

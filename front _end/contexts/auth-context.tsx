"use client"

import React, { createContext, useState, useEffect, useCallback, useMemo } from "react"
import { useRouter } from "next/navigation"
import api from "@/lib/api"
import type { User, LoginCredentials, RegisterData, AuthContextType } from "@/lib/types"

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isClient, setIsClient] = useState(false)
  const router = useRouter()

  // 确保只在客户端运行
  useEffect(() => {
    setIsClient(true)
  }, [])

  const checkAuth = useCallback(async () => {
    if (!isClient) return // 只在客户端运行

    setIsLoading(true)
    try {
      const storedToken = localStorage.getItem("authToken")
      if (storedToken) {
        // In a real app, you might want to verify the token with the backend here
        // For this mock, we'll use a getCurrentUser function that simulates token validation
        const currentUser = await api.getCurrentUser(storedToken)
        if (currentUser) {
          setUser(currentUser)
          setToken(storedToken)
        } else {
          // Token invalid or expired
          localStorage.removeItem("authToken")
          setUser(null)
          setToken(null)
        }
      } else {
        setUser(null)
        setToken(null)
      }
    } catch (error) {
      console.error("Error checking auth status:", error)
      if (typeof window !== 'undefined') {
        localStorage.removeItem("authToken")
      }
      setUser(null)
      setToken(null)
    } finally {
      setIsLoading(false)
    }
  }, [isClient])

  useEffect(() => {
    if (isClient) {
      checkAuth()
    }
  }, [isClient, checkAuth])

  const login = async (credentials: LoginCredentials) => {
    try {
      const { access, user: loggedInUser } = await api.login(credentials)
      if (typeof window !== 'undefined') {
        localStorage.setItem("authToken", access)
      }
      setToken(access)
      setUser(loggedInUser)
      router.push("/") // Redirect to home or dashboard
    } catch (error) {
      console.error("Login failed:", error)
      throw error // Rethrow to be caught by the form
    }
  }

  const register = async (userData: RegisterData) => {
    try {
      await api.register(userData)
      // Optionally log in the user directly after registration
      // For now, redirect to login page
      router.push("/login?registrationSuccess=true")
    } catch (error) {
      console.error("Registration failed:", error)
      throw error
    }
  }

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem("authToken")
    }
    setUser(null)
    setToken(null)
    router.push("/login")
  }

  const isAuthenticated = !!token && !!user

  // 使用 useMemo 优化 context value
  const contextValue = useMemo(() => ({
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    checkAuth
  }), [user, token, isAuthenticated, isLoading, login, register, logout, checkAuth])

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthContext

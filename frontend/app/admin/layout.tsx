"use client"

import React, { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { apiClient } from "@/lib/api-client"
import { AdminSidebar } from '@/components/admin/admin-sidebar'
import { Header } from '@/components/header'
import { Loader2 } from "lucide-react"

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [isAuthorized, setIsAuthorized] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const isValid = await apiClient.validateToken()
        if (!isValid) {
          // usePathname 대신 window.location을 사용하여 확실하게 현재 주소를 가져옵니다.
          const currentPath = window.location.pathname + window.location.search
          console.log("[AdminLayout] Token invalid, redirecting from:", currentPath)

          const redirectUrl = currentPath ? `?redirect_url=${encodeURIComponent(currentPath)}` : ""
          console.log("[AdminLayout] Redirecting to:", `/login${redirectUrl}`)

          router.replace(`/login${redirectUrl}`)
        } else {
          setIsAuthorized(true)
        }
      } catch (error) {
        console.error("Admin auth check failed:", error)
        const currentPath = window.location.pathname + window.location.search
        const redirectUrl = currentPath ? `?redirect_url=${encodeURIComponent(currentPath)}` : ""
        router.replace(`/login${redirectUrl}`)
      }
    }
    checkAuth()
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    router.push('/login')
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header isLoggedIn={true} onLogout={handleLogout} />
      <div className="flex flex-1 overflow-hidden">
        <AdminSidebar />
        <main className="min-w-0 flex-1 overflow-auto p-6 md:p-8">{children}</main>
      </div>
    </div>
  )
}

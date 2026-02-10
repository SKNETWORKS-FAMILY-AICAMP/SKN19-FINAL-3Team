"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api-client"

export function useAuth() {
    const router = useRouter()
    const [isLoggedIn, setIsLoggedIn] = useState(false)

    const requireAuth = async (): Promise<boolean> => {
        const isValid = await apiClient.validateToken()
        if (!isValid) {
            setIsLoggedIn(false)
            router.replace("/")
            return false
        }
        return true
    }

    const logout = () => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        setIsLoggedIn(false)
        router.replace("/")
    }

    const checkAuthOnMount = async () => {
        const isValid = await apiClient.validateToken()
        if (isValid) {
            router.replace("/main")
        } else {
            router.replace("/login")
        }
    }

    return {
        isLoggedIn,
        setIsLoggedIn,
        requireAuth,
        logout,
        checkAuthOnMount,
    }
}

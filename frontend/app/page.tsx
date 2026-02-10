"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { apiClient } from "@/lib/api-client"
import { Loader2 } from "lucide-react"

export default function IndexPage() {
    const router = useRouter()
    const pathname = usePathname()
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const checkAuth = async () => {
            // CloudFront/S3 fallback 이슈 해결 (History Hack):
            // /admin 등 하위 경로로 접속 시 서버는 index.html(루트)을 반환합니다.
            // 이때 Next.js 라우터는 이미 해당 URL에 있다고 판단하여 router.replace()를 무시할 수 있습니다.
            // 따라서 브라우저 히스토리를 강제로 '/'로 잠시 변경하여 라우터를 깨운 뒤, 원래 경로로 이동시킵니다.
            if (pathname && pathname !== "/") {
                window.history.replaceState(null, '', '/')
                router.replace(pathname)
                return
            }

            try {
                const isValid = await apiClient.validateToken()
                if (isValid) {
                    router.replace("/main")
                } else {
                    // 토큰이 유효하지 않으면 로그인 페이지로 이동
                    // 단, 무한 루프 방지를 위해 현재 경로가 이미 /login 인지 확인하는 로직은
                    // page.tsx(루트)에서는 필요 없지만(루트는 /login이 아니므로),
                    // 네트워크 오류 등이 발생했을 때 무조건 리다이렉트 하는 것을 방지
                    const redirectUrl = pathname && pathname !== "/" ? `?redirect_url=${encodeURIComponent(pathname)}` : ""
                    router.replace(`/login${redirectUrl}`)
                }
            } catch (err) {
                console.error("Auth check failed:", err)
                // 네트워크 오류 등 발생 시 무한 루프 방지를 위해 리다이렉트 하지 않고 에러 표시
                setError("인증 서버에 연결할 수 없습니다. (Infinite Loop Protection)")
            }
        }

        checkAuth()
    }, [router])

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="bg-card p-8 rounded-xl shadow-md border border-border">
                    <p className="text-destructive text-center">{error}</p>
                    <p className="text-sm text-muted-foreground text-center mt-2">로그인 페이지로 이동합니다...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="bg-card p-8 rounded-xl shadow-md border border-border">
                <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
                <p className="mt-4 text-muted-foreground text-center">잠시만 기다려주세요...</p>
            </div>
        </div>
    )
}

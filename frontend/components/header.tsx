"use client"

import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"
import Image from "next/image"
import { useRouter } from "next/navigation"
import Link from "next/link"

interface HeaderProps {
  isLoggedIn: boolean
  onLogout: () => void
}

export function Header({ isLoggedIn, onLogout }: HeaderProps) {
  const router = useRouter()

  return (
    <header className="bg-card border-b border-border px-6 py-3 flex items-center justify-between flex-shrink-0">
      <Link href="/" className="cursor-pointer">
        <Image src="/logo.png" alt="AJC" width={80} height={40} className="h-7 w-auto" />
      </Link>
      <div className="flex items-center gap-3">
        {isLoggedIn ? (
          <Button variant="ghost" className="h-9 gap-2 text-muted-foreground hover:text-foreground" onClick={onLogout}>
            <LogOut className="w-4 h-4" />
            <span className="text-sm">로그아웃</span>
          </Button>
        ) : (
          <Button className="h-9" onClick={() => router.push("/login")}>
            로그인
          </Button>
        )}
      </div>
    </header>
  )
}

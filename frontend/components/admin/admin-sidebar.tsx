'use client'

import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  FileText,
  Shield,
  Tags,
  Users,
  Activity,
  FileSearch,
  LogOut,
} from 'lucide-react'

const navItems = [
  {
    title: '민감정보 정규식',
    href: '/admin',
    icon: FileSearch,
  },
  {
    title: '문서 접근권한',
    href: '/admin/permissions',
    icon: Shield,
  },
  {
    title: '카테고리 관리',
    href: '/admin/categories',
    icon: Tags,
  },
  {
    title: '사용자 관리',
    href: '/admin/users',
    icon: Users,
  },
  {
    title: '감사 로그',
    href: '/admin/audit-logs',
    icon: Activity,
  },
]

export function AdminSidebar() {
  const router = useRouter()
  const pathname = usePathname()

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    router.replace("/login")
  }

  return (
    <aside className="hidden w-64 border-r border-border bg-card md:block">
      <div className="flex h-full flex-col">
        <nav className="flex-1 space-y-1 p-4">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <Icon className="h-5 w-5" />
                {item.title}
              </Link>
            )
          })}
        </nav>
      </div>
    </aside>
  )
}

'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { Search, FileText, Shield, User, Tag, Download, Eye, Trash2 } from 'lucide-react'

type TaskTypeCode = "DOC_INDEX" | "DOC_UPDATE" | "MERGE_PROP"

type AuditLog = {
    log_seq: number
    operator_seq: number
    team_seq: number
    task_type_code: TaskTypeCode
    task_id: string
    start_task_id: string
    created_at: Date
}

const logs: AuditLog[] = [
    {
        log_seq: 1,
        operator_seq: 1,
        team_seq: 1,
        task_type_code: 'DOC_INDEX',
        task_id: '684411d2-c8ef-4ba6-b31e-5817341ebf5b',
        start_task_id: '684411d2-c8ef-4ba6-b31e-5817341ebf5b',
        created_at: new Date('2026-01-30 09:15:23')
    },
    {
        log_seq: 2,
        operator_seq: 2,
        team_seq: 2,
        task_type_code: 'DOC_INDEX',
        task_id: '684411d2-c8ef-4ba6-b31e-5817341ebf5b',
        start_task_id: '684411d2-c8ef-4ba6-b31e-5817341ebf5b',
        created_at: new Date('2026-01-31 10:15:40')
    }
]


const taskTypeConfig = {
    DOC_INDEX: { icon: FileText, color: 'bg-blue-500/10 text-blue-500', label: '문서 생성' },
    DOC_UPDATE: { icon: Eye, color: 'bg-green-500/10 text-green-500', label: '문서 수정' },
    MERGE_PROP: { icon: Tag, color: 'bg-yellow-500/10 text-yellow-500', label: '병합 제안' }
}

export default function AuditLogsPage() {
    const [searchQuery, setSearchQuery] = useState('')
    const [taskFilter, setTaskFilter] = useState('all')

    const filteredLogs = logs.filter(log => {
        const matchesSearch =
            log.task_type_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
            log.task_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
            log.start_task_id.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesTask = taskFilter === 'all' || log.task_type_code === taskFilter
        return matchesSearch && matchesTask
    })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground">
                    감사 로그
                </h1>
                <p className="text-muted-foreground">
                    모든 시스템 활동을 추적하고 모니터링합니다
                </p>
            </div>

            <div className="flex items-center gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        placeholder="활동, 사용자 또는 대상 검색..."
                        className="pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <Select value={taskFilter} onValueChange={setTaskFilter}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="활동 유형" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">전체 활동</SelectItem>
                        <SelectItem value="create">생성</SelectItem>
                        <SelectItem value="read">조회</SelectItem>
                        <SelectItem value="update">수정</SelectItem>
                        <SelectItem value="delete">삭제</SelectItem>
                        <SelectItem value="permission">권한</SelectItem>
                        <SelectItem value="auth">인증</SelectItem>
                    </SelectContent>
                </Select>
                <Select defaultValue="today">
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="기간" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="today">오늘</SelectItem>
                        <SelectItem value="week">이번 주</SelectItem>
                        <SelectItem value="month">이번 달</SelectItem>
                        <SelectItem value="all">전체</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <div className="grid gap-6 md:grid-cols-4">
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            오늘 활동
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">234</div>
                    </CardContent>
                </Card>
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            문서 조회
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-500">145</div>
                    </CardContent>
                </Card>
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            권한 변경
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-yellow-500">23</div>
                    </CardContent>
                </Card>
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            보안 이벤트
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-500">5</div>
                    </CardContent>
                </Card>
            </div>

            <Card className="bg-card">
                <CardHeader>
                    <CardTitle>활동 기록</CardTitle>
                    <CardDescription>
                        총 {filteredLogs.length}개의 로그 항목
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>로그 ID</TableHead>
                                <TableHead>사용자 ID</TableHead>
                                <TableHead>팀 ID</TableHead>
                                <TableHead>작업</TableHead>
                                <TableHead>최초 작업</TableHead>
                                <TableHead>시간</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredLogs.map((log) => {
                                const config = taskTypeConfig[log.task_type_code]
                                const Icon = config.icon
                                return (
                                    <TableRow key={log.log_seq}>
                                        <TableCell className="font-medium">
                                            {log.log_seq}
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {log.operator_seq}
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {log.team_seq}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {log.task_id}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {log.start_task_id}
                                        </TableCell>
                                        <TableCell>
                                            <Badge className={config.color}>
                                                <Icon className="mr-1 h-3 w-3" />
                                                {config.label}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {log.operator_seq === null ? (
                                                <Badge variant="outline">시스템</Badge>
                                            ) : (
                                                log.operator_seq
                                            )}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {log.task_id}
                                        </TableCell>
                                        <TableCell className="text-sm text-muted-foreground">
                                            {log.created_at.toLocaleString()}
                                        </TableCell>
                                    </TableRow>
                                )
                            })}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    )
}

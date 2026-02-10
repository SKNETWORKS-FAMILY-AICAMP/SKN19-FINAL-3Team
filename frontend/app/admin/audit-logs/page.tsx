'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
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
import { Search, FileText, Eye, Tag, Loader2, Filter, X } from 'lucide-react'
import { getAuditLogs, type AuditLog, type ReadAuditLogRequest } from '@/lib/api/audit-logs'

const taskTypeConfig: Record<string, { icon: any, color: string, label: string }> = {
    DOC_INDEX: { icon: FileText, color: 'bg-blue-500/10 text-blue-500', label: '문서 생성' },
    DOC_UPDATE: { icon: Eye, color: 'bg-green-500/10 text-green-500', label: '문서 수정' },
    MERGE_PROP: { icon: Tag, color: 'bg-yellow-500/10 text-yellow-500', label: '병합 제안' }
}

// Helper function to get start of the week (Monday)
const getStartOfWeek = (): Date => {
    const now = new Date()
    const day = now.getDay() // 0 (Sunday) to 6 (Saturday)
    const diff = day === 0 ? -6 : 1 - day // Adjust to Monday
    const monday = new Date(now)
    monday.setDate(now.getDate() + diff)
    monday.setHours(0, 0, 0, 0)
    return monday
}

// Helper function to format date for datetime-local input
const formatDateTimeLocal = (date: Date): string => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
}

export default function AuditLogsPage() {
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [showFilters, setShowFilters] = useState(false)

    // Filter states - default to this week
    const [startDate, setStartDate] = useState(() => formatDateTimeLocal(getStartOfWeek()))
    const [endDate, setEndDate] = useState(() => formatDateTimeLocal(new Date()))
    const [taskTypeCode, setTaskTypeCode] = useState<string>('')
    const [operatorSeq, setOperatorSeq] = useState<string>('')
    const [teamSeq, setTeamSeq] = useState<string>('')

    useEffect(() => {
        // Load audit logs with default this week filter
        const filters: ReadAuditLogRequest = {}

        if (startDate) {
            filters.start_date = new Date(startDate).toISOString()
        }
        if (endDate) {
            filters.end_date = new Date(endDate).toISOString()
        }

        loadAuditLogs(filters)
    }, [])

    const loadAuditLogs = async (filters?: ReadAuditLogRequest) => {
        setLoading(true)
        const data = await getAuditLogs(filters)
        setLogs(data)
        setLoading(false)
    }

    const handleApplyFilters = () => {
        const filters: ReadAuditLogRequest = {}

        if (startDate) {
            filters.start_date = new Date(startDate).toISOString()
        }
        if (endDate) {
            filters.end_date = new Date(endDate).toISOString()
        }
        if (taskTypeCode && taskTypeCode !== 'all') {
            filters.task_type_code = taskTypeCode
        }
        if (operatorSeq) {
            filters.operator_seq = parseInt(operatorSeq)
        }
        if (teamSeq) {
            filters.team_seq = parseInt(teamSeq)
        }

        loadAuditLogs(filters)
    }

    const handleClearFilters = () => {
        setStartDate('')
        setEndDate('')
        setTaskTypeCode('')
        setOperatorSeq('')
        setTeamSeq('')
        loadAuditLogs()
    }

    const filteredLogs = logs.filter(log => {
        const matchesSearch =
            log.task_type_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
            log.task_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
            log.start_task_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (log.operator_seq?.toString() || '').includes(searchQuery) ||
            (log.team_seq?.toString() || '').includes(searchQuery)
        return matchesSearch
    })

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        })
    }

    // Calculate statistics
    const taskTypeCounts = logs.reduce((acc, log) => {
        acc[log.task_type_code] = (acc[log.task_type_code] || 0) + 1
        return acc
    }, {} as Record<string, number>)

    return (
        <div className="min-w-0 space-y-6 overflow-hidden">
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
                        placeholder="작업 유형, 작업 ID, 사용자 ID, 팀 ID 검색..."
                        className="pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <Button
                    variant={showFilters ? "default" : "outline"}
                    className="gap-2"
                    onClick={() => setShowFilters(!showFilters)}
                >
                    <Filter className="h-4 w-4" />
                    필터
                </Button>
            </div>

            {showFilters && (
                <Card className="bg-card">
                    <CardHeader>
                        <CardTitle className="text-lg">필터 옵션</CardTitle>
                        <CardDescription>
                            원하는 조건으로 감사 로그를 필터링하세요
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            <div className="space-y-2">
                                <Label htmlFor="start-date">시작 날짜</Label>
                                <Input
                                    id="start-date"
                                    type="datetime-local"
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="end-date">종료 날짜</Label>
                                <Input
                                    id="end-date"
                                    type="datetime-local"
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="task-type">작업 유형</Label>
                                <Select value={taskTypeCode} onValueChange={setTaskTypeCode}>
                                    <SelectTrigger id="task-type">
                                        <SelectValue placeholder="전체" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">전체</SelectItem>
                                        <SelectItem value="DOC_INDEX">문서 생성</SelectItem>
                                        <SelectItem value="DOC_UPDATE">문서 수정</SelectItem>
                                        <SelectItem value="MERGE_PROP">병합 제안</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="operator-seq">사용자 ID</Label>
                                <Input
                                    id="operator-seq"
                                    type="number"
                                    placeholder="사용자 ID 입력"
                                    value={operatorSeq}
                                    onChange={(e) => setOperatorSeq(e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="team-seq">팀 ID</Label>
                                <Input
                                    id="team-seq"
                                    type="number"
                                    placeholder="팀 ID 입력"
                                    value={teamSeq}
                                    onChange={(e) => setTeamSeq(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={handleApplyFilters} className="gap-2">
                                <Filter className="h-4 w-4" />
                                필터 적용
                            </Button>
                            <Button variant="outline" onClick={handleClearFilters} className="gap-2">
                                <X className="h-4 w-4" />
                                필터 초기화
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-6 md:grid-cols-4">
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            전체 로그
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-foreground">{logs.length}</div>
                    </CardContent>
                </Card>
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            문서 생성
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-500">{taskTypeCounts['DOC_INDEX'] || 0}</div>
                    </CardContent>
                </Card>
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            문서 수정
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-500">{taskTypeCounts['DOC_UPDATE'] || 0}</div>
                    </CardContent>
                </Card>
                <Card className="bg-card">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            병합 제안
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-yellow-500">{taskTypeCounts['MERGE_PROP'] || 0}</div>
                    </CardContent>
                </Card>
            </div>

            <Card className="overflow-hidden bg-card">
                <CardHeader>
                    <CardTitle>활동 기록</CardTitle>
                    <CardDescription>
                        총 {filteredLogs.length}개의 로그 항목
                    </CardDescription>
                </CardHeader>
                <CardContent className="overflow-hidden">
                    <div className="max-h-[500px] w-full overflow-auto rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="whitespace-nowrap">시간</TableHead>
                                    <TableHead className="whitespace-nowrap">로그 ID</TableHead>
                                    <TableHead className="whitespace-nowrap">사용자 ID</TableHead>
                                    <TableHead className="whitespace-nowrap">팀 ID</TableHead>
                                    <TableHead className="whitespace-nowrap">작업 유형</TableHead>
                                    <TableHead className="whitespace-nowrap">작업 ID</TableHead>
                                    <TableHead className="whitespace-nowrap">시작 작업 ID</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center py-8">
                                            <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                                        </TableCell>
                                    </TableRow>
                                ) : filteredLogs.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                                            로그가 없습니다
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredLogs.map((log) => {
                                        const config = taskTypeConfig[log.task_type_code] || {
                                            icon: FileText,
                                            color: 'bg-gray-500/10 text-gray-500',
                                            label: log.task_type_code
                                        }
                                        const Icon = config.icon
                                        return (
                                            <TableRow key={log.log_seq}>
                                                <TableCell className="whitespace-nowrap text-sm text-muted-foreground text-right">
                                                    {formatDate(log.created_at)}
                                                </TableCell>
                                                <TableCell className="whitespace-nowrap font-medium text-center">
                                                    {log.log_seq}
                                                </TableCell>
                                                <TableCell className="whitespace-nowrap font-medium text-center">
                                                    {log.operator_seq === null ? (
                                                        <Badge className="bg-muted text-muted-foreground">시스템</Badge>
                                                    ) : (
                                                        log.operator_seq
                                                    )}
                                                </TableCell>
                                                <TableCell className="whitespace-nowrap font-medium text-center">
                                                    {log.team_seq === null ? (
                                                        <Badge className="bg-muted text-muted-foreground">-</Badge>
                                                    ) : (
                                                        log.team_seq
                                                    )}
                                                </TableCell>
                                                <TableCell className="whitespace-nowrap">
                                                    <Badge className={config.color}>
                                                        <Icon className="mr-1 h-3 w-3" />
                                                        {config.label}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="whitespace-nowrap text-muted-foreground font-mono text-xs">
                                                    {log.task_id}
                                                </TableCell>
                                                <TableCell className="whitespace-nowrap text-muted-foreground font-mono text-xs">
                                                    {log.start_task_id}
                                                </TableCell>
                                            </TableRow>
                                        )
                                    })
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

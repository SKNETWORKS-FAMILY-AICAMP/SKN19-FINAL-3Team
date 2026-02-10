'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Plus, Edit, Trash2, Check, X, Loader2 } from 'lucide-react'
import {
  getAllPatterns,
  createPattern,
  updatePattern,
  deletePattern,
  type Pattern,
} from '@/lib/api/regex'
import { useToast } from '@/hooks/use-toast'

export default function RegexPage() {
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingPattern, setEditingPattern] = useState<Pattern | null>(null)
  const [testText, setTestText] = useState('')
  const [testResults, setTestResults] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  // Form states
  const [newPatternName, setNewPatternName] = useState('')
  const [newPatternRegex, setNewPatternRegex] = useState('')
  const [editPatternName, setEditPatternName] = useState('')
  const [editPatternRegex, setEditPatternRegex] = useState('')

  const { toast } = useToast()

  useEffect(() => {
    loadPatterns()
  }, [])

  const loadPatterns = async () => {
    setLoading(true)
    const data = await getAllPatterns()
    setPatterns(data)
    setLoading(false)
  }

  const handleCreatePattern = async () => {
    if (!newPatternName.trim() || !newPatternRegex.trim()) {
      toast({
        title: '오류',
        description: '패턴 이름과 정규식을 모두 입력해주세요.',
        variant: 'destructive',
      })
      return
    }

    console.log('[Regex] Creating pattern:', { newPatternName, newPatternRegex })
    const success = await createPattern(newPatternName, newPatternRegex)
    console.log('[Regex] Create result:', success)

    // Always close dialog and reload patterns
    setNewPatternName('')
    setNewPatternRegex('')
    setIsDialogOpen(false)
    await loadPatterns()

    if (!success) {
      toast({
        title: '오류',
        description: '패턴 추가에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const handleToggle = async (pattern: Pattern) => {
    const success = await updatePattern(
      pattern.pattern_seq,
      pattern.pattern_name,
      pattern.regex_pattern,
      !pattern.is_active
    )

    if (success) {
      toast({
        title: '성공',
        description: '패턴이 업데이트되었습니다.',
      })
      loadPatterns()
    } else {
      toast({
        title: '오류',
        description: '패턴 업데이트에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const handleEditPattern = async () => {
    if (!editingPattern || !editPatternName.trim() || !editPatternRegex.trim()) {
      toast({
        title: '오류',
        description: '패턴 이름과 정규식을 모두 입력해주세요.',
        variant: 'destructive',
      })
      return
    }

    const success = await updatePattern(
      editingPattern.pattern_seq,
      editPatternName,
      editPatternRegex,
      editingPattern.is_active
    )

    if (success) {
      toast({
        title: '성공',
        description: '패턴이 성공적으로 수정되었습니다.',
      })
      setIsEditDialogOpen(false)
      setEditingPattern(null)
      loadPatterns()
    } else {
      toast({
        title: '오류',
        description: '패턴 수정에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const handleDeletePattern = async (pattern_seq: number) => {
    if (!confirm('정말 이 패턴을 삭제하시겠습니까?')) {
      return
    }

    const success = await deletePattern(pattern_seq)
    if (success) {
      toast({
        title: '성공',
        description: '패턴이 성공적으로 삭제되었습니다.',
        variant: 'destructive',
      })
      loadPatterns()
    } else {
      toast({
        title: '오류',
        description: '패턴 삭제에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const openEditDialog = (pattern: Pattern) => {
    setEditingPattern(pattern)
    setEditPatternName(pattern.pattern_name)
    setEditPatternRegex(pattern.regex_pattern)
    setIsEditDialogOpen(true)
  }

  const handleTest = () => {
    const results: string[] = []
    patterns.filter(p => p.is_active).forEach(pattern => {
      try {
        const regex = new RegExp(pattern.regex_pattern, 'g')
        const matches = testText.match(regex)
        if (matches) {
          results.push(`${pattern.pattern_name}: ${matches.length}개 탐지 - ${matches.join(', ')}`)
        }
      } catch (error) {
        console.error('[v0] Invalid regex:', pattern.regex_pattern, error)
      }
    })
    setTestResults(results)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            민감정보 정규식 관리
          </h1>
          <p className="text-muted-foreground">
            전역적으로 적용될 민감정보 탐지 패턴을 관리합니다
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              새 패턴 추가
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>정규식 패턴 추가</DialogTitle>
              <DialogDescription>
                새로운 민감정보 탐지 패턴을 추가합니다
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>패턴 이름</Label>
                <Input
                  placeholder="예: 주민등록번호"
                  value={newPatternName}
                  onChange={(e) => setNewPatternName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>정규식 패턴</Label>
                <Input
                  placeholder="예: \\d{6}-[1-4]\\d{6}"
                  className="font-mono"
                  value={newPatternRegex}
                  onChange={(e) => setNewPatternRegex(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleCreatePattern}>
                추가
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>정규식 패턴 수정</DialogTitle>
              <DialogDescription>
                패턴을 수정합니다
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>패턴 이름</Label>
                <Input
                  placeholder="예: 주민등록번호"
                  value={editPatternName}
                  onChange={(e) => setEditPatternName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>정규식 패턴</Label>
                <Input
                  placeholder="예: \\d{6}-[1-4]\\d{6}"
                  className="font-mono"
                  value={editPatternRegex}
                  onChange={(e) => setEditPatternRegex(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleEditPattern}>
                저장
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card className="bg-card">
            <CardHeader>
              <CardTitle>등록된 패턴</CardTitle>
              <CardDescription>
                현재 시스템에 등록된 {patterns.length}개의 정규식 패턴
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>이름</TableHead>
                    <TableHead>패턴</TableHead>
                    <TableHead className="text-right">활성화</TableHead>
                    <TableHead className="text-right">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                      </TableCell>
                    </TableRow>
                  ) : patterns.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                        등록된 패턴이 없습니다
                      </TableCell>
                    </TableRow>
                  ) : (
                    patterns.map((pattern) => (
                      <TableRow key={pattern.pattern_seq}>
                        <TableCell className="font-medium">
                          {pattern.pattern_name}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {pattern.regex_pattern}
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={pattern.is_active}
                            onCheckedChange={() => handleToggle(pattern)}
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openEditDialog(pattern)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeletePattern(pattern.pattern_seq)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="bg-card">
            <CardHeader>
              <CardTitle>패턴 테스트</CardTitle>
              <CardDescription>
                텍스트를 입력하여 등록된 패턴을 테스트합니다
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>테스트 텍스트</Label>
                <Textarea
                  placeholder="테스트할 텍스트를 입력하세요&#10;예: 홍길동 123456-1234567&#10;카드번호: 1234-5678-9012-3456"
                  value={testText}
                  onChange={(e) => setTestText(e.target.value)}
                  rows={6}
                />
              </div>
              <Button onClick={handleTest} className="w-full">
                패턴 테스트
              </Button>
              {testResults.length > 0 && (
                <div className="space-y-2 rounded-lg border border-border bg-secondary p-4">
                  <p className="text-sm font-medium">탐지 결과</p>
                  <div className="space-y-2">
                    {testResults.map((result, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-2 text-sm"
                      >
                        <Check className="h-4 w-4 text-accent" />
                        <span className="text-secondary-foreground">{result}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {testResults.length === 0 && testText && (
                <div className="flex items-start gap-2 rounded-lg border border-border bg-secondary p-4 text-sm">
                  <X className="h-4 w-4 text-muted-foreground" />
                  <span className="text-secondary-foreground">탐지된 패턴이 없습니다</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

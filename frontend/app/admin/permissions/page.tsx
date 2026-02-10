'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Search, Shield, Eye, Edit, Trash2, Download, Plus, Loader2 } from 'lucide-react'
import {
  getAllPermissions,
  createPermission,
  updatePermission,
  deletePermission,
  type Permission,
} from '@/lib/api/permissions'
import { useToast } from '@/hooks/use-toast'

// Role code to Korean label mapping
const getRoleLabel = (roleCode: string): string => {
  const roleMap: Record<string, string> = {
    'R_ADMIN': '관리자',
    'R_EDITOR': '편집자',
    'R_VIEWER': '열람자',
  }
  return roleMap[roleCode] || roleCode
}

const ROLE_OPTIONS = [
  { value: 'R_ADMIN', label: '관리자' },
  { value: 'R_EDITOR', label: '편집자' },
  { value: 'R_VIEWER', label: '열람자' },
]

export default function PermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedPermission, setSelectedPermission] = useState<Permission | null>(null)
  const [loading, setLoading] = useState(true)

  // Form states
  const [recipeSeq, setRecipeSeq] = useState('')
  const [userSeq, setUserSeq] = useState('')
  const [roleCode, setRoleCode] = useState('')

  const { toast } = useToast()

  const setSelectedDoc = (permission: Permission) => {
    setSelectedPermission(permission)
  }

  useEffect(() => {
    loadPermissions()
  }, [])

  const loadPermissions = async () => {
    setLoading(true)
    const data = await getAllPermissions()
    setPermissions(data)
    setLoading(false)
  }

  const handleCreatePermission = async () => {
    if (!recipeSeq || !userSeq || !roleCode) {
      toast({
        title: '오류',
        description: '모든 필드를 입력해주세요.',
        variant: 'destructive',
      })
      return
    }

    const success = await createPermission(
      Number(recipeSeq),
      Number(userSeq),
      roleCode
    )

    if (success) {
      toast({
        title: '성공',
        description: '권한이 성공적으로 추가되었습니다.',
      })
      setRecipeSeq('')
      setUserSeq('')
      setRoleCode('')
      setIsCreateDialogOpen(false)
      loadPermissions()
    } else {
      toast({
        title: '오류',
        description: '권한 추가에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const handleUpdatePermission = async () => {
    if (!selectedPermission || !roleCode) {
      toast({
        title: '오류',
        description: '역할 코드를 입력해주세요.',
        variant: 'destructive',
      })
      return
    }

    const success = await updatePermission(
      selectedPermission.recipe_seq,
      selectedPermission.user_seq,
      roleCode
    )

    if (success) {
      toast({
        title: '성공',
        description: '권한이 성공적으로 수정되었습니다.',
      })
      setIsEditDialogOpen(false)
      setSelectedPermission(null)
      loadPermissions()
    } else {
      toast({
        title: '오류',
        description: '권한 수정에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const handleDeletePermission = async (recipe_seq: number, user_seq: number) => {
    if (!confirm('정말 이 권한을 삭제하시겠습니까?')) {
      return
    }

    const success = await deletePermission(recipe_seq, user_seq)

    if (success) {
      toast({
        title: '성공',
        description: '권한이 성공적으로 삭제되었습니다.',
      })
      loadPermissions()
    } else {
      toast({
        title: '오류',
        description: '권한 삭제에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const openEditDialog = (permission: Permission) => {
    setSelectedPermission(permission)
    setRoleCode(permission.role_code)
    setIsEditDialogOpen(true)
  }

  const filteredPermissions = permissions.filter(p =>
    p.recipe_seq.toString().includes(searchQuery) ||
    p.user_seq.toString().includes(searchQuery) ||
    p.role_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.doc_name && p.doc_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (p.user_name && p.user_name.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            문서 접근권한 관리
          </h1>
          <p className="text-muted-foreground">
            특정 문서에 대한 접근 권한을 설정하고 관리합니다
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              권한 추가
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>문서 권한 추가</DialogTitle>
              <DialogDescription>
                새로운 문서 접근 권한을 추가합니다
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>문서 ID (recipe_seq)</Label>
                <Input
                  type="number"
                  placeholder="예: 1"
                  value={recipeSeq}
                  onChange={(e) => setRecipeSeq(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>사용자 ID (user_seq)</Label>
                <Input
                  type="number"
                  placeholder="예: 1"
                  value={userSeq}
                  onChange={(e) => setUserSeq(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>역할</Label>
                <Select value={roleCode} onValueChange={setRoleCode}>
                  <SelectTrigger>
                    <SelectValue placeholder="역할을 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLE_OPTIONS.map((role) => (
                      <SelectItem key={role.value} value={role.value}>
                        {role.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleCreatePermission}>
                추가
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="문서명, 사용자명, ID 또는 역할 검색..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <Card className="bg-card">
        <CardHeader>
          <CardTitle>문서 목록</CardTitle>
          <CardDescription>
            총 {filteredPermissions.length}개의 문서
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>문서 ID</TableHead>
                <TableHead>문서명</TableHead>
                <TableHead>사용자 ID</TableHead>
                <TableHead>사용자명</TableHead>
                <TableHead>역할 코드</TableHead>
                <TableHead className="text-right">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                  </TableCell>
                </TableRow>
              ) : filteredPermissions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    등록된 권한이 없습니다
                  </TableCell>
                </TableRow>
              ) : (
                filteredPermissions.map((permission, index) => (
                  <TableRow key={`${permission.recipe_seq}-${permission.user_seq}-${index}`}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-muted-foreground" />
                        {permission.recipe_seq}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{permission.doc_name || '-'}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{permission.user_seq}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{permission.user_name || '-'}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{getRoleLabel(permission.role_code)}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(permission)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeletePermission(permission.recipe_seq, permission.user_seq)}
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

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>문서 권한 수정</DialogTitle>
            <DialogDescription>
              권한 정보를 수정합니다
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>문서 ID (recipe_seq)</Label>
              <Input
                type="number"
                value={selectedPermission?.recipe_seq || ''}
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label>사용자 ID (user_seq)</Label>
              <Input
                type="number"
                value={selectedPermission?.user_seq || ''}
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label>역할</Label>
              <Select value={roleCode} onValueChange={setRoleCode}>
                <SelectTrigger>
                  <SelectValue placeholder="역할을 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  {ROLE_OPTIONS.map((role) => (
                    <SelectItem key={role.value} value={role.value}>
                      {role.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleUpdatePermission}>
              저장
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
import { Plus, Edit, Trash2, Tag, Loader2 } from 'lucide-react'
import {
  getAllCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  type Category,
} from '@/lib/api/categories'
import { useToast } from '@/hooks/use-toast'

const colorOptions = [
  { value: 'bg-blue-500', label: '파랑' },
  { value: 'bg-green-500', label: '초록' },
  { value: 'bg-purple-500', label: '보라' },
  { value: 'bg-orange-500', label: '주황' },
  { value: 'bg-red-500', label: '빨강' },
  { value: 'bg-yellow-500', label: '노랑' },
  { value: 'bg-pink-500', label: '분홍' },
  { value: 'bg-indigo-500', label: '남색' },
]

const initialCategories: Category[] = [
  // Define initial categories here if needed
]

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [loading, setLoading] = useState(true)

  // Form states for create
  const [newTagName, setNewTagName] = useState('')
  const [newDepth, setNewDepth] = useState('1')
  const [newSummary, setNewSummary] = useState('')

  // Form states for edit
  const [editTagName, setEditTagName] = useState('')
  const [editDepth, setEditDepth] = useState('1')
  const [editSummary, setEditSummary] = useState('')
  const [editColor, setEditColor] = useState('')

  const { toast } = useToast()

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    setLoading(true)
    const data = await getAllCategories()
    setCategories(data)
    setLoading(false)
  }

  const handleCreateCategory = async () => {
    if (!newTagName.trim() || !newSummary.trim()) {
      toast({
        title: '오류',
        description: '카테고리 이름과 설명을 모두 입력해주세요.',
        variant: 'destructive',
      })
      return
    }

    const success = await createCategory(newTagName, Number(newDepth), newSummary)

    if (success) {
      toast({
        title: '성공',
        description: '카테고리가 성공적으로 추가되었습니다.',
      })
      setNewTagName('')
      setNewDepth('1')
      setNewSummary('')
      setIsCreateDialogOpen(false)
      loadCategories()
    } else {
      toast({
        title: '오류',
        description: '카테고리 추가에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const handleUpdateCategory = async () => {
    if (!editingCategory || !editTagName.trim() || !editSummary.trim()) {
      toast({
        title: '오류',
        description: '카테고리 이름과 설명을 모두 입력해주세요.',
        variant: 'destructive',
      })
      return
    }

    const success = await updateCategory(
      editingCategory.tag_seq,
      editTagName,
      Number(editDepth),
      editSummary,
      editColor
    )

    if (success) {
      toast({
        title: '성공',
        description: '카테고리가 성공적으로 수정되었습니다.',
      })
      setIsEditDialogOpen(false)
      setEditingCategory(null)
      loadCategories()
    } else {
      toast({
        title: '오류',
        description: '카테고리 수정에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const handleDeleteCategory = async (tag_seq: number) => {
    if (!confirm('정말 이 카테고리를 삭제하시겠습니까?')) {
      return
    }

    const success = await deleteCategory(tag_seq)

    if (success) {
      toast({
        title: '성공',
        description: '카테고리가 성공적으로 삭제되었습니다.',
      })
      loadCategories()
    } else {
      toast({
        title: '오류',
        description: '카테고리 삭제에 실패했습니다.',
        variant: 'destructive',
      })
    }
  }

  const openEditDialog = (category: Category) => {
    setEditingCategory(category)
    setEditTagName(category.tag_name)
    setEditDepth(category.depth.toString())
    setEditSummary(category.summary)
    setEditColor(category.color)
    setIsEditDialogOpen(true)
  }

  const getColorForDepth = (depth: number): string => {
    const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500', 'bg-red-500']
    return colors[(depth - 1) % colors.length]
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            카테고리 관리
          </h1>
          <p className="text-muted-foreground">
            문서를 분류할 카테고리(태그)를 관리합니다
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              새 카테고리
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>카테고리 추가</DialogTitle>
              <DialogDescription>
                새로운 문서 카테고리를 생성합니다
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>카테고리 이름</Label>
                <Input placeholder="예: 재무" value={newTagName} onChange={(e) => setNewTagName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>깊이 레벨 (1-5)</Label>
                <Select value={newDepth} onValueChange={setNewDepth}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Level 1</SelectItem>
                    <SelectItem value="2">Level 2</SelectItem>
                    <SelectItem value="3">Level 3</SelectItem>
                    <SelectItem value="4">Level 4</SelectItem>
                    <SelectItem value="5">Level 5</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>설명</Label>
                <Textarea placeholder="카테고리에 대한 설명을 입력하세요" value={newSummary} onChange={(e) => setNewSummary(e.target.value)} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleCreateCategory}>
                추가
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : categories.length === 0 ? (
        <Card className="p-12">
          <div className="text-center text-muted-foreground">
            등록된 카테고리가 없습니다
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {categories.map((category) => {
            const categoryColor = getColorForDepth(category.depth)
            return (
              <Card key={category.tag_seq} className="bg-card transition-all hover:shadow-lg">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`h-10 w-10 rounded-lg ${categoryColor} flex items-center justify-center`}>
                        <Tag className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{category.tag_name}</CardTitle>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="rounded-lg bg-secondary p-4 space-y-3">
                      <div className="space-y-1">
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                          설명
                        </p>
                        <p className="text-sm text-foreground leading-relaxed">
                          {category.summary}
                        </p>
                      </div>
                      <div className="flex items-center gap-4 pt-2 border-t border-border">
                        <div className="space-y-1">
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                            깊이 레벨
                          </p>
                          <p className="text-2xl font-bold text-foreground">
                            {category.depth}
                          </p>
                        </div>
                        <div className="flex gap-1 flex-1 justify-end">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <div
                              key={i}
                              className={`h-8 w-8 rounded-md flex items-center justify-center text-xs font-semibold ${i < category.depth
                                ? `${categoryColor} text-white`
                                : 'bg-muted text-muted-foreground'
                                }`}
                            >
                              {i + 1}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="flex-1 bg-transparent"
                        onClick={() => openEditDialog(category)}
                      >
                        <Edit className="mr-2 h-4 w-4" />
                        편집
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleDeleteCategory(category.tag_seq)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>카테고리 편집</DialogTitle>
            <DialogDescription>
              카테고리 정보를 수정합니다
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>카테고리 이름</Label>
              <Input
                value={editTagName}
                onChange={(e) => setEditTagName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>깊이 레벨 (1-5)</Label>
              <Select value={editDepth} onValueChange={setEditDepth}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Level 1</SelectItem>
                  <SelectItem value="2">Level 2</SelectItem>
                  <SelectItem value="3">Level 3</SelectItem>
                  <SelectItem value="4">Level 4</SelectItem>
                  <SelectItem value="5">Level 5</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>설명</Label>
              <Textarea
                value={editSummary}
                onChange={(e) => setEditSummary(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleUpdateCategory}>
              저장
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

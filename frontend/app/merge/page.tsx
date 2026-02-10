"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Loader2, FileText } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels"
import { MarkdownViewer } from "@/components/markdown-viewer"
import { Header } from "@/components/header"
import { SearchBar } from "@/components/search-bar"
import Loading from "../loading"

// --- Interfaces matching Backend Schema (MergeSelectionResponse) ---

interface MergeText {
  is_changed: boolean
  text_seq: number
  section_seq: number
  text_before: string
  text_after: string | null
}

interface MergeRecipe {
  recipe_seq: number
  is_merge: boolean
  title: string | null
  doc_type_code: string | null
  texts: MergeText[]
}

interface MergeSelectionResponse {
  task_id: string
  recipes: MergeRecipe[]
}

interface TaskStatusResponse {
  task_id: string
  task_type: string
  task_status: string
}

function MergePageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const taskId = searchParams.get("task_id")

  const [isPolling, setIsPolling] = useState(true)
  const [taskStatus, setTaskStatus] = useState<string>("PENDING")
  const [recipes, setRecipes] = useState<MergeRecipe[]>([])
  const [selectedRecipe, setSelectedRecipe] = useState<MergeRecipe | null>(null)
  const [checkedRecipeSeqs, setCheckedRecipeSeqs] = useState<Set<number>>(new Set())
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      const isValid = await apiClient.validateToken()
      setIsLoggedIn(isValid)

      if (!isValid) {
        setError("로그인이 필요합니다.")
        setIsPolling(false)
        router.replace("/login")
        return
      }
    }
    checkAuth()

    if (!taskId) {
      setError("task_id가 필요합니다.")
      setIsPolling(false)
      return
    }

    // Direct fetch since previous page ensured completion
    const controller = new AbortController()
    fetchSelection(taskId, controller.signal)

    return () => {
      controller.abort()
    }
  }, [taskId])

  // Fetch Selection (Results of the update task)
  const fetchSelection = async (taskId: string, signal?: AbortSignal) => {
    // Check sessionStorage first (optimization to avoid double fetch from page.tsx)
    const storedData = sessionStorage.getItem(`merge_selection_${taskId}`)
    if (storedData) {
      try {
        const data: MergeSelectionResponse = JSON.parse(storedData)
        console.log("Loaded selection from sessionStorage")

        // sessionStorage.removeItem(`merge_selection_${taskId}`) // Removed to support Strict Mode double-invocation

        if (data.recipes.length === 0) {
          setIsPolling(false)
          alert("변경된 문서가 없습니다.")
          router.push("/")
          return
        }

        setRecipes(data.recipes)
        if (data.recipes.length > 0) {
          setSelectedRecipe(data.recipes[0])
          setCheckedRecipeSeqs(new Set(data.recipes.map(r => r.recipe_seq)))
        }
        setIsPolling(false)
        return
      } catch (e) {
        console.error("Failed to parse stored selection", e)
        // If parse fails, fall through to fetch
      }
    }

    try {
      const response = await apiClient.fetchWithAuth(`/api/v1/documents/selection?task_id=${taskId}`, { signal })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: MergeSelectionResponse = await response.json()

      if (data.recipes.length === 0) {
        // Just in case
        setIsPolling(false)
        alert("변경된 문서가 없습니다.")
        router.push("/")
        return
      }

      setRecipes(data.recipes)
      if (data.recipes.length > 0) {
        setSelectedRecipe(data.recipes[0])
        // Initialize all checked by default
        setCheckedRecipeSeqs(new Set(data.recipes.map(r => r.recipe_seq)))
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        console.log("Fetch aborted")
        return
      }
      console.error("Selection fetch error:", err)
      setError("변경 사항을 불러오는데 실패했습니다.")
    } finally {
      setIsPolling(false)
    }
  }

  // Handle Update Action -> Apply Final
  const handleUpdate = async () => {
    const isValid = await apiClient.validateToken()
    if (!isValid) {
      alert("로그인이 필요합니다.")
      setIsLoggedIn(false)
      router.replace("/login")
      return
    }

    if (!taskId) return

    if (checkedRecipeSeqs.size === 0) {
      alert("적용할 문서가 선택되지 않았습니다.")
      return
    }

    setIsUpdating(true)

    try {
      const finalResponse = await apiClient.fetchWithAuth(`/api/v1/documents/apply_final`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task_id: taskId,
          has_merge_section: true,
          recipe_seq_list_selected: Array.from(checkedRecipeSeqs)
        })
      })

      if (!finalResponse.ok) {
        throw new Error(`Apply final error! status: ${finalResponse.status}`)
      }

      alert("선택된 문서가 성공적으로 업데이트되었습니다.")
      router.push("/")
    } catch (finalErr) {
      console.error("Final apply error:", finalErr)
      alert("최종 적용 중 오류가 발생했습니다.")
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDocumentSelect = (recipe: MergeRecipe) => {
    setSelectedRecipe(recipe)
  }

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    setIsLoggedIn(false)
    router.push("/login")
  }

  // Map MergeText[] to the Section format expected by MarkdownViewer
  // Or simpler: pass the content directly if MarkdownViewer supports it. 
  // Let's reuse MarkdownViewer's Section interface by mapping.
  // MarkdownViewer Section: { is_changed: boolean, original_text: string, ... }
  // We want to show 'text_after' if changed.
  const getViewerSections = (recipe: MergeRecipe | null) => {
    if (!recipe) return []
    return recipe.texts.map(t => ({
      ...t,
      // If changed, show text_after (falling back to text_before if null, though it shouldn't be).
      // MarkdownViewer uses 'original_text' prop to render.
      original_text: t.is_changed ? (t.text_after || "") : t.text_before
    }))
  }

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden relative">
      <div className="absolute top-2 left-1/2 -translate-x-1/2 z-50 w-[450px]">
        <Suspense fallback={null}>
          <SearchBar onSearch={(query) => console.log("Search:", query)} placeholder="문서 검색..." />
        </Suspense>
      </div>
      <Header isLoggedIn={isLoggedIn} onLogout={handleLogout} />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {isPolling ? (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
            <p className="text-lg text-gray-700">작업 처리 중...</p>
            <p className="text-sm text-gray-500">상태: {taskStatus}</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <p className="text-lg text-red-600">{error}</p>
            <Button onClick={() => router.push("/")} className="bg-blue-500 hover:bg-blue-600 text-white">
              홈으로 돌아가기
            </Button>
          </div>
        ) : (
          <PanelGroup direction="horizontal" className="h-full">
            {/* Left Panel - Document List */}
            <Panel defaultSize={25} minSize={15} maxSize={40}>
              <aside className="h-full bg-gray-100 flex flex-col">
                <div className="p-3">
                  <h3 className="text-sm font-medium text-gray-600">영향받을 문서 목록</h3>
                </div>
                <div className="flex-1 p-2 overflow-y-auto">
                  <div className="space-y-1">
                    {recipes.length === 0 ? (
                      <div className="text-sm text-gray-500 text-center py-4">
                        영향받을 문서가 없습니다.
                      </div>
                    ) : (
                      recipes.map((recipe) => {
                        const similarCount = recipe.texts.filter(s => s.is_changed).length
                        const totalCount = recipe.texts.length
                        const percentage = totalCount > 0 ? Math.round((similarCount / totalCount) * 100) : 0

                        return (
                          <div
                            key={recipe.recipe_seq}
                            onClick={() => handleDocumentSelect(recipe)}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded text-sm min-w-0 cursor-pointer border ${selectedRecipe?.recipe_seq === recipe.recipe_seq
                              ? "bg-blue-50 text-blue-700 border-blue-200"
                              : "text-gray-700 hover:bg-gray-50 border-transparent"
                              }`}
                          >
                            <div className="flex items-center" onClick={(e) => e.stopPropagation()}>
                              <Checkbox
                                className="w-5 h-5 border-gray-400 data-[state=checked]:border-blue-500 data-[state=checked]:bg-blue-500"
                                checked={checkedRecipeSeqs.has(recipe.recipe_seq)}
                                onCheckedChange={(checked) => {
                                  const next = new Set(checkedRecipeSeqs)
                                  if (checked) {
                                    next.add(recipe.recipe_seq)
                                  } else {
                                    next.delete(recipe.recipe_seq)
                                  }
                                  setCheckedRecipeSeqs(next)
                                }}
                              />
                            </div>
                            <FileText className="w-5 h-5 flex-shrink-0 text-gray-400" />
                            <div className="flex-1 text-left min-w-0">
                              <div className="font-medium truncate">{recipe.title || `문서 ${recipe.recipe_seq}`}</div>
                              <div className="text-xs text-gray-500">
                                {similarCount}/{totalCount}개 섹션 ({percentage}%)
                              </div>
                            </div>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
                <div className="p-3 flex gap-3">
                  <button
                    onClick={handleUpdate}
                    disabled={isUpdating || checkedRecipeSeqs.size === 0}
                    className="w-full flex items-center justify-center bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isUpdating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    업데이트
                  </button>
                  <button
                    onClick={() => router.push('/')}
                    className="w-full flex items-center justify-center bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded text-sm font-medium transition-colors">
                    거부
                  </button>
                </div>
              </aside>
            </Panel>

            <PanelResizeHandle className="w-[1px] bg-gray-300 hover:bg-blue-500 hover:w-[2px] transition-all cursor-col-resize" />

            {/* Center Panel - Document Content */}
            <Panel defaultSize={75} minSize={40}>
              <MarkdownViewer
                sections={getViewerSections(selectedRecipe)}
                isLoading={false}
                loadingError={null}
              />
            </Panel>
          </PanelGroup>
        )}
      </div>
    </div>
  )
}

export default function MergePage() {
  return (
    <Suspense fallback={<Loading />}>
      <MergePageContent />
    </Suspense>
  )
}

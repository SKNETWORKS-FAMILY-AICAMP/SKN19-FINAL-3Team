import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Loader2, FileText } from "lucide-react"
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels"
import { MarkdownViewer } from "@/components/markdown-viewer"

// --- Interfaces ---

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

interface MergeViewProps {
    recipes: MergeRecipe[]
    onConfirm: (selectedRecipeSeqs: number[]) => Promise<void>
    onCancel: () => void
    isUpdating: boolean
}

export function MergeView({ recipes, onConfirm, onCancel, isUpdating }: MergeViewProps) {
    const [selectedRecipe, setSelectedRecipe] = useState<MergeRecipe | null>(null)
    const [checkedRecipeSeqs, setCheckedRecipeSeqs] = useState<Set<number>>(new Set())

    // Initialize selection
    useEffect(() => {
        if (recipes.length > 0) {
            setSelectedRecipe(recipes[0])
            setCheckedRecipeSeqs(new Set(recipes.map(r => r.recipe_seq)))
        }
    }, [recipes])

    const handleUpdate = () => {
        if (checkedRecipeSeqs.size === 0) {
            alert("적용할 문서가 선택되지 않았습니다.")
            return
        }
        onConfirm(Array.from(checkedRecipeSeqs))
    }

    const handleDocumentSelect = (recipe: MergeRecipe) => {
        setSelectedRecipe(recipe)
    }

    // Map MergeText[] to the Section format expected by MarkdownViewer
    const getViewerSections = (recipe: MergeRecipe | null) => {
        if (!recipe) return []
        return recipe.texts.map(t => ({
            ...t,
            original_text: t.is_changed ? (t.text_after || "") : t.text_before
        }))
    }

    return (
        <div className="h-full flex flex-col bg-gray-100 overflow-hidden relative">
            <PanelGroup direction="horizontal" className="h-full">
                {/* Left Panel - Document List */}
                <Panel defaultSize={25} minSize={20} maxSize={40}>
                    <aside className="h-full bg-gray-100 flex flex-col border-r border-gray-300">
                        <div className="p-3 bg-white border-b border-gray-200">
                            <h3 className="text-sm font-medium text-gray-800">영향받을 문서 목록</h3>
                        </div>
                        <div className="flex-1 p-2 overflow-y-auto bg-gray-50">
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
                                                className={`w-full flex items-center gap-3 px-3 py-3 rounded text-sm min-w-0 cursor-pointer border transition-all ${selectedRecipe?.recipe_seq === recipe.recipe_seq
                                                        ? "bg-white text-blue-700 border-blue-200 shadow-sm"
                                                        : "text-gray-700 hover:bg-white hover:border-gray-200 border-transparent"
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
                                                <FileText className={`w-5 h-5 flex-shrink-0 ${selectedRecipe?.recipe_seq === recipe.recipe_seq ? "text-blue-500" : "text-gray-400"
                                                    }`} />
                                                <div className="flex-1 text-left min-w-0">
                                                    <div className="font-medium truncate text-gray-900">{recipe.title || `문서 ${recipe.recipe_seq}`}</div>
                                                    <div className="text-xs text-gray-500 mt-0.5">
                                                        {similarCount}/{totalCount}개 섹션 변경 ({percentage}%)
                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    })
                                )}
                            </div>
                        </div>
                        <div className="p-4 bg-white border-t border-gray-200 flex gap-3 shadow-md z-10">
                            <button
                                onClick={handleUpdate}
                                disabled={isUpdating || checkedRecipeSeqs.size === 0}
                                className="flex-1 flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white px-3 py-2.5 rounded-md text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                            >
                                {isUpdating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                                변경사항 적용
                            </button>
                            <button
                                onClick={onCancel}
                                disabled={isUpdating}
                                className="flex-1 flex items-center justify-center bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 px-3 py-2.5 rounded-md text-sm font-semibold transition-colors shadow-sm"
                            >
                                취소
                            </button>
                        </div>
                    </aside>
                </Panel>

                <PanelResizeHandle className="w-[1px] bg-gray-300 hover:bg-blue-500 hover:w-[2px] transition-all cursor-col-resize" />

                {/* Center Panel - Document Content */}
                <Panel defaultSize={75} minSize={40}>
                    <div className="h-full bg-white flex flex-col">
                        <div className="h-10 flex items-center px-4 bg-gray-50 border-b border-gray-200">
                            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">변경 미리보기</span>
                        </div>
                        <div className="flex-1 overflow-hidden relative">
                            <MarkdownViewer
                                sections={getViewerSections(selectedRecipe)}
                                isLoading={false}
                                loadingError={null}
                                content={""} // Not used when sections provided
                            />
                        </div>
                    </div>
                </Panel>
            </PanelGroup>
        </div>
    )
}

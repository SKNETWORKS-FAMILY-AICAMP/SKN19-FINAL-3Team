"use client"

import React from "react"

import { useState, useRef, useEffect } from "react"
import { Plus, FileText, Cloud, Laptop, Loader2, Pencil, Copy, Trash2, ChevronsLeft } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

interface Document {
  doc_name: string
  doc_type: string
  content: string
}

interface CloudDocumentResponse {
  recipe_seq: number
  doc_type_code: string
  title: string | null
  text: string | null
  recipe_value: string
  created_at: string
  updated_at: string
}

interface ContextMenuState {
  visible: boolean
  x: number
  y: number
  type: "local" | "cloud"
  fileName?: string
  recipeSeq?: number
  title?: string
}

interface FilePanelProps {
  docList: Document[]
  cloudDocuments: CloudDocumentResponse[]
  selectedFile: string
  docName: string
  docType: string
  storageMode: "local" | "cloud"
  isLoadingCloud: boolean
  isLoggedIn: boolean
  autoRenameFile?: string | null  // 로컬 파일 자동 리네임
  autoRenameRecipeSeq?: number | null  // 클라우드 문서 자동 리네임
  onDocNameChange: (name: string) => void
  onDocTypeChange: (type: string) => void
  onFileSelect: (fileName: string) => void
  onCloudDocumentSelect: (recipe_seq: number, title: string, type: string) => void
  onStorageModeChange: (mode: "local" | "cloud") => void
  onAddNewFile: () => void
  onRenameFile?: (oldName: string, newName: string) => void
  onCopyFile?: (fileName: string) => void
  onDeleteFile?: (fileName: string) => void
  onRenameCloudDoc?: (recipeSeq: number, newTitle: string) => void
  onCopyCloudDoc?: (recipeSeq: number) => void
  onDeleteCloudDoc?: (recipeSeq: number) => void
  onToggleCollapse?: () => void
}

export function FilePanel({
  docList,
  cloudDocuments,
  selectedFile,
  storageMode,
  isLoadingCloud,
  isLoggedIn,
  autoRenameFile,
  autoRenameRecipeSeq,
  onFileSelect,
  onCloudDocumentSelect,
  onStorageModeChange,
  onAddNewFile,
  onRenameFile,
  onCopyFile,
  onDeleteFile,
  onRenameCloudDoc,
  onCopyCloudDoc,
  onDeleteCloudDoc,
  onToggleCollapse,
}: FilePanelProps) {
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    type: "local",
  })
  const [isRenaming, setIsRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState("")
  const renameInputRef = useRef<HTMLInputElement>(null)
  const contextMenuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (contextMenuRef.current && !contextMenuRef.current.contains(e.target as Node)) {
        setContextMenu((prev) => ({ ...prev, visible: false }))
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  useEffect(() => {
    if (isRenaming && renameInputRef.current) {
      renameInputRef.current.focus()
      renameInputRef.current.select()
    }
  }, [isRenaming])

  // 새 파일 생성 시 자동으로 리네임 모드 진입
  useEffect(() => {
    if (storageMode === "local" && autoRenameFile) {
      // 로컬 모드: 파일 이름 기반
      const fileName = autoRenameFile.replace(".md", "")
      setIsRenaming(autoRenameFile)
      setRenameValue(fileName)
    } else if (storageMode === "cloud" && autoRenameRecipeSeq) {
      // 클라우드 모드: recipe_seq 기반
      const doc = cloudDocuments.find((d) => d.recipe_seq === autoRenameRecipeSeq)
      if (doc) {
        setIsRenaming(`cloud_${autoRenameRecipeSeq}`)
        setRenameValue(doc.title || "새 문서")
      }
    }
  }, [autoRenameFile, autoRenameRecipeSeq, storageMode, cloudDocuments])

  const handleContextMenu = (
    e: React.MouseEvent,
    type: "local" | "cloud",
    fileName?: string,
    recipeSeq?: number,
    title?: string
  ) => {
    e.preventDefault()
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      type,
      fileName,
      recipeSeq,
      title,
    })
  }

  const handleRename = () => {
    if (contextMenu.type === "local" && contextMenu.fileName) {
      setIsRenaming(contextMenu.fileName)
      setRenameValue(contextMenu.fileName)
    } else if (contextMenu.type === "cloud" && contextMenu.recipeSeq) {
      setIsRenaming(`cloud_${contextMenu.recipeSeq}`)
      setRenameValue(contextMenu.title || "")
    }
    setContextMenu((prev) => ({ ...prev, visible: false }))
  }

  const handleRenameSubmit = (oldName: string, isCloud: boolean, recipeSeq?: number) => {
    if (isCloud && recipeSeq && onRenameCloudDoc) {
      onRenameCloudDoc(recipeSeq, renameValue)
    } else if (!isCloud && onRenameFile) {
      onRenameFile(oldName, renameValue)
    }
    setIsRenaming(null)
    setRenameValue("")
  }

  const handleCopy = () => {
    if (contextMenu.type === "local" && contextMenu.fileName && onCopyFile) {
      onCopyFile(contextMenu.fileName)
    } else if (contextMenu.type === "cloud" && contextMenu.recipeSeq && onCopyCloudDoc) {
      onCopyCloudDoc(contextMenu.recipeSeq)
    }
    setContextMenu((prev) => ({ ...prev, visible: false }))
  }

  const handleDelete = () => {
    if (contextMenu.type === "local" && contextMenu.fileName && onDeleteFile) {
      onDeleteFile(contextMenu.fileName)
    } else if (contextMenu.type === "cloud" && contextMenu.recipeSeq && onDeleteCloudDoc) {
      onDeleteCloudDoc(contextMenu.recipeSeq)
    }
    setContextMenu((prev) => ({ ...prev, visible: false }))
  }

  return (
    <aside className="h-full bg-card border-r border-border flex flex-col relative">
      <div className="flex-1 p-3 overflow-auto">
        <div className="flex items-center justify-between mb-4 px-1 pt-1">
          <h3 className="text-sm font-semibold text-muted-foreground">파일</h3>
          <div className="flex items-center gap-1">
            <TooltipProvider delayDuration={0}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={onAddNewFile}
                    className="p-1.5 hover:bg-accent hover:text-accent-foreground rounded-md transition-colors"
                  >
                    <Plus className="w-4 h-4 text-muted-foreground" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>새 파일 추가</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <div className="flex items-center border border-border rounded-md overflow-hidden bg-background">
              <TooltipProvider delayDuration={0}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => onStorageModeChange("local")}
                      className={`p-1.5 transition-colors ${storageMode === "local" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                        }`}
                    >
                      <Laptop className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p>로컬 저장소</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <TooltipProvider delayDuration={0}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => onStorageModeChange("cloud")}
                      className={`p-1.5 transition-colors ${storageMode === "cloud" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                        } ${!isLoggedIn ? "opacity-50 cursor-not-allowed" : ""}`}
                      disabled={!isLoggedIn}
                    >
                      <Cloud className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p>{isLoggedIn ? "클라우드 저장소" : "로그인이 필요합니다"}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>

        {isLoadingCloud ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : storageMode === "local" ? (
          <div className="space-y-1">
            {docList.map((doc) => (
              <div key={doc.doc_name}>
                {isRenaming === doc.doc_name ? (
                  <div className="flex items-center gap-2 px-3 py-2">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <input
                      ref={renameInputRef}
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRenameSubmit(doc.doc_name, false)
                        if (e.key === "Escape") setIsRenaming(null)
                      }}
                      onBlur={() => handleRenameSubmit(doc.doc_name, false)}
                      className="flex-1 text-sm px-1 py-0.5 border border-primary rounded outline-none bg-background text-foreground"
                    />
                  </div>
                ) : (
                  <button
                    onClick={() => onFileSelect(doc.doc_name)}
                    onContextMenu={(e) => handleContextMenu(e, "local", doc.doc_name)}
                    className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm min-w-0 transition-colors ${selectedFile === doc.doc_name ? "bg-primary text-primary-foreground font-medium" : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                      }`}
                  >
                    <FileText className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{doc.doc_name}</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-1">
            {cloudDocuments.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-4">클라우드 문서가 없습니다.</div>
            ) : (
              cloudDocuments.map((doc) => (
                <div key={doc.recipe_seq}>
                  {isRenaming === `cloud_${doc.recipe_seq}` ? (
                    <div className="flex items-start gap-2 px-3 py-2">
                      <FileText className="w-4 h-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                      <input
                        ref={renameInputRef}
                        type="text"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleRenameSubmit("", true, doc.recipe_seq)
                          if (e.key === "Escape") setIsRenaming(null)
                        }}
                        onBlur={() => handleRenameSubmit("", true, doc.recipe_seq)}
                        className="flex-1 text-sm px-1 py-0.5 border border-primary rounded outline-none bg-background text-foreground"
                      />
                    </div>
                  ) : (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            onClick={() =>
                              onCloudDocumentSelect(doc.recipe_seq, doc.title || `문서 ${doc.recipe_seq}`, doc.doc_type_code)
                            }
                            onContextMenu={(e) =>
                              handleContextMenu(e, "cloud", undefined, doc.recipe_seq, doc.title || `문서 ${doc.recipe_seq}`)
                            }
                            className={`w-full flex items-start gap-2 px-3 py-2 rounded-md text-sm min-w-0 transition-colors ${selectedFile === `recipe_${doc.recipe_seq}`
                              ? "bg-primary text-primary-foreground font-medium"
                              : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                              }`}
                          >
                            <FileText className="w-4 h-4 mt-0.5 flex-shrink-0" />
                            <div className="flex-1 text-left min-w-0">
                              <div className="truncate">{doc.title || `문서 ${doc.recipe_seq}`}</div>
                              <div className={`text-xs truncate ${selectedFile === `recipe_${doc.recipe_seq}` ? "text-primary-foreground/80" : "text-muted-foreground/70"}`}>
                                {doc.doc_type_code}
                              </div>
                            </div>
                          </button>
                        </TooltipTrigger>
                        <TooltipContent side="right" className="text-xs">
                          <div className="space-y-1">
                            <div>생성일: {formatDate(doc.created_at)}</div>
                            <div>수정일: {formatDate(doc.updated_at)}</div>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Context Menu */}
      {contextMenu.visible && (
        <div
          ref={contextMenuRef}
          className="fixed bg-popover border border-border rounded-lg shadow-lg py-1 z-50 min-w-[140px] text-popover-foreground"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button
            onClick={handleRename}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
          >
            <Pencil className="w-4 h-4" />
            이름 변경
          </button>
          <button
            onClick={handleCopy}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
          >
            <Copy className="w-4 h-4" />
            복사
          </button>
          <hr className="my-1 border-border" />
          <button
            onClick={handleDelete}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10"
          >
            <Trash2 className="w-4 h-4" />
            삭제
          </button>
        </div>
      )}
    </aside>
  )
}

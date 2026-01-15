"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ChevronDown, Plus, FileText, CloudUpload, Save, Redo2, Cloud, Laptop, Loader2 } from "lucide-react"
import ReactMarkdown from "react-markdown"
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels"
import { Image } from "next/image"

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

interface CloudDocument {
  recipe_seq: number
  doc_type_code: string
  title: string
  text: string
  recipe_value: number[]
  created_at: string
  updated_at: string
}

interface LlmTaskRequest {
  text: string
}

interface LlmTaskResponse {
  task_id: string
  task_type: string
  task_status: string
}

interface IndexRequest {
  text: string
  index_seq: number
  origin_type_code: string
}

interface IndexResponse {
  text: string
  index_seq: number
  origin_type_code: string
}

export default function MarkdownEditorPage() {
  const [docList, setDocList] = useState<Document[]>([
    { doc_name: "README.md", doc_type: "가이드라인", content: `# AJC 툴 사용자 가이드라인

## 1. 개요

본 툴은 문서를 **클라우드와 로컬에 동시에 저장**하고,
문서 수정 시 **의미적으로 유사한 섹션을 자동으로 감지하여 동기화**하는 문서 관리 시스템입니다.

단순 파일 동기화가 아니라,
**문서를 ‘의미 단위(섹션)’로 분석·관리**하는 것을 핵심 개념으로 합니다.

---

## 2. 지원 저장 방식

### 2.1 클라우드 저장

* 문서는 서버에 안전하게 저장됩니다.
* 계정 로그인 시 언제든 접근 가능합니다.
* 버전 관리 및 변경 이력 추적이 지원됩니다.

### 2.2 로컬 저장

* 사용자의 로컬 환경(PC)에 문서를 저장할 수 있습니다.
* 인터넷 연결 없이도 편집 가능합니다.
* 로컬 문서는 필요 시 클라우드와 동기화됩니다.

---

## 3. 문서 구조 원칙

이 툴은 문서를 **하나의 텍스트로 취급하지 않습니다**.

### 3.1 섹션 기반 관리

* 문서는 자동으로 **섹션 단위로 분리**됩니다.
* 섹션 기준:

  * 제목(Heading)
  * 문단 구조
  * 의미적 흐름

### 3.2 권장 작성 방식

* 제목(`##`, `###`)을 명확히 사용하세요.
* 하나의 섹션에는 하나의 핵심 주제만 담으세요.
* 너무 긴 문단은 나누는 것이 동기화 정확도를 높입니다.

---

## 4. 자동 섹션 동기화 기능

### 4.1 동기화 동작 방식

1. 문서를 수정하면 수정된 섹션이 자동 분석됩니다.
3. 기존 섹션들과 **의미적 유사도**를 비교합니다.
4. 유사도가 높은 섹션이 자동으로 연결·동기화됩니다.

✔ 제목이 달라도 내용이 비슷하면 동기화될 수 있습니다.
✔ 단순 문자열 비교가 아닌 의미 기반 분석을 사용합니다.

---

### 4.2 자동 동기화 예시

* 로컬에서 문서 A의 “아키텍처 설계” 섹션 수정
* 클라우드 문서 B에 의미적으로 유사한 섹션 존재
* 시스템이 해당 섹션을 자동 감지하여 동기화

---

## 5. 충돌 처리 규칙

### 5.1 동기화 충돌 발생 시

다음 상황에서는 자동 병합이 중단됩니다.

* 동일 섹션을 서로 다른 환경에서 동시에 수정한 경우
* 의미 유사도는 높으나 수정 방향이 크게 다른 경우

### 5.2 사용자 선택

* 로컬 버전 유지
* 클라우드 버전 유지
* 수동 병합

---

## 6. 사용자 주의사항

* 문서 구조를 자주 크게 변경하면 동기화 정확도가 떨어질 수 있습니다.
* 제목 없이 긴 텍스트를 작성하면 섹션 분리가 부정확해질 수 있습니다.
* 의미 기반 동기화 특성상, 완전히 다른 주제는 자동 연결되지 않습니다.

---

## 7. 권장 사용 시나리오

* 기술 문서 관리
* 기획서 버전 관리
* 연구 노트 / 리포트
* AI 학습용 문서 정리
* 팀 간 문서 정합성 유지
` },
    { doc_name: "notes.md", doc_type: "메모", content: "# 메모\n\n여기에 메모를 작성하세요." },
  ])
  const [cloudDocuments, setCloudDocuments] = useState<CloudDocumentResponse[]>([])
  const [selectedFile, setSelectedFile] = useState("README.md")
  const [docName, setDocName] = useState("README.md")
  const [docType, setDocType] = useState("가이드라인")
  const [markdownContent, setMarkdownContent] = useState("## Markdown 문서 수정 및 확인이 가능")
  const [storageMode, setStorageMode] = useState<"local" | "cloud">("local")
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingCloud, setIsLoadingCloud] = useState(false)
  const [isLoadingContent, setIsLoadingContent] = useState(false)
  const [loadingError, setLoadingError] = useState<string | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem("doc_list")
    if (saved) {
      try {
        const parsedList = JSON.parse(saved)
        setDocList(parsedList)
        if (parsedList.length > 0) {
          const firstDoc = parsedList[0]
          setSelectedFile(firstDoc.doc_name)
          setDocName(firstDoc.doc_name)
          setDocType(firstDoc.doc_type)
          setMarkdownContent(firstDoc.content)
        }
      } catch (e) {
        console.error("Failed to parse localStorage", e)
      }
    }
  }, [])

  useEffect(() => {
    if (storageMode === "cloud") {
      fetchCloudDocuments()
    }
  }, [storageMode])

  const fetchCloudDocuments = async () => {
    setIsLoadingCloud(true)
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
      const response = await fetch(`${apiBaseUrl}/api/v1/documents?skip=0&limit=100`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const documents: CloudDocumentResponse[] = await response.json()
      setCloudDocuments(documents)
    } catch (error) {
      console.error("Failed to fetch cloud documents:", error)
      alert("클라우드 문서 목록을 불러오는데 실패했습니다.")
    } finally {
      setIsLoadingCloud(false)
    }
  }

  const handleFileSelect = (fileName: string) => {
    const doc = docList.find((d) => d.doc_name === fileName)
    if (doc) {
      setSelectedFile(fileName)
      setDocName(doc.doc_name)
      setDocType(doc.doc_type)
      setMarkdownContent(doc.content)
    }
  }

  const handleCloudDocumentSelect = async (recipe_seq: number, previewTitle: string, previewType: string) => {
    setSelectedFile(`recipe_${recipe_seq}`)
    setIsLoadingContent(true)
    setLoadingError(null)

    const timeoutId = setTimeout(() => {
      setLoadingError("문제가 발생했거나 로딩이 지연되고 있습니다.")
    }, 10000)

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
      const response = await fetch(`${apiBaseUrl}/api/v1/documents/${recipe_seq}`)

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const document: CloudDocument = await response.json()

      setDocName(document.title || `문서 ${recipe_seq}`)
      setDocType(document.doc_type_code)
      setMarkdownContent(document.text || "내용이 없습니다.")
    } catch (error) {
      clearTimeout(timeoutId)
      console.error("Failed to fetch cloud document content:", error)
      setLoadingError("문서 내용을 불러오는데 실패했습니다.")
      setDocName(previewTitle)
      setDocType(previewType)
      setMarkdownContent("문서를 불러올 수 없습니다.")
    } finally {
      setIsLoadingContent(false)
    }
  }

  const handleLocalSave = () => {
    const updatedList = docList.map((doc) =>
      doc.doc_name === selectedFile ? { ...doc, doc_name: docName, doc_type: docType, content: markdownContent } : doc,
    )
    setDocList(updatedList)
    localStorage.setItem("doc_list", JSON.stringify(updatedList))
    // alert("로컬에 저장되었습니다!")
  }

  const handleRevert = () => {
    const saved = localStorage.getItem("doc_list")
    if (saved) {
      try {
        const parsedList = JSON.parse(saved)
        const doc = parsedList.find((d: Document) => d.doc_name === selectedFile)
        if (doc) {
          setMarkdownContent(doc.content)
          setDocName(doc.doc_name)
          setDocType(doc.doc_type)
          // alert("저장된 내용으로 되돌렸습니다!")
        }
      } catch (e) {
        console.error("Failed to revert", e)
      }
    }
  }

  const handleCloudSave = async () => {
    setIsSaving(true)
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
      const request: IndexRequest = {
        text: markdownContent,
        index_seq: 0,
        origin_type_code: "TEXT",
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/documents/index`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result: IndexResponse = await response.json()
      console.log("Cloud save response:", result)
      // alert(`클라우드에 저장되었습니다!`)
    } catch (error) {
      console.error("Cloud save error:", error)
      alert("클라우드 저장에 실패했습니다. 네트워크 연결을 확인해주세요.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleAddNewFile = () => {
    let counter = 1
    let newFileName = `new-document-${counter}.md`
    while (docList.some((doc) => doc.doc_name === newFileName)) {
      counter++
      newFileName = `new-document-${counter}.md`
    }

    const newDoc: Document = {
      doc_name: newFileName,
      doc_type: "문서",
      content: "# 새 문서\n\n내용을 입력하세요.",
    }

    const updatedList = [...docList, newDoc]
    setDocList(updatedList)
    localStorage.setItem("doc_list", JSON.stringify(updatedList))

    setSelectedFile(newFileName)
    setDocName(newFileName)
    setDocType(newDoc.doc_type)
    setMarkdownContent(newDoc.content)
  }

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden">
      {/* Header */}
      <header className="bg-gray-200 border-b border-gray-300 px-3 py-1 flex items-center justify-between flex-shrink-0">
  {/* Logo */}
  <div className="flex items-center">
    <Image
      src="/logo.png"
      // alt="AJC 솔루션"
      width={120}
      height={32}
      priority
    />
  </div>
      </header>

  

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal" className="h-full">
          {/* Left Sidebar Panel */}
          <Panel defaultSize={20} minSize={15} maxSize={40}>
            <aside className="h-full bg-gray-100 flex flex-col">
              <div className="p-2 border-b border-gray-300 flex-shrink-0">
                <h3 className="text-sm text-gray-600 mb-2">문서 제목</h3>
                <Input
                  type="text"
                  placeholder="제목을 입력하세요"
                  value={docName}
                  onChange={(e) => setDocName(e.target.value)}
                  className="w-full h-9 bg-white text-sm"
                />
              </div>

              <div className="p-2 border-b border-gray-300 flex-shrink-0">
                <h3 className="text-sm text-gray-600 mb-2">문서 유형</h3>
                <div className="relative">
                  <select
                    value={docType}
                    onChange={(e) => setDocType(e.target.value)}
                    className="w-full h-9 px-3 pr-8 bg-white border border-gray-300 rounded-md text-sm appearance-none cursor-pointer"
                  >
                    <option>가이드라인</option>
                    <option>메모</option>
                    <option>문서</option>
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                </div>
              </div>

              <div className="flex-1 p-2 overflow-auto">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm text-gray-600">파일</h3>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={handleAddNewFile}
                      className="p-1 hover:bg-gray-100 rounded"
                      disabled={storageMode === "cloud"}
                      title="새 파일 추가"
                    >
                      <Plus className={`w-4 h-4 ${storageMode === "cloud" ? "text-gray-300" : "text-gray-600"}`} />
                    </button>
                    <div className="flex items-center border border-gray-300 rounded overflow-hidden">
                      <button
                        onClick={() => setStorageMode("local")}
                        className={`p-1 transition-colors ${
                          storageMode === "local"
                            ? "bg-blue-500 text-white"
                            : "bg-white text-gray-600 hover:bg-gray-100"
                        }`}
                        title="로컬 저장소"
                      >
                        <Laptop className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setStorageMode("cloud")}
                        className={`p-1 transition-colors ${
                          storageMode === "cloud"
                            ? "bg-blue-500 text-white"
                            : "bg-white text-gray-600 hover:bg-gray-100"
                        }`}
                        title="클라우드 저장소"
                      >
                        <Cloud className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {isLoadingCloud ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                  </div>
                ) : storageMode === "local" ? (
                  <div className="space-y-1">
                    {docList.map((doc) => (
                      <button
                        key={doc.doc_name}
                        onClick={() => handleFileSelect(doc.doc_name)}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm ${
                          selectedFile === doc.doc_name ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        <FileText className="w-4 h-4" />
                        {doc.doc_name}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-1">
                    {cloudDocuments.length === 0 ? (
                      <div className="text-sm text-gray-500 text-center py-4">클라우드 문서가 없습니다.</div>
                    ) : (
                      cloudDocuments.map((doc) => (
                        <button
                          key={doc.recipe_seq}
                          onClick={() =>
                            handleCloudDocumentSelect(
                              doc.recipe_seq,
                              doc.title || `문서 ${doc.recipe_seq}`,
                              doc.doc_type_code,
                            )
                          }
                          className={`w-full flex items-start gap-2 px-3 py-2 rounded text-sm ${
                            selectedFile === `recipe_${doc.recipe_seq}`
                              ? "bg-blue-50 text-blue-700"
                              : "text-gray-700 hover:bg-gray-50"
                          }`}
                        >
                          <FileText className="w-4 h-4 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 text-left">
                            <div className="font-medium">{doc.title || `문서 ${doc.recipe_seq}`}</div>
                            <div className="text-xs text-gray-500 truncate">{doc.doc_type_code}</div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            </aside>
          </Panel>

          {/* Panel Resize Handle */}
          <PanelResizeHandle className="w-[1px] bg-gray-300 hover:bg-blue-500 hover:w-[2px] transition-all cursor-col-resize" />

          {/* Center Preview Panel */}
          <Panel defaultSize={40} minSize={25}>
            <div className="h-full bg-white overflow-y-auto">
              {isLoadingContent ? (
                <div className="flex flex-col items-center justify-center h-full gap-4">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                  <p className="text-sm text-gray-600">문서 내용을 불러오는 중...</p>
                  {loadingError && <p className="text-sm text-orange-600">{loadingError}</p>}
                </div>
              ) : (
                <div className="p-6">
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{markdownContent}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          </Panel>

          {/* Panel Resize Handle */}
          <PanelResizeHandle className="w-[1px] bg-gray-300 hover:bg-blue-500 hover:w-[3px] transition-all cursor-col-resize" />

          {/* Right Editor Panel */}
          <Panel defaultSize={40} minSize={25}>
            <div className="h-full flex flex-col bg-white overflow-hidden">
              <textarea
                value={markdownContent}
                onChange={(e) => setMarkdownContent(e.target.value)}
                className="flex-1 p-2 text-sm font-mono resize-none outline-none overflow-y-auto"
                placeholder="마크다운 내용을 입력하세요..."
              />
            </div>
          </Panel>
        </PanelGroup>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-300 px-4 py-2 flex items-center justify-between flex-shrink-0">
        <div />
        <div className="flex items-center gap-3">
          <Button
            variant="default"
            className="h-8 bg-blue-500 hover:bg-blue-700 text-white"
            onClick={handleCloudSave}
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                저장 중...
              </>
            ) : (
              <>
                <CloudUpload className="w-4 h-4 mr-2" />
                클라우드 저장
              </>
            )}
          </Button>
          <Button variant="default" className="h-8 bg-gray-600 hover:bg-gray-800 text-white" onClick={handleLocalSave}>
            <Save className="w-4 h-4 mr-2" />
            로컬 저장
          </Button>
          <Button variant="default" className="h-8 bg-red-600 hover:bg-red-700 text-white" onClick={handleRevert}>
            <Redo2 className="w-4 h-4 mr-2" />
            되돌리기
          </Button>
        </div>
      </footer>
    </div>
  )
}

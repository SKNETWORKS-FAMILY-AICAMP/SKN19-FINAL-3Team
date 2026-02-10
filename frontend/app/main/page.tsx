"use client"

import { Loader2 } from "lucide-react"

import { SearchBar } from "@/components/search-bar"
import { useState, useEffect, useRef } from "react"
import { apiClient } from "@/lib/api-client"
import { useRouter } from "next/navigation"
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels"
import { FilePanel } from "@/components/file-panel"
import { MarkdownViewer } from "@/components/markdown-viewer"
import { MarkdownEditor } from "@/components/markdown-editor"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
import { useConfirm } from "@/hooks/use-confirm"

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

interface CloudDocumentDetail {
  recipe_seq: number
  doc_type_code: string
  title: string
  text: string
  recipe_value: Record<string, unknown>
  created_at: string
  updated_at: string
}

interface IndexRequest {
  recipe_seq: number
  text: string
}

interface IndexResponse {
  task_id: string
  task_type: string
  task_status: string
}

interface TaskStatusResponse {
  task_id: string
  task_type: string
  task_status: string
}

interface Section {
  is_changed: boolean
  original_text: string
  section_seq: number
  text_seq: number
}

interface ProposalDocument {
  recipe_seq: number
  title: string
  sections: Section[]
}

interface ProposalResponse {
  target_recipes: ProposalDocument[]
  task_id: string
}

export default function MarkdownEditorPage() {
  const [docList, setDocList] = useState<Document[]>([
    { doc_name: "README.md", doc_type: "가이드라인", content: "## Markdown 문서 수정 및 확인이 가능" },
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
  const [currentRecipeSeq, setCurrentRecipeSeq] = useState<number | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("잠시만 기다려주세요.")
  const [autoRenameFile, setAutoRenameFile] = useState<string | null>(null)  // 로컬 파일 자동 리네임
  const [autoRenameRecipeSeq, setAutoRenameRecipeSeq] = useState<number | null>(null)  // 클라우드 문서 자동 리네임
  const [highlightEditorTitle, setHighlightEditorTitle] = useState(false)
  const router = useRouter()

  const handlePreviewClick = () => {
    setHighlightEditorTitle(true)
    setTimeout(() => {
      setHighlightEditorTitle(false)
    }, 300)
  }
  const searchParams = useSearchParams()
  const { confirm, ConfirmDialog } = useConfirm()

  const loadingMessages = [
    "문서를 분석하고 있습니다...",
    "AI가 변경 사항을 감지하고 있습니다...",
    "저장소와 동기화를 진행 중입니다...",
    "잠시만 기다려주세요...",
  ]

  // useEffect for dynamic loading messages removed in favor of progress-based updates

  useEffect(() => {
    // 로그인 상태 확인 및 리다이렉트
    const checkAuth = async () => {
      const isValid = await apiClient.validateToken()
      if (!isValid) {
        router.replace("/login")
        return
      }
      setIsLoggedIn(true)
    }
    checkAuth()

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

  const markdownRef = useRef(markdownContent)

  useEffect(() => {
    markdownRef.current = markdownContent
  }, [markdownContent])

  useEffect(() => {
    if (storageMode === "cloud") {
      fetchCloudDocuments()
    }
  }, [storageMode])

  // 개발중 오토세이브 끔
  if (false)
    useEffect(() => {
      const intervalId = setInterval(() => {
        if (!currentRecipeSeq || currentRecipeSeq <= 0) {
          return
        }

        handleAutoSave()
      }, 1000)

      return () => clearInterval(intervalId)
    }, [currentRecipeSeq])

  const fetchCloudDocuments = async () => {
    // apiClient 내부에서 토큰 유무 및 갱신을 처리하므로, 여기서는 단순히 호출만 하면 됩니다.
    // 단, UI 상태 처리를 위해 토큰 존재 여부를 확인하는 로직은 유지하거나 apiClient의 에러 핸들링에 맡길 수 있습니다.
    // 현재 구조상 로그인 상태(isLoggedIn)가 useEffect로 관리되므로, 이를 신뢰합니다.
    const isValid = await apiClient.validateToken()
    if (!isValid) {
      await confirm({ title: "알림", message: "로그인이 필요합니다.", variant: "alert" })
      setIsLoggedIn(false)
      setStorageMode("local")
      router.replace("/login")
      return
    }

    setIsLoadingCloud(true)
    try {
      // apiClient를 사용하여 요청. base url은 apiClient가 처리하므로 제외합니다.
      // fetchWithAuth는 내부적으로 /api/v1/auth/refresh 로직을 수행합니다.
      const response = await apiClient.fetchWithAuth("/api/v1/documents?skip=0&limit=100")

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const documents: CloudDocumentResponse[] = await response.json()
      setCloudDocuments(documents)
    } catch (error) {
      console.error("Failed to fetch cloud documents:", error)
      await confirm({ title: "오류", message: "클라우드 문서 목록을 불러오는데 실패했습니다.", variant: "alert" })
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
      setCurrentRecipeSeq(null) // 로컬 파일 선택 시 recipe_seq 초기화
    }
  }

  const handleCloudDocumentSelect = async (recipe_seq: number, previewTitle: string, previewType: string) => {
    const isValid = await apiClient.validateToken()
    if (!isValid) {
      await confirm({ title: "알림", message: "로그인이 필요합니다.", variant: "alert" })
      setIsLoggedIn(false)
      router.replace("/login")
      return
    }

    // 0 or negative seq means it's a new unsaved document
    if (recipe_seq <= 0) {
      const doc = cloudDocuments.find(d => d.recipe_seq === recipe_seq)
      setSelectedFile(`recipe_${recipe_seq}`)
      setDocName(doc?.title || previewTitle)
      setDocType(doc?.doc_type_code || previewType)
      setMarkdownContent(doc?.text || "")
      setCurrentRecipeSeq(recipe_seq)
      return
    }

    setSelectedFile(`recipe_${recipe_seq}`)
    setIsLoadingContent(true)
    setLoadingError(null)

    const timeoutId = setTimeout(() => {
      setLoadingError("문제가 발생했거나 로딩이 지연되고 있습니다.")
    }, 10000)

    try {
      // apiClient 사용
      const response = await apiClient.fetchWithAuth(`/api/v1/documents/${recipe_seq}`)

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const document: CloudDocumentDetail = await response.json()

      setDocName(document.title || previewTitle || `문서 ${recipe_seq}`)
      setDocType(document.doc_type_code || previewType)
      setMarkdownContent(document.text || "내용이 없습니다.")
      setCurrentRecipeSeq(recipe_seq) // 클라우드 문서 선택 시 recipe_seq 저장
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
    confirm({ title: "저장 완료", message: "로컬에 저장되었습니다!", variant: "alert" })
  }

  const handleAutoSave = async () => {
    const isValid = await apiClient.validateToken()
    if (!isValid) {
      await confirm({ title: "알림", message: "로그인이 필요합니다.", variant: "alert" })
      setIsLoggedIn(false)
      router.replace("/login")
      return
    }

    try {
      const recipeSeqToSend = (currentRecipeSeq && currentRecipeSeq > 0) ? currentRecipeSeq : 0

      const request = {
        recipe_seq: recipeSeqToSend,
        text: markdownRef.current,
      }

      const response = await apiClient.fetchWithAuth(
        "/api/v1/documents/local",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
        }
      )

      console.log("Saved")

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

    } catch (error) {
    }
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
          confirm({ title: "알림", message: "저장된 내용으로 되돌렸습니다!", variant: "alert" })
        }
      } catch (e) {
        console.error("Failed to revert", e)
      }
    }
  }



  const isSavingRef = useRef(false)

  // ... (existing code)

  const handleCloudSave = async () => {
    if (isSavingRef.current) {
      console.warn("handleCloudSave already in progress")
      return
    }
    isSavingRef.current = true

    const isValid = await apiClient.validateToken()
    if (!isValid) {
      await confirm({ title: "알림", message: "로그인이 필요합니다.", variant: "alert" })
      isSavingRef.current = false
      setIsLoggedIn(false)
      router.replace("/login")
      return
    }

    setIsSaving(true)
    setLoadingMessage("문서를 분석하고 있습니다...")

    try {
      console.log("Starting Cloud Save Flow")
      // Step 1: Indexing Request
      const recipeSeqToSend = (currentRecipeSeq && currentRecipeSeq > 0) ? currentRecipeSeq : 0
      const request: IndexRequest = {
        recipe_seq: recipeSeqToSend,
        text: markdownContent,
      }

      const indexResponse = await apiClient.fetchWithAuth("/api/v1/documents/index", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      })

      if (!indexResponse.ok) throw new Error(`Indexing failed: ${indexResponse.status}`)
      const indexResult: IndexResponse = await indexResponse.json()
      const taskId = indexResult.task_id

      console.log(`🌟 step: indexing, task_id: ${taskId}`)

      // Step 2: Polling Indexing Task
      setLoadingMessage("AI가 문서를 처리하고 있습니다...")
      await pollTask(taskId)

      console.log(`🌟 step: polling, task_id: ${taskId}`)

      // Step 3: Fetch Proposal -> Now returns Update Task ID directly
      const proposalResponse = await apiClient.fetchWithAuth(`/api/v1/documents/proposal?task_id=${taskId}`)
      if (!proposalResponse.ok) throw new Error(`Fetch proposal failed: ${proposalResponse.status}`)

      const proposalResult: TaskStatusResponse = await proposalResponse.json()
      const proposalTaskId = proposalResult.task_id
      const proposalTaskStatus = proposalResult.task_status

      console.log(`🌟 step: proposal, task_id: ${proposalTaskId}`)

      const applyFinalAndFinish = async (hasMergeSection: boolean, message: string) => {
        setLoadingMessage("자동으로 저장하고 있습니다...")
        const finalResponse = await apiClient.fetchWithAuth(`/api/v1/documents/apply_final`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task_id: proposalTaskId,
            has_merge_section: hasMergeSection,
            recipe_seq_list_selected: [recipeSeqToSend],
            title: recipeSeqToSend === 0 ? docName : undefined  // 신규 문서인 경우 현재 docName 전달
          })
        })

        if (!finalResponse.ok) throw new Error(`Final apply failed: ${finalResponse.status}`)

        // 백엔드 응답에서 recipe_seq 받기
        const finalResult = await finalResponse.json()
        const savedRecipeSeq = finalResult.recipe_seq

        // 신규 문서였다면 currentRecipeSeq를 업데이트
        if (recipeSeqToSend === 0 && savedRecipeSeq) {
          console.log(`[DEBUG] Updating currentRecipeSeq from 0 to ${savedRecipeSeq}`)
          setCurrentRecipeSeq(savedRecipeSeq)
          setSelectedFile(`recipe_${savedRecipeSeq}`)

          // 클라우드 문서 목록에서 음수 ID를 실제 ID로 업데이트
          if (currentRecipeSeq && currentRecipeSeq < 0) {
            setCloudDocuments(prev =>
              prev.map(doc =>
                doc.recipe_seq === currentRecipeSeq
                  ? { ...doc, recipe_seq: savedRecipeSeq, title: docName }
                  : doc
              )
            )
          }
        }

        await confirm({ title: "알림", message: message, variant: "alert" })

        if (storageMode === "cloud") {
          fetchCloudDocuments()
        }
      }

      // If task is already completed (e.g. no changes or fast process), apply immediately
      if (proposalTaskStatus === "COMPLETED") {
        await applyFinalAndFinish(false, "저장이 완료되었습니다.")
        return
      }
      else {
        await pollTask(proposalTaskId)
      }

      // Step 5: Fetch Selection to check results
      console.log("Fetching selection...")
      const selectionResponse = await apiClient.fetchWithAuth(`/api/v1/documents/selection?task_id=${proposalTaskId}`)
      if (!selectionResponse.ok) throw new Error(`Fetch selection failed: ${selectionResponse.status}`)

      const selectionData = await selectionResponse.json()

      // Check if there are any changes
      // Based on schema: recipes -> texts -> is_changed
      const hasChanges = selectionData.recipes?.some((recipe: any) =>
        recipe.texts?.some((text: any) => text.is_changed)
      )

      if (!hasChanges) {
        // No changes: automatically apply final
        await applyFinalAndFinish(true, "변경된 내용이 없어 자동으로 저장되었습니다.")
        return
      }

      // Step 6: Redirect to Merge Page for user confirmation
      sessionStorage.setItem(`merge_selection_${proposalTaskId}`, JSON.stringify(selectionData))
      router.push(`/merge?task_id=${proposalTaskId}`)

    } catch (error) {
      console.error("Cloud save failed:", error)
      await confirm({ title: "오류", message: "클라우드 저장 처리 중 오류가 발생했습니다.", variant: "alert" })
    } finally {
      setIsSaving(false)
      isSavingRef.current = false
    }
  }

  // Helper for polling
  const pollTask = async (taskId: string) => {
    const maxRetries = 120 // 1 minute timeout approx
    let retries = 0

    while (retries < maxRetries) {
      const response = await apiClient.fetchWithAuth(`/api/v1/tasks/${taskId}/status`)
      if (!response.ok) throw new Error(`Polling failed: ${response.status}`)

      const statusData: TaskStatusResponse = await response.json()

      if (statusData.task_status === "COMPLETED") {
        return
      } else if (statusData.task_status === "FAILED" || statusData.task_status === "ERROR") {
        throw new Error(`Task failed with status: ${statusData.task_status}`)
      }

      await new Promise(resolve => setTimeout(resolve, 1000))
      retries++
    }
    throw new Error("Task polling timed out")
  }

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    setIsLoggedIn(false)
    router.replace("/login")
  }

  const handleRenameFile = (oldName: string, newName: string) => {
    if (oldName === newName) return
    if (docList.some((doc) => doc.doc_name === newName)) {
      confirm({ title: "알림", message: "이미 존재하는 파일 이름입니다.", variant: "alert" })
      return
    }
    const updatedList = docList.map((doc) =>
      doc.doc_name === oldName ? { ...doc, doc_name: newName } : doc
    )
    setDocList(updatedList)
    localStorage.setItem("doc_list", JSON.stringify(updatedList))
    if (selectedFile === oldName) {
      setSelectedFile(newName)
      setDocName(newName)
    }
    // 리네임 완료 후 autoRenameFile 리셋
    setAutoRenameFile(null)
  }


  const handleCopyFile = (fileName: string) => {
    const doc = docList.find((d) => d.doc_name === fileName)
    if (!doc) return

    let counter = 1
    let newName = `${fileName.replace(".md", "")}-copy.md`
    while (docList.some((d) => d.doc_name === newName)) {
      counter++
      newName = `${fileName.replace(".md", "")}-copy-${counter}.md`
    }

    const newDoc: Document = {
      doc_name: newName,
      doc_type: doc.doc_type,
      content: doc.content,
    }

    const updatedList = [...docList, newDoc]
    setDocList(updatedList)
    localStorage.setItem("doc_list", JSON.stringify(updatedList))
  }

  const handleDeleteFile = async (fileName: string) => {
    const confirmed = await confirm({
      title: "파일 삭제",
      message: `"${fileName}" 파일을 삭제하시겠습니까?`,
    })
    if (!confirmed) return

    const updatedList = docList.filter((doc) => doc.doc_name !== fileName)
    setDocList(updatedList)
    localStorage.setItem("doc_list", JSON.stringify(updatedList))

    if (selectedFile === fileName && updatedList.length > 0) {
      const firstDoc = updatedList[0]
      setSelectedFile(firstDoc.doc_name)
      setDocName(firstDoc.doc_name)
      setDocType(firstDoc.doc_type)
      setMarkdownContent(firstDoc.content)
    }
  }

  const handleAddNewFile = () => {
    if (storageMode === "cloud") {
      const tempId = -Date.now() // 임시 음수 ID 생성
      const newDoc: CloudDocumentResponse = {
        recipe_seq: tempId,
        doc_type_code: "문서",
        title: "새 문서",
        text: "# 새 문서\n\n내용을 입력하세요.",
        recipe_value: "",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      setCloudDocuments([newDoc, ...cloudDocuments])
      setSelectedFile(`recipe_${tempId}`)
      setDocName(newDoc.title!)
      setDocType(newDoc.doc_type_code)
      setMarkdownContent(newDoc.text!)
      setCurrentRecipeSeq(tempId)

      // 클라우드 신규 문서 생성 후 자동으로 리네임 모드 진입
      setAutoRenameRecipeSeq(tempId)
    } else {
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
      setCurrentRecipeSeq(null) // 새 파일 생성 시 recipe_seq 초기화
      setStorageMode("local")

      // 새 파일 생성 후 자동으로 리네임 모드 진입
      setAutoRenameFile(newFileName)
    }
  }

  const handleRenameCloudDoc = async (recipeSeq: number, newTitle: string) => {
    // 신규 문서 (음수 ID)는 로컬 상태만 업데이트
    if (recipeSeq < 0) {
      setCloudDocuments((prev) =>
        prev.map((doc) => (doc.recipe_seq === recipeSeq ? { ...doc, title: newTitle } : doc)),
      )

      // Also update if selected
      if (currentRecipeSeq === recipeSeq) {
        setDocName(newTitle)
      }
      // 리네임 완료 후 autoRenameRecipeSeq 리셋
      setAutoRenameRecipeSeq(null)
      return
    }

    const isValid = await apiClient.validateToken()
    if (!isValid) {
      await confirm({ title: "알림", message: "로그인이 필요합니다.", variant: "alert" })
      setIsLoggedIn(false)
      router.replace("/login")
      return
    }

    try {
      const response = await apiClient.fetchWithAuth(`/api/v1/documents/${recipeSeq}/title`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "이름 변경 실패")
      }

      // Update successful, local update
      setCloudDocuments((prev) =>
        prev.map((doc) => (doc.recipe_seq === recipeSeq ? { ...doc, title: newTitle } : doc)),
      )

      // Also update if selected
      if (currentRecipeSeq === recipeSeq) {
        setDocName(newTitle)
      }
    } catch (e: any) {
      console.error(e)
      await confirm({ title: "오류", message: e.message, variant: "alert" })
    }
  }

  const handleDeleteCloudDoc = async (recipeSeq: number) => {
    // 클라우드 문서 삭제 전 커스텀 컨펌창 표시
    const doc = cloudDocuments.find((d) => d.recipe_seq === recipeSeq)
    const docTitle = doc?.title || `문서 ${recipeSeq}`

    const confirmed = await confirm({
      title: "클라우드 문서 삭제",
      message: `"${docTitle}" 문서를 삭제하시겠습니까?`,
    })

    if (!confirmed) return

    // 신규 문서 (음수 ID)는 로컬 상태에서만 삭제
    if (recipeSeq < 0) {
      setCloudDocuments((prev) => prev.filter((d) => d.recipe_seq !== recipeSeq))

      // 현재 선택된 문서였다면 선택 해제
      if (currentRecipeSeq === recipeSeq) {
        setCurrentRecipeSeq(null)
        setSelectedFile("")
        setMarkdownContent("")
        setDocName("")
        setDocType("")
      }

      return
    }

    // 로그인 확인
    const isValid = await apiClient.validateToken()
    if (!isValid) {
      alert("로그인이 필요합니다.")
      setIsLoggedIn(false)
      router.replace("/login")
      return
    }

    try {
      // API 호출하여 문서 삭제
      const response = await apiClient.fetchWithAuth(`/api/v1/documents/${recipeSeq}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error("문서 삭제 권한이 없습니다.")
        } else if (response.status === 404) {
          throw new Error("문서를 찾을 수 없습니다.")
        }
        throw new Error(`삭제 실패: ${response.status}`)
      }

      // 성공 시 로컬 상태 업데이트
      setCloudDocuments((prev) => prev.filter((d) => d.recipe_seq !== recipeSeq))

      // 현재 선택된 문서였다면 선택 해제
      if (currentRecipeSeq === recipeSeq) {
        setCurrentRecipeSeq(null)
        setSelectedFile("")
        setMarkdownContent("")
        setDocName("")
        setDocType("")
      }

      await confirm({ title: "성공", message: "문서가 성공적으로 삭제되었습니다.", variant: "alert" })
    } catch (error: any) {
      console.error("문서 삭제 실패:", error)
      await confirm({ title: "오류", message: error.message || "문서 삭제 중 오류가 발생했습니다.", variant: "alert" })

    }
  }


  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden relative">
      <ConfirmDialog />
      <div className="absolute top-2 left-1/2 -translate-x-1/2 z-50 w-[450px]">
        <Suspense fallback={null}>
          <SearchBar
            placeholder="문서 검색..."
            onSearch={(query) => console.log("Search:", query)}
            onSelectResult={(result) => {
              if (result.type === "로컬") {
                setStorageMode("local")
                handleFileSelect(result.title)
              } else {
                setStorageMode("cloud")
                handleCloudDocumentSelect(result.id, result.title, result.type)
              }
            }}
          />
        </Suspense>
      </div>
      <Header isLoggedIn={isLoggedIn} onLogout={handleLogout} />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal" className="h-full">
          <Panel defaultSize={20} minSize={15} maxSize={40}>
            <FilePanel
              docList={docList}
              cloudDocuments={cloudDocuments}
              selectedFile={selectedFile}
              docName={docName}
              docType={docType}
              storageMode={storageMode}
              isLoadingCloud={isLoadingCloud}
              isLoggedIn={isLoggedIn}
              autoRenameFile={autoRenameFile}
              autoRenameRecipeSeq={autoRenameRecipeSeq}
              onDocNameChange={setDocName}
              onDocTypeChange={setDocType}
              onFileSelect={handleFileSelect}
              onCloudDocumentSelect={handleCloudDocumentSelect}
              onStorageModeChange={setStorageMode}
              onAddNewFile={handleAddNewFile}
              onRenameFile={handleRenameFile}
              onCopyFile={handleCopyFile}
              onDeleteFile={handleDeleteFile}
              onRenameCloudDoc={handleRenameCloudDoc}
              onDeleteCloudDoc={handleDeleteCloudDoc}
            />

          </Panel>

          <PanelResizeHandle className="w-[1px] bg-border hover:bg-primary hover:w-[2px] transition-all cursor-col-resize" />

          {/* Editor Panel */}
          <Panel defaultSize={40} minSize={25}>
            <div className="h-full flex flex-col bg-background">
              <div className={`h-9 flex items-center px-4 border-b border-border transition-colors duration-300 ${highlightEditorTitle ? "bg-primary/20" : "bg-muted/50"
                }`}>
                <span
                  className={`text-xs font-semibold uppercase tracking-wider transition-all duration-300 ${highlightEditorTitle ? "text-primary scale-110 font-bold" : "text-muted-foreground"
                    }`}
                >
                  편집
                </span>
              </div>
              <div className="flex-1 overflow-hidden">
                <MarkdownEditor content={markdownContent} onChange={setMarkdownContent} />
              </div>
            </div>
          </Panel>

          <PanelResizeHandle className="w-[1px] bg-border hover:bg-primary hover:w-[2px] transition-all cursor-col-resize" />

          {/* Preview Panel */}
          <Panel defaultSize={40} minSize={25}>
            <div
              className="h-full flex flex-col bg-muted cursor-pointer"
              onClick={handlePreviewClick}
            >
              <div className="h-9 flex items-center px-4 bg-muted/50 border-b border-border">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">미리보기</span>
              </div>
              <div className="flex-1 overflow-hidden">
                <MarkdownViewer content={markdownContent} isLoading={isLoadingContent} loadingError={loadingError} />
              </div>
            </div>
          </Panel>
        </PanelGroup>
      </div>

      {/* Full Screen Loading Overlay */}
      {isSaving && (
        <div className="absolute inset-0 z-[100] bg-black/50 flex flex-col items-center justify-center text-white backdrop-blur-sm">
          <Loader2 className="w-12 h-12 animate-spin mb-4 text-blue-400" />
          <p className="text-xl font-semibold">클라우드 저장 처리 중...</p>
          <p className="text-sm text-gray-200 mt-2 min-h-[20px] transition-all duration-300">{loadingMessage}</p>
        </div>
      )}

      <Footer
        isSaving={isSaving}
        isLoggedIn={isLoggedIn}
        onCloudSave={handleCloudSave}
        onLocalSave={handleLocalSave}
        onRevert={handleRevert}
      />
    </div>
  )
}

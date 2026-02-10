"use client"

import { Button } from "@/components/ui/button"
import { CloudUpload, Save, Redo2, Loader2 } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

interface FooterProps {
  isSaving: boolean
  isLoggedIn: boolean
  onCloudSave: () => void
  onLocalSave: () => void
  onRevert: () => void
}

export function Footer({ isSaving, isLoggedIn, onCloudSave, onLocalSave, onRevert }: FooterProps) {
  return (
    <footer className="bg-white border-t border-gray-300 px-4 py-2 flex items-center justify-between flex-shrink-0">
      <div />
      <div className="flex items-center gap-3">
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="default"
              className="h-8 bg-blue-500 hover:bg-blue-700 text-white disabled:bg-gray-400"
              disabled={isSaving || !isLoggedIn}
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  저장 중...
                </>
              ) : (
                <>
                  <CloudUpload className="w-4 h-4" />
                  클라우드 저장
                </>
              )}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>저장 확인</AlertDialogTitle>
              <AlertDialogDescription>
                저장 하시겠습니까?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>아니오</AlertDialogCancel>
              <AlertDialogAction onClick={onCloudSave}>예</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        <Button variant="default" className="h-8 bg-gray-600 hover:bg-gray-800 text-white" onClick={onLocalSave}>
          <Save className="w-4 h-4" />
          로컬 저장
        </Button>
        <Button variant="default" className="h-8 bg-red-600 hover:bg-red-700 text-white" onClick={onRevert}>
          <Redo2 className="w-4 h-4" />
          초기화
        </Button>
      </div>
    </footer>
  )
}

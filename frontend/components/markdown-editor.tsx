"use client"

interface MarkdownEditorProps {
  content: string
  onChange: (content: string) => void
}

export function MarkdownEditor({ content, onChange }: MarkdownEditorProps) {
  return (
    <div className="h-full flex flex-col bg-white overflow-hidden">
      <textarea
        value={content}
        onChange={(e) => onChange(e.target.value)}
        className="flex-1 p-2 text-sm font-mono resize-none outline-none overflow-y-auto"
        placeholder="마크다운 내용을 입력하세요..."
      />
    </div>
  )
}

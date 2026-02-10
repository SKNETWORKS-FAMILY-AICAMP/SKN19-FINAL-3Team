"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeRaw from "rehype-raw"
import { Loader2 } from "lucide-react"
import { DiffViewer } from "./diff-viewer"

interface Section {
  is_changed: boolean
  original_text: string
  text_before?: string // Optional compatibility
  text_after?: string | null
  section_seq: number
  text_seq: number
}

interface MarkdownViewerProps {
  content?: string
  sections?: Section[]
  isLoading: boolean
  loadingError: string | null
}

export function MarkdownViewer({ content, sections, isLoading, loadingError }: MarkdownViewerProps) {
  const components = {
    h1: ({ node, ...props }: any) => <h1 className="text-4xl font-bold mb-4 mt-6" {...props} />,
    h2: ({ node, ...props }: any) => <h2 className="text-3xl font-bold mb-3 mt-5" {...props} />,
    h3: ({ node, ...props }: any) => <h3 className="text-2xl font-bold mb-2 mt-4" {...props} />,
    h4: ({ node, ...props }: any) => <h4 className="text-xl font-bold mb-2 mt-3" {...props} />,
    h5: ({ node, ...props }: any) => <h5 className="text-lg font-bold mb-1 mt-2" {...props} />,
    h6: ({ node, ...props }: any) => <h6 className="text-base font-bold mb-1 mt-2" {...props} />,
    p: ({ node, ...props }: any) => <p className="text-base leading-relaxed mb-4" {...props} />,
    a: ({ node, ...props }: any) => <a className="text-blue-600 hover:text-blue-800 underline" {...props} />,
    ul: ({ node, ...props }: any) => <ul className="list-disc list-inside mb-4 space-y-2" {...props} />,
    ol: ({ node, ...props }: any) => <ol className="list-decimal list-inside mb-4 space-y-2" {...props} />,
    li: ({ node, ...props }: any) => <li className="text-base" {...props} />,
    blockquote: ({ node, ...props }: any) => (
      <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700 my-4" {...props} />
    ),
    code: ({ node, inline, ...props }: any) =>
      inline ? (
        <code className="bg-gray-100 text-pink-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
      ) : (
        <code
          className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto font-mono text-sm"
          {...props}
        />
      ),
    pre: ({ node, ...props }: any) => <pre className="mb-4" {...props} />,
    table: ({ node, ...props }: any) => (
      <div className="overflow-x-auto mb-4">
        <table className="min-w-full border-collapse border border-gray-300" {...props} />
      </div>
    ),
    thead: ({ node, ...props }: any) => <thead className="bg-gray-100" {...props} />,
    th: ({ node, ...props }: any) => (
      <th className="border border-gray-300 px-4 py-2 text-left font-semibold" {...props} />
    ),
    td: ({ node, ...props }: any) => <td className="border border-gray-300 px-4 py-2" {...props} />,
    hr: ({ node, ...props }: any) => <hr className="my-6 border-t-2 border-gray-300" {...props} />,
    img: ({ node, ...props }: any) => <img className="max-w-full h-auto rounded-lg my-4" {...props} />,
    mark: ({ node, ...props }: any) => <mark className="bg-yellow-200 text-gray-900 px-1 rounded" {...props} />,
  }

  return (
    <div className="h-full bg-white overflow-y-auto">
      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-sm text-gray-600">문서 내용을 불러오는 중...</p>
          {loadingError && <p className="text-sm text-orange-600">{loadingError}</p>}
        </div>
      ) : (
        <div className="p-4">
          <article className="prose prose-slate prose-lg max-w-none">
            {sections ? (
              // Render by sections if provided
              sections.map((section, idx) => (
                <div
                  key={`${section.section_seq}-${idx}`}
                  className={section.is_changed ? "bg-yellow-50 p-4 rounded-lg border border-yellow-200 -mx-2 my-2" : ""}
                >
                  {section.is_changed && section.text_after ? (
                    <DiffViewer
                      beforeText={section.text_before || section.original_text}
                      afterText={section.text_after}
                    />
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                      components={components}
                    >
                      {section.original_text}
                    </ReactMarkdown>
                  )}
                </div>
              ))
            ) : (
              // Fallback to content string
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={components}
              >
                {content || ""}
              </ReactMarkdown>
            )}
          </article>
        </div>
      )}
    </div>
  )
}


"use client"

import { diff_match_patch, DIFF_DELETE, DIFF_INSERT, DIFF_EQUAL } from "diff-match-patch"
import { useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeRaw from "rehype-raw"
import { Eye, Code, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"

interface DiffViewerProps {
    beforeText: string
    afterText: string
}

export function DiffViewer({ beforeText, afterText }: DiffViewerProps) {
    const [diffs, setDiffs] = useState<[number, string][]>([])
    const [beforeViewMode, setBeforeViewMode] = useState<"preview" | "code">("preview")
    const [afterViewMode, setAfterViewMode] = useState<"preview" | "code">("preview")

    useEffect(() => {
        const dmp = new diff_match_patch()
        const diff = dmp.diff_main(beforeText, afterText)
        // dmp.diff_cleanupSemantic(diff) // Removed to improve markdown structural rendering
        setDiffs(diff)
    }, [beforeText, afterText])

    // Helper to generate markdown with embedded styles for diffs
    const getHighlightedMarkdown = (type: "before" | "after") => {
        return diffs.reduce((acc, part) => {
            const [op, text] = part

            // STRICT FILTERING: 
            // - Before view should NOT show inserted text
            // - After view should NOT show deleted text
            if (op === DIFF_INSERT && type === "before") return acc
            if (op === DIFF_DELETE && type === "after") return acc

            if (op === DIFF_EQUAL) {
                return acc + text
            }

            // Define highlight styles
            // Use background color and text color. 
            // Avoid padding on empty lines to prevent visual artifacts.
            const isDelete = op === DIFF_DELETE
            const baseStyle = isDelete
                ? "background-color: #fecaca; color: #7f1d1d;"
                : "background-color: #bbf7d0; color: #14532d;"

            // Process per line to preserve Markdown structure
            const lines = text.split('\n')
            const processedLines = lines.map((line) => {
                if (!line) return "" // Handle empty split artifacts if any, or preserve empty lines

                // Regex to capture Markdown structural markers that must remain OUTSIDE the span
                // Captures: 
                // 1. Headers (e.g., "# ", "## ")
                // 2. Unordered lists (e.g., "- ", "* ")
                // 3. Ordered lists (e.g., "1. ")
                // 4. Blockquotes (e.g., "> ")
                const structureMatch = line.match(/^(\s*(?:#{1,6}|-|\*|\d+\.|>)\s+)(.*)$/)

                if (structureMatch) {
                    const marker = structureMatch[1]
                    const body = structureMatch[2]
                    // If body is empty (just a marker), don't style it
                    if (!body.trim()) return line

                    return `${marker}<span style="${baseStyle} border-radius: 2px; padding: 0 2px;">${body}</span>`
                } else {
                    // Plain line
                    if (!line.trim()) return line // Do not highlight empty whitespace lines
                    return `<span style="${baseStyle} border-radius: 2px; padding: 0 2px;">${line}</span>`
                }
            })

            return acc + processedLines.join('\n')
        }, "")
    }

    const components = {
        h1: ({ node, ...props }: any) => <h1 className="text-2xl font-bold mb-3 mt-4" {...props} />,
        h2: ({ node, ...props }: any) => <h2 className="text-xl font-bold mb-2 mt-3" {...props} />,
        h3: ({ node, ...props }: any) => <h3 className="text-lg font-bold mb-2 mt-3" {...props} />,
        p: ({ node, ...props }: any) => <p className="text-sm leading-relaxed mb-2" {...props} />,
        ul: ({ node, ...props }: any) => <ul className="list-disc list-inside mb-2" {...props} />,
        ol: ({ node, ...props }: any) => <ol className="list-decimal list-inside mb-2" {...props} />,
        li: ({ node, ...props }: any) => <li className="text-sm" {...props} />,
        blockquote: ({ node, ...props }: any) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700 my-2" {...props} />,
        code: ({ node, inline, ...props }: any) =>
            inline ? <code className="bg-gray-100 text-pink-600 px-1 py-0.5 rounded text-xs font-mono" {...props} /> : <code className="block bg-gray-900 text-gray-100 p-2 rounded overflow-x-auto font-mono text-xs" {...props} />,
        // specific styling for spans if needed, but style attribute handles it
        span: ({ node, ...props }: any) => <span {...props} />,
    }

    return (
        <div className="flex flex-col gap-3 font-mono text-sm leading-relaxed relative">
            {/* Before View */}
            <div className="bg-red-50 border border-red-100 rounded-lg overflow-hidden">
                <div className="bg-red-100/50 px-3 py-1.5 border-b border-red-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-red-600 uppercase tracking-wider">Before (변경 전)</span>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 px-2 text-[10px] bg-white/50 hover:bg-white border border-red-200 text-red-700 rounded shadow-sm gap-1"
                        onClick={() => setBeforeViewMode(beforeViewMode === "preview" ? "code" : "preview")}
                    >
                        {beforeViewMode === "preview" ? <Code className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                        {beforeViewMode === "preview" ? "Markdown" : "Preview"}
                    </Button>
                </div>
                <div className="p-3 text-gray-700">
                    {beforeViewMode === "code" ? (
                        <div className="whitespace-pre-wrap break-all">
                            {diffs.map((part, index) => {
                                const [type, text] = part
                                if (type === DIFF_EQUAL) {
                                    return <span key={index}>{text}</span>
                                } else if (type === DIFF_DELETE) {
                                    return (
                                        <span key={index} className="bg-red-200 text-red-900 decoration-red-900/50 px-0.5 rounded-sm">
                                            {text}
                                        </span>
                                    )
                                }
                                return null
                            })}
                        </div>
                    ) : (
                        <div className="prose prose-sm max-w-none text-gray-700">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]} components={components}>
                                {getHighlightedMarkdown("before")}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            </div>

            {/* Arrow Indicator */}
            <div className="flex justify-center text-gray-400 -my-2 z-10">
                <div className="bg-white rounded-full p-1 border border-gray-200 shadow-sm">
                    <ArrowRight className="w-4 h-4 rotate-90" />
                </div>
            </div>

            {/* After View */}
            <div className="bg-green-50 border border-green-100 rounded-lg overflow-hidden">
                <div className="bg-green-100/50 px-3 py-1.5 border-b border-green-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-green-600 uppercase tracking-wider">After (변경 후)</span>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 px-2 text-[10px] bg-white/50 hover:bg-white border border-green-200 text-green-700 rounded shadow-sm gap-1"
                        onClick={() => setAfterViewMode(afterViewMode === "preview" ? "code" : "preview")}
                    >
                        {afterViewMode === "preview" ? <Code className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                        {afterViewMode === "preview" ? "Markdown" : "Preview"}
                    </Button>
                </div>
                <div className="p-3 text-gray-800">
                    {afterViewMode === "code" ? (
                        <div className="whitespace-pre-wrap break-all">
                            {diffs.map((part, index) => {
                                const [type, text] = part
                                if (type === DIFF_EQUAL) {
                                    return <span key={index}>{text}</span>
                                } else if (type === DIFF_INSERT) {
                                    return (
                                        <span key={index} className="bg-green-200 text-green-900 px-0.5 rounded-sm">
                                            {text}
                                        </span>
                                    )
                                }
                                return null
                            })}
                        </div>
                    ) : (
                        <div className="prose prose-sm max-w-none text-gray-800">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]} components={components}>
                                {getHighlightedMarkdown("after")}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

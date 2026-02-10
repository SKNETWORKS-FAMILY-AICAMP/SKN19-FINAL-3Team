"use client"

import React from "react"
import { createPortal } from "react-dom"
import { useState, useRef, useEffect } from "react"
import { Search, X, FileText, Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface SearchBarProps {
  onSearch?: (query: string) => void
  onSelectResult?: (result: SearchResult) => void
  placeholder?: string
}

interface SearchResult {
  id: number
  title: string
  type: string // "로컬" | "클라우드"
  preview: string
}

export function SearchBar({
  onSearch,
  onSelectResult,
  placeholder = "문서 검색...",
}: SearchBarProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [query, setQuery] = useState("")
  const [storageType, setStorageType] = useState<"local" | "cloud">("cloud")
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [mounted, setMounted] = useState(false)

  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // --------------------
  // Debounce Search
  // --------------------
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) {
        fetchSearchResults(query)
      } else {
        setSearchResults([])
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query, storageType])

  const fetchSearchResults = async (searchQuery: string) => {
    setIsLoading(true)
    try {
      const encodedQuery = encodeURIComponent(searchQuery)
      const response = await apiClient.fetchWithAuth(
        `/api/v1/documents/search?q=${encodedQuery}&type=${storageType}`
      )

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`)
      }

      const data: SearchResult[] = await response.json()
      setSearchResults(data)
    } catch (error) {
      console.error("Search error:", error)
      setSearchResults([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isExpanded])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (onSearch && query.trim()) {
      onSearch(query)
      setIsExpanded(false)
    }
  }

  const handleClear = () => {
    setQuery("")
    setSearchResults([])
    inputRef.current?.focus()
  }

  const handleSelectResult = (result: SearchResult) => {
    onSelectResult?.(result)
    setIsExpanded(false)
  }

  return (
    <div ref={containerRef} className="relative flex items-center justify-center">
      {/* Collapsed Button */}
      {!isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className="flex items-center gap-2 px-6 h-9 bg-card border border-border rounded-md text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-all shadow-sm"
        >
          <Search className="w-4 h-4" />
          <span className="hidden sm:inline">검색</span>
        </button>
      )}

      {/* Expanded Search */}
      {isExpanded && mounted &&
        createPortal(
          <div className="fixed inset-0 z-[100] flex items-start justify-center pt-4">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
              onClick={() => setIsExpanded(false)}
            />

            {/* Left: Storage Toggle */}
            <div className="relative z-10 mr-10">
              <div className="flex bg-muted p-1 rounded-lg border border-border gap-1">
                {(["local", "cloud"] as const).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setStorageType(type)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${storageType === type
                      ? "bg-card text-foreground shadow-sm ring-1 ring-black/5"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                      }`}
                  >
                    {type === "local" ? "로컬" : "클라우드"}
                  </button>
                ))}
              </div>
            </div>

            {/* Search Box */}
            <div className="relative z-10 w-[300px] md:w-[500px]">
              <form onSubmit={handleSubmit}>
                <div className="bg-card border border-border rounded-xl shadow-2xl overflow-hidden ring-1 ring-black/5">
                  {/* Input */}
                  <div className="flex items-center border-b border-border">
                    <Search className="w-5 h-5 text-muted-foreground ml-2" />
                    <input
                      ref={inputRef}
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder={placeholder}
                      className="flex-1 px-2 py-2 text-base outline-none bg-transparent text-foreground placeholder:text-muted-foreground"
                    />
                    {query ? (
                      <button
                        type="button"
                        onClick={handleClear}
                        className="mr-2 p-1 hover:bg-accent rounded-full text-muted-foreground"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setIsExpanded(false)}
                        className="mr-2 text-xs text-muted-foreground"
                      >
                        ESC
                      </button>
                    )}
                  </div>

                  {/* Results */}
                  <div className="max-h-[60vh] overflow-y-auto bg-card">
                    {isLoading ? (
                      <div className="py-12 text-center">
                        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
                        <p className="text-sm text-muted-foreground">검색중...</p>
                      </div>
                    ) : searchResults.length > 0 ? (
                      <ul className="py-2">
                        {searchResults.map((result) => (
                          <li key={result.id}>
                            <button
                              type="button"
                              onClick={() => handleSelectResult(result)}
                              className="w-full flex gap-3 px-4 py-3 text-left hover:bg-accent hover:text-accent-foreground transition-colors"
                            >
                              <FileText className="w-4 h-4 mt-1 text-muted-foreground" />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-semibold truncate text-foreground">
                                    {result.title}
                                  </span>
                                  <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-border bg-muted text-muted-foreground">
                                    {result.type}
                                  </span>
                                </div>
                                <p className="text-xs text-muted-foreground truncate">
                                  {result.preview}
                                </p>
                              </div>
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : query.trim() ? (
                      <div className="py-12 text-center text-sm text-muted-foreground">
                        검색 결과가 없습니다.
                      </div>
                    ) : (
                      <div className="py-12 text-center text-sm text-muted-foreground">
                        문서를 검색해보세요.
                      </div>
                    )}
                  </div>
                </div>
              </form>
            </div>
          </div>,
          document.body
        )}
    </div>
  )
}

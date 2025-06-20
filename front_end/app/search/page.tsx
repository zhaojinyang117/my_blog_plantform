"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import SearchBox from "@/components/search/search-box"
import SearchResults from "@/components/search/search-results"
import { Card, CardContent } from "@/components/ui/card"

function SearchPageContent() {
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''
  const type = searchParams.get('type') || 'all'
  const ordering = searchParams.get('ordering') || '-created_at'

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* 搜索框 */}
      <div className="max-w-2xl mx-auto">
        <SearchBox 
          placeholder="搜索文章、作者..."
          className="w-full"
          showSuggestions={true}
        />
      </div>

      {/* 搜索结果 */}
      {query ? (
        <SearchResults 
          initialQuery={query}
          initialType={type}
          initialOrdering={ordering}
        />
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <h2 className="text-2xl font-bold mb-4">搜索文章</h2>
            <p className="text-muted-foreground text-center max-w-md">
              在上方输入关键词来搜索文章。你可以搜索文章标题、内容或作者名称。
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto mb-8">
          <div className="h-10 bg-muted rounded animate-pulse" />
        </div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="space-y-3">
                  <div className="h-6 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2" />
                  <div className="h-4 bg-muted rounded w-full" />
                  <div className="h-4 bg-muted rounded w-5/6" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    }>
      <SearchPageContent />
    </Suspense>
  )
}

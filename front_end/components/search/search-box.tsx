"use client"

import { useState, useRef, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Search, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface SearchBoxProps {
  placeholder?: string
  className?: string
  showSuggestions?: boolean
}

export default function SearchBox({ 
  placeholder = "搜索文章...", 
  className = "",
  showSuggestions = true 
}: SearchBoxProps) {
  const [query, setQuery] = useState("")
  const [isOpen, setIsOpen] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)

  // 从localStorage获取搜索历史
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const history = localStorage.getItem('searchHistory')
      if (history) {
        try {
          const parsedHistory = JSON.parse(history)
          setSuggestions(parsedHistory.slice(0, 5)) // 只显示最近5条
        } catch (error) {
          console.error('解析搜索历史失败:', error)
        }
      }
    }
  }, [])

  const handleSearch = (searchQuery: string = query) => {
    const trimmedQuery = searchQuery.trim()
    if (!trimmedQuery) return

    // 保存到搜索历史
    saveToSearchHistory(trimmedQuery)
    
    // 跳转到搜索结果页
    router.push(`/search?q=${encodeURIComponent(trimmedQuery)}`)
    setIsOpen(false)
  }

  const saveToSearchHistory = (searchQuery: string) => {
    if (typeof window === 'undefined') return

    try {
      const history = localStorage.getItem('searchHistory')
      let searchHistory: string[] = history ? JSON.parse(history) : []
      
      // 移除重复项
      searchHistory = searchHistory.filter(item => item !== searchQuery)
      
      // 添加到开头
      searchHistory.unshift(searchQuery)
      
      // 限制历史记录数量
      searchHistory = searchHistory.slice(0, 10)
      
      localStorage.setItem('searchHistory', JSON.stringify(searchHistory))
      setSuggestions(searchHistory.slice(0, 5))
    } catch (error) {
      console.error('保存搜索历史失败:', error)
    }
  }

  const clearSearchHistory = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('searchHistory')
      setSuggestions([])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSearch()
    }
    if (e.key === 'Escape') {
      setIsOpen(false)
      inputRef.current?.blur()
    }
  }

  return (
    <div className={`relative ${className}`}>
      {showSuggestions ? (
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverTrigger asChild>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                ref={inputRef}
                type="text"
                placeholder={placeholder}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsOpen(true)}
                className="pl-10 pr-10"
              />
              {query && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                  onClick={() => setQuery("")}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          </PopoverTrigger>
          <PopoverContent className="w-[400px] p-0" align="start">
            <Command>
              <CommandInput
                placeholder="搜索文章..."
                value={query}
                onValueChange={setQuery}
              />
              <CommandList>
                {suggestions.length > 0 ? (
                  <CommandGroup heading="搜索历史">
                    {suggestions.map((suggestion, index) => (
                      <CommandItem
                        key={index}
                        onSelect={() => handleSearch(suggestion)}
                        className="cursor-pointer"
                      >
                        <Search className="mr-2 h-4 w-4" />
                        {suggestion}
                      </CommandItem>
                    ))}
                    <CommandItem
                      onSelect={clearSearchHistory}
                      className="cursor-pointer text-muted-foreground"
                    >
                      <X className="mr-2 h-4 w-4" />
                      清除搜索历史
                    </CommandItem>
                  </CommandGroup>
                ) : (
                  <CommandEmpty>暂无搜索历史</CommandEmpty>
                )}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      ) : (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            ref={inputRef}
            type="text"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="pl-10 pr-10"
          />
          {query && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
              onClick={() => setQuery("")}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

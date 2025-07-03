// 文章缓存管理
const articleCache = new Map<string, { article: any; timestamp: number }>()
const CACHE_DURATION = parseInt(process.env.NEXT_PUBLIC_CACHE_DURATION || '5000') // 缓存时间（毫秒）

export const getCachedArticle = (articleId: string) => {
  const cached = articleCache.get(articleId)
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.article
  }
  return null
}

export const setCachedArticle = (articleId: string, article: any) => {
  articleCache.set(articleId, {
    article,
    timestamp: Date.now()
  })
}

export const clearArticleCache = (articleId?: string) => {
  if (articleId) {
    articleCache.delete(articleId)
  } else {
    articleCache.clear()
  }
}
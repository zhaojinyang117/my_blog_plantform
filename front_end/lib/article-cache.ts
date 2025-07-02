// 文章缓存管理
const articleCache = new Map<string, { article: any; timestamp: number }>()
const CACHE_DURATION = 5000 // 5秒缓存时间

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
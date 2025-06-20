"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Eye } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface Article {
  id: number;
  title: string;
  author_name: string;
  view_count: number;
  created_at: string;
}

interface PopularArticlesProps {
  limit?: number;
}

export default function PopularArticles({ limit = 10 }: PopularArticlesProps) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPopularArticles();
  }, []);

  const fetchPopularArticles = async () => {
    try {
      const response = await fetch('/api/articles/hot');
      if (!response.ok) {
        throw new Error('Failed to fetch popular articles');
      }
      const data = await response.json();
      // 如果有limit属性，只取前limit个文章
      setArticles(limit ? data.slice(0, limit) : data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>热门文章</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>热门文章</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">加载失败: {error}</p>
        </CardContent>
      </Card>
    );
  }

  if (articles.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>热门文章</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">暂无热门文章</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>热门文章</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {articles.map((article, index) => (
            <div key={article.id} className="flex items-start gap-3">
              <Badge variant="secondary" className="mt-1">
                {index + 1}
              </Badge>
              <div className="flex-1 min-w-0">
                <Link
                  href={`/articles/${article.id}`}
                  className="text-sm font-medium hover:underline line-clamp-2"
                >
                  {article.title}
                </Link>
                <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                  <span>{article.author_name}</span>
                  <div className="flex items-center gap-1">
                    <Eye className="h-3 w-3" />
                    <span>{article.view_count}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
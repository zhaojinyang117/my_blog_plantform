"use client"

import SiteStats from "@/components/dashboard/site-stats"
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function StatsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* 页面标题 */}
        <div className="text-center">
          <h1 className="text-3xl font-bold">数据统计</h1>
          <p className="text-muted-foreground mt-2">
            博客平台的整体数据概览和趋势分析
          </p>
        </div>

        {/* 统计组件 */}
        <SiteStats />

        {/* 说明卡片 */}
        <Card>
          <CardHeader>
            <CardTitle>关于统计数据</CardTitle>
            <CardDescription>
              <ul className="list-disc list-inside space-y-1 mt-2">
                <li>文章阅读量会在每次访问时自动增加</li>
                <li>只统计已发布的文章，草稿不计入统计</li>
                <li>热门文章根据阅读量实时排序</li>
                <li>发布趋势显示最近6个月的数据</li>
              </ul>
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </div>
  )
}
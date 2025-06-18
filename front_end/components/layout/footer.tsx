export default function Footer() {
  return (
    <footer className="py-6 md:py-8 border-t bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-center gap-4 md:h-20 md:flex-row md:justify-between lg:justify-center lg:gap-8">
          {/* 版权信息 */}
          <div className="text-center md:text-right lg:text-center">
            <p className="text-sm leading-loose text-muted-foreground lg:text-base">
              &copy; {new Date().getFullYear()} 我的博客. 版权所有.
            </p>
          </div>

          {/* 技术信息 */}
          <div className="text-center md:text-left lg:text-center">
            <p className="text-sm leading-loose text-muted-foreground lg:text-base">
              基于 Next.js 和 Django 构建.
            </p>
          </div>
        </div>

        {/* 在大屏幕上居中显示的额外信息 */}
        <div className="hidden lg:block mt-4 pt-4 border-t border-border/40">
          <div className="text-center">
            <p className="text-xs text-muted-foreground/80">
              一个现代化的全栈博客平台 • 支持 Markdown • 响应式设计
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}

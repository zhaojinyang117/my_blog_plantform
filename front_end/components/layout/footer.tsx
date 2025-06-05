export default function Footer() {
  return (
    <footer className="py-6 md:px-8 md:py-0 border-t">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-20 md:flex-row">
        <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
          &copy; {new Date().getFullYear()} 我的博客. 版权所有.
        </p>
        <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
          基于 Next.js 和 Django 构建.
        </p>
      </div>
    </footer>
  )
}

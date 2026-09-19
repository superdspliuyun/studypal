import { useState } from 'react';
import ThemeToggle from './ThemeToggle';

export type SidebarView = 'analytics' | 'chat-advice' | 'goals';

interface SidebarProps {
  activeView: SidebarView;
  onChangeView: (view: SidebarView) => void;
}

interface NavItem {
  id: SidebarView;
  label: string;
}

const navItems: readonly NavItem[] = [
  { id: 'analytics', label: '学习数据' },
  { id: 'chat-advice', label: 'AI 对话建议' },
  { id: 'goals', label: '学习目标' },
];

/**
 * 导航列表子组件（被桌面侧栏与移动抽屉共用）。
 * active 项用 accent 高亮，非 active 项用 muted + hover。
 */
function NavList({
  activeView,
  onChangeView,
}: {
  activeView: SidebarView;
  onChangeView: (view: SidebarView) => void;
}) {
  const baseClass =
    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background';
  const inactiveClass = 'text-muted hover:bg-background/80 hover:text-foreground';
  const activeClass = 'bg-accent/15 text-accent';

  return (
    <nav className="flex flex-col gap-1" aria-label="主导航">
      {navItems.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onChangeView(item.id)}
          aria-current={activeView === item.id ? 'page' : undefined}
          className={`${baseClass} ${
            activeView === item.id ? activeClass : inactiveClass
          }`}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}

/**
 * Sidebar 导航（spec「左侧 Sidebar 导航」+「响应式布局」）。
 *
 * 行为：
 *   - ≥ 1024px (lg)：固定在视口左侧，宽 240px，包含 Brand + NavList + ThemeToggle。
 *   - < 1024px：顶部 56px 横向窄条 + 汉堡按钮，点击展开为右侧抽屉（带 backdrop）。
 *
 * 主题：复用 useTheme / ThemeToggle；token 全部走 bg-background / border-border /
 * text-foreground / text-muted / accent，零内联 style。
 */
export default function Sidebar({ activeView, onChangeView }: SidebarProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleSelect = (view: SidebarView): void => {
    onChangeView(view);
    setDrawerOpen(false);
  };

  return (
    <>
      {/* 移动端顶部窄条（< 1024px 显示） */}
      <header className="fixed inset-x-0 top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-background/70 px-4 backdrop-blur lg:hidden print:hidden">
        <span className="text-sm font-semibold tracking-tight text-foreground">
          StudyPal
        </span>
        <button
          type="button"
          aria-label={drawerOpen ? '关闭菜单' : '打开菜单'}
          aria-expanded={drawerOpen}
          onClick={() => setDrawerOpen((v) => !v)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-border text-foreground hover:bg-background/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          {drawerOpen ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5"
              aria-hidden="true"
            >
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          )}
        </button>
      </header>

      {/* 移动端抽屉 backdrop（点击关闭） */}
      <button
        type="button"
        aria-label="关闭菜单"
        onClick={() => setDrawerOpen(false)}
        tabIndex={drawerOpen ? 0 : -1}
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity lg:hidden print:hidden ${
          drawerOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      />

      {/* 移动端右侧抽屉 */}
      <aside
        className={`fixed right-0 top-0 z-50 flex h-full w-64 flex-col border-l border-border bg-background p-4 transition-transform duration-200 lg:hidden print:hidden ${
          drawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="mb-6 flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">StudyPal</span>
          <ThemeToggle />
        </div>
        <NavList activeView={activeView} onChangeView={handleSelect} />
      </aside>

      {/* 桌面端左侧固定侧栏（≥ 1024px 显示） */}
      <aside
        className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-background/80 p-4 backdrop-blur lg:flex print:hidden"
      >
        <div className="mb-6 flex items-center justify-between">
          <span className="text-base font-semibold tracking-tight text-foreground">
            StudyPal
          </span>
          <ThemeToggle />
        </div>
        <NavList activeView={activeView} onChangeView={onChangeView} />
      </aside>
    </>
  );
}

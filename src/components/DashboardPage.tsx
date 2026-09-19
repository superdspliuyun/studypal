import HeroBackground from './HeroBackground';
import AnalyticsView from './views/AnalyticsView';
import ChatView from './views/ChatView';
import GoalsView from './views/GoalsView';
import { studyPalData } from '../data/studyPal';
import type { SidebarView } from './Sidebar';

interface DashboardPageProps {
  activeView: SidebarView;
}

const titles: Record<SidebarView, string> = {
  analytics: '学习数据',
  'chat-advice': 'AI 对话建议',
  goals: '学习目标',
};

/**
 * Dashboard 主区域（spec 全局行为 + design Decision 3 + 6）。
 *
 * 关键点：
 *   - 接收 activeView prop（state 提升至 App 层），按 view 切换顶部标题 + 主区域内容。
 *   - <HeroBackground /> 绝对定位 -z-10 铺底（延续品牌站视觉 DNA）。
 *   - 数据流：当前直接 import studyPalData（Phase 2 末切到 props 注入，
 *     未来切到 useStudyPal hook 时只改 import 路径）。
 *   - 响应式：移动端 pt-14（让出 56px 顶部窄条），桌面端 lg:pl-60（让出 240px 侧栏）。
 */
export default function DashboardPage({ activeView }: DashboardPageProps) {
  return (
    <main className="relative min-h-screen w-full overflow-hidden">
      <HeroBackground />

      <div className="relative z-10 pt-14 lg:pt-0 lg:pl-60">
        <header className="border-b border-border bg-background/60 px-6 py-6 backdrop-blur md:py-8 print:hidden">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
            {titles[activeView]}
          </h1>
        </header>

        <div className="px-6 py-8 md:px-10 md:py-10">
          {activeView === 'analytics' && <AnalyticsView />}
          {activeView === 'chat-advice' && (
            <ChatView accessToken={localStorage.getItem('studypal_access_token')} />
          )}
          {activeView === 'goals' && <GoalsView goals={studyPalData.dailyGoals} />}
        </div>
      </div>
    </main>
  );
}

import type { StudyPalStats } from '../../data/studyPal';
import StatsCards from '../StatsCards';

interface DashboardViewProps {
  stats: StudyPalStats;
}

/**
 * Dashboard 主视图（spec「Sidebar 导航」active='dashboard'）。
 * 当前仅渲染顶部统计卡片，更多面板（如最近会话 / 推荐课程）
 * 留待后续 change 增量引入。
 */
export default function DashboardView({ stats }: DashboardViewProps) {
  return (
    <section aria-label="Dashboard 总览" className="space-y-8">
      <StatsCards stats={stats} />
    </section>
  );
}

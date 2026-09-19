import type { StudyPalStats } from '../data/studyPal';

interface StatsCardsProps {
  stats: StudyPalStats;
}

/**
 * 学习时长格式化（spec「数据统计卡片 - 学习时长格式化」）：
 *   - ≥ 60 分钟：显示 "X 小时"
 *   - < 60 分钟：显示 "X 分钟"
 */
function formatMinutes(value: number): string {
  if (value >= 60) {
    const hours = Math.floor(value / 60);
    return `${hours} 小时`;
  }
  return `${value} 分钟`;
}

interface CardSpec {
  key: keyof StudyPalStats;
  label: string;
  format: (v: number) => string;
}

const cards: readonly CardSpec[] = [
  { key: 'totalLearningMinutes', label: '总学习时长', format: formatMinutes },
  { key: 'completedCourses', label: '已完成课程', format: (v) => `${v} 门` },
  { key: 'streakDays', label: '连续打卡', format: (v) => `${v} 天` },
] as const;

/**
 * 顶部 3 张统计卡片（spec「数据统计卡片」）。
 * 字段缺失降级（spec Scenario "mock 数据缺失"）：任一字段非有限数字时显示 [数据待接入]。
 */
export default function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div
      role="group"
      aria-label="学习统计"
      className="grid grid-cols-1 gap-4 sm:grid-cols-3"
    >
      {cards.map((card) => {
        const raw = stats[card.key];
        const hasValue = typeof raw === 'number' && Number.isFinite(raw);
        return (
          <div
            key={card.key}
            className="rounded-lg border border-border bg-background p-6 transition-colors"
          >
            <div className="text-sm font-medium text-muted">{card.label}</div>
            <div className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              {hasValue ? card.format(raw) : '[数据待接入]'}
            </div>
          </div>
        );
      })}
    </div>
  );
}

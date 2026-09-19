import type { StudyPalDailyGoal } from '../../data/studyPal';
import DailyGoals from '../DailyGoals';

interface GoalsViewProps {
  goals: readonly StudyPalDailyGoal[];
}

/**
 * Goals 主视图（spec「Sidebar 导航」active='goals'）。
 */
export default function GoalsView({ goals }: GoalsViewProps) {
  return (
    <section aria-label="今日目标" className="space-y-6">
      <DailyGoals goals={goals} />
    </section>
  );
}

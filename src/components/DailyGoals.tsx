import { useState } from 'react';
import type { StudyPalDailyGoal } from '../data/studyPal';

interface DailyGoalsProps {
  goals: readonly StudyPalDailyGoal[];
}

/**
 * 每日目标清单（spec「每日目标清单」）。
 *
 * 关键点：
 *   - 勾选状态仅存于本地 React state，**不写入 localStorage**，刷新即重置
 *     （spec Out-of-Scope：数据持久化）。
 *   - 完成态视觉：删除线 + 文本 muted（`line-through text-muted`）。
 *   - 顶部计数器 "已完成 X/Y"，全部完成时 SHOULD 显示鼓励文案。
 *   - 空数组兜底：渲染 "今日暂无目标" 文本而非空 <ul>。
 */
export default function DailyGoals({ goals }: DailyGoalsProps) {
  const [checked, setChecked] = useState<Set<string>>(() => new Set());

  const toggle = (id: string): void => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (goals.length === 0) {
    return (
      <p className="text-base text-muted" role="status">
        今日暂无目标
      </p>
    );
  }

  const done = goals.filter((g) => checked.has(g.id)).length;
  const total = goals.length;
  const allDone = done === total;

  return (
    <div>
      <div
        className="mb-4 flex items-baseline justify-between"
        aria-live="polite"
      >
        <span className="text-sm text-muted">
          已完成 {done}/{total}
        </span>
        {allDone && (
          <span className="text-sm font-medium text-accent">
            [今日目标已达成]
          </span>
        )}
      </div>
      <ul className="space-y-3" aria-label="今日任务清单">
        {goals.map((goal) => {
          const isChecked = checked.has(goal.id);
          return (
            <li
              key={goal.id}
              className="flex items-start gap-3 rounded-md border border-border bg-background p-4"
            >
              <input
                type="checkbox"
                checked={isChecked}
                onChange={() => toggle(goal.id)}
                aria-label={isChecked ? `取消完成: ${goal.title}` : `完成: ${goal.title}`}
                className="mt-1 h-4 w-4 cursor-pointer accent-[color:var(--color-accent)]"
              />
              <div className="flex-1">
                <div
                  className={
                    isChecked
                      ? 'text-base text-muted line-through'
                      : 'text-base text-foreground'
                  }
                >
                  {goal.title}
                </div>
                <div className="mt-1 text-xs text-muted">
                  预计 {goal.estimatedMinutes} 分钟
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

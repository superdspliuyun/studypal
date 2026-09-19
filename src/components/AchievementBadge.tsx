import type { Achievement } from '../lib/analyticsApi';

interface AchievementBadgeProps {
  achievement: Achievement;
}

export function AchievementBadge({ achievement }: AchievementBadgeProps) {
  const pct = Math.min(100, Math.round((achievement.progress / achievement.target) * 100));
  const baseClass = achievement.unlocked
    ? 'border-accent/40 bg-accent/15 text-foreground'
    : 'border-border bg-muted text-foreground/80';
  return (
    <div className={`flex flex-col gap-2 rounded-lg border p-4 ${baseClass}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{achievement.title}</h3>
        {achievement.unlocked && (
          <span className="rounded-full bg-accent px-2 py-0.5 text-xs text-background">
            已解锁
          </span>
        )}
      </div>
      <p className="text-xs text-foreground/70">{achievement.description}</p>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
        <div
          className={achievement.unlocked ? 'h-full bg-accent' : 'h-full bg-foreground/40'}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-foreground/60">
        {achievement.progress} / {achievement.target}
      </p>
    </div>
  );
}
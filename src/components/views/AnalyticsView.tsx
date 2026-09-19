import { useEffect, useState } from 'react';
import { AchievementBadge } from '../AchievementBadge';
import { HeatmapCalendar } from '../HeatmapCalendar';
import {
  type Achievement,
  type CalendarDay,
  currentStreakDays,
  getAchievements,
  getCalendar,
} from '../../lib/analyticsApi';

export default function AnalyticsView() {
  const [days, setDays] = useState<CalendarDay[] | null>(null);
  const [achievements, setAchievements] = useState<Achievement[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadTick, setReloadTick] = useState(0);

  useEffect(() => {
    const onAuth = () => {
      setDays(null);
      setAchievements(null);
      setError(null);
      setReloadTick((t) => t + 1);
    };
    window.addEventListener('studypal:auth', onAuth);
    return () => window.removeEventListener('studypal:auth', onAuth);
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const [cal, ach] = await Promise.all([getCalendar(90), getAchievements()]);
        if (cancelled) return;
        setDays(cal);
        setAchievements(ach);
        setError(null);
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [reloadTick]);

  if (error) {
    return (
      <div
        role="alert"
        className="rounded-md border border-border bg-muted p-4 text-sm text-foreground"
      >
        加载学习数据失败：{error}
      </div>
    );
  }

  const streak = days ? currentStreakDays(days) : 0;

  return (
    <section aria-label="学习数据" className="space-y-6">
      <header className="rounded-lg border border-border bg-background/40 p-4">
        <p className="text-xs text-foreground/60">连续学习天数</p>
        <p className="text-3xl font-semibold text-foreground">{streak} 天</p>
      </header>

      <div>
        <h2 className="mb-2 text-base font-semibold text-foreground">近 90 天学习日历</h2>
        {days ? (
          <HeatmapCalendar days={days} />
        ) : (
          <div className="h-32 animate-pulse rounded-md border border-border bg-background/40" />
        )}
      </div>

      <div>
        <h2 className="mb-2 text-base font-semibold text-foreground">成就</h2>
        {achievements ? (
          <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {achievements.map((a) => (
              <li key={a.id}>
                <AchievementBadge achievement={a} />
              </li>
            ))}
          </ul>
        ) : (
          <div className="h-32 animate-pulse rounded-md border border-border bg-background/40" />
        )}
      </div>
    </section>
  );
}
import type { CalendarDay } from '../lib/analyticsApi';

interface HeatmapCalendarProps {
  days: CalendarDay[];
}

/**
 * Pure-SVG 7-row × ceil(N/7)-col heatmap. Each cell picks an accent-token
 * opacity bucket by minutes; empty days get a muted border outline.
 */
export function HeatmapCalendar({ days }: HeatmapCalendarProps) {
  if (days.length === 0) {
    return (
      <div className="rounded-md border border-border p-4 text-sm text-foreground/60">
        暂无学习数据
      </div>
    );
  }

  const cols = Math.ceil(days.length / 7);
  const cell = 14;
  const gap = 3;
  const w = cols * (cell + gap);
  const h = 7 * (cell + gap);

  function bucket(m: number): string {
    if (m <= 0) return 'fill-border stroke-border';
    if (m <= 10) return 'fill-accent/15';
    if (m <= 30) return 'fill-accent/40';
    if (m <= 60) return 'fill-accent/70';
    return 'fill-accent';
  }

  return (
    <div className="rounded-md border border-border bg-background/40 p-3">
      <svg
        viewBox={`0 0 ${w} ${h}`}
        width="100%"
        height={h + 4}
        role="img"
        aria-label={`近 ${days.length} 天学习日历`}
      >
        {days.map((d, i) => {
          const col = Math.floor(i / 7);
          const row = i % 7;
          const x = col * (cell + gap);
          const y = row * (cell + gap);
          return (
            <rect
              key={d.date}
              x={x}
              y={y}
              width={cell}
              height={cell}
              rx={2}
              ry={2}
              className={bucket(d.minutes)}
              data-date={d.date}
              data-minutes={d.minutes}
            >
              <title>{`${d.date}: ${d.minutes} 分钟`}</title>
            </rect>
          );
        })}
      </svg>
      <div className="mt-2 flex items-center gap-2 text-xs text-foreground/60">
        <span>少</span>
        <span className="inline-block h-3 w-3 rounded-sm border border-border" />
        <span className="inline-block h-3 w-3 rounded-sm bg-accent/15" />
        <span className="inline-block h-3 w-3 rounded-sm bg-accent/40" />
        <span className="inline-block h-3 w-3 rounded-sm bg-accent/70" />
        <span className="inline-block h-3 w-3 rounded-sm bg-accent" />
        <span>多</span>
      </div>
    </div>
  );
}
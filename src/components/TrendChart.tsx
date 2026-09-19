import type { StudyPalTrendPoint } from '../data/studyPal';

interface TrendChartProps {
  weekly: readonly StudyPalTrendPoint[];
  monthly: readonly StudyPalTrendPoint[];
}

/**
 * 周柱状图（spec「周/月趋势图」周视图）。
 * viewBox 自适应：7 个柱，每柱 28px + 间隔 12px = 总宽 7*28 + 6*12 = 268。
 * 高度按 minutes / maxMinutes * 80 缩放。
 */
function WeeklyChart({ weekly }: { weekly: readonly StudyPalTrendPoint[] }) {
  if (weekly.length === 0) {
    return (
      <div
        role="status"
        className="relative flex h-32 items-center justify-center rounded-md border border-border bg-background"
      >
        <span className="text-sm text-muted">暂无数据</span>
      </div>
    );
  }

  const max = Math.max(...weekly.map((p) => p.minutes), 1);
  const barWidth = 28;
  const gap = 12;
  const chartWidth = weekly.length * barWidth + (weekly.length - 1) * gap;
  const chartHeight = 80;
  const labelOffset = 20;

  return (
    <svg
      viewBox={`0 0 ${chartWidth} ${chartHeight + labelOffset}`}
      className="block w-full max-w-md text-accent"
      role="img"
      aria-label="近 7 天学习分钟数柱状图"
    >
      <title>近 7 天学习分钟数柱状图</title>
      {weekly.map((point, i) => {
        const h = (point.minutes / max) * chartHeight;
        const x = i * (barWidth + gap);
        const y = chartHeight - h;
        return (
          <g key={point.date}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={h}
              rx={2}
              className="fill-current"
            />
            <text
              x={x + barWidth / 2}
              y={chartHeight + 14}
              textAnchor="middle"
              className="fill-[color:var(--color-muted)] text-[10px]"
            >
              {point.date}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/**
 * 月折线图（spec「周/月趋势图」月视图）。
 * viewBox 固定 600x144；30 个点 X 等距分布。
 * 折线 + 数据点 + 半透明面积（可选装饰）。
 */
function MonthlyChart({ monthly }: { monthly: readonly StudyPalTrendPoint[] }) {
  if (monthly.length === 0) {
    return (
      <div
        role="status"
        className="relative flex h-40 items-center justify-center rounded-md border border-border bg-background"
      >
        <span className="text-sm text-muted">暂无数据</span>
      </div>
    );
  }

  const max = Math.max(...monthly.map((p) => p.minutes), 1);
  const chartWidth = 600;
  const chartHeight = 120;
  const labelOffset = 24;
  const stepX =
    monthly.length > 1 ? chartWidth / (monthly.length - 1) : chartWidth;

  const coords = monthly.map((p, i) => {
    const x = i * stepX;
    const y = chartHeight - (p.minutes / max) * chartHeight;
    return { x, y };
  });

  const polylinePoints = coords.map((c) => `${c.x},${c.y}`).join(' ');
  const areaPath =
    `M0,${chartHeight} ` +
    coords.map((c) => `L${c.x},${c.y}`).join(' ') +
    ` L${chartWidth},${chartHeight} Z`;

  return (
    <svg
      viewBox={`0 0 ${chartWidth} ${chartHeight + labelOffset}`}
      className="block w-full max-w-3xl text-accent"
      role="img"
      aria-label="近 30 天学习分钟数折线图"
    >
      <title>近 30 天学习分钟数折线图</title>
      <path d={areaPath} className="fill-current opacity-20" />
      <polyline
        points={polylinePoints}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {coords.map((c, i) => (
        <circle
          key={monthly[i]!.date}
          cx={c.x}
          cy={c.y}
          r={2.5}
          className="fill-current"
        />
      ))}
    </svg>
  );
}

/**
 * 趋势图容器（spec「周/月趋势图」）。
 * 主题切换：图表颜色全部走 Tailwind token（text-accent / fill-current /
 * fill-muted 文字），主题切换后 ≤ 1 秒内跟随。
 */
export default function TrendChart({ weekly, monthly }: TrendChartProps) {
  return (
    <div className="space-y-8">
      <div>
        <h3 className="mb-3 text-base font-medium text-foreground">近 7 天</h3>
        <WeeklyChart weekly={weekly} />
      </div>
      <div>
        <h3 className="mb-3 text-base font-medium text-foreground">近 30 天</h3>
        <MonthlyChart monthly={monthly} />
      </div>
    </div>
  );
}

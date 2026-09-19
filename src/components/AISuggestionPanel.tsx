import type { StudyPalAiSuggestion } from '../data/studyPal';

interface AISuggestionPanelProps {
  suggestions: readonly StudyPalAiSuggestion[];
}

/**
 * AI 建议学习面板（spec「AI 建议学习面板」）。
 *
 * 关键点：
 *   - 顶部固定显示 `[AI 占位]` 字样，**明示数据非真实 AI 生成**。
 *   - 每条建议含 title / reason / estimatedMinutes 三字段。
 *   - 空数组兜底：渲染 `[AI 占位] 暂无建议` 文本而非空 <ul>。
 *   - 真实 AI 接入（spec Out-of-Scope）由后续 change 处理，本组件只做渲染。
 */
export default function AISuggestionPanel({ suggestions }: AISuggestionPanelProps) {
  if (suggestions.length === 0) {
    return (
      <p className="text-sm text-muted" role="status">
        [AI 占位] 暂无建议
      </p>
    );
  }

  return (
    <section aria-label="AI 学习建议" className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded-full border border-border bg-background/60 px-2.5 py-0.5 text-xs font-medium text-muted">
          [AI 占位]
        </span>
        <span className="text-xs text-muted">
          以下内容为 mock 数据，非真实 AI 生成
        </span>
      </div>
      <ul className="space-y-3">
        {suggestions.map((s) => (
          <li
            key={s.id}
            className="rounded-md border border-border bg-background p-4 transition-colors hover:border-accent"
          >
            <h3 className="text-base font-medium text-foreground">
              {s.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">{s.reason}</p>
            <div className="mt-3 text-xs text-muted">
              预计 {s.estimatedMinutes} 分钟
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

import type {
  StudyPalAiSuggestion,
  StudyPalTrendPoint,
} from '../../data/studyPal';
import AISuggestionPanel from '../AISuggestionPanel';
import TrendChart from '../TrendChart';

interface InsightsViewProps {
  suggestions: readonly StudyPalAiSuggestion[];
  weekly: readonly StudyPalTrendPoint[];
  monthly: readonly StudyPalTrendPoint[];
}

/**
 * Insights 主视图（spec「Sidebar 导航」active='insights'）。
 * 组合周/月趋势图 + AI 建议面板。
 */
export default function InsightsView({
  suggestions,
  weekly,
  monthly,
}: InsightsViewProps) {
  return (
    <section aria-label="学习洞察" className="space-y-10">
      <TrendChart weekly={weekly} monthly={monthly} />
      <AISuggestionPanel suggestions={suggestions} />
    </section>
  );
}

/**
 * StudyPal mock 数据层（design Decision 5）。
 *
 * 字段命名采用 camelCase，与未来 FastAPI 端点 GET /api/study-pal/snapshot
 * 的 Pydantic → JSON 序列化结果保持一致，便于后续零摩擦切换为真实数据源。
 *
 * 数据形态（按 spec Requirement: mock 数据结构稳定性）：
 *   - stats：单页 Dashboard 顶部 3 张统计卡片的数据源
 *   - dailyGoals：今日任务清单
 *   - aiSuggestions：AI 建议面板的占位内容（**非真实 AI 生成**）
 *   - weeklyTrend：近 7 天学习分钟数（柱状图）
 *   - monthlyTrend：近 30 天学习分钟数（折线图）
 *
 * 该文件纯静态、无副作用；组件应通过 props 传入数据，而非直接 import 此常量
 * （便于 Phase 2 之后从 mock 切换到 fetch）。
 */

export interface StudyPalStats {
  totalLearningMinutes: number;
  completedCourses: number;
  streakDays: number;
}

export interface StudyPalDailyGoal {
  id: string;
  title: string;
  estimatedMinutes: number;
}

export interface StudyPalAiSuggestion {
  id: string;
  title: string;
  reason: string;
  estimatedMinutes: number;
}

export interface StudyPalTrendPoint {
  date: string;
  minutes: number;
}

export interface StudyPalData {
  stats: StudyPalStats;
  dailyGoals: readonly StudyPalDailyGoal[];
  aiSuggestions: readonly StudyPalAiSuggestion[];
  weeklyTrend: readonly StudyPalTrendPoint[];
  monthlyTrend: readonly StudyPalTrendPoint[];
}

export const studyPalData: StudyPalData = {
  stats: {
    totalLearningMinutes: 145,
    completedCourses: 8,
    streakDays: 12,
  },
  dailyGoals: [
    {
      id: 'goal-1',
      title: '完成 React 19 服务端组件教程',
      estimatedMinutes: 45,
    },
    {
      id: 'goal-2',
      title: '复习 useState 状态提升',
      estimatedMinutes: 20,
    },
    {
      id: 'goal-3',
      title: '阅读 Tailwind v4 changelog',
      estimatedMinutes: 15,
    },
  ],
  aiSuggestions: [
    {
      id: 'ai-1',
      title: '复习 React Server Components',
      reason: '基于你最近浏览的 React 19 教程，推荐先复习 RSC 数据流',
      estimatedMinutes: 30,
    },
    {
      id: 'ai-2',
      title: '完成 FastAPI 依赖注入章节',
      reason: '你标记了 FastAPI 为下一阶段重点，提前打基础',
      estimatedMinutes: 60,
    },
    {
      id: 'ai-3',
      title: 'TypeScript 严格模式实战',
      reason: '当前项目已开启 strict，配套练习能减少一半编译错误',
      estimatedMinutes: 40,
    },
  ],
  weeklyTrend: [
    { date: '09-12', minutes: 45 },
    { date: '09-13', minutes: 60 },
    { date: '09-14', minutes: 30 },
    { date: '09-15', minutes: 90 },
    { date: '09-16', minutes: 120 },
    { date: '09-17', minutes: 75 },
    { date: '09-18', minutes: 145 },
  ],
  monthlyTrend: [
    { date: '08-20', minutes: 25 },
    { date: '08-21', minutes: 40 },
    { date: '08-22', minutes: 30 },
    { date: '08-23', minutes: 55 },
    { date: '08-24', minutes: 20 },
    { date: '08-25', minutes: 0 },
    { date: '08-26', minutes: 60 },
    { date: '08-27', minutes: 75 },
    { date: '08-28', minutes: 45 },
    { date: '08-29', minutes: 50 },
    { date: '08-30', minutes: 80 },
    { date: '08-31', minutes: 35 },
    { date: '09-01', minutes: 65 },
    { date: '09-02', minutes: 90 },
    { date: '09-03', minutes: 40 },
    { date: '09-04', minutes: 70 },
    { date: '09-05', minutes: 55 },
    { date: '09-06', minutes: 85 },
    { date: '09-07', minutes: 30 },
    { date: '09-08', minutes: 95 },
    { date: '09-09', minutes: 60 },
    { date: '09-10', minutes: 100 },
    { date: '09-11', minutes: 50 },
    { date: '09-12', minutes: 45 },
    { date: '09-13', minutes: 60 },
    { date: '09-14', minutes: 30 },
    { date: '09-15', minutes: 90 },
    { date: '09-16', minutes: 120 },
    { date: '09-17', minutes: 75 },
    { date: '09-18', minutes: 145 },
  ],
};

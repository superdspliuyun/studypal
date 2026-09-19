import { useState } from 'react';
import Sidebar, { type SidebarView } from './components/Sidebar';
import DashboardPage from './components/DashboardPage';

/**
 * App 顶层组合（spec 全局行为 + design Decision 3）。
 *
 * - view state 提升至 App 层，Sidebar 与 DashboardPage 都从 props 接收。
 * - 旧品牌站组件（Navigation / Hero / Projects / Contact）已停止引用，
 *   文件暂留作回滚参考，Phase 3.1 清理。
 */
function App() {
  const [activeView, setActiveView] = useState<SidebarView>('analytics');

  return (
    <>
      <Sidebar activeView={activeView} onChangeView={setActiveView} />
      <DashboardPage activeView={activeView} />
    </>
  );
}

export default App;

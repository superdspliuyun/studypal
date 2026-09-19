import { useState } from 'react';
import { LoginPanel } from './components/LoginPanel';
import Sidebar, { type SidebarView } from './components/Sidebar';
import DashboardPage from './components/DashboardPage';

/**
 * App 顶层组合（spec 全局行为 + design Decision 3）。
 *
 * - view state 提升至 App 层，Sidebar 与 DashboardPage 都从 props 接收。
 * - LoginPanel 在未登录时浮在顶部，提供注册/登录入口；登录后折叠为右上角小 chip。
 */
function App() {
  const [activeView, setActiveView] = useState<SidebarView>('analytics');

  return (
    <>
      <LoginPanel />
      <Sidebar activeView={activeView} onChangeView={setActiveView} />
      <DashboardPage activeView={activeView} />
    </>
  );
}

export default App;

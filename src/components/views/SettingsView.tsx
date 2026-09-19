/**
 * Settings 占位视图（spec「Sidebar 导航」active='settings'）。
 * 完整功能（账号 / 偏好 / 数据导出等）留待后续 change 增量引入。
 */
export default function SettingsView() {
  return (
    <section aria-label="设置" className="space-y-6">
      <p className="text-base text-muted">
        [Settings 占位] 此模块在后续 change 中实现
      </p>
    </section>
  );
}

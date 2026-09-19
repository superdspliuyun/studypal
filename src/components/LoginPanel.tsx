import { useEffect, useState } from 'react';
import { getStoredEmail, login, register, logout } from '../lib/authApi';

type AuthMode = 'login' | 'register';

const MIN_PASSWORD_LEN = 8;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Floating top-center login/register panel. Shown when there is no
 * studypal_access_token in localStorage. Renders nothing after login so
 * the rest of the dashboard is unobstructed.
 */
export function LoginPanel() {
  const [mode, setMode] = useState<AuthMode>('register');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signedInEmail, setSignedInEmail] = useState<string | null>(null);

  useEffect(() => {
    const refresh = () => setSignedInEmail(getStoredEmail());
    refresh();
    window.addEventListener('studypal:auth', refresh);
    window.addEventListener('storage', refresh);
    return () => {
      window.removeEventListener('studypal:auth', refresh);
      window.removeEventListener('storage', refresh);
    };
  }, []);

  if (signedInEmail) {
    return (
      <div className="fixed right-4 top-4 z-50 flex items-center gap-2 rounded-full border border-border bg-background/80 px-4 py-2 text-sm text-foreground shadow-sm backdrop-blur">
        <span className="text-foreground/70">已登录：</span>
        <span className="font-medium">{signedInEmail}</span>
        <button
          type="button"
          onClick={() => {
            logout();
          }}
          className="ml-2 text-xs text-foreground/60 underline hover:text-foreground"
        >
          退出
        </button>
      </div>
    );
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!EMAIL_PATTERN.test(email)) {
      setError('请输入合法邮箱');
      return;
    }
    if (password.length < MIN_PASSWORD_LEN) {
      setError(`密码至少 ${MIN_PASSWORD_LEN} 个字符`);
      return;
    }
    setSubmitting(true);
    try {
      if (mode === 'register') {
        await register(email, password);
      } else {
        await login(email, password);
      }
      // auth event will trigger signedInEmail update
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-x-0 top-4 z-50 mx-auto flex max-w-md flex-col gap-3 rounded-lg border border-border bg-background/95 p-6 shadow-lg backdrop-blur">
      <h2 className="text-lg font-semibold text-foreground">
        {mode === 'register' ? '注册账号' : '登录'}
      </h2>
      <p className="text-xs text-foreground/60">
        注册或登录后才能使用 AI 学习助手、学习数据等功能。
      </p>
      <form onSubmit={submit} className="flex flex-col gap-3">
        <input
          type="email"
          required
          autoComplete="email"
          placeholder="邮箱"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-md border border-border bg-background px-3 py-2 text-foreground placeholder:text-foreground/40 focus:outline-none focus:ring-2 focus:ring-accent"
          disabled={submitting}
        />
        <input
          type="password"
          required
          autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
          placeholder={`密码（至少 ${MIN_PASSWORD_LEN} 个字符）`}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded-md border border-border bg-background px-3 py-2 text-foreground placeholder:text-foreground/40 focus:outline-none focus:ring-2 focus:ring-accent"
          disabled={submitting}
        />
        {error && (
          <p role="alert" className="text-xs text-red-500">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-accent px-4 py-2 text-background hover:bg-accent-hover disabled:opacity-50"
        >
          {submitting ? '处理中…' : mode === 'register' ? '注册并登录' : '登录'}
        </button>
      </form>
      <button
        type="button"
        onClick={() => {
          setMode((m) => (m === 'register' ? 'login' : 'register'));
          setError(null);
        }}
        className="text-xs text-foreground/60 underline hover:text-foreground"
      >
        {mode === 'register' ? '已有账号？去登录' : '没有账号？去注册'}
      </button>
    </div>
  );
}
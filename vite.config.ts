import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// 部署到 GitHub Pages：仓库为 https://<username>.github.io/studypal/，
// 故 SPA base 必须设为 '/studypal/'。
export default defineConfig({
  base: '/studypal/',
  plugins: [react(), tailwindcss()],
})
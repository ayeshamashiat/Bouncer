import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// envDir '..' so the repo-root .env (VITE_API_URL, VITE_USE_MOCKS) is used.
// fs.allow '..' so dev mode can import ../contracts/mocks and ../data/demo.
export default defineConfig({
  plugins: [react()],
  envDir: '..',
  server: { port: 5173, fs: { allow: ['..'] } },
})

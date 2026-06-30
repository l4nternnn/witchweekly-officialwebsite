import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      input: {
        home: resolve(__dirname, 'index.html'),
        search: resolve(__dirname, 'search/index.html'),
        news: resolve(__dirname, 'news/index.html'),
        trivia: resolve(__dirname, 'trivia/index.html'),
        officialWorks: resolve(__dirname, 'official-works/index.html'),
        submitFeedback: resolve(__dirname, 'submit-feedback/index.html'),
      },
    },
  },
})

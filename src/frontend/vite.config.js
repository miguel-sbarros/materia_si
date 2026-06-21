import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Em container (Docker no macOS), fsevents não propaga: polling habilita o HMR
  // a ver edições no volume montado.
  server: {
    host: true,
    watch: { usePolling: true },
  },
})

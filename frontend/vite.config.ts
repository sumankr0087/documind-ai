import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/documents": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/questions": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/docs": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/openapi.json": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});

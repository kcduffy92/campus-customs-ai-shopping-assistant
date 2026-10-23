import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// In development the browser only talks to Vite (port 5173); API calls and product images
// are forwarded to the FastAPI backend, so no CORS setup or hard-coded backend URL is needed in app code.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backend = env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": backend,
        "/media": backend,
      },
    },
  };
});

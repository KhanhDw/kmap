import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  envDir: path.resolve(fileURLToPath(new URL(".", import.meta.url)), ".."),
  resolve: {
    alias: { "@": path.resolve(fileURLToPath(new URL(".", import.meta.url)), "src") },
  },
  server: { host: true, port: 5173 },
});

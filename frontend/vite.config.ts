import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/",
  server: {
    proxy: {
      "/world": {
        target: process.env.VITE_WORLD_TARGET ?? "http://127.0.0.1:8139",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "../ontology_author/world/static",
    emptyOutDir: true,
  },
});

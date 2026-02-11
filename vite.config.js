import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "justyol_dashboard/public/js"),
    },
  },
  build: {
    outDir: path.resolve(
      __dirname,
      "justyol_dashboard/public/dist/js"
    ),
    emptyOutDir: true,
    lib: {
      entry: path.resolve(
        __dirname,
        "justyol_dashboard/public/js/dashboard.bundle.js"
      ),
      name: "JustyolDashboard",
      formats: ["iife"],
      fileName: () => "dashboard.bundle.js",
    },
    rollupOptions: {
      external: [],
      output: {
        globals: {},
        // Keep CSS in a single file
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith(".css")) {
            return "dashboard.bundle.css";
          }
          return assetInfo.name;
        },
      },
    },
    // Inline all dependencies (Vue, eCharts, etc.) into the bundle
    commonjsOptions: {
      include: [/node_modules/],
    },
    minify: "terser",
    sourcemap: false,
  },
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
});

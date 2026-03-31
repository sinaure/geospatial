import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function serveGeojsonPlugin() {
  return {
    name: "serve-geojson",
    configureServer(server) {
      server.middlewares.use("/geojson", (req, res, next) => {
        const safeName = path.basename(req.url);
        const filePath = path.resolve(__dirname, "..", "geojson", safeName);
        if (fs.existsSync(filePath) && filePath.endsWith(".geojson")) {
          res.setHeader("Content-Type", "application/json");
          res.setHeader("Access-Control-Allow-Origin", "*");
          fs.createReadStream(filePath).pipe(res);
        } else {
          next();
        }
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), serveGeojsonPlugin()],
  server: {
    port: 5173,
    open: true,
  },
});

export const BASEMAPS = {
  osm: {
    id: "osm",
    name: "OpenStreetMap",
    icon: "🗺",
    style: {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "&copy; OpenStreetMap contributors",
        },
      },
      layers: [{ id: "osm-tiles", type: "raster", source: "osm" }],
    },
  },
  satellite: {
    id: "satellite",
    name: "Satellite",
    icon: "🛰",
    style: {
      version: 8,
      sources: {
        esri: {
          type: "raster",
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          ],
          tileSize: 256,
          attribution: "&copy; Esri",
        },
      },
      layers: [{ id: "esri-tiles", type: "raster", source: "esri" }],
    },
  },
  dark: {
    id: "dark",
    name: "Dark",
    icon: "🌑",
    style: {
      version: 8,
      sources: {
        carto: {
          type: "raster",
          tiles: [
            "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          ],
          tileSize: 256,
          attribution: "&copy; CARTO",
        },
      },
      layers: [{ id: "carto-tiles", type: "raster", source: "carto" }],
    },
  },
  topo: {
    id: "topo",
    name: "Topographic",
    icon: "⛰",
    style: {
      version: 8,
      sources: {
        topo: {
          type: "raster",
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
          ],
          tileSize: 256,
          attribution: "&copy; Esri",
        },
      },
      layers: [{ id: "topo-tiles", type: "raster", source: "topo" }],
    },
  },
};

export const DEFAULT_BASEMAP = "osm";

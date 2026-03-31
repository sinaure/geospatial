import { useState, useCallback, useRef } from "react";
import MapView from "./components/MapView";
import Sidebar from "./components/Sidebar";
import StatusBar from "./components/StatusBar";
import { buildInitialLayers } from "./config/layers";
import { DEFAULT_BASEMAP } from "./config/basemaps";

export default function App() {
  const [layers, setLayers] = useState(buildInitialLayers);
  const [basemap, setBasemap] = useState(DEFAULT_BASEMAP);
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [cursorCoords, setCursorCoords] = useState(null);
  const [zoom, setZoom] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const mapRef = useRef(null);

  const toggleLayer = useCallback((layerId) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === layerId ? { ...l, visible: !l.visible } : l)),
    );
  }, []);

  const updateLayerData = useCallback((layerId, geojson, geometryType) => {
    setLayers((prev) =>
      prev.map((l) =>
        l.id === layerId ? { ...l, loaded: true, geojson, geometryType } : l,
      ),
    );
  }, []);

  const zoomToLayer = useCallback(
    (layerId) => {
      const layer = layers.find((l) => l.id === layerId);
      if (!layer?.geojson || !mapRef.current) return;
      const map = mapRef.current;

      const bounds = new maplibregl.LngLatBounds();
      const addCoords = (coords) => {
        if (typeof coords[0] === "number") {
          bounds.extend(coords);
        } else {
          coords.forEach(addCoords);
        }
      };

      const features = layer.geojson.features || [layer.geojson];
      features.forEach((f) => addCoords(f.geometry.coordinates));

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, { padding: 60, maxZoom: 14 });
      }
    },
    [layers],
  );

  return (
    <div style={{ display: "flex", width: "100%", height: "100%" }}>
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((o) => !o)}
        layers={layers}
        basemap={basemap}
        selectedFeature={selectedFeature}
        onToggleLayer={toggleLayer}
        onChangeBasemap={setBasemap}
        onZoomToLayer={zoomToLayer}
        onClearFeature={() => setSelectedFeature(null)}
      />
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <MapView
          ref={mapRef}
          layers={layers}
          basemap={basemap}
          onMouseMove={setCursorCoords}
          onZoomChange={setZoom}
          onFeatureClick={setSelectedFeature}
          onLayerLoaded={updateLayerData}
        />
        <StatusBar
          coords={cursorCoords}
          zoom={zoom}
          layerCount={layers.filter((l) => l.visible).length}
        />
      </div>
    </div>
  );
}

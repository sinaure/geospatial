import {
  useEffect,
  useRef,
  forwardRef,
  useImperativeHandle,
  useCallback,
} from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { BASEMAPS } from "../config/basemaps";

const INITIAL_VIEW = { lng: 143.5, lat: -5.5, zoom: 6 };

const MapView = forwardRef(function MapView(
  {
    layers,
    basemap,
    onMouseMove,
    onZoomChange,
    onFeatureClick,
    onLayerLoaded,
  },
  ref,
) {
  const containerRef = useRef(null);
  const mapInstance = useRef(null);
  const loadedSources = useRef(new Set());
  const prevBasemap = useRef(basemap);

  useImperativeHandle(ref, () => mapInstance.current, []);

  const addGeojsonLayer = useCallback(
    (map, layer) => {
      if (loadedSources.current.has(layer.id)) return;

      fetch(`/geojson/${layer.file}`)
        .then((r) => r.json())
        .then((geojson) => {
          if (!map.getSource(layer.id)) {
            const fc =
              geojson.type === "FeatureCollection"
                ? geojson
                : { type: "FeatureCollection", features: [geojson] };

            const geomType = fc.features[0]?.geometry?.type || "Polygon";
            onLayerLoaded(layer.id, fc, geomType);

            map.addSource(layer.id, { type: "geojson", data: fc });

            if (geomType === "Point" || geomType === "MultiPoint") {
              map.addLayer({
                id: `${layer.id}-circle`,
                type: "circle",
                source: layer.id,
                paint: {
                  "circle-radius": 7,
                  "circle-color": layer.color,
                  "circle-stroke-color": "#fff",
                  "circle-stroke-width": 2,
                  "circle-opacity": 0.9,
                },
                layout: { visibility: layer.visible ? "visible" : "none" },
              });
              map.addLayer({
                id: `${layer.id}-label`,
                type: "symbol",
                source: layer.id,
                layout: {
                  "text-field": ["get", "name"],
                  "text-size": 11,
                  "text-offset": [0, 1.5],
                  "text-anchor": "top",
                  "text-optional": true,
                  visibility: layer.visible ? "visible" : "none",
                },
                paint: {
                  "text-color": "#e4e6ed",
                  "text-halo-color": "#000",
                  "text-halo-width": 1.5,
                },
              });
            } else {
              map.addLayer({
                id: `${layer.id}-fill`,
                type: "fill",
                source: layer.id,
                paint: {
                  "fill-color": layer.color,
                  "fill-opacity": 0.2,
                },
                layout: { visibility: layer.visible ? "visible" : "none" },
              });
              map.addLayer({
                id: `${layer.id}-outline`,
                type: "line",
                source: layer.id,
                paint: {
                  "line-color": layer.color,
                  "line-width": 2,
                },
                layout: { visibility: layer.visible ? "visible" : "none" },
              });
              map.addLayer({
                id: `${layer.id}-label`,
                type: "symbol",
                source: layer.id,
                layout: {
                  "text-field": ["get", "name"],
                  "text-size": 12,
                  "text-optional": true,
                  visibility: layer.visible ? "visible" : "none",
                },
                paint: {
                  "text-color": "#e4e6ed",
                  "text-halo-color": "#000",
                  "text-halo-width": 1.5,
                },
              });
            }

            loadedSources.current.add(layer.id);
          }
        })
        .catch((err) => console.warn(`Failed to load ${layer.file}:`, err));
    },
    [onLayerLoaded],
  );

  useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAPS[basemap].style,
      center: [INITIAL_VIEW.lng, INITIAL_VIEW.lat],
      zoom: INITIAL_VIEW.zoom,
      attributionControl: false,
    });

    map.addControl(
      new maplibregl.AttributionControl({ compact: true }),
      "bottom-right",
    );
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(
      new maplibregl.ScaleControl({ maxWidth: 150 }),
      "bottom-right",
    );

    map.on("mousemove", (e) => {
      onMouseMove({ lng: e.lngLat.lng, lat: e.lngLat.lat });
    });

    map.on("zoom", () => {
      onZoomChange(map.getZoom());
    });

    map.on("load", () => {
      onZoomChange(map.getZoom());
      layers.forEach((layer) => {
        if (layer.visible) addGeojsonLayer(map, layer);
      });
    });

    map.on("click", (e) => {
      const queryLayers = [];
      loadedSources.current.forEach((id) => {
        ["circle", "fill", "outline"].forEach((suffix) => {
          if (map.getLayer(`${id}-${suffix}`)) {
            queryLayers.push(`${id}-${suffix}`);
          }
        });
      });

      if (queryLayers.length === 0) return;

      const features = map.queryRenderedFeatures(e.point, {
        layers: queryLayers,
      });

      if (features.length > 0) {
        const f = features[0];
        onFeatureClick({
          properties: f.properties,
          geometry: f.geometry,
          layerId: f.source,
          lngLat: e.lngLat,
        });
      } else {
        onFeatureClick(null);
      }
    });

    const setCursorPointer = () => (map.getCanvas().style.cursor = "pointer");
    const resetCursor = () => (map.getCanvas().style.cursor = "");

    map.on("styledata", () => {
      loadedSources.current.forEach((id) => {
        ["circle", "fill"].forEach((suffix) => {
          const layerName = `${id}-${suffix}`;
          if (map.getLayer(layerName)) {
            map.on("mouseenter", layerName, setCursorPointer);
            map.on("mouseleave", layerName, resetCursor);
          }
        });
      });
    });

    mapInstance.current = map;

    return () => {
      map.remove();
      mapInstance.current = null;
      loadedSources.current.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle basemap change by re-setting the style and re-adding layers
  useEffect(() => {
    const map = mapInstance.current;
    if (!map || basemap === prevBasemap.current) return;
    prevBasemap.current = basemap;

    const center = map.getCenter();
    const zoom = map.getZoom();

    loadedSources.current.clear();
    map.setStyle(BASEMAPS[basemap].style);

    map.once("style.load", () => {
      map.setCenter(center);
      map.setZoom(zoom);
      layers.forEach((layer) => {
        if (layer.visible) addGeojsonLayer(map, layer);
      });
    });
  }, [basemap, layers, addGeojsonLayer]);

  // Handle layer visibility
  useEffect(() => {
    const map = mapInstance.current;
    if (!map || !map.isStyleLoaded()) return;

    layers.forEach((layer) => {
      if (!loadedSources.current.has(layer.id) && layer.visible) {
        addGeojsonLayer(map, layer);
        return;
      }

      ["circle", "fill", "outline", "label"].forEach((suffix) => {
        const layerName = `${layer.id}-${suffix}`;
        if (map.getLayer(layerName)) {
          map.setLayoutProperty(
            layerName,
            "visibility",
            layer.visible ? "visible" : "none",
          );
        }
      });
    });
  }, [layers, addGeojsonLayer]);

  return (
    <div
      ref={containerRef}
      style={{
        flex: 1,
        position: "relative",
      }}
    />
  );
});

export default MapView;

import { useMemo } from "react";

const styles = {
  section: {
    padding: "0 16px",
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: "11px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: "var(--color-text-muted)",
    padding: "12px 4px 6px",
  },
  layerItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "7px 8px",
    borderRadius: "var(--radius-sm)",
    cursor: "pointer",
    transition: "background var(--transition)",
    userSelect: "none",
  },
  colorDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    flexShrink: 0,
  },
  layerName: {
    flex: 1,
    fontSize: "13px",
    lineHeight: 1.3,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  eyeBtn: {
    background: "none",
    border: "none",
    padding: 0,
    cursor: "pointer",
    fontSize: "14px",
    lineHeight: 1,
    flexShrink: 0,
  },
  zoomBtn: {
    background: "none",
    border: "none",
    padding: 0,
    cursor: "pointer",
    fontSize: "12px",
    lineHeight: 1,
    flexShrink: 0,
    color: "var(--color-text-muted)",
    transition: "color var(--transition)",
  },
};

function LayerItem({ layer, onToggle, onZoomTo }) {
  const handleToggle = () => onToggle(layer.id);
  const handleZoom = (e) => {
    e.stopPropagation();
    if (layer.loaded) onZoomTo(layer.id);
  };

  return (
    <div
      style={{
        ...styles.layerItem,
        opacity: layer.visible ? 1 : 0.5,
      }}
      onClick={handleToggle}
      onMouseEnter={(e) =>
        (e.currentTarget.style.background = "var(--color-bg-hover)")
      }
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      <span style={{ ...styles.colorDot, background: layer.color }} />
      <span
        style={{
          ...styles.layerName,
          color: layer.visible
            ? "var(--color-text-primary)"
            : "var(--color-text-secondary)",
        }}
      >
        {layer.name}
      </span>
      {layer.loaded && (
        <button
          style={styles.zoomBtn}
          onClick={handleZoom}
          title="Zoom to layer"
          onMouseEnter={(e) =>
            (e.currentTarget.style.color = "var(--color-accent)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--color-text-muted)")
          }
        >
          ⊕
        </button>
      )}
      <button
        style={{
          ...styles.eyeBtn,
          color: layer.visible
            ? "var(--color-accent)"
            : "var(--color-text-muted)",
        }}
        onClick={(e) => {
          e.stopPropagation();
          handleToggle();
        }}
        title={layer.visible ? "Hide layer" : "Show layer"}
      >
        {layer.visible ? "👁" : "👁‍🗨"}
      </button>
    </div>
  );
}

export default function LayerPanel({ layers, onToggle, onZoomTo }) {
  const groups = useMemo(() => {
    const map = {};
    layers.forEach((l) => {
      if (!map[l.group]) map[l.group] = [];
      map[l.group].push(l);
    });
    return map;
  }, [layers]);

  return (
    <div style={styles.section}>
      <div style={styles.sectionTitle}>Layers</div>
      {Object.entries(groups).map(([group, items]) => (
        <div key={group}>
          <div
            style={{
              fontSize: "11px",
              color: "var(--color-text-muted)",
              padding: "8px 8px 4px",
              fontWeight: 500,
            }}
          >
            {group}
          </div>
          {items.map((layer) => (
            <LayerItem
              key={layer.id}
              layer={layer}
              onToggle={onToggle}
              onZoomTo={onZoomTo}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

const styles = {
  bar: {
    height: "var(--statusbar-height)",
    background: "var(--color-bg-secondary)",
    borderTop: "1px solid var(--color-border)",
    display: "flex",
    alignItems: "center",
    padding: "0 16px",
    gap: 24,
    flexShrink: 0,
    fontSize: "11px",
    fontFamily: "'Inter', monospace",
    color: "var(--color-text-secondary)",
  },
  item: {
    display: "flex",
    alignItems: "center",
    gap: 6,
  },
  label: {
    color: "var(--color-text-muted)",
  },
  value: {
    color: "var(--color-text-secondary)",
    fontVariantNumeric: "tabular-nums",
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: "var(--color-success)",
  },
};

export default function StatusBar({ coords, zoom, layerCount }) {
  return (
    <div style={styles.bar}>
      <div style={styles.item}>
        <span style={styles.dot} />
        <span style={styles.value}>Ready</span>
      </div>

      <div style={styles.item}>
        <span style={styles.label}>Lat</span>
        <span style={styles.value}>
          {coords ? coords.lat.toFixed(5) : "—"}
        </span>
      </div>

      <div style={styles.item}>
        <span style={styles.label}>Lng</span>
        <span style={styles.value}>
          {coords ? coords.lng.toFixed(5) : "—"}
        </span>
      </div>

      <div style={styles.item}>
        <span style={styles.label}>Zoom</span>
        <span style={styles.value}>{zoom.toFixed(1)}</span>
      </div>

      <div style={{ marginLeft: "auto" }}>
        <div style={styles.item}>
          <span style={styles.label}>Active layers</span>
          <span style={styles.value}>{layerCount}</span>
        </div>
      </div>
    </div>
  );
}

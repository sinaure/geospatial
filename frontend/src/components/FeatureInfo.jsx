const styles = {
  section: {
    padding: "0 16px",
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: "11px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: "var(--color-text-muted)",
    padding: "12px 4px 6px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  closeBtn: {
    background: "none",
    border: "none",
    color: "var(--color-text-muted)",
    cursor: "pointer",
    fontSize: "14px",
    padding: "0 2px",
    lineHeight: 1,
  },
  card: {
    background: "var(--color-bg-tertiary)",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--color-border)",
    overflow: "hidden",
  },
  row: {
    display: "flex",
    padding: "8px 12px",
    borderBottom: "1px solid var(--color-border)",
    gap: 8,
  },
  key: {
    fontSize: "11px",
    fontWeight: 600,
    color: "var(--color-text-muted)",
    minWidth: 80,
    flexShrink: 0,
    textTransform: "capitalize",
  },
  value: {
    fontSize: "12px",
    color: "var(--color-text-primary)",
    wordBreak: "break-word",
  },
  coords: {
    padding: "8px 12px",
    fontSize: "11px",
    color: "var(--color-text-muted)",
    fontFamily: "monospace",
  },
};

export default function FeatureInfo({ feature, onClose }) {
  if (!feature) return null;

  const props = feature.properties || {};
  const entries = Object.entries(props).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );

  return (
    <div style={styles.section}>
      <div style={styles.sectionTitle}>
        <span>Feature Info</span>
        <button style={styles.closeBtn} onClick={onClose} title="Close">
          ✕
        </button>
      </div>
      <div style={styles.card}>
        {entries.length > 0 ? (
          entries.map(([key, value], i) => (
            <div
              key={key}
              style={{
                ...styles.row,
                ...(i === entries.length - 1 && !feature.lngLat
                  ? { borderBottom: "none" }
                  : {}),
              }}
            >
              <span style={styles.key}>{key.replace(/_/g, " ")}</span>
              <span style={styles.value}>{String(value)}</span>
            </div>
          ))
        ) : (
          <div style={{ ...styles.row, borderBottom: "none" }}>
            <span style={styles.value}>No properties</span>
          </div>
        )}
        {feature.lngLat && (
          <div style={styles.coords}>
            {feature.lngLat.lat.toFixed(6)}, {feature.lngLat.lng.toFixed(6)}
          </div>
        )}
      </div>
    </div>
  );
}

import { BASEMAPS } from "../config/basemaps";

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
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 6,
  },
  card: {
    padding: "10px 8px",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--color-border)",
    cursor: "pointer",
    textAlign: "center",
    transition: "all var(--transition)",
    background: "var(--color-bg-tertiary)",
  },
  cardActive: {
    borderColor: "var(--color-accent)",
    background: "var(--color-bg-active)",
  },
  icon: {
    fontSize: "18px",
    display: "block",
    marginBottom: 4,
  },
  label: {
    fontSize: "11px",
    color: "var(--color-text-secondary)",
    fontWeight: 500,
  },
  labelActive: {
    color: "var(--color-accent)",
  },
};

export default function BasemapSwitcher({ current, onChange }) {
  return (
    <div style={styles.section}>
      <div style={styles.sectionTitle}>Basemap</div>
      <div style={styles.grid}>
        {Object.values(BASEMAPS).map((bm) => {
          const active = bm.id === current;
          return (
            <div
              key={bm.id}
              style={{ ...styles.card, ...(active ? styles.cardActive : {}) }}
              onClick={() => onChange(bm.id)}
              onMouseEnter={(e) => {
                if (!active)
                  e.currentTarget.style.borderColor =
                    "var(--color-text-muted)";
              }}
              onMouseLeave={(e) => {
                if (!active)
                  e.currentTarget.style.borderColor = "var(--color-border)";
              }}
            >
              <span style={styles.icon}>{bm.icon}</span>
              <span
                style={{
                  ...styles.label,
                  ...(active ? styles.labelActive : {}),
                }}
              >
                {bm.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

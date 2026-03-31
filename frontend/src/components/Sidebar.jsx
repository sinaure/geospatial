import LayerPanel from "./LayerPanel";
import BasemapSwitcher from "./BasemapSwitcher";
import FeatureInfo from "./FeatureInfo";

const styles = {
  sidebar: {
    width: "var(--sidebar-width)",
    height: "100%",
    background: "var(--color-bg-secondary)",
    borderRight: "1px solid var(--color-border)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    flexShrink: 0,
    transition: "margin-left var(--transition)",
  },
  collapsed: {
    marginLeft: "calc(-1 * var(--sidebar-width))",
  },
  header: {
    padding: "16px 20px",
    borderBottom: "1px solid var(--color-border)",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    flexShrink: 0,
  },
  logo: {
    width: 32,
    height: 32,
    borderRadius: "var(--radius-md)",
    background: "linear-gradient(135deg, #4dabf7, #3b5bdb)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "16px",
    fontWeight: 700,
    color: "#fff",
    flexShrink: 0,
  },
  title: {
    fontSize: "15px",
    fontWeight: 600,
    color: "var(--color-text-primary)",
    lineHeight: 1.2,
  },
  subtitle: {
    fontSize: "11px",
    color: "var(--color-text-muted)",
    marginTop: 2,
  },
  body: {
    flex: 1,
    overflowY: "auto",
    padding: "12px 0",
  },
  toggleBtn: {
    position: "fixed",
    top: 12,
    left: 12,
    zIndex: 1000,
    width: 36,
    height: 36,
    borderRadius: "var(--radius-md)",
    background: "var(--color-bg-secondary)",
    border: "1px solid var(--color-border)",
    color: "var(--color-text-primary)",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
    transition: "background var(--transition)",
  },
};

export default function Sidebar({
  open,
  onToggle,
  layers,
  basemap,
  selectedFeature,
  onToggleLayer,
  onChangeBasemap,
  onZoomToLayer,
  onClearFeature,
}) {
  return (
    <>
      {!open && (
        <button
          style={styles.toggleBtn}
          onClick={onToggle}
          title="Open sidebar"
        >
          ☰
        </button>
      )}
      <aside style={{ ...styles.sidebar, ...(open ? {} : styles.collapsed) }}>
        <div style={styles.header}>
          <div style={styles.logo}>G</div>
          <div>
            <div style={styles.title}>GeoSpatial</div>
            <div style={styles.subtitle}>Mining Sites Explorer</div>
          </div>
          <button
            onClick={onToggle}
            style={{
              marginLeft: "auto",
              background: "none",
              border: "none",
              color: "var(--color-text-secondary)",
              cursor: "pointer",
              fontSize: "18px",
              padding: 4,
              lineHeight: 1,
            }}
            title="Collapse sidebar"
          >
            ✕
          </button>
        </div>
        <div style={styles.body}>
          <LayerPanel
            layers={layers}
            onToggle={onToggleLayer}
            onZoomTo={onZoomToLayer}
          />
          <BasemapSwitcher current={basemap} onChange={onChangeBasemap} />
          {selectedFeature && (
            <FeatureInfo feature={selectedFeature} onClose={onClearFeature} />
          )}
        </div>
      </aside>
    </>
  );
}

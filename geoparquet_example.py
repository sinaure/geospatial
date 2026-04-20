#!/usr/bin/env python3
"""
GeoParquet Example — Spectral Index Samples for Enga Province, PNG
====================================================================
Reads pre-computed spectral index GeoTIFFs (NDVI, NDWI, NDBI, …) and
produces two GeoParquet files:

  data/enga_samples.parquet   — regular-grid point sample of every index
  data/enga_hotspots.parquet  — high-NDVI / low-NDVI "hotspot" polygons
                                derived by thresholding + vectorising NDVI

Why GeoParquet?
  • Columnar Parquet layout → fast analytical queries on millions of points
    without loading geometry into a GIS.
  • Embedded spatial metadata (bbox, CRS, geometry encoding) per the
    GeoParquet 1.0 spec so tools like DuckDB, QGIS, lonboard read it natively.
  • Dramatically smaller than equivalent Shapefile or GeoJSON for large samples.
  • Works directly with GeoPandas, pandas, PyArrow, DuckDB, and Spark.

Usage:
    python geoparquet_example.py                        # default paths
    python geoparquet_example.py --index-dir data/enga/out \\
        --output-dir data --stride 100

Requires: geopandas, pyarrow, rasterio, numpy, shapely
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyarrow.parquet as pq
import rasterio
import rasterio.features
from shapely.geometry import MultiPolygon, Point, Polygon, shape

# ── Index catalogue ────────────────────────────────────────────────────────────

INDEX_FILES: list[tuple[str, str]] = [
    ("NDVI",            "Normalised Difference Vegetation Index  [-1, 1]"),
    ("NDWI",            "Normalised Difference Water Index       [-1, 1]"),
    ("NDBI",            "Normalised Difference Built-up Index    [-1, 1]"),
    ("NBR",             "Normalised Burn Ratio                   [-1, 1]"),
    ("BSI",             "Bare Soil Index                         [-1, 1]"),
    ("iron_oxide",      "Iron Oxide Ratio                        [>0]"),
    ("clay_mineral",    "Clay Mineral Ratio                      [>0]"),
    ("mining_composite","Mining Composite                        (raw)"),
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _find(directory: Path, stem: str) -> Path | None:
    for ext in (".tif", ".tiff"):
        p = directory / f"{stem}{ext}"
        if p.is_file():
            return p
    return None


def _pixel_to_lonlat(transform, row: int, col: int) -> tuple[float, float]:
    """Convert (row, col) pixel centre to (lon, lat) using an Affine transform."""
    lon = transform.c + (col + 0.5) * transform.a
    lat = transform.f + (row + 0.5) * transform.e
    return lon, lat


# ── Part 1 — regular-grid point samples ───────────────────────────────────────

def build_sample_points(
    index_dir: Path,
    output_path: Path,
    stride: int = 200,
) -> None:
    """
    Sample every index raster on a regular pixel grid (every `stride` pixels)
    and write to GeoParquet.

    Each row in the output is one pixel location with columns:
        geometry (Point), row, col, lon, lat, NDVI, NDWI, …

    stride=200 on an ~19 k × 24 k image yields ~11 k sample points — large
    enough to be analytically interesting, small enough to be fast.
    """
    print(f"\n── Part 1: Regular-grid point samples (stride={stride}) ──────────")

    # Collect available index paths
    layers: list[tuple[str, Path]] = []
    for stem, _ in INDEX_FILES:
        p = _find(index_dir, stem)
        if p is not None:
            layers.append((stem, p))

    if not layers:
        raise FileNotFoundError(f"No index TIFFs found in {index_dir}")
    print(f"Loaded indices: {[l[0] for l in layers]}")

    # Read all arrays + derive grid coordinates from first layer
    ref_path = layers[0][1]
    with rasterio.open(ref_path) as src:
        transform = src.transform
        crs       = src.crs.to_epsg() or src.crs.to_wkt()
        height, width = src.shape

    # Build (row, col) sample grid
    rows = np.arange(0, height, stride)
    cols = np.arange(0, width,  stride)
    grid_cols, grid_rows = np.meshgrid(cols, rows)
    grid_rows = grid_rows.ravel()
    grid_cols = grid_cols.ravel()
    n = len(grid_rows)
    print(f"Sample points  : {n:,}  ({len(rows)} rows × {len(cols)} cols)")

    # Vectorised pixel → lon/lat
    lons = transform.c + (grid_cols + 0.5) * transform.a
    lats = transform.f + (grid_rows + 0.5) * transform.e

    records: dict[str, np.ndarray] = {
        "row": grid_rows.astype(np.int32),
        "col": grid_cols.astype(np.int32),
        "lon": lons.astype(np.float64),
        "lat": lats.astype(np.float64),
    }

    # Sample each index at grid positions
    for name, path in layers:
        with rasterio.open(path) as src:
            arr = src.read(1)          # float32 single-band
        values = arr[grid_rows, grid_cols]
        # Replace nodata (0.0 in source) with NaN where the index is exactly 0
        # and surrounding pixels are all NaN — conservative, keeps true zeros.
        records[name] = values.astype(np.float32)

    # Build GeoDataFrame
    geometries = gpd.array.from_shapely(
        np.array([Point(lon, lat) for lon, lat in zip(lons, lats)])
    )
    gdf = gpd.GeoDataFrame(records, geometry=geometries, crs=f"EPSG:{crs}"
                           if isinstance(crs, int) else crs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(output_path, index=False)
    print(f"Written → {output_path}  ({output_path.stat().st_size / 1024:.1f} KB)")

    # ── Demonstrate reading back with a DuckDB-style query via PyArrow ─────────
    print("\nRead-back demo (PyArrow):")
    tbl = pq.read_table(output_path, columns=["lon", "lat", "NDVI", "NDWI"])
    print(f"  Rows: {len(tbl):,}")

    import pyarrow.compute as pc
    ndvi_col = tbl.column("NDVI").to_pylist()
    valid    = [v for v in ndvi_col if v is not None and not (v != v)]
    print(f"  NDVI — mean: {np.mean(valid):.4f}  "
          f"min: {np.min(valid):.4f}  max: {np.max(valid):.4f}")

    return gdf


# ── Part 2 — vectorised NDVI threshold polygons ────────────────────────────────

def build_hotspot_polygons(
    index_dir: Path,
    output_path: Path,
    high_thresh: float =  0.4,
    low_thresh:  float = -0.05,
    min_pixels:  int   = 50,
) -> None:
    """
    Threshold NDVI to produce two classes of "hotspot" polygons:

        class 1  NDVI > high_thresh  → dense vegetation
        class -1 NDVI < low_thresh   → bare soil / disturbed ground

    Uses rasterio.features.shapes (GDAL polygonise) to vectorise connected
    regions, then filters out tiny patches by minimum pixel count.

    The result is written as GeoParquet with columns:
        geometry (Polygon/MultiPolygon), class_id, class_label,
        pixel_count, area_deg2, ndvi_mean
    """
    print(f"\n── Part 2: NDVI hotspot polygons ─────────────────────────────────")

    ndvi_path = _find(index_dir, "NDVI")
    if ndvi_path is None:
        raise FileNotFoundError(f"NDVI.tif not found in {index_dir}")

    with rasterio.open(ndvi_path) as src:
        ndvi      = src.read(1)
        transform = src.transform
        crs_str   = src.crs.to_epsg()
        nodata    = src.nodata

    # Build binary masks
    valid = ~np.isnan(ndvi)
    if nodata is not None:
        valid &= (ndvi != nodata)

    high_mask = valid & (ndvi >  high_thresh)
    low_mask  = valid & (ndvi <  low_thresh)

    classes = [
        (high_mask,  1, f"Dense vegetation (NDVI > {high_thresh})"),
        (low_mask,  -1, f"Bare/disturbed   (NDVI < {low_thresh})"),
    ]

    rows: list[dict] = []
    for mask, class_id, label in classes:
        if mask.sum() == 0:
            print(f"  No pixels for class {class_id} ({label})")
            continue

        # polygonise: yields (geometry_dict, value) pairs where value=1 inside mask
        shapes = list(rasterio.features.shapes(
            mask.astype(np.uint8),
            mask=mask,
            transform=transform,
        ))

        print(f"  Class {class_id:+d} ({label}): {len(shapes):,} raw polygons")

        for geom_dict, _ in shapes:
            poly = shape(geom_dict)
            # Rough pixel count: area / pixel_area
            pixel_area = abs(transform.a * transform.e)
            px_count   = int(poly.area / pixel_area)
            if px_count < min_pixels:
                continue

            # Sample NDVI values inside the bounding box to compute mean
            r0 = int((poly.bounds[3] - transform.f) / transform.e)
            r1 = int((poly.bounds[1] - transform.f) / transform.e) + 1
            c0 = int((poly.bounds[0] - transform.c) / transform.a)
            c1 = int((poly.bounds[2] - transform.c) / transform.a) + 1
            r0, r1 = sorted([max(0, r0), min(ndvi.shape[0], r1)])
            c0, c1 = sorted([max(0, c0), min(ndvi.shape[1], c1)])
            patch      = ndvi[r0:r1, c0:c1]
            patch_mask = mask[r0:r1, c0:c1]
            ndvi_mean  = float(patch[patch_mask].mean()) if patch_mask.any() else float("nan")

            rows.append({
                "geometry":    poly,
                "class_id":    class_id,
                "class_label": label,
                "pixel_count": px_count,
                "area_deg2":   float(poly.area),
                "ndvi_mean":   round(ndvi_mean, 6),
            })

    if not rows:
        print("  No hotspot polygons survived the minimum-pixel filter.")
        return

    gdf = gpd.GeoDataFrame(rows, crs=f"EPSG:{crs_str}" if crs_str else None)
    gdf = gdf.sort_values("pixel_count", ascending=False).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(output_path, index=False)
    size_kb = output_path.stat().st_size / 1024
    print(f"  Kept {len(gdf):,} hotspot polygons → {output_path}  ({size_kb:.1f} KB)")

    # Summary by class
    for cid, grp in gdf.groupby("class_id"):
        label = grp["class_label"].iloc[0]
        print(f"  class {cid:+d}  {len(grp):4d} polygons  "
              f"largest={grp['pixel_count'].max():,} px  "
              f"NDVI mean={grp['ndvi_mean'].mean():.4f}   {label}")


# ── Part 3 — quick analytics on the parquet files ──────────────────────────────

def analytics_demo(samples_path: Path, hotspots_path: Path) -> None:
    """
    Demonstrate some common GeoParquet read patterns using GeoPandas.
    """
    print("\n── Part 3: Analytics demo ─────────────────────────────────────────")

    # 3a. Load samples and compute a vegetation / water ratio per lat band
    if samples_path.is_file():
        gdf = gpd.read_parquet(samples_path)
        print(f"Samples GDF: {len(gdf):,} rows, CRS={gdf.crs}")

        # Bin by latitude (0.05° bands ≈ ~5 km)
        gdf["lat_bin"] = (gdf["lat"] // 0.05 * 0.05).round(2)
        if "NDVI" in gdf.columns and "NDWI" in gdf.columns:
            summary = (
                gdf.groupby("lat_bin")[["NDVI", "NDWI"]]
                .mean()
                .dropna()
                .sort_index()
            )
            print("\n  Mean NDVI / NDWI by 0.05° latitude band (sample):")
            print(summary.head(8).to_string())

    # 3b. Spatial filter: restrict to a bounding box around Porgera mine area
    #     (approx 143.05 – 143.25 E, 5.40 – 5.60 S)
    if samples_path.is_file():
        from shapely.geometry import box
        aoi = box(143.05, -5.60, 143.25, -5.40)
        mine_area = gdf[gdf.geometry.within(aoi)]
        print(f"\n  Points in Porgera AOI: {len(mine_area):,}")
        if len(mine_area) and "NDVI" in mine_area.columns:
            print(f"  AOI NDVI mean: {mine_area['NDVI'].mean():.4f}")
            print(f"  AOI BSI  mean: {mine_area['BSI'].mean():.4f}"
                  if "BSI" in mine_area.columns else "")

    # 3c. Hotspot top-5
    if hotspots_path.is_file():
        hdf = gpd.read_parquet(hotspots_path)
        print(f"\n  Hotspot GDF: {len(hdf):,} polygons, CRS={hdf.crs}")
        top5 = hdf.nlargest(5, "pixel_count")[
            ["class_label", "pixel_count", "ndvi_mean"]
        ]
        print("\n  Top-5 hotspot polygons by pixel count:")
        print(top5.to_string(index=False))


# ── CLI ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-dir",  type=Path, default=Path("data/enga/out"),
                        help="Directory containing index GeoTIFFs")
    parser.add_argument("--output-dir", type=Path, default=Path("data"),
                        help="Output directory for GeoParquet files")
    parser.add_argument("--stride",     type=int,  default=200,
                        help="Pixel stride for point sampling (default: 200)")
    parser.add_argument("--high-ndvi",  type=float, default=0.4,
                        help="NDVI threshold for 'dense vegetation' class")
    parser.add_argument("--low-ndvi",   type=float, default=-0.05,
                        help="NDVI threshold for 'bare/disturbed' class")
    parser.add_argument("--min-pixels", type=int,   default=50,
                        help="Minimum pixel count to keep a hotspot polygon")
    args = parser.parse_args()

    index_dir  = args.index_dir.resolve()
    output_dir = args.output_dir
    samples_p  = output_dir / "enga_samples.parquet"
    hotspots_p = output_dir / "enga_hotspots.parquet"

    build_sample_points(index_dir, samples_p,  stride=args.stride)
    build_hotspot_polygons(index_dir, hotspots_p,
                           high_thresh=args.high_ndvi,
                           low_thresh=args.low_ndvi,
                           min_pixels=args.min_pixels)
    analytics_demo(samples_p, hotspots_p)


if __name__ == "__main__":
    main()

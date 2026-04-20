#!/usr/bin/env python3
"""
Zarr Example — Sentinel-2 Band Cube for Enga Province, PNG
===========================================================
Reads individual per-band GeoTIFFs and packs them into a single Zarr v2 store
on disk.  The resulting store is structured as:

    enga.zarr/
      bands/           # (band, y, x) uint16 array — raw DN values
      indices/         # (index, y, x) float32 array — pre-computed indices
      attrs            # CRS, transform, band names, nodata, …

Why Zarr?
  • Cloud-optimised chunked access — read any spatial window without loading
    the full raster into memory.
  • Lossless compression (Blosc/LZ4) baked in at the chunk level.
  • Easy multi-band stacking without GDAL VRT or memory duplication.
  • Direct NumPy/Dask compatibility for downstream ML or analysis pipelines.

Usage:
    python zarr_example.py                    # default paths
    python zarr_example.py --input data/enga --output data/enga.zarr

Requires: zarr, rasterio, numpy
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
import zarr
from zarr.storage import DirectoryStore

# ── Band catalogue ─────────────────────────────────────────────────────────────

BANDS: list[tuple[str, str]] = [
    ("B02", "Blue (490 nm)"),
    ("B03", "Green (560 nm)"),
    ("B04", "Red (665 nm)"),
    ("B05", "Red Edge 1 (705 nm)"),
    ("B06", "Red Edge 2 (740 nm)"),
    ("B07", "Red Edge 3 (783 nm)"),
    ("B08", "NIR Broad (842 nm)"),
    ("B8A", "NIR Narrow (865 nm)"),
    ("B11", "SWIR 1 (1610 nm)"),
    ("B12", "SWIR 2 (2190 nm)"),
]

INDICES: list[tuple[str, str]] = [
    ("NDVI",            "Normalised Difference Vegetation Index"),
    ("NDWI",            "Normalised Difference Water Index"),
    ("NDBI",            "Normalised Difference Built-up Index"),
    ("NBR",             "Normalised Burn Ratio"),
    ("BSI",             "Bare Soil Index"),
    ("iron_oxide",      "Iron Oxide Ratio"),
    ("clay_mineral",    "Clay Mineral Ratio"),
    ("mining_composite","Mining Composite"),
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _find(directory: Path, stem: str) -> Path | None:
    for ext in (".tif", ".tiff", ".jp2"):
        p = directory / f"{stem}{ext}"
        if p.is_file():
            return p
    return None


def _open_meta(path: Path) -> tuple[dict, tuple[int, int]]:
    with rasterio.open(path) as src:
        meta = {
            "crs":       src.crs.to_wkt(),
            "transform": list(src.transform),  # affine 6-tuple: a,b,c,d,e,f
            "nodata":    src.nodata,
            "width":     src.width,
            "height":    src.height,
        }
        return meta, src.shape


def _read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


# ── Core routine ───────────────────────────────────────────────────────────────

def build_zarr_store(
    input_dir: Path,
    index_dir: Path,
    output_path: Path,
    chunks: tuple[int, int] = (512, 512),
    compressor: zarr.Blosc | None = None,
) -> None:
    if compressor is None:
        compressor = zarr.Blosc(cname="lz4", clevel=5, shuffle=zarr.Blosc.SHUFFLE)

    # ── Collect available bands ────────────────────────────────────────────────
    available_bands: list[tuple[str, str, Path]] = []
    for stem, desc in BANDS:
        p = _find(input_dir, stem)
        if p is not None:
            available_bands.append((stem, desc, p))

    if not available_bands:
        raise FileNotFoundError(f"No S2 band files found in {input_dir}")

    # ── Collect available index rasters ────────────────────────────────────────
    available_indices: list[tuple[str, str, Path]] = []
    for stem, desc in INDICES:
        p = _find(index_dir, stem)
        if p is not None:
            available_indices.append((stem, desc, p))

    # ── Read spatial metadata from first band ──────────────────────────────────
    meta, (height, width) = _open_meta(available_bands[0][2])
    print(f"Grid  : {height} rows × {width} cols")
    print(f"CRS   : {meta['crs'][:60]}…")
    print(f"Chunks: {chunks}")

    # ── Open / create the Zarr store ──────────────────────────────────────────
    store = DirectoryStore(str(output_path))
    root  = zarr.open_group(store, mode="w")

    # ── bands group ───────────────────────────────────────────────────────────
    n_bands  = len(available_bands)
    band_arr = root.require_dataset(
        "bands",
        shape=(n_bands, height, width),
        chunks=(1, *chunks),        # one chunk per spatial tile per band
        dtype=np.uint16,
        compressor=compressor,
    )
    band_arr.attrs["names"]        = [b[0] for b in available_bands]
    band_arr.attrs["descriptions"] = [b[1] for b in available_bands]
    band_arr.attrs["dim_order"]    = ["band", "y", "x"]
    band_arr.attrs["nodata"]       = meta["nodata"]

    print(f"\nWriting {n_bands} bands …")
    for i, (stem, desc, path) in enumerate(available_bands):
        data = _read(path)
        band_arr[i] = data
        print(f"  [{i:2d}] {stem:4s}  shape={data.shape}  dtype={data.dtype}")

    # ── indices group ─────────────────────────────────────────────────────────
    if available_indices:
        n_idx  = len(available_indices)
        idx_arr = root.require_dataset(
            "indices",
            shape=(n_idx, height, width),
            chunks=(1, *chunks),
            dtype=np.float32,
            compressor=compressor,
        )
        idx_arr.attrs["names"]        = [x[0] for x in available_indices]
        idx_arr.attrs["descriptions"] = [x[1] for x in available_indices]
        idx_arr.attrs["dim_order"]    = ["index", "y", "x"]

        print(f"\nWriting {n_idx} index layers …")
        for i, (stem, desc, path) in enumerate(available_indices):
            data = _read(path)
            idx_arr[i] = data
            vmin, vmax = float(np.nanmin(data)), float(np.nanmax(data))
            print(f"  [{i:2d}] {stem:20s}  min={vmin:.4f}  max={vmax:.4f}")

    # ── Root-level spatial metadata ────────────────────────────────────────────
    root.attrs["crs"]       = meta["crs"]
    root.attrs["transform"] = meta["transform"]
    root.attrs["width"]     = width
    root.attrs["height"]    = height
    root.attrs["source"]    = str(input_dir)
    root.attrs["provider"]  = "Sentinel-2 L2A"
    root.attrs["region"]    = "Enga Province, Papua New Guinea"

    print(f"\nZarr store written → {output_path}")
    print(zarr.open(store).info)


# ── Read-back demo ─────────────────────────────────────────────────────────────

def demo_read(output_path: Path) -> None:
    """Demonstrate common read patterns on the finished store."""
    root = zarr.open(str(output_path), mode="r")
    print("\n── Read-back demo ────────────────────────────────────────")

    # 1. Inspect metadata
    print("Metadata:", json.dumps({k: v for k, v in root.attrs.items()
                                   if k not in ("crs",)}, indent=2))

    # 2. Read a single band by name
    band_names = root["bands"].attrs["names"]
    ndvi_band  = "B08"
    if ndvi_band in band_names:
        idx = band_names.index(ndvi_band)
        tile = root["bands"][idx, :512, :512]   # top-left 512×512 window
        print(f"\nB08 NIR tile [0:512, 0:512]:  mean={tile.mean():.1f}  "
              f"min={tile.min()}  max={tile.max()}")

    # 3. Read NDVI from the indices group — use a mid-scene tile to avoid nodata edges
    if "indices" in root:
        idx_names = root["indices"].attrs["names"]
        if "NDVI" in idx_names:
            i     = idx_names.index("NDVI")
            h, w  = root["indices"].shape[1], root["indices"].shape[2]
            r0    = h // 2 - 256
            c0    = w // 2 - 256
            ndvi  = root["indices"][i, r0:r0+512, c0:c0+512]
            valid = ndvi[~np.isnan(ndvi) & (ndvi != 0)]
            if valid.size:
                print(f"NDVI mid-scene tile [{r0}:{r0+512}, {c0}:{c0+512}]:  "
                      f"mean={valid.mean():.4f}  min={valid.min():.4f}  max={valid.max():.4f}")
            else:
                print("NDVI mid-scene tile: no valid pixels in this window")

    # 4. Show chunk information
    print(f"\nbands  chunks : {root['bands'].chunks}")
    if "indices" in root:
        print(f"indices chunks: {root['indices'].chunks}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",   type=Path, default=Path("data/enga"),
                        help="Directory containing per-band S2 GeoTIFFs")
    parser.add_argument("--indices", type=Path, default=None,
                        help="Directory containing pre-computed index TIFFs "
                             "(default: <input>/out)")
    parser.add_argument("--output",  type=Path, default=Path("data/enga.zarr"),
                        help="Output Zarr store path")
    parser.add_argument("--chunk",   type=int,  default=512,
                        help="Spatial chunk size in pixels (default: 512)")
    args = parser.parse_args()

    input_dir  = args.input.resolve()
    index_dir  = (args.indices or args.input / "out").resolve()
    output     = args.output

    build_zarr_store(input_dir, index_dir, output, chunks=(args.chunk, args.chunk))
    demo_read(output)


if __name__ == "__main__":
    main()

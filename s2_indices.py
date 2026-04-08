#!/usr/bin/env python3
"""
Compute Sentinel-2 spectral indices from per-band GeoTIFFs in a folder.

Expected band files (any one name per band is accepted):
  B2  → B02.tif, B2.tif, b02.tif, ...
  B3  → B03.tif, B3.tif, ...
  B4  → B04.tif, B4.tif, ...
  B8  → B08.tif, B8.tif, ...
  B11 → B11.tif, B11.jp2, ...
  B12 → B12.tif, B12.jp2, ...

Writes one float32 GeoTIFF per index (eight files). Missing input bands yield
a same-grid raster filled with NaN for that index.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import rasterio
from rasterio.transform import Affine


BAND_ALIASES: dict[str, list[str]] = {
    "B2": ["B02", "B2", "b02", "b2"],
    "B3": ["B03", "B3", "b03", "b3"],
    "B4": ["B04", "B4", "b04", "b4"],
    "B8": ["B08", "B8", "b08", "b8"],
    "B11": ["B11", "b11"],
    "B12": ["B12", "b12"],
}

EXTENSIONS = (".tif", ".tiff", ".jp2", ".j2k")


def find_band_raster(directory: Path, canonical: str) -> Path | None:
    """Return path to the first matching raster for a canonical S2 band name."""
    for alias in BAND_ALIASES.get(canonical, [canonical]):
        for ext in EXTENSIONS:
            p = directory / f"{alias}{ext}"
            if p.is_file():
                return p
    return None


def reference_profile_and_shape(directory: Path) -> tuple[dict, tuple[int, int]]:
    """Single-band float32 output profile and (height, width) from any available band."""
    for canonical in ("B2", "B3", "B4", "B8", "B11", "B12"):
        path = find_band_raster(directory, canonical)
        if path is None:
            continue
        with rasterio.open(path) as src:
            if src.count != 1:
                raise ValueError(
                    f"{path} has {src.count} bands; expected a single-band file for reference grid."
                )
            profile = src.profile.copy()
            profile.update(
                count=1,
                dtype=rasterio.float32,
                nodata=None,
                compress="deflate",
                predictor=3,
            )
            return profile, src.shape
    raise FileNotFoundError(f"No S2 band rasters found in {directory}")


def load_aligned_bands(
    directory: Path,
    needed: Iterable[str],
) -> tuple[dict[str, np.ndarray], dict]:
    """
    Load bands as float32 arrays. All must share shape, transform, and CRS.
    Returns (bands_dict, reference_profile_for_single_band_float).
    """
    paths: dict[str, Path] = {}
    missing: list[str] = []
    for name in needed:
        p = find_band_raster(directory, name)
        if p is None:
            missing.append(name)
        else:
            paths[name] = p

    if missing:
        hints = "; ".join(
            f"{m} ({', '.join(BAND_ALIASES.get(m, [m]))})" for m in missing
        )
        raise FileNotFoundError(
            f"Missing band file(s) in {directory}: {', '.join(missing)}. Expected stems: {hints}"
        )

    bands: dict[str, np.ndarray] = {}
    ref_profile: dict | None = None
    ref_shape: tuple[int, int] | None = None
    ref_transform: Affine | None = None
    ref_crs = None

    for name, path in paths.items():
        with rasterio.open(path) as src:
            if src.count != 1:
                raise ValueError(f"{path} has {src.count} bands; expected a single-band file.")
            arr = src.read(1).astype(np.float32, copy=False)
            if ref_profile is None:
                ref_profile = src.profile.copy()
                ref_shape = arr.shape
                ref_transform = src.transform
                ref_crs = src.crs
            else:
                if arr.shape != ref_shape:
                    raise ValueError(
                        f"Shape mismatch: {path} {arr.shape} vs reference {ref_shape}."
                    )
                if src.transform != ref_transform or src.crs != ref_crs:
                    raise ValueError(f"Georeferencing mismatch for {path}.")
        bands[name] = arr

    assert ref_profile is not None
    # Output: single-band float32 GeoTIFF
    out_profile = ref_profile.copy()
    out_profile.update(
        count=1,
        dtype=rasterio.float32,
        nodata=None,
        compress="deflate",
        predictor=3,
    )
    return bands, out_profile


def norm_diff(a: np.ndarray, b: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    """(a - b) / (a + b) with safe denominator."""
    num = a - b
    den = a + b
    out = np.full_like(num, np.nan, dtype=np.float32)
    mask = np.abs(den) > eps
    out[mask] = (num[mask] / den[mask]).astype(np.float32)
    return out


def safe_ratio(num: np.ndarray, den: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    out = np.full_like(num, np.nan, dtype=np.float32)
    mask = np.abs(den) > eps
    out[mask] = (num[mask] / den[mask]).astype(np.float32)
    return out


def write_index(path: Path, data: np.ndarray, profile: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype(np.float32), 1)


def run_indices(
    input_dir: Path,
    output_dir: Path,
    eps: float,
) -> None:
    all_canonical = ("B2", "B3", "B4", "B8", "B11", "B12")
    try:
        placeholder_profile, placeholder_shape = reference_profile_and_shape(input_dir)
    except (FileNotFoundError, ValueError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    available = [b for b in all_canonical if find_band_raster(input_dir, b) is not None]
    print(f"Found bands: {', '.join(available)}")

    specs: list[tuple[str, tuple[str, ...], Callable[[dict[str, np.ndarray]], np.ndarray]]] = [
        (
            "BSI",
            ("B11", "B4", "B8", "B2"),
            lambda z: norm_diff(z["B11"] + z["B4"], z["B8"] + z["B2"], eps),
        ),
        ("NDBI", ("B11", "B8"), lambda z: norm_diff(z["B11"], z["B8"], eps)),
        ("NDVI", ("B8", "B4"), lambda z: norm_diff(z["B8"], z["B4"], eps)),
        ("NBR", ("B8", "B12"), lambda z: norm_diff(z["B8"], z["B12"], eps)),
        ("NDWI", ("B3", "B8"), lambda z: norm_diff(z["B3"], z["B8"], eps)),
        ("iron_oxide", ("B4", "B2"), lambda z: safe_ratio(z["B4"], z["B2"], eps)),
        ("clay_mineral", ("B11", "B12"), lambda z: safe_ratio(z["B11"], z["B12"], eps)),
        (
            "mining_composite",
            ("B11", "B12", "B8"),
            lambda z: ((z["B11"] + z["B12"]) * 0.5 - z["B8"]).astype(np.float32),
        ),
    ]

    for short_name, required, compute in specs:
        out_path = output_dir / f"{short_name}.tif"
        if not set(required).issubset(set(available)):
            need = ", ".join(sorted(set(required) - set(available)))
            data = np.full(placeholder_shape, np.nan, dtype=np.float32)
            write_index(out_path, data, placeholder_profile)
            print(f"Wrote {out_path} (NaN placeholder; missing {need})")
            continue
        try:
            bands, profile = load_aligned_bands(input_dir, required)
        except (FileNotFoundError, ValueError) as e:
            data = np.full(placeholder_shape, np.nan, dtype=np.float32)
            write_index(out_path, data, placeholder_profile)
            print(f"Wrote {out_path} (NaN placeholder; {e})")
            continue
        result = compute(bands)
        write_index(out_path, result, profile)
        print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/enga"),
        help="Folder containing per-band S2 rasters (default: data/enga)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output folder for index GeoTIFFs (default: <input-dir>/indices)",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=1e-10,
        help="Minimum |denominator| for ratio / normalized difference (default: 1e-10)",
    )
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        sys.exit(1)
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else (input_dir / "indices")
    )
    run_indices(input_dir, output_dir, args.eps)


if __name__ == "__main__":
    main()

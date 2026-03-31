import os
import requests
from pyrosm import OSM
import geopandas as gpd


# ---------------------------
# CONFIG
# ---------------------------
pbf_url = "https://download.geofabrik.de/australia-oceania/papua-new-guinea-latest.osm.pbf"
pbf_file = "data.osm.pbf"
output_geojson = "roads.geojson"

area = gpd.read_file("geojson/enga.geojson")


# ---------------------------
# STEP 1: Download PBF
# ---------------------------
def download_pbf(url, filename):
    if os.path.exists(filename):
        print("PBF already exists, skipping download.")
        return

    print("Downloading PBF...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print("Download complete.")

# ---------------------------
# STEP 2: Extract roads
# ---------------------------
def extract_roads(pbf_path):
    print("Loading OSM data...")
    osm = OSM(pbf_path)

    print("Extracting road network...")
    roads = osm.get_network(network_type="driving")

    return roads

# ---------------------------
# STEP 3: Save to GeoJSON
# ---------------------------
def save_geojson(gdf, output_path):
    print("Saving GeoJSON...")
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"Saved to {output_path}")

# ---------------------------
# MAIN
# ---------------------------
if __name__ == "__main__":
    download_pbf(pbf_url, pbf_file)
    roads_gdf = extract_roads(pbf_file)
    roads_gdf = gpd.clip(roads_gdf, area)
    save_geojson(roads_gdf, output_geojson)
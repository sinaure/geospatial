# Image for running s2_indices.py (Sentinel-2 index GeoTIFFs).
# Build: docker build -t s2-indices .
# Run:   docker run --rm -v /path/to/bands:/data/in:ro -v /path/to/out:/data/out s2-indices

FROM python:3.10-slim-bookworm

WORKDIR /app

# build-essential: pyrobuf (pyrosm) Cython compile. libexpat1: rasterio/GDAL at runtime (libexpat.so.1).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt constraints.txt .
# Constraints apply to build-isolation envs; fixes pyrobuf + setuptools>=81 (dry_run removed).
ENV PIP_CONSTRAINT=/app/constraints.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -c constraints.txt -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY s2_indices.py .

ENTRYPOINT ["python", "/app/s2_indices.py"]
CMD ["--input-dir", "/data/in", "--output-dir", "/data/out"]

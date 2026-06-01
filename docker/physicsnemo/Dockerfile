# syntax=docker/dockerfile:1
#
# PhysicsNeMo-CFD signal source for the two-container demo. Apache-2.0; runs in
# the customer's boundary like the appliance. PhysicsNeMo (torch + any checkpoint)
# lives ONLY here — never in the appliance image, so model licenses stay here.

FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Torch (CPU) + real PhysicsNeMo (Apache-2.0) + a tiny HTTP server. CPU torch
# keeps the demo portable; swap the index-url for a CUDA build on a GPU host.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --no-cache-dir nvidia-physicsnemo flask

WORKDIR /srv
COPY docker/physicsnemo/server.py /srv/server.py
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=24 \
  CMD curl -sf http://127.0.0.1:8000/health || exit 1
CMD ["python", "/srv/server.py"]

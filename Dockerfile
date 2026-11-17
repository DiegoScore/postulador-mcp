# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MCP_TRANSPORT=stdio \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

# Dependencias primero para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install -r requirements.txt

# Usuario sin privilegios (UID configurable para que coincida con tu usuario del host en Linux)
ARG UID=1000
RUN useradd --uid ${UID} --create-home --shell /usr/sbin/nologin mcp

COPY --chown=mcp:mcp postulador/ postulador/
COPY --chown=mcp:mcp server.py .
# data/ y salidas/ se montan como volúmenes; estas copias son el respaldo si no montas nada
COPY --chown=mcp:mcp data/ data/
RUN mkdir -p salidas && chown -R mcp:mcp /app

USER mcp
EXPOSE 8000

CMD ["python", "server.py"]

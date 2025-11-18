# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Traefik API Gateway
# US #83: API Gateway Path Routing
# SPEC-100: Runtime-Agnostic Federation
# SPEC-145: Multi-Runtime Multi-Architecture Container Builds

FROM traefik:v2.10

# Metadata
LABEL maintainer="platform@medhasys.com" \
      version="1.0.0" \
      description="Traefik API Gateway for ninaivalaigal" \
      service="gateway" \
      runtime="apple-container-cli" \
      org.opencontainers.image.source="https://github.com/Arunosaur/ninaivalaigal"

# Copy configuration files
# Static configuration
COPY traefik.yml /etc/traefik/traefik.yml

# Dynamic configuration (routing rules)
# Note: This will be mounted at runtime, but we include a default
COPY dynamic.yml /etc/traefik/dynamic/dynamic.yml

# Create log directory
RUN mkdir -p /var/log/traefik && \
    chmod 755 /var/log/traefik

# Expose ports
# Standard HTTP/HTTPS ports (not subject to runtime offsets per ports.nv.yaml)
EXPOSE 80 443 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD traefik healthcheck --ping || exit 1

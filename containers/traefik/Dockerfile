# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Traefik API Gateway
# US #83: API Gateway Path Routing

FROM traefik:v2.10

# Copy configuration files
COPY traefik.yml /etc/traefik/traefik.yml
COPY dynamic.yml /etc/traefik/dynamic.yml

# Expose ports
EXPOSE 80 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD traefik healthcheck --ping || exit 1

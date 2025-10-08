# Admin Console Dockerfile - Serves internal/staff pages only
FROM node:20-alpine

WORKDIR /app

# Copy ONLY admin/internal pages (SPEC-083 separation)
COPY ../../frontend/admin ./admin

# Install http-server for serving static files
RUN npm install -g http-server

# Expose port
EXPOSE 8102

# Serve the admin directory
CMD ["http-server", "./admin", "-p", "8102", "--cors"]

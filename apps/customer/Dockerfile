# Customer App Dockerfile - Serves customer-facing pages only
FROM node:20-alpine

WORKDIR /app

# Copy ONLY customer-facing pages (SPEC-083 separation)
COPY ../../frontend/customer ./customer

# Install http-server for serving static files
RUN npm install -g http-server

# Expose port
EXPOSE 8101

# Serve the customer directory
CMD ["http-server", "./customer", "-p", "8101", "--cors"]

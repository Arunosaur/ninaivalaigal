# Customer App Dockerfile - Serves React/Vite build (SPEC-083)
FROM node:20-alpine

WORKDIR /app

# Copy ONLY the production build from dist
COPY dist ./dist

# Install serve for serving static files with SPA support
RUN npm install -g serve

# Expose port (internal container port)
EXPOSE 8101

# Serve React build with SPA routing support
# -s: single-page application mode (fallback to index.html)
# -p: listen port
# --no-clipboard: disable clipboard in container
CMD ["serve", "-s", "./dist", "-p", "8101", "--no-clipboard"]

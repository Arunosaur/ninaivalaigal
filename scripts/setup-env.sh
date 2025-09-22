#!/bin/bash
set -euo pipefail

# Setup Environment Variables for ninaivalaigal
# This script creates a .env file with necessary environment variables

echo "🔧 Setting up ninaivalaigal environment variables..."

# Create .env file
cat > .env << 'EOF'
# Database Configuration
NINAIVALAIGAL_DATABASE_URL=postgresql://mem0user:mem0pass@localhost:5432/mem0db  # pragma: allowlist secret
NINAIVALAIGAL_JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# Graph Database Configuration
GRAPH_DB_PASSWORD=graphpass
REDIS_PASSWORD=redispass

# MCP Configuration
PYTHON_PATH=/opt/homebrew/anaconda3/bin/python
MCP_SERVER_PATH=/path/to/your/mcp_server.py
MCP_CODE_REVIEWER_PATH=/path/to/your/mcp_code_reviewer.py
NINAIVALAIGAL_SERVER_URL=http://127.0.0.1:13370

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
EOF

echo "✅ Environment file created at .env"
echo "⚠️  Please update the values in .env with your actual configuration"
echo "🔒 Never commit .env to version control!"

# Generate config files from templates
if [ -f "ninaivalaigal.config.json.template" ]; then
    echo "📝 Generating config files from templates..."
    envsubst < ninaivalaigal.config.json.template > ninaivalaigal.config.json
    envsubst < mcp-client-config.json.template > mcp-client-config.json
    echo "✅ Config files generated"
fi

echo "🎉 Environment setup complete!"

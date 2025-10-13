#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail

# Ninaivalaigal Installation Script for Apple Silicon
# Installs Apple Container CLI, dependencies, and ninaivalaigal stack

VERSION="${VERSION:-latest}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.ninaivalaigal}"
BIN_DIR="${BIN_DIR:-/usr/local/bin}"

echo "🚀 Ninaivalaigal Installation Script"
echo "===================================="
echo "Version: $VERSION"
echo "Install Directory: $INSTALL_DIR"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This installer is designed for macOS (Apple Silicon)"
    echo "   For other platforms, see: https://github.com/Arunosaur/ninaivalaigal"
    exit 1
fi

# Check if running on Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  Warning: This installer is optimized for Apple Silicon (ARM64)"
    echo "   You may experience performance issues on Intel Macs"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install via Homebrew
install_with_brew() {
    local package=$1
    echo "📦 Installing $package via Homebrew..."
    if ! command_exists brew; then
        echo "❌ Homebrew not found. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install "$package"
}

echo "🔍 Checking dependencies..."

# Check and install Apple Container CLI
if ! command_exists container; then
    echo "📦 Installing Apple Container CLI..."
    install_with_brew container
else
    echo "✅ Apple Container CLI already installed"
fi

# Check and install required tools
REQUIRED_TOOLS=("jq" "curl" "git" "make")
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command_exists "$tool"; then
        echo "📦 Installing $tool..."
        install_with_brew "$tool"
    else
        echo "✅ $tool already installed"
    fi
done

# Install PostgreSQL client for database operations
if ! command_exists psql; then
    echo "📦 Installing PostgreSQL client..."
    install_with_brew postgresql
else
    echo "✅ PostgreSQL client already installed"
fi

echo ""
echo "📥 Downloading ninaivalaigal..."

# Create install directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download or clone repository
if [ "$VERSION" = "latest" ]; then
    echo "🔄 Cloning latest version from GitHub..."
    if [ -d ".git" ]; then
        git pull origin main
    else
        git clone https://github.com/Arunosaur/ninaivalaigal.git .
    fi
else
    echo "📦 Downloading version $VERSION..."
    curl -fsSL "https://github.com/Arunosaur/ninaivalaigal/archive/refs/tags/$VERSION.tar.gz" | tar -xz --strip-components=1
fi

echo ""
echo "🔧 Setting up ninaivalaigal..."

# Make scripts executable
chmod +x scripts/*.sh

# Create symlink for easy access
if [ -w "$BIN_DIR" ]; then
    ln -sf "$INSTALL_DIR/scripts/nv-stack-start.sh" "$BIN_DIR/ninaivalaigal"
    echo "✅ Created symlink: ninaivalaigal command available globally"
else
    echo "⚠️  Cannot create global symlink (no write access to $BIN_DIR)"
    echo "   Add to your PATH: export PATH=\"$INSTALL_DIR/scripts:\$PATH\""
fi

# Build required container images
echo ""
echo "🏗️  Building container images..."
echo "   This may take a few minutes on first run..."

# Build PgBouncer image
container build -t nina-pgbouncer:arm64 -f containers/pgbouncer/Dockerfile containers/pgbouncer/

# Build API image (if Dockerfile exists)
if [ -f "Dockerfile" ]; then
    container build -t nina-api:arm64 .
else
    echo "⚠️  API Dockerfile not found. You may need to build it manually."
fi

echo ""
echo "🧪 Testing installation..."

# Test basic functionality
cd "$INSTALL_DIR"
if make health >/dev/null 2>&1; then
    echo "✅ Stack is already running and healthy"
else
    echo "🚀 Starting development stack for testing..."
    if timeout 60 make dev-up; then
        echo "✅ Installation test successful!"
        echo "🛑 Stopping test stack..."
        make dev-down
    else
        echo "⚠️  Installation test failed, but components are installed"
        echo "   You can manually test with: cd $INSTALL_DIR && make dev-up"
    fi
fi

echo ""
echo "✅ Ninaivalaigal installation complete!"
echo ""
echo "📋 Quick Start:"
echo "   cd $INSTALL_DIR"
echo "   make dev-up      # Start development stack"
echo "   make health      # Check health status"
echo "   make dev-down    # Stop stack"
echo ""
echo "🌍 Remote Access:"
echo "   make tunnel-start REMOTE_HOST=your-server.com"
echo "   make deploy-aws KEY_NAME=your-key"
echo "   make deploy-gcp PROJECT_ID=your-project"
echo ""
echo "📚 Documentation:"
echo "   README.md                        # Getting started"
echo "   docs/APPLE_CONTAINER_CLI.md      # Apple Container CLI guide"
echo "   docs/REMOTE_ACCESS_CLOUD.md      # Cloud deployment"
echo "   INSTALL_APPLE_SILICON.md         # Detailed installation"
echo ""
echo "🆘 Support:"
echo "   GitHub Issues: https://github.com/Arunosaur/ninaivalaigal/issues"
echo "   Documentation: https://github.com/Arunosaur/ninaivalaigal/tree/main/docs"
echo ""

# Add to shell profile for easy access
SHELL_PROFILE=""
if [ -n "${ZSH_VERSION:-}" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -n "${BASH_VERSION:-}" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if [ -n "$SHELL_PROFILE" ] && [ -f "$SHELL_PROFILE" ]; then
    if ! grep -q "ninaivalaigal" "$SHELL_PROFILE"; then
        echo ""
        echo "🔧 Adding ninaivalaigal to your shell profile..."
        echo "" >> "$SHELL_PROFILE"
        echo "# Ninaivalaigal" >> "$SHELL_PROFILE"
        echo "export NINAIVALAIGAL_HOME=\"$INSTALL_DIR\"" >> "$SHELL_PROFILE"
        echo "alias nv=\"cd \$NINAIVALAIGAL_HOME\"" >> "$SHELL_PROFILE"
        echo "✅ Added shortcuts to $SHELL_PROFILE"
        echo "   Restart your shell or run: source $SHELL_PROFILE"
        echo "   Then use: nv && make dev-up"
    fi
fi

echo ""
echo "🎉 Welcome to ninaivalaigal! Happy coding! 🚀"

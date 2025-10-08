#!/usr/bin/env bash
set -euo pipefail

# Generate all 9 compose files from template
# 3 runtimes × 3 environments = 9 combinations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TEMPLATE="$PROJECT_ROOT/compose.template.yml"
RUNTIMES=("docker" "colima" "apple")
ENVIRONMENTS=("dev" "stage" "prod")

echo "🔧 Generating compose files from template..."
echo "Template: $TEMPLATE"
echo ""

if [[ ! -f "$TEMPLATE" ]]; then
    echo "❌ Template not found: $TEMPLATE"
    exit 1
fi

generated=0

for runtime in "${RUNTIMES[@]}"; do
    for env in "${ENVIRONMENTS[@]}"; do
        output="$PROJECT_ROOT/compose.${runtime}.${env}.yml"

        # Simply copy template - environment variables will be substituted at runtime
        cp "$TEMPLATE" "$output"

        echo "✓ Generated: compose.${runtime}.${env}.yml"
        ((generated++))
    done
done

echo ""
echo "✅ Generated $generated compose files"
echo ""
echo "📝 Next steps:"
echo "   1. Review environment files in configs/.env.{runtime}.{env}"
echo "   2. Start a stack: ./scripts/nina-stack.sh start docker dev"
echo "   3. Check status: ./scripts/nina-stack.sh status docker dev"

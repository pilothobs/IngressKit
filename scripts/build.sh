#!/bin/bash
set -e

# IngressKit build script for local development

echo "🔨 Building IngressKit Docker images..."

# Build both variants
echo "📦 Building ingresskit-server..."
docker build --target ingresskit-server -t pilothobs/ingresskit:server-local .

echo "📦 Building ingresskit-core..."  
docker build --target ingresskit-core -t pilothobs/ingresskit:core-local .

# Tag latest
docker tag pilothobs/ingresskit:server-local pilothobs/ingresskit:latest

echo "✅ Build complete!"
echo ""
echo "🚀 Usage:"
echo "  Server: docker run -p 8080:8080 pilothobs/ingresskit:latest"
echo "  CLI:    docker run -v \$(pwd):/data pilothobs/ingresskit:core-local --in /data/input.csv --out /data/output.csv --schema contacts"
echo ""
echo "🧪 Test:"
echo "  docker-compose up -d"
echo "  curl http://localhost:8080/ping"
